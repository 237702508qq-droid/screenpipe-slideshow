# ScreenPipe 产品价值介绍 — 交互式网页演示（HyperFrames Slideshow）

10 页主线 + 2 页分支的《ScreenPipe 产品价值介绍》可交互演示，基于
[HyperFrames](https://github.com/heygen-com/hyperframes) 0.8.41 standalone slideshow harness 构建。
所有依赖（player bundle、GSAP、runtime、字体、图片）均已本地化，**离线可用**。

## 打开方式（重要）

`file://` 直接双击打开会因浏览器 iframe 跨源限制而**降级失效**（Chrome 禁止 file:// 页面读取
file:// iframe），务必通过本地 HTTP 服务器打开：

```bash
cd slideshow
python3 -m http.server 8642 --bind 127.0.0.1
# 或 npm start
```

然后浏览器访问 **http://127.0.0.1:8642/**

> 备选：`npx hyperframes present ./composition`（会打印自己的 URL，直接打开即可）。
> 包装器 index.html 已内置 Present（演讲者）模式按钮——点导航胶囊上的 Present 图标或按 `P`。

## 操作

| 按键 / 操作 | 效果 |
|---|---|
| `→` / `Space` / Next 按钮 | 下一步；在 fragment 页逐步展开内容 |
| `←` / `Backspace` | 上一步 / 从分支返回宿主页 |
| 点击分支卡片**下方的热点胶囊按钮**（⊕，P8、P9 每张卡片各一个） | 进入对应分支页，返回时精确回到原位 |
| `P` / Present 图标 | 演讲者模式（双屏：观众全屏 + 本机备注） |
| 导航胶囊 | 翻页、页码、（静音） |

## 页面结构

| # | 场景 ID | 标题 |
|---|---|---|
| 1 | `p1-cover` | 封面：ScreenPipe — 让 AI 记住你在电脑上做过的一切 |
| 2 | `p2-positioning` | 一句话定位：Record / Rewind / Ask（4 个 fragment） |
| 3 | `p3-find` | 场景 1：找回丢失的信息 |
| 4 | `p4-meeting` | 场景 2：会议自动纪要（2 个 fragment） |
| 5 | `p5-mcp` | 场景 3：一行命令给 AI「开天眼」 |
| 6 | `p6-faq` | FAQ 上：隐私 / 性能 / 磁盘 / 多屏（4 个 fragment） |
| 7 | `p7-compare` | FAQ 下 + 竞品对比表 |
| 8 | `p8-pipes` | Pipes 插件系统（3 张分支卡片 → `pipe-detail`） |
| 9 | `p9-value` | 三大价值理由（3 张分支卡片 → `value-reasons`） |
| 10 | `p10-cta` | 开始使用：下载 / 定价 / 开发者入口 |
| 分支 | `b-pipe` | Pipe 实例详解（从 P8 卡片进入） |
| 分支 | `b-value` | 价值理由详解（从 P9 卡片进入） |

## 交互设计

- **Fragment 逐步展示**：P2 / P4 / P6 / P8 进入后先停在首屏，按 Next 逐个揭示卡片，
  全部展开后再按 Next 翻页（时间轴 seek 驱动，可任意回退）。
- **Hotspot 分支导航**：P8 的三个 Pipe 内置示例、P9 的三大价值理由做成可点击分支卡片
  （悬停有浮起反馈），点击进入分支页，Prev / `←` 弹栈精确回到宿主 fragment。
- **演讲者备注**：每页带中文 presenter notes，Present 模式下可编辑（localStorage 持久化）。

## 文件结构

```
slideshow/
├── index.html               # 入口（standalone harness：player + slideshow 包装器 + 副本 island）
├── composition/
│   └── index.html           # HyperFrames 组合：12 个 scene + JSON island + GSAP 时间线
├── vendor/                  # 本地化依赖（player 已打补丁指向本地 runtime，无 CDN 请求）
│   ├── hyperframes-player.global.js
│   ├── hyperframes-slideshow.global.js
│   ├── hyperframe.runtime.iife.js
│   └── gsap.min.js
├── assets/                  # PIL 生成的产品示意图 + picsum 照片 + 本地 Noto Sans CJK 字体
├── scripts/selfcheck.py     # 自查：island schema / fragment 时间范围 / node --check 等
└── package.json             # npm start / present / check
```

## 校验

```bash
npm run check   # JSON island 双份一致性、sceneId 解析、fragment 落在 [start,end]、
                # island↔JS fragment 一致、内嵌 JS node --check、资产与 vendor 存在性
```

## 制作说明

- hyperframes@0.8.41 本地安装（`--ignore-scripts` 跳过 onnxruntime-node 的 GPU 二进制下载，
  deck 运行不需要它）；player bundle 中硬编码的 CDN runtime URL 已重写为 `../vendor/`。
- 数据口径来自 `../OUTLINE.md`（官网 / GitHub VISION / LICENSE / v2.7.42）。
