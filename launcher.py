#!/usr/bin/env python3
"""Cross-platform launcher for the local Serious Game installation."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import signal
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
import webbrowser


ROOT = Path(__file__).resolve().parent
BACKEND = ROOT / "code" / "backend"
WEB = ROOT / "code" / "frontend" / "web"
VENV = ROOT / ".venv"
BACKEND_URL = "http://127.0.0.1:8100"
WEB_URL = "http://127.0.0.1:3001"


class LaunchError(RuntimeError):
    pass


def log(message: str) -> None:
    print(message, flush=True)


def command_path(name: str) -> str:
    value = shutil.which(name)
    if not value:
        raise LaunchError(f"未找到 {name}，请先安装并重新打开启动器。")
    return value


def run(command: list[str], *, cwd: Path) -> None:
    display = subprocess.list2cmdline(command) if os.name == "nt" else " ".join(command)
    log(f"运行：{display}")
    result = subprocess.run(command, cwd=cwd)
    if result.returncode != 0:
        raise LaunchError(f"命令执行失败，退出码 {result.returncode}。")


def node_command() -> tuple[str, str]:
    node = shutil.which("node.exe" if os.name == "nt" else "node") or shutil.which("node")
    if not node:
        raise LaunchError("未找到 Node.js，请先安装 Node.js 22.13 或更高版本。")
    npm = command_path("npm.cmd" if os.name == "nt" else "npm")
    version = subprocess.check_output([node, "--version"], text=True).strip().lstrip("v")
    try:
        major, minor = (int(value) for value in version.split(".")[:2])
    except ValueError as exc:
        raise LaunchError(f"无法识别 Node.js 版本：{version}") from exc
    if (major, minor) < (22, 13):
        raise LaunchError("需要 Node.js 22.13 或更高版本。")
    return node, npm


def npm_process(npm: str) -> list[str]:
    return [npm]


def venv_python() -> Path:
    python = VENV / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    if not python.is_file():
        log("[1/4] 正在创建本地 Python 环境…")
        run([sys.executable, "-m", "venv", str(VENV)], cwd=ROOT)
    if not python.is_file():
        raise LaunchError("无法创建 Python 本地环境，请检查 Python 的 venv 组件。")
    return python


def ensure_python_dependencies(python: Path) -> None:
    probe = [
        str(python),
        "-c",
        "import fastapi, pydantic, uvicorn, pymysql, cryptography",
    ]
    if subprocess.run(probe, cwd=BACKEND).returncode == 0:
        return
    log("正在安装后端依赖，首次运行需要联网…")
    run(
        [
            str(python),
            "-m",
            "pip",
            "install",
            "--disable-pip-version-check",
            "-r",
            str(BACKEND / "requirements.txt"),
        ],
        cwd=BACKEND,
    )


def ensure_web_dependencies(npm: str) -> None:
    required = (
        WEB / "node_modules" / ".bin" / ("vinext.cmd" if os.name == "nt" else "vinext"),
        WEB / "node_modules" / "next" / "package.json",
        WEB / "node_modules" / "react" / "package.json",
        WEB / "node_modules" / "react-dom" / "package.json",
    )
    if all(path.exists() for path in required):
        return
    log("正在安装网页依赖，首次运行需要联网…")
    npm = npm_process(npm)
    if (WEB / "package-lock.json").is_file():
        run([*npm, "ci"], cwd=WEB)
    else:
        run([*npm, "install"], cwd=WEB)


def backend_ready() -> bool:
    try:
        with urllib.request.urlopen(f"{BACKEND_URL}/health/live", timeout=3) as response:
            live = json.loads(response.read().decode("utf-8"))
        if (
            live.get("service") != "serious-game-backend"
            or live.get("terminal_protocol_version") != "text-gameplay-v3"
        ):
            return False
        with urllib.request.urlopen(f"{BACKEND_URL}/health/ready", timeout=3) as response:
            value = json.loads(response.read().decode("utf-8"))
        return (
            value.get("status") == "ready"
            and value.get("repository") == "sqlite"
            and value.get("default_package_id") == "pkg_gameplay_v3"
        )
    except (OSError, ValueError, urllib.error.URLError):
        return False


def web_ready() -> bool:
    try:
        with urllib.request.urlopen(WEB_URL, timeout=3) as response:
            return response.status == 200 and "浊流之上" in response.read().decode("utf-8", "ignore")
    except (OSError, urllib.error.URLError):
        return False


def wait_for(check, label: str, timeout: int = 60) -> None:
    limit = time.monotonic() + timeout
    while time.monotonic() < limit:
        if check():
            return
        time.sleep(0.5)
    raise LaunchError(f"{label}未能在 {timeout} 秒内就绪。")


def port_in_use(port: int) -> bool:
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=0.5):
            return True
    except OSError:
        return False


def spawn(command: list[str], *, cwd: Path, env: dict[str, str]) -> subprocess.Popen:
    kwargs: dict = {"cwd": cwd, "env": env}
    if os.name == "nt":
        kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        kwargs["start_new_session"] = True
    return subprocess.Popen(command, **kwargs)


def stop_process(process: subprocess.Popen | None) -> None:
    if process is None or process.poll() is not None:
        return
    if os.name == "nt":
        subprocess.run(
            ["taskkill", "/PID", str(process.pid), "/T", "/F"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
    else:
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass


def launch(python: Path, npm: str, *, open_browser: bool) -> None:
    backend_env = os.environ.copy()
    backend_env.update(
        {
            "PYTHONUTF8": "1",
            "PYTHONIOENCODING": "utf-8",
            "GAME_REPOSITORY": "sqlite",
            "GAME_DATABASE_PATH": "data/serious_game.db",
            "ROLE_LLM_TIMEOUT_SECONDS": "15",
            "ROLE_LLM_MAX_RETRIES": "1",
        }
    )
    processes: list[subprocess.Popen] = []
    try:
        if not backend_ready():
            if port_in_use(8100):
                raise LaunchError("端口 8100 已被其他程序占用，请先关闭旧后端再启动。")
            log("[3/4] 正在启动本地后端…")
            processes.append(
                spawn(
                    [
                        str(python),
                        str(BACKEND / "run_server.py"),
                        "--host",
                        "127.0.0.1",
                        "--port",
                        "8100",
                    ],
                    cwd=BACKEND,
                    env=backend_env,
                )
            )
            wait_for(backend_ready, "后端", 60)
        if not web_ready():
            if port_in_use(3001):
                raise LaunchError("端口 3001 已被其他网站占用，请先关闭旧网页服务再启动。")
            log("[4/4] 正在启动网页客户端…")
            processes.append(
                spawn(
                    [*npm_process(npm), "run", "dev", "--", "--port", "3001"],
                    cwd=WEB,
                    env=os.environ.copy(),
                )
            )
            wait_for(web_ready, "网页客户端", 90)
        log(f"游戏已就绪：{WEB_URL}")
        log("关闭此窗口会结束游戏；游戏存档保存在 code/backend/data/serious_game.db。")
        if open_browser:
            webbrowser.open(WEB_URL)
        while processes:
            for process in processes:
                code = process.poll()
                if code is not None:
                    raise LaunchError(f"游戏服务意外退出，退出码 {code}。")
            time.sleep(1)
    except KeyboardInterrupt:
        log("正在关闭游戏…")
    finally:
        for process in reversed(processes):
            stop_process(process)


def main() -> int:
    parser = argparse.ArgumentParser(description="浊流之上本地启动器")
    parser.add_argument("--check", action="store_true", help="只检查并安装依赖")
    parser.add_argument("--no-browser", action="store_true", help="就绪后不自动打开浏览器")
    args = parser.parse_args()

    try:
        if sys.version_info < (3, 11):
            raise LaunchError("需要 Python 3.11 或更高版本。")
        for path in (BACKEND / "run_server.py", WEB / "package.json"):
            if not path.is_file():
                raise LaunchError("项目文件不完整，请重新下载完整压缩包。")
        _node, npm = node_command()
        python = venv_python()
        log("[2/4] 正在检查本地依赖…")
        ensure_python_dependencies(python)
        ensure_web_dependencies(npm)
        if args.check:
            log("检查通过：Python、Node.js、后端与网页依赖均已就绪。")
            log(f"网页地址：{WEB_URL}")
            return 0
        launch(python, npm, open_browser=not args.no_browser)
        return 0
    except LaunchError as exc:
        print(f"[错误] {exc}", file=sys.stderr, flush=True)
        return 1
    except Exception as exc:
        print(f"[错误] 启动失败：{exc}", file=sys.stderr, flush=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
