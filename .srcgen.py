# -*- coding: utf-8 -*-
"""把三张问卷表渲染成可在浏览器里直接查看的源数据页，并拷出原始 xls 供下载。"""
import os, shutil, html
import openpyxl

ROOT = r"F:\LCY\大学生理财"
SRC = os.path.join(ROOT, "_xls")
OUT = os.path.join(ROOT, "assets", "src")
os.makedirs(OUT, exist_ok=True)

MODS = [
    ("m1", "模块一 · 大学生消费状况调查", "模块一_大学生消费状况调查_200人", "壹 · 日常收支觉察"),
    ("m2", "模块二 · 消费不满意与理财痛点调查", "模块二_消费不满意与理财痛点调查_200人", "贰 · 预算从无到有"),
    ("m3", "模块三 · 产品使用后收支变化与感受调查", "模块三_产品使用后收支变化与感受调查_200人", "叁 · 长期规划萌芽"),
]

TPL = u"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<title>{title} · 源文件</title>
<style>
  :root{{--navy:#16233a;--blue:#2f5fd0;--line:#e3e8f0;--ink:#1d2530;}}
  *{{box-sizing:border-box;}}
  body{{margin:0;background:#f3f6fb;color:var(--ink);
    font-family:"Microsoft YaHei","PingFang SC",sans-serif;}}
  header{{background:#0f1d33;color:#fff;padding:22px 34px;}}
  header small{{display:block;font-size:12px;color:#9fb0c9;letter-spacing:.18em;margin-bottom:8px;}}
  header h1{{margin:0;font-size:22px;font-weight:600;letter-spacing:.02em;}}
  header p{{margin:8px 0 0;font-size:13px;color:#c9d6ea;}}
  .bar{{display:flex;align-items:center;gap:14px;flex-wrap:wrap;
    padding:16px 34px;background:#fff;border-bottom:1px solid var(--line);position:sticky;top:0;z-index:5;}}
  .bar .f{{font-size:13px;color:#5d6a7c;}}
  .bar b{{font-size:13px;color:#12306b;}}
  .bar a{{margin-left:auto;text-decoration:none;background:var(--blue);color:#fff;
    padding:9px 18px;border-radius:8px;font-size:13px;}}
  .bar a.ghost{{background:#fff;color:#31415a;border:1px solid var(--line);margin-left:0;}}
  .wrap{{padding:18px 34px 60px;overflow:auto;}}
  table{{border-collapse:collapse;background:#fff;font-size:12.5px;white-space:nowrap;
    box-shadow:0 2px 12px rgba(20,40,80,.06);border-radius:10px;overflow:hidden;}}
  th,td{{padding:8px 12px;border-bottom:1px solid var(--line);text-align:left;}}
  th{{background:#eef3fb;color:#12306b;font-weight:600;position:sticky;top:0;z-index:2;}}
  tbody tr:nth-child(even){{background:#fafbfe;}}
  tbody tr:hover{{background:#eef4ff;}}
  td.num{{text-align:right;font-variant-numeric:tabular-nums;}}
  .cnt{{font-size:12px;color:#8792a5;margin:0 0 10px;}}
</style></head>
<body>
<header>
  <small>账宝 · 源文件</small>
  <h1>{title}</h1>
  <p>{sub}　·　共 {n} 条记录 / {c} 个字段</p>
</header>
<div class="bar">
  <span class="f">原始文件</span><b>{file}.xls</b>
  <a href="{file}.xls" download>下载源文件</a>
  <a class="ghost" href="../data-bg.jpg" hidden></a>
</div>
<div class="wrap">
  <p class="cnt">下表为源文件中全部记录，未作任何删改。</p>
  <table>
    <thead><tr>{head}</tr></thead>
    <tbody>
{rows}
    </tbody>
  </table>
</div>
</body></html>
"""


def cell(v):
    if v is None:
        return ""
    if isinstance(v, float) and abs(v - round(v)) < 1e-9:
        v = int(round(v))
    s = html.escape(str(v))
    return s


def main():
    for key, title, fname, sub in MODS:
        xlsx = os.path.join(SRC, fname + ".xlsx")
        wb = openpyxl.load_workbook(xlsx, read_only=True)
        ws = wb.active
        it = ws.iter_rows(values_only=True)
        head = next(it)
        body = []
        for row in it:
            if row is None or all(v is None for v in row):
                continue
            tds = []
            for v in row:
                cls = ' class="num"' if isinstance(v, (int, float)) else ""
                tds.append("<td%s>%s</td>" % (cls, cell(v)))
            body.append("<tr>" + "".join(tds) + "</tr>")
        hd = "".join("<th>%s</th>" % html.escape(str(h)) for h in head)
        out = TPL.format(title=title, sub=sub, n=len(body), c=len(head),
                         file=key, head=hd, rows="\n".join(body))
        with open(os.path.join(OUT, key + ".html"), "w", encoding="utf-8", newline="\n") as f:
            f.write(out)
        # 原始 xls 拷一份供下载
        src_xls = os.path.join(r"F:\LCY", fname + ".xls")
        if os.path.exists(src_xls):
            shutil.copyfile(src_xls, os.path.join(OUT, key + ".xls"))
        print("ok", key, len(body), "rows")


main()
