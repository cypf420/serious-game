# 浊流之上 · 严肃游戏 1.0

本地运行的中文严肃治理游戏。浏览器负责界面，Python 后端负责规则、存档和 AI 接口调用；玩家存档只保存在玩家自己的电脑上。

## 运行环境

- Python 3.11 或更高版本
- Node.js 22.13 或更高版本（随附 npm）
- 可访问所选 OpenAI 兼容模型接口的网络

首次启动会自动创建项目内的 `.venv`、安装后端依赖，并在缺少 `node_modules` 时执行 `npm ci`。后续启动会复用本地依赖。

## 一键启动

### Windows

双击根目录的 `BEGIN.BAT`。脚本会自动：

1. 检查 Python 与 Node.js；
2. 安装缺失依赖；
3. 启动后端和网页；
4. 等待服务就绪并打开浏览器。

仅检查环境、不启动游戏：

```bat
BEGIN.BAT --check
```

### macOS

双击 `BEGIN.command`。如果系统提示没有执行权限，在该文件夹打开终端并运行一次：

```sh
chmod +x BEGIN.command
```

之后的启动方式保持不变。也可以在终端运行：

```sh
./BEGIN.command --check
```

### Linux

```sh
chmod +x BEGIN.sh
./BEGIN.sh
```

启动后访问 <http://127.0.0.1:3001>。保持启动器窗口开启；按 `Ctrl+C` 或关闭该窗口即可停止游戏。

## AI 接口

NPC 对话、审阅和文书生成需要有效的 OpenAI 兼容接口、模型名和 API Key。密钥只保存在当前后端进程内，不写入项目源码；后端重启后，按游戏提示重新配置一次。

API 地址需包含服务商要求的路径，例如 `https://api.qianzhang-ai.cn/v1`。使用 Clash TUN 的 Fake-IP DNS 时，后端会通过 Cloudflare HTTPS DNS 查询该域名的真实公网 IPv4 地址，仍会拒绝内网和保留地址；此兼容模式需要能访问 `cloudflare-dns.com`（连接固定到 `1.1.1.1` 或 `1.0.0.1`）。

## 本地存档

默认 SQLite 存档位置：

```text
code/backend/data/serious_game.db
```

该目录、数据库、日志、依赖、构建缓存和模型密钥均已加入 `.gitignore`，不应提交到 GitHub。

## 手动启动

Windows 后端：

```bat
py -3 code/backend/run_server.py --host 127.0.0.1 --port 8100
```

macOS / Linux 后端：

```sh
python3 code/backend/run_server.py --host 127.0.0.1 --port 8100
```

网页（各平台相同）：

```sh
cd code/frontend/web
npm run dev -- --port 3001
```

## 校验

```sh
cd code/backend
python -m compileall -q src

cd ../frontend/web
npm run typecheck
npm run lint
npm run build
```

后端启动后可访问 `/api/game/package/validation` 检查剧本包结构；当前发布包为 `pkg_gameplay_v3`。
