#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$ROOT_DIR"

echo "[1/6] 检查 Python..."
if ! command -v python3 >/dev/null 2>&1; then
  echo "未找到 python3，请先安装 Python 3.11+。"
  exit 1
fi

echo "[2/6] 检查 Node.js..."
if ! command -v node >/dev/null 2>&1; then
  echo "未找到 Node.js，请先安装 Node.js 18+。"
  exit 1
fi

echo "[3/6] 创建虚拟环境并安装后端依赖..."
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt

echo "[4/6] 安装前端依赖并构建..."
cd frontend
npm install
npm run build
cd "$ROOT_DIR"

echo "[5/6] 准备环境文件..."
if [ ! -f .env ]; then
  cp .env.example .env
  echo "已生成 .env，可按需修改。"
fi

echo "[6/6] 完成。启动命令："
echo "cd $ROOT_DIR && source .venv/bin/activate && ./start.sh"
echo "默认地址：http://localhost:18790"
