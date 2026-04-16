#!/bin/bash
# 博餐 Agent OS 一键安装脚本
set -e

echo "🏮 博餐 Agent OS 安装程序"
echo "================================"

# 检测 Python 版本
PYTHON_CMD=""
for cmd in python3.12 python3.11 python3.10 python3; do
    if command -v $cmd &> /dev/null; then
        ver=$($cmd --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
        if [[ $(echo "$ver >= 3.10" | bc) -eq 1 ]]; then
            PYTHON_CMD=$cmd
            break
        fi
    fi
done

if [ -z "$PYTHON_CMD" ]; then
    echo "❌ 需要 Python 3.10+"
    echo "请先安装 Python: https://www.python.org/downloads/"
    exit 1
fi

echo "✅ 使用 Python: $($PYTHON_CMD --version)"

# 创建虚拟环境
VENV_DIR="${VENV_DIR:-venv}"

if [ ! -d "$VENV_DIR" ]; then
    echo "📦 创建虚拟环境..."
    $PYTHON_CMD -m venv $VENV_DIR
fi

echo "✅ 激活虚拟环境..."
source $VENV_DIR/bin/activate

# 升级 pip
echo "📚 安装依赖..."
pip install --upgrade pip

# 安装项目
pip install -e ".[dev]" 2>/dev/null || pip install -e .

# 安装 Playwright (RPA Claw 需要)
if command -v playwright &> /dev/null; then
    echo "🎭 安装 Playwright 浏览器..."
    playwright install chromium
fi

echo ""
echo "================================"
echo "✅ 安装完成！"
echo ""
echo "快速开始："
echo "  1. 激活环境: source $VENV_DIR/bin/activate"
echo "  2. 查看帮助:  bocan --help"
echo "  3. 初始化:    bocan init"
echo ""
echo "或者直接运行示例："
echo "  bocan chat --task '查看当前排队人数'"
echo ""
