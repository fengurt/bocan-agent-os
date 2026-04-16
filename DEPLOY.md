# 🚀 博餐 Agent OS - 部署指南

## 一、项目结构

```
bocan-agent-os/
├── bocan/                    # 核心框架
│   ├── brain/               # 大脑层（意图规划+记忆）
│   ├── claw/                 # 抓手层（API/抓包/RPA）
│   ├── core/                 # 核心（Agent/Manifest）
│   ├── infra/                # 基建层（Vault/限流/反爬）
│   ├── skill_hub/           # 技能总线
│   └── skills/              # 技能实现
│       ├── meituan_queue.py      # 🔄 排队管理
│       ├── inventory_sync.py     # 📦 库存同步
│       ├── review_defender.py   # 🛡️ 舆情监控
│       └── coupon_dispatch.py   # 🎫 优惠券
├── web/
│   ├── standalone.py         # Web Dashboard (FastAPI)
│   └── dashboard.html       # 前端页面
├── skills/                   # 外部 Skill 扩展目录
└── pyproject.toml
```

---

## 二、快速安装

```bash
git clone https://github.com/fengurt/bocan-agent-os.git
cd bocan-agent-os
pip install -e .
```

---

## 三、Dashboard 部署

### 方案 A：本地运行
```bash
python web/standalone.py
# 访问 http://localhost:8000
```

### 方案 B：Docker 部署
```bash
docker build -t bocan-agent-os .
docker run -p 8000:8000 bocan-agent-os
```

### 方案 C：Cloudflare Pages（仅前端）
```bash
# 1. Fork/Clone 本仓库
# 2. 登录 Cloudflare Pages
# 3. 连接到 GitHub 仓库
# 4. 构建命令留空，输出目录：web
# 5. 部署！

# 注意：Cloudflare Pages 仅支持静态托管
# Python 后端需部署到其他平台（见下方）
```

### 方案 D：Railway/Render（Python 后端）
```bash
# 1. push 到 GitHub
# 2. Railway.app → New Project → Connect GitHub
# 3. 选择仓库，设置启动命令：
#    uvicorn web.standalone:app --host 0.0.0.0 --port $PORT
# 4. 环境变量：设置 API Keys
# 5. Deploy!
```

### 方案 E：VPS（完整部署）
```bash
# 1. SSH 到服务器
# 2. git clone https://github.com/fengurt/bocan-agent-os.git
# 3. cd bocan-agent-os
# 4. pip install -e .
# 5. uvicorn web.standalone:app --host 0.0.0.0 --port 8000 --reload
```

---

## 四、开发调试

### 安装依赖
```bash
pip install -e ".[dev]"      # 开发依赖
pip install -e ".[anthropic]" # Anthropic 模型支持
```

### 测试 Skills
```python
from bocan.skills.meituan_queue import MeituanQueueSkill
from bocan.skill_hub.base import SkillContext

skill = MeituanQueueSkill()
ctx = SkillContext(tenant_id="demo")
# result = await skill.execute(claw=None, context=ctx)
```

### 创建新 Skill
```python
# 1. 创建文件 bocan/skills/my_skill.py
from bocan.skills.base import BocanBaseSkill

class MySkill(BocanBaseSkill):
    NAME = "my_skill"
    description = "我的自定义技能"
    operation_level = OperationLevel.YELLOW
    
    async def _execute(self, claw, context):
        # 实现业务逻辑
        return {"result": "done"}
```

### 创建新 Claw
```python
# 1. 创建文件 bocan/claw/my_claw.py
from bocan.claw.base import BaseClaw

class MyClaw(BaseClaw):
    name = "my_claw"
    
    async def fetch_data(self, params):
        # 实现抓取逻辑
        return {}
    
    async def write_data(self, params):
        return {}
```

---

## 五、Skill API 参考

### MeituanQueueSkill（美团排队）
```python
action="get_queue"     # 获取排队状态
action="call_next"     # 叫号
action="close_queue"    # 关闭排队
```

### InventorySyncSkill（库存同步）
```python
action="sync_item"      # 同步单个商品
action="sync_batch"     # 批量同步
action="get_stock"      # 查询库存
```

### ReviewDefenderSkill（舆情监控）
```python
action="check_new"      # 检查新评价
action="reply"          # 生成回复
action="compensate"     # 生成补偿方案
```

### CouponDispatchSkill（优惠券）
```python
action="dispatch"      # 发放优惠券
action="dispatch_batch" # 批量发放
action="check_available" # 查询可用券
```

---

## 六、连接真实后端

部署后修改前端 API 地址：
```javascript
const API_BASE = 'https://your-backend.railway.app';
```

或在 `standalone.py` 中修改：
```python
CORS_ORIGINS = ['https://your-frontend.pages.dev']
```

---

## 七、环境变量

| 变量 | 说明 | 示例 |
|------|------|------|
| `PORT` | 服务端口 | `8000` |
| `MEITUAN_TOKEN` | 美团 Token | `Bearer xxx` |
| `CORS_ORIGINS` | 允许的域名 | `*` |

---

## 八、架构说明

### HITL 审批机制
- 🟢 GREEN：自动执行（查数据、读状态）
- 🟡 YELLOW：执行并记录日志（发券、回评）
- 🔴 RED：只生成草稿，需人工审批（退款、退单）
