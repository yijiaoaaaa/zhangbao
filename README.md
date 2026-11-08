# 账宝

大学生消费前瞻预测与专属金融服务平台 —— 参赛展示站点。

## 页面

- 封面 `#nav`：樱花照片背景，右上卡片进数据页，右下卡片进计划书页，中间按钮进 AI 工作台。
- 数据页 `#data`：三个模块玻璃卡，点「查看全部」进明细层，每组数据都有条形图与结论；右下角「源文件」打开原始问卷表。
- 计划书页 `#plan`：整份项目计划书，左侧目录随滚动高亮。
- 工作台 `#work`：AI 对话，流式输出。

## AI 对话

前端请求 `POST /api/chat`，服务端实现是 `functions/api/chat.js`（Cloudflare Pages Function）。

环境变量：

| 名称 | 值 | 说明 |
| --- | --- | --- |
| `DEEPSEEK_API_KEY` | 你的 DeepSeek key | 必填，只在服务端读取 |

改完环境变量需要重新部署一次才生效，Pages 不会对旧部署回填变量。

接口不可用时（本地双击 html、或 key 没配），前端会自动退回内置的规则回复，页面不会白屏。

## 本地预览

直接双击 `index.html` 只能看静态部分，对话走兜底回复。要试真接口：

```bash
npx wrangler pages dev .
```

先把 `DEEPSEEK_API_KEY` 写进 `.env`（已被 git 忽略），wrangler 会读取。

## 资料

- `assets/src/m1.html` ~ `m3.html`：三份问卷的可读版，对应 `m1.xls` ~ `m3.xls` 原始文件。
- `.plangen.py` / `.srcgen.py`：计划书页与源数据页的生成脚本，改源文件后重跑即可。

## 部署

推到 `main` 即自动构建，Cloudflare Pages 会同时发布静态资源与 `functions/` 下的函数。
