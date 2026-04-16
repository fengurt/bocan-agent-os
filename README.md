# 🏮 博餐 Agent OS

> 餐饮智能体操作系统 — 让每家餐厅都拥有自己的 AI 店长

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 核心定位

**博餐 Agent OS** 是一套面向餐饮行业的 AI Agent 操作系统。不是给每家店写爬虫，而是构建：

```
自然语言指令 → Agent 大脑 → 标准 Skill 总线 → 多模态 Claw → 各平台 API/抓包/RPA/IoT
```

## 五大架构

```
┌─────────────────────────────────────────────────────────────┐
│  ① 多模态交互层  (语音/微信/美团私信/大众点评)              │
├─────────────────────────────────────────────────────────────┤
│  ② 大脑中枢层     Intent Planner + Short/Long Memory       │
├─────────────────────────────────────────────────────────────┤
│  ③ 技能总线层     Skill Hub (标准化接口)                   │
│     └─ queue_skill / inventory_skill / coupon_skill      │
├─────────────────────────────────────────────────────────────┤
│  ④ 抓手调度层     Claw Router                            │
│     ├─ API Claw (白盒)   美团开放平台                     │
│     ├─ Protocol Hook (灰盒)  抓包逆向 App 接口            │
│     ├─ Web RPA (黑盒)     Playwright 模拟操作              │
│     └─ IoT Vision (物理)  摄像头/VLM 判翻台               │
├─────────────────────────────────────────────────────────────┤
│  ⑤ 安全基建层     Identity Vault (凭证加密+自动刷新)       │
└─────────────────────────────────────────────────────────────┘
```

## 核心概念

### Skill（技能）
标准化的技能模块，通过统一接口调用：

```python
from bocan.skills.meituan_queue import MeituanQueueSkill

skill = MeituanQueueSkill()
result = await skill.execute(claw, {"action": "get_queue", "shop_id": "123"})
# → {"wait_count": 8, "avg_wait_min": 35}
```

### Claw（抓手）
对接不同平台的执行器，自动路由：

```python
# Agent 根据 manifest 配置自动选择正确的 Claw
claw = claw_router.route("meituan_queue")  # → MeituanQueueClaw
result = await claw.execute("get_queue_status", {"shop_id": "..."})
```

### HITL（人在环）
三级安全机制：

| 等级 | 操作 | 示例 | 处理方式 |
|------|------|------|---------|
| 🟢 GREEN | 读操作 | 查询排队数 | Agent 全自动 |
| 🟡 YELLOW | 软写 | 发优惠券 | 自动执行 + 日志 |
| 🔴 RED | 硬写 | 退单/改价 | 只生成草稿，等待审批 |

## 快速开始

### 安装

```bash
pip install bocan-agent-os
```

### 初始化门店

```bash
bocan init
# 按向导填写：门店名、人设、平台接入情况
```

### 启动对话

```bash
bocan run --manifest ./tenant_manifest.json
```

示例对话：
```
你: 帮我看看现在排队多少人
AI店长: 当前等位8桌，预计等候35分钟

你: 有顾客等了40分钟了，发张优惠券挽留一下
AI店长: ✅ 已自动发放10元代金券给顾客

你: 把三鲜水饺下架
AI店长: ⏳ 操作需要审批：

【待审批操作草稿】
动作: 将"三鲜水饺"标记为售罄
影响: 美团、饿了么、门店POS同步更新
建议: [同意] [修改] [取消]
```

## 项目结构

```
bocan-agent-os/
├── bocan/
│   ├── core/          # 核心类型、Agent基类
│   ├── brain/         # 意图规划、记忆系统
│   ├── skill_hub/    # 技能总线
│   ├── claw/         # 抓手路由层
│   ├── infra/         # 凭证库、安全基建
│   └── skills/        # 平台Skills实现
│       └── meituan_queue.py
├── examples/          # 使用示例
└── tests/             # 测试
```

## 开发自己的 Skill

```python
from bocan.skill_hub.hub import BaseSkill, SkillHub
from bocan.core.types import SkillResult

class MyRestaurantSkill(BaseSkill):
    name = "my_skill"
    description = "我的自定义技能"
    required_claws = ["my_claw"]
    
    async def execute(self, claw, context: dict) -> SkillResult:
        result = await claw.execute("my_action", context)
        return SkillResult(
            skill_name=self.name,
            success=True,
            data=result
        )

# 注册到总线
hub = SkillHub()
hub.register(MyRestaurantSkill())
```

## 合规声明

⚠️ 本项目仅供技术研究学习。逆向工程和抓包可能违反平台服务协议，使用者需自行承担风险。

## License

MIT License
