// Vercel Serverless Function：/api/chat
// 把前端的对话请求转发给 DeepSeek，key 只存在于服务端环境变量里。

const MODEL = process.env.CHAT_MODEL || "deepseek-chat";

const SYSTEM = `你是「账宝」，一个面向大学生的记账与消费管理助手。

说话要求：
- 简体中文，语气平实，像同学聊天，不要客服腔，不要列表和加粗。
- 每次回复控制在三句话以内，先说结论再说理由。
- 用户说了一笔花销，就先确认记下了什么（金额、类别），再顺带给一句本月该项的进度判断。
- 涉及金额时用阿拉伯数字加「元」，不要编造用户没有提供过的数据；需要的话说明这是按已记录数据估算。
- 不提供具体投资建议，不推荐任何金融产品。`;

function buildMessages(history, text) {
  const msgs = [{ role: "system", content: SYSTEM }];
  if (Array.isArray(history)) {
    for (const m of history.slice(-8)) {
      if (!m || typeof m.content !== "string") continue;
      msgs.push({ role: m.role === "user" ? "user" : "assistant", content: m.content.slice(0, 2000) });
    }
  }
  msgs.push({ role: "user", content: String(text || "").slice(0, 2000) });
  return msgs;
}

module.exports = async function handler(req, res) {
  if (req.method === "OPTIONS") {
    res.setHeader("Access-Control-Allow-Origin", "*");
    res.setHeader("Access-Control-Allow-Methods", "POST, OPTIONS");
    res.setHeader("Access-Control-Allow-Headers", "Content-Type");
    return res.status(204).end();
  }
  if (req.method !== "POST") {
    res.status(405).json({ error: "method_not_allowed" });
    return;
  }

  const key = process.env.DEEPSEEK_API_KEY;
  if (!key) {
    res.status(500).json({ error: "missing_key" });
    return;
  }

  let body = req.body;
  if (typeof body === "string") {
    try { body = JSON.parse(body); } catch { body = {}; }
  }
  body = body || {};

  const payload = {
    model: MODEL,
    messages: buildMessages(body.history, body.message),
    stream: true,
    temperature: 0.6,
    max_tokens: 400
  };

  let upstream;
  try {
    upstream = await fetch("https://api.deepseek.com/chat/completions", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${key}`
      },
      body: JSON.stringify(payload)
    });
  } catch (e) {
    res.status(502).json({ error: "upstream_unreachable" });
    return;
  }

  if (!upstream.ok) {
    const detail = await upstream.text().catch(() => "");
    res.status(upstream.status).json({ error: "upstream_error", detail: detail.slice(0, 400) });
    return;
  }

  res.setHeader("Content-Type", "text/event-stream; charset=utf-8");
  res.setHeader("Cache-Control", "no-cache, no-transform");
  res.setHeader("Connection", "keep-alive");
  res.setHeader("X-Accel-Buffering", "no");

  const reader = upstream.body.getReader();
  const decoder = new TextDecoder();
  let buf = "";
  let full = "";

  try {
    for (;;) {
      const { done, value } = await reader.read();
      if (done) break;
      buf += decoder.decode(value, { stream: true });
      const parts = buf.split("\n");
      buf = parts.pop() || "";
      for (const line of parts) {
        const s = line.trim();
        if (!s.startsWith("data:")) continue;
        const data = s.slice(5).trim();
        if (data === "[DONE]") {
          res.write(`data: ${JSON.stringify({ done: true })}\n\n`);
          continue;
        }
        try {
          const j = JSON.parse(data);
          const delta = j.choices?.[0]?.delta?.content;
          if (delta) {
            full += delta;
            res.write(`data: ${JSON.stringify({ delta })}\n\n`);
          }
        } catch { /* 忽略半包 */ }
      }
    }
  } catch {
    /* 客户端断开或上游中断，保持已发送内容 */
  }

  res.write(`data: ${JSON.stringify({ done: true, text: full })}\n\n`);
  res.end();
}
