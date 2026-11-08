// Cloudflare Pages Function：/api/chat
// 路径：functions/api/chat.js → 线上地址 /api/chat
// key 只从环境变量 DEEPSEEK_API_KEY 读取，不写进任何前端文件。

const MODEL = "deepseek-chat";

const SYSTEM = `你是「账宝」，一个面向大学生的记账与消费管理助手。

说话要求：
- 简体中文，语气平实，像同学聊天，不要客服腔，不要列表和加粗。
- 每次回复控制在三句话以内，先说结论再说理由。
- 不要用「记下了」「我记下了」「我认」「我服」「收到」「明白」「好的」「没问题」这类应声词或表态词开头，也不要单独成句。直接把金额和类别说出来，像在念一行账目。
- 一笔花销要写成一个完整的意思：先说类别和金额，再补一句本月这一项的进度或一句提醒。不要只丢一个短语。
- 不要复述用户的原话，不要寒暄，直接给信息。
- 涉及金额时用阿拉伯数字加「元」，不要编造用户没有提供过的数据；需要的话说明这是按已记录数据估算。
- 不提供具体投资建议，不推荐任何金融产品。`;

const CORS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type"
};

function buildMessages(history, text) {
  const msgs = [{ role: "system", content: SYSTEM }];
  if (Array.isArray(history)) {
    for (const m of history.slice(-8)) {
      if (!m || typeof m.content !== "string") continue;
      msgs.push({
        role: m.role === "user" ? "user" : "assistant",
        content: m.content.slice(0, 2000)
      });
    }
  }
  msgs.push({ role: "user", content: String(text || "").slice(0, 2000) });
  return msgs;
}

function sse(obj) {
  return new TextEncoder().encode(`data: ${JSON.stringify(obj)}\n\n`);
}

export async function onRequestOptions() {
  return new Response(null, { status: 204, headers: CORS });
}

export async function onRequestPost(context) {
  const { request, env } = context;

  const key = env.DEEPSEEK_API_KEY;
  if (!key) {
    return new Response(JSON.stringify({ error: "missing_key" }), {
      status: 500,
      headers: { ...CORS, "Content-Type": "application/json; charset=utf-8" }
    });
  }

  let body = {};
  try {
    body = await request.json();
  } catch {
    body = {};
  }

  let upstream;
  try {
    upstream = await fetch("https://api.deepseek.com/chat/completions", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${key}`
      },
      body: JSON.stringify({
        model: MODEL,
        messages: buildMessages(body.history, body.message),
        stream: true,
        temperature: 0.6,
        max_tokens: 400
      })
    });
  } catch (e) {
    return new Response(JSON.stringify({ error: "upstream_unreachable" }), {
      status: 502,
      headers: { ...CORS, "Content-Type": "application/json; charset=utf-8" }
    });
  }

  if (!upstream.ok || !upstream.body) {
    const detail = await upstream.text().catch(() => "");
    return new Response(JSON.stringify({ error: "upstream_error", detail: detail.slice(0, 400) }), {
      status: 502,
      headers: { ...CORS, "Content-Type": "application/json; charset=utf-8" }
    });
  }

  // 把 DeepSeek 的 SSE 转成前端要的 {delta} 格式
  const { readable, writable } = new TransformStream();
  const writer = writable.getWriter();
  const decoder = new TextDecoder();

  (async () => {
    const reader = upstream.body.getReader();
    let buf = "";
    let full = "";
    try {
      for (;;) {
        const { done, value } = await reader.read();
        if (done) break;
        buf += decoder.decode(value, { stream: true });
        const lines = buf.split("\n");
        buf = lines.pop() || "";
        for (const line of lines) {
          const s = line.trim();
          if (!s.startsWith("data:")) continue;
          const data = s.slice(5).trim();
          if (data === "[DONE]") continue;
          try {
            const j = JSON.parse(data);
            const delta = j.choices?.[0]?.delta?.content;
            if (delta) {
              full += delta;
              await writer.write(sse({ delta }));
            }
          } catch {
            /* 忽略半包 */
          }
        }
      }
    } catch {
      /* 上游中断，保留已发送内容 */
    }
    try {
      await writer.write(sse({ done: true, text: full }));
      await writer.close();
    } catch {
      /* 客户端已断开 */
    }
  })();

  return new Response(readable, {
    headers: {
      ...CORS,
      "Content-Type": "text/event-stream; charset=utf-8",
      "Cache-Control": "no-cache, no-transform"
    }
  });
}
