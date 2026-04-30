# Image-Gen-WebUI

一个轻量级本地 Web UI，通过 OpenAI 兼容 API 实现文生图和图生图。服务仅绑定 localhost，图片和凭据不会离开本机（API 调用除外）。

## 工作原理

```
 浏览器 (127.0.0.1:5000)
        │
   ┌────▼─────┐     .env_* 配置文件    ┌──────────────┐
   │  Flask   │◄────────────────────────│  API 服务商   │
   │ (app.py) │     OpenAI SDK          │  (远程)       │
   └────┬─────┘                         └──────────────┘
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
- **多配置文件** — 在 Web UI 中切换不同 API 服务商
- **Model Info 编辑器** — 在浏览器中创建、编辑和切换 `.env_*` 配置
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

首次启动时，应用检测到无配置会自动切换到 **Model Info** 标签页，引导你创建第一个配置。

## 手动启动

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

然后打开：http://127.0.0.1:5000

## 配置

配置通过 `.env_*` 文件管理，可在 Web UI 的 **Model Info** 标签页中编辑。每个文件存储一个 API 服务商的设置：

```ini
provider_name=my_provider
base_url=https://api.example.com/v1
api_key=sk-xxxxxxxxxxxxxxxx
model=openai/gpt-image-2
```

当前激活的配置文件记录在 `.env_current` 中（单行文件，指向活跃的 `.env_*` 文件）。你可以创建多个配置（如 `.env_cherryin`、`.env_openai`）并在界面中切换。

也可以手动创建这些文件：

```bash
echo "provider_name=cherryin"      > .env_cherryin
echo "base_url=https://open.cherryin.net/v1" >> .env_cherryin
echo "api_key=sk-xxx"             >> .env_cherryin
echo "model=openai/gpt-image-2"    >> .env_cherryin
echo ".env_cherryin"               > .env_current
```

所有 `.env_*` 文件和 `.env_current` 均已 git 忽略，**切勿提交或分享**。

## 项目结构

```
Image-Gen-WebUI/
├── app.py                 # Flask Web 服务（主入口）
├── config_manager.py      # 共享配置加载模块
├── test_image_size.py     # 分辨率兼容性快速测试
├── run.sh                 # 一键启动脚本
├── requirements.txt       # Python 依赖
├── templates/
│   └── index.html         # 单页 Web 界面（Jinja2 模板）
├── .env_*                 # API 服务商配置（git 已忽略）
├── .env_current           # 当前激活配置指针（git 已忽略）
├── outputs/               # 生成的图片（git 已忽略）
└── uploads/               # 上传的原图（git 已忽略）
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
| `/api/config` | GET | 获取当前配置状态（key 脱敏） |
| `/api/config/save` | POST | 保存到 `.env_*` 文件 |
| `/api/config/switch` | POST | 切换活跃配置 |
| `/api/config/new` | POST | 创建新的 `.env_*` 文件 |

### `test_image_size.py` — 分辨率兼容性测试

快速检测某个 provider 的模型实际支持哪些图片尺寸。编辑脚本中的 `SIZES_TO_TEST`，取消注释或添加要测试的分辨率，然后运行 `python test_image_size.py`。适用于接入新 API provider 时，在 Web UI 使用前先验证支持的分辨率范围。通过 `config_manager.py` 加载当前配置。

### `config_manager.py` — 共享配置模块

提供 `load_current_config()`、`save_config()`、`switch_env()`、`get_client()` 等函数，所有 Python 脚本共用。

## 依赖

- **Flask**（>=3.0）— Web 框架
- **openai**（>=1.0）— OpenAI SDK，用于 API 通信
- **send2trash**（>=1.8）— 安全删除到系统回收站
- **Pillow** — 验证图片分辨率（可选，test 和 edit 脚本使用）

## 安全性

- 服务仅绑定 **127.0.0.1** — 局域网无法访问
- 已关闭 `debug` 模式 — Werkzeug 调试控制台已禁用
- `.env_*`、`.env_current`、`outputs/`、`uploads/`、`edit/` 均已 git 忽略
- API Key 在 Web UI 中默认脱敏显示（密码框 + Show/Hide 切换）
- 启动时清除代理环境变量，防止请求泄露
- 此项目为**个人本地工具** — 非多用户或网络部署用途
