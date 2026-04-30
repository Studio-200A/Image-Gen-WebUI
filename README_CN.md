# Image-Gen-WebUI

一个轻量级本地 Web UI，通过 OpenAI 兼容 API 实现文生图和图生图。服务仅绑定 localhost，图片和凭据不会离开本机（API 调用除外）。

## 工作原理

```
 浏览器 (127.0.0.1:5000)
        │
   ┌────▼─────┐     credentials.json      ┌──────────────┐
   │  Flask   │◄──────────────────────────│  API 服务商   │
   │ (app.py) │     OpenAI SDK            │  (远程)       │
   └────┬─────┘                           └──────────────┘
        │
   ┌────▼────┐     ┌────────┐
   │ outputs/│     │uploads/│
   └─────────┘     └────────┘
```

1. 用户打开 `http://127.0.0.1:5000`，输入提示词
2. **文生图**：无上传图片 → Flask 调用 `client.images.generate()` 生成图片
3. **图生图**：上传图片 → Flask 调用 `client.images.edit()` 编辑图片
4. API 返回 base64 编码的 PNG → Flask 解码后保存到 `outputs/` 目录
5. 结果页面展示图片，并提供下载和历史图库

## 功能

- 文本生成图片
- 以图改图（上传图片 + 提示词）
- 支持多种分辨率：1024x1024 至 3840x2160
- 画质选择（auto / low / medium / high）
- 历史图库（最近 20 张）
- 大图预览、一键下载
- 删除到回收站（而非永久删除）
- 生成中的加载动画
- 复制提示词

## 快速开始

```bash
./run.sh
```

脚本会自动检测 python3、创建 `.venv` 虚拟环境、安装依赖、启动服务并打开浏览器。

## 手动启动

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

然后打开：http://127.0.0.1:5000

## 配置

在项目根目录创建 `credentials.json`：

```json
{
  "api_key": "你的API密钥",
  "base_url": "https://api.example.com/v1",
  "model": "openai/gpt-image-2"
}
```

此文件已被 git 忽略，**切勿提交或分享**。

## 项目结构

```
Image-Gen-WebUI/
├── app.py                 # Flask Web 服务（主入口）
├── edit_image.py          # 命令行图片编辑脚本
├── test_image_size.py     # 分辨率测试脚本
├── run.sh                 # 一键启动脚本
├── requirements.txt       # Python 依赖
├── templates/
│   └── index.html         # 单页 Web 界面（Jinja2 模板）
├── credentials.json       # API 凭据（git 已忽略）
├── outputs/               # 生成的图片（git 已忽略）
├── uploads/               # 上传的原图（git 已忽略）
└── edit/                  # edit_image.py 输出目录（git 已忽略）
```

## 脚本说明

### `app.py` — Web 界面

主程序，提供 Web 界面并处理所有 API 调用。

| 路由 | 方法 | 说明 |
|------|------|------|
| `/` | GET | 返回 Web 界面 |
| `/` | POST | 生成或编辑图片 |
| `/outputs/<path>` | GET | 提供生成的图片文件 |
| `/delete` | POST | 将图片移入系统回收站 |

### `edit_image.py` — 命令行图生图

命令行工具，读取 `edit/input.png`，用增强画质的提示词调用 API，结果保存到 `edit/` 目录。

### `test_image_size.py` — 分辨率测试

测试 API 支持哪些图片尺寸。编辑脚本中的 `SIZES_TO_TEST` 来修改测试的分辨率列表。

## 依赖

- **Flask**（≥3.0）— Web 框架
- **openai**（≥1.0）— OpenAI SDK，用于 API 通信
- **send2trash**（≥1.8）— 安全删除到系统回收站
- **Pillow** — 验证图片分辨率（可选，test 和 edit 脚本使用）

## 安全性

- 服务仅绑定 **127.0.0.1** — 局域网无法访问
- 已关闭 `debug` 模式 — Werkzeug 调试控制台已禁用
- `credentials.json`、`outputs/`、`uploads/`、`edit/` 均已 git 忽略
- 启动时清除代理环境变量，防止请求泄露
- 此项目为**个人本地工具** — 非多用户或网络部署用途
