# -*- coding: utf-8 -*-
"""从项目计划书 docx 生成 #plan 区块的 HTML，并替换 index.html 里的旧区块。"""
import os
import re
import docx

HERE = r"F:\LCY\大学生理财"
DOC = r"F:\LCY\「账宝」项目计划书（公文格式·蓝底封面）.docx"
MAX_P = 99  # 每个二级标题下最多取几段
MAX_REF = 60  # 参考文献章最多保留几条


def esc(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


d = docx.Document(DOC)
blocks = []          # [('h1'|'h2'|'h3'|'lead'|'p', text)]
buf = 0
CAP = re.compile(r"^\s*(表|图)\s*[0-9A-Za-z]*\s*[-\u2013]?\s*\d")
for para in d.paragraphs:
    t = para.text.strip()
    if not t:
        continue
    if "□" in t:
        t = re.sub(r"□(?=\S)", "□ ", t)
    t = re.sub(r"^(附录[A-C])(?=\S)", r"\1 ", t)
    st = para.style.name
    if st.startswith("目录") or st in ("表题", "图题", "插图"):
        continue
    if st == "Heading 1":
        blocks.append(("h1", t))
        buf = -1
    elif st == "Heading 2":
        blocks.append(("h2", t))
        buf = 0
    elif st == "Heading 3":
        blocks.append(("h3", t))
        buf = 0
    else:
        if CAP.match(t):
            continue          # 表题/图题，表格没带过来，直接跳过
        if buf < 0:
            blocks.append(("pre", t))    # 章首段落
        elif buf < MAX_P:
            blocks.append(("p", t))
            buf += 1

# 组织成章节
chapters = []
cur = None
for kind, text in blocks:
    if kind == "h1":
        cur = {"title": text, "pre": [], "secs": []}
        chapters.append(cur)
        buf = -1
    elif cur is None:
        continue
    elif kind == "pre":
        cur["pre"].append(text)
    elif kind == "h2":
        cur["secs"].append({"title": text, "h3": [], "paras": []})
    elif kind == "h3":
        if cur["secs"]:
            cur["secs"][-1]["h3"].append({"title": text, "paras": []})
    elif kind == "p":
        if cur["secs"]:
            sec = cur["secs"][-1]
            if sec["h3"]:
                sec["h3"][-1]["paras"].append(text)
            else:
                sec["paras"].append(text)

IDX = ["ch%d" % (i + 1) for i in range(len(chapters))]

parts = []
parts.append('''<section id="plan" class="view">
  <header class="plan-head">
    <div class="ph-left">
      <div class="ph-kicker">2026 年「工商银行杯」全国大学生金融科技创新大赛</div>
      <h1>「账宝」大学生消费前瞻预测<br>与专属金融服务平台</h1>
      <div class="ph-rule"></div>
      <div class="ph-meta">
        <span><b>参赛院校</b>山东大学</span>
        <span><b>团队名称</b>账宝团队</span>
        <span><b>团队成员</b>刘晨宇 · 刘晓钰 · 梁雨熹 · 马高瑞 · 邓邦辰 · 张亦巍 · 苟金伟 · 张宇峻豪</span>
        <span><b>联系方式</b>18363429057</span>
        <span><b>版本</b>二〇二六年十月</span>
      </div>
    </div>
  </header>
  <button class="float-back" id="backNav2">← 返回封面</button>

  <div class="plan-wrap">
    <aside class="plan-index">
      <div class="pi-title">目录</div>
      <ol>''')

for i, ch in enumerate(chapters):
    parts.append('        <li><a href="#%s" data-ch="%s">%s</a></li>' % (IDX[i], IDX[i], esc(ch["title"])))

parts.append('''      </ol>
      <div class="pi-foot">共 %d 章</div>
    </aside>

    <div class="plan-doc">''' % len(chapters))

for i, ch in enumerate(chapters):
    parts.append('      <section class="chap" id="%s">' % IDX[i])
    parts.append('        <h2>%s</h2>' % esc(ch["title"]))
    is_ref = "参考文献" in ch["title"]
    if ch["pre"]:
        if is_ref:
            for one in ch["pre"][:MAX_REF]:
                parts.append('        <p class="ref">%s</p>' % esc(one))
        else:
            parts.append('        <p class="lead">%s</p>' % esc(ch["pre"][0]))
    for sec in ch["secs"]:
        parts.append('        <h3>%s</h3>' % esc(sec["title"]))
        for p in sec["paras"]:
            parts.append('        <p>%s</p>' % esc(p))
        for sub in sec["h3"]:
            parts.append('        <h4>%s</h4>' % esc(sub["title"]))
            for p in sub["paras"]:
                parts.append('        <p>%s</p>' % esc(p))
    parts.append('      </section>')

parts.append('''    </div>
  </div>

  <footer class="plan-foot">
    <div class="cols">
      <div>
        <div class="fbrand">账宝</div>
        <p>大学生消费前瞻预测与专属金融服务平台</p>
      </div>
      <div><b>产品</b><span>消费罗盘</span><span>景气指数看板</span></div>
      <div><b>团队</b><span>账宝团队</span><span>山东大学</span></div>
      <div><b>联系</b><span>18363429057</span><span>二〇二六年十月</span></div>
    </div>
  </footer>
</section>''')

frag = "\n".join(parts)
open(os.path.join(HERE, "_plan_block.html"), "w", encoding="utf-8").write(frag)

# 替换 index.html 中的旧 plan 区块
p = os.path.join(HERE, "index.html")
html = open(p, encoding="utf-8").read()
start = html.index('<!-- ============ 计划书 ============ -->')
end = html.index('<!-- ============ 工作台（AI 对话） ============ -->')
html = html[:start] + '<!-- ============ 计划书 ============ -->\n' + frag + "\n\n" + html[end:]
open(p, "w", encoding="utf-8", newline="\n").write(html)
print("chapters", len(chapters), "chars", len(frag))
