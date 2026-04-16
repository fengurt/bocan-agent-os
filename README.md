# 🏮 博餐 Agent OS

> 餐饮智能体操作系统 — 让每家餐厅都拥有自己的 AI 店长

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 核心定位

**博餐 Agent OS** 是一套面向餐饮行业的 AI Agent 操作系统。不是给每家店写爬虫，而是构建：

```
自然语言指令 → Agent 大脑 → 标准 Skill 总线 → 多模态 Claw → 各平台 API/抓包/RPA/IoT
```

## 🎯 四大核心 Skill（已实现）

| Skill | 功能 | 状态 |
|-------|------|------|
| 🔄 **meituan_queue** | 美团排队实时监控+叫号 | ✅ 可用 |
| 📦 **inventory_sync** | 全域库存同步（一句话"估清"所有平台） | ✅ 可用 |
| 🛡️ **review_defender** | 舆情监控+黄金5分钟危机公关 | ✅ 可用 |
| 🎫 **coupon_dispatch** | 优惠券引擎（等位/雨天/差评自动发券） | ✅ 可用 |

## 🖥️ Web Dashboard

```bash
# 本地运行
python web/standalone.py
# 访问 http://localhost:8000
```

![Dashboard Preview](https://img.shields.io/badge/Dashboard-红色主题-blue.svg)

## 📦 快速安装

```bash
git clone https://github.com/fengurt/bocan-agent-os.git
cd bocan-agent-os
pip install -e .
```

## 🚀 一键部署

### Docker
```bash
docker build -t bocan-agent-os .
docker run -p 8000:8000 bocan-agent-os
```

### Railway / Render
```bash
# 1. Push to GitHub
# 2. Connect to Railway.app
# 3. Start command: uvicorn web.standalone:app --host 0.0.0.0 --port $PORT
```

### Cloudflare Pages（仅前端）
```bash
# 1. Fork 本仓库
# 2. Cloudflare Pages → 连接到 GitHub
# 3. 构建命令留空，输出目录：web
```

详细部署文档：[DEPLOY.md](DEPLOY.md)

## 🏗️ 五层架构

```
┌─────────────────────────────────────────────────────────────┐
│  ① 多模态交互层  (语音/微信/美团私信/大众点评)              │
├─────────────────────────────────────────────────────────────┤
│  ② 大脑中枢层     Intent Planner + Short/Long Memory       │
├─────────────────────────────────────────────────────────────┤
│  ③ 技能总线层     Skill Hub (标准化接口)                   │
│     └─ queue_skill / inventory_skill / coupon_skill      │
├─────────────────────────────────────────────────────────────┤
│  ④ 抓手调度层     Claw Router                             │
│     ├─ API Claw (白盒)   美团开放平台                     │
│     ├─ Protocol Hook (灰盒)  抓包逆向 App 接口           │
│     ├─ Web RPA (黑盒)     Playwright 模拟操作              │
│     └─ IoT Vision (物理)  摄像头/VLM 判翻台              │
├─────────────────────────────────────────────────────────────┤
│  ⑤ 安全基建层     Identity Vault (凭证加密+自动刷新)      │
└─────────────────────────────────────────────────────────────┘
```

## 🛡️ HITL 审批机制

| 等级 | 操作 | 处理方式 |
|------|------|---------|
| 🟢 GREEN | 查数据、读状态 | Agent 全自动 |
| 🟡 YELLOW | 发券、回评 | Agent 执行 + 日志记录 |
| 🔴 RED | 退款、退单、改价 | 只生成草稿，人工审批 |

## 📁 项目结构

```
bocan-agent-os/
├── bocan/
│   ├── brain/          # 意图规划 + 记忆
│   ├── claw/           # 抓手层
│   ├── core/           # 核心 Agent
│   ├── infra/          # Vault + 限流 + 反爬
│   ├── skill_hub/      # Skill 总线
│   └── skills/         # 四大 Skill 实现
├── web/
│   ├── standalone.py   # Web Dashboard
│   └── dashboard.html  # 前端页面
├── skills/             # 外部 Skill 扩展
├── DEPLOY.md           # 部署指南
└── pyproject.toml
```

## 📚 Skill 开发

```python
from bocan.skills.meituan_queue import MeituanQueueSkill

skill = MeituanQueueSkill()
result = await skill.execute(claw, context)
```

详见 [DEPLOY.md](DEPLOY.md) 的「开发调试」和「Skill API 参考」。

## 📄 License

MIT
