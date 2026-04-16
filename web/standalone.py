"""
Bocan Agent OS Web Dashboard - Standalone Version
模拟真实 Agent 连接 Skills 的演示版本
"""
import os
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import asyncio

app = FastAPI(title="博餐 Agent OS", version="0.1.0")

class ChatReq(BaseModel):
    message: str

# ==========================================
# Demo Data
# ==========================================

STATS = {
    "today_visitors": 127,
    "queue_now": 8,
    "avg_wait_minutes": 25,
    "revenue_today": 4523,
    "ai_actions_today": 23,
    "bad_reviews": 0,
    "active_customers": 15,
}

QUEUE_DATA = [
    {"shop": "城厢古城主题餐厅", "wait_count": 8, "avg_wait": 25},
    {"shop": "金谷园饺子馆(城厢店)", "wait_count": 3, "avg_wait": 10},
]

LOG = [
    {"time": "13:02", "action": "自动发放等位券", "target": "张先生", "status": "✅"},
    {"time": "12:45", "action": "库存同步(美团/饿了么)", "target": "招牌水饺-售罄", "status": "✅"},
    {"time": "12:30", "action": "舆情检查完成", "target": "3平台无异常", "status": "✅"},
    {"time": "11:15", "action": "回复差评(大众点评)", "target": "匿名顾客#4521", "status": "✅"},
    {"time": "10:00", "action": "天气营销推送", "target": "私域客户87人", "status": "✅"},
]

COUNTER = 100

# ==========================================
# Skill Simulators
# ==========================================

def sim_queue(params: dict) -> dict:
    """模拟排队 Skill"""
    return {
        "success": True,
        "data": {
            "level": "green",
            "queue": QUEUE_DATA,
            "total_wait": 8,
            "recommendation": "排队正常，无需干预"
        }
    }

def sim_inventory(params: dict) -> dict:
    """模拟库存同步 Skill"""
    item = params.get("item", "未知商品")
    action = params.get("action", "查询")
    platforms = ["美团", "饿了么", "抖音团购"]
    return {
        "success": True,
        "data": {
            "level": "yellow",
            "action": action,
            "item": item,
            "synced_platforms": platforms,
            "time_taken": "2.3秒",
            "status": f"已在3个平台标记「{item}」为售罄"
        }
    }

def sim_review(params: dict) -> dict:
    """模拟舆情 Skill"""
    return {
        "success": True,
        "data": {
            "level": "yellow",
            "new_bad_reviews": 0,
            "checked_platforms": ["美团", "大众点评", "饿了么"],
            "last_check": datetime.now().strftime("%H:%M:%S"),
            "summary": "✅ 近1小时无新增差评"
        }
    }

def sim_coupon(params: dict) -> dict:
    """模拟优惠券 Skill"""
    scenario = params.get("scenario", "等位超时")
    customer_count = params.get("count", 1)
    return {
        "success": True,
        "data": {
            "level": "yellow",
            "scenario": scenario,
            "coupon_sent": customer_count,
            "coupon_type": "5元凉菜券",
            "time_taken": "1.2秒",
            "status": f"已向{customer_count}位顾客发放优惠券"
        }
    }

def sim_vip(params: dict) -> dict:
    """模拟VIP Skill"""
    return {
        "success": True,
        "data": {
            "level": "green",
            "vip_total": 23,
            "vip_active_month": 18,
            "top_vip": {"name": "张先生", "total_spent": 8888, "level": "钻石"},
            "birthday_today": 0,
            "recommendation": "VIP活跃度良好，本月无需特殊营销"
        }
    }

# ==========================================
# AI Response Router
# ==========================================

def route_to_skill(message: str) -> dict:
    """根据消息路由到对应 Skill"""
    msg = message.lower()
    
    # 排队
    if any(k in msg for k in ["排队", "等位", "多少人", "桌位"]):
        return sim_queue({})
    
    # 库存/估清/下架
    if any(k in msg for k in ["估清", "下架", "售罄", "缺货", "补货", "上架"]):
        item = "虾仁水饺"
        for kw in ["招牌", "三鲜", "韭菜", "玉米"]:
            if kw in msg: item = kw + "水饺"
        return sim_inventory({"item": item, "action": "标记售罄"})
    
    # 舆情/差评
    if any(k in msg for k in ["舆情", "差评", "投诉", "评价", "检查"]):
        return sim_review({})
    
    # 优惠券/营销
    if any(k in msg for k in ["优惠券", "发券", "营销", "折扣", "雨天", "活动"]):
        scenario = "雨天营销"
        if "等位" in msg or "超时" in msg: scenario = "等位超时"
        if "vip" in msg or "会员" in msg: scenario = "VIP专项"
        return sim_coupon({"scenario": scenario, "count": 1})
    
    # VIP
    if any(k in msg for k in ["vip", "会员", "熟客", "老客"]):
        return sim_vip({})
    
    # 营收
    if any(k in msg for k in ["营收", "收入", "销售", "今日"]):
        return {
            "success": True,
            "data": {
                "level": "green",
                "revenue": STATS["revenue_today"],
                "vs_yesterday": "+12%",
                "top_items": [("招牌水饺", 1832), ("凉菜拼盘", 856), ("饺子套餐", 654)],
                "recommendation": "今日营收表现良好，招牌水饺持续热销"
            }
        }
    
    # 未知
    return {
        "success": True,
        "message": f"已收到指令：「{message}」\n\n🤖 博餐 Agent OS 正在学习这个新场景...\n\n当前已支持的指令：排队 / 库存同步 / 舆情 / 优惠券 / VIP / 营收"
    }

# ==========================================
# API Routes
# ==========================================

@app.get("/")
async def root():
    html = open("web/dashboard.html").read() if os.path.exists("web/dashboard.html") else get_dashboard_html()
    return HTMLResponse(content=html)

@app.post("/api/chat")
async def chat(req: ChatReq):
    global COUNTER, LOG, STATS
    COUNTER += 1
    STATS["ai_actions_today"] = COUNTER
    
    # Add to log
    LOG.insert(0, {
        "time": datetime.now().strftime("%H:%M"),
        "action": req.message[:12],
        "target": "-",
        "status": "⏳"
    })
    
    # Route and execute
    result = route_to_skill(req.message)
    
    # Update log status
    LOG[0]["status"] = "✅" if result.get("success") else "❌"
    if len(LOG) > 10: LOG[:] = LOG[:10]
    
    return result

@app.get("/api/stats")
async def stats():
    return STATS

@app.get("/api/queue")
async def queue():
    return {"queue": QUEUE_DATA, "updated_at": datetime.now().isoformat()}

@app.get("/api/log")
async def log():
    return LOG

@app.get("/api/health")
async def health():
    return {
        "status": "healthy",
        "version": "0.1.0",
        "skills": {
            "meituan_queue": "✅ 就绪",
            "inventory_sync": "✅ 就绪",
            "review_defender": "✅ 就绪",
            "coupon_dispatch": "✅ 就绪",
        },
        "claws": {
            "meituan_api": "🔗 已连接",
            "protocol_hook": "🔗 已连接",
            "rpa": "🔗 已连接",
        }
    }

# ==========================================
# Dashboard HTML
# ==========================================

def get_dashboard_html() -> str:
    return """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>博餐 Agent OS - 城厢古城餐厅</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#f5f6fa;color:#2c3e50}
.header{background:linear-gradient(135deg,#e74c3c,#c0392b);color:#fff;padding:20px 30px}
.header h1{font-size:24px}.header .sub{opacity:.9;font-size:13px;margin-top:4px}
.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:15px;padding:20px}
.stat{background:#fff;border-radius:12px;padding:20px;text-align:center;box-shadow:0 2px 8px rgba(0,0,0,.05)}
.stat .v{font-size:30px;font-weight:700;color:#e74c3c}
.stat .l{font-size:12px;color:#7f8c8d;margin-top:4px}
.main{display:grid;grid-template-columns:1fr 360px;gap:20px;padding:0 20px 20px;height:calc(100vh-220px)}
.chat{background:#fff;border-radius:12px;display:flex;flex-direction:column;box-shadow:0 2px 8px rgba(0,0,0,.05);overflow:hidden}
.chat-h{padding:15px 20px;border-bottom:1px solid #eee;font-weight:600;font-size:14px;display:flex;justify-content:space-between;align-items:center}
.badge{background:#e74c3c;color:#fff;font-size:11px;padding:2px 8px;border-radius:10px}
.msgs{fxxlex:1;overflow-y:auto;padding:20px;display:flex;flex-direction:column;gap:10px;max-height:400px}
.msg{max-width:85%;padding:12px 16px;border-radius:16px;font-size:14px;line-height:1.6}
.msg.bot{background:#f8f9fa;align-self:flex-start;border-bottom-left-radius:4px}
.msg.user{background:#e74c3c;color:#fff;align-self:flex-end;border-bottom-right-radius:4px}
.msg.error{background:#fee;color:#c00;border:1px solid #fcc;align-self:flex-start}
.msg.loading{background:#f8f9fa;align-self:flex-start;color:#7f8c8d}
.input-area{padding:15px 20px;border-top:1px solid #eee;display:flex;gap:10px}
.inp{flex:1;padding:12px 16px;border:1px solid #ddd;border-radius:24px;font-size:14px;outline:none}
.inp:focus{border-color:#e74c3c}
.btn{padding:12px 24px;background:#e74c3c;color:#fff;border:none;border-radius:24px;cursor:pointer;font-weight:600}
.btn:hover{background:#c0392b}
.side{display:flex;flex-direction:column;gap:15px;overflow-y:auto}
.panel{background:#fff;border-radius:12px;padding:15px;box-shadow:0 2px 8px rgba(0,0,0,.05)}
.panel h3{font-size:14px;margin-bottom:12px;color:#2c3e50}
.actions{display:grid;grid-template-columns:1fr 1fr;gap:8px}
.act{padding:10px;background:#f8f9fa;border:none;border-radius:8px;font-size:12px;cursor:pointer;transition:all .2s}
.act:hover{background:#e74c3c;color:#fff}
.log-item{display:flex;align-items:center;gap:8px;font-size:12px;padding:6px;background:#f8f9fa;border-radius:6px;margin-bottom:6px}
.log-t{color:#95a5a6;min-width:40px}.log-s{flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.log-r{font-size:14px}
.health{display:grid;grid-template-columns:1fr 1fr;gap:6px;font-size:11px}
.health-item{background:#f8f9fa;padding:8px;border-radius:6px;text-align:center}
@media(max-width:900px){.main{grid-template-columns:1fr}.stats{grid-template-columns:repeat(2,1fr)}}
</style>
</head>
<body>
<div class="header">
  <h1>🏮 博餐 Agent OS</h1>
  <div class="sub">城厢古城主题餐厅 · AI 店长控制台 · v0.1.0</div>
</div>
<div class="stats">
  <div class="stat"><div class="v" id="v1">--</div><div class="l">今日客流</div></div>
  <div class="stat"><div class="v" id="v2">--</div><div class="l">当前排队(桌)</div></div>
  <div class="stat"><div class="v" id="v3">--</div><div class="l">今日营收(¥)</div></div>
  <div class="stat"><div class="v" id="v4">--</div><div class="l">AI执行次数</div></div>
</div>
<div class="main">
  <div class="chat">
    <div class="chat-h">
      💬 AI 店长对话
      <span class="badge" id="status-badge">🟢 在线</span>
    </div>
    <div class="msgs" id="msgs">
      <div class="msg bot">👋 你好！我是博餐 AI 店长。<br><br>🏮 当前模式：演示版本（模拟数据）<br>🚀 真实部署后连接 Skills + Claws<br><br>试试快捷指令：</div>
    </div>
    <div class="input-area">
      <input class="inp" id="inp" placeholder="输入指令：查看排队 / 虾仁水饺估清 / 检查舆情" onkeypress="if(event.key==='Enter')send()">
      <button class="btn" onclick="send()">发送</button>
    </div>
  </div>
  <div class="side">
    <div class="panel">
      <h3>⚡ 快捷指令</h3>
      <div class="actions">
        <button class="act" onclick="q('查看当前排队人数')">📊 排队人数</button>
        <button class="act" onclick="q('查看今日营收')">💰 今日营收</button>
        <button class="act" onclick="q('虾仁水饺估清')">📦 估清下架</button>
        <button class="act" onclick="q('检查最新评价')">🛡️ 检查舆情</button>
        <button class="act" onclick="q('发放雨天外卖券')">🌧️ 雨天营销</button>
        <button class="act" onclick="q('VIP客户情况')">👑 VIP营销</button>
      </div>
    </div>
    <div class="panel">
      <h3>📜 最近操作记录</h3>
      <div id="log"></div>
    </div>
    <div class="panel">
      <h3>🟢 系统状态</h3>
      <div class="health" id="health"></div>
    </div>
  </div>
</div>
<script>
const inp=document.getElementById('inp');
const msgs=document.getElementById('msgs');
function add(html,type){
  const d=document.createElement('div');d.className='msg '+type;d.innerHTML=html;
  msgs.appendChild(d);msgs.scrollTop=msgs.scrollHeight;return d;
}
function q(m){inp.value=m;send()}
async function send(){
  const v=inp.value.trim();if(!v)return;
  add(v,'user');inp.value='';
  const loading=add('⚙️ 处理中...','loading');
  try{
    const r=await fetch('/api/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:v})}).then(r=>r.json());
    loading.remove();
    if(r.success){
      const data=r.data||{};
      if(data.level==='green') add(r.data? JSON.stringify(data,null,2): r.message||'执行完成','bot');
      else if(data.level==='yellow') add('⚠️ '+r.data? JSON.stringify(data,null,2): r.message,'bot');
      else add(r.data? JSON.stringify(data,null,2): r.message,'bot');
    } else add('❌ '+r.message,'error');
  }catch(e){loading.remove();add('❌ 网络错误','error');}
  loadAll();
}
async function loadAll(){loadStats();loadLog();loadHealth();}
async function loadStats(){
  try{const d=await fetch('/api/stats').then(r=>r.json());document.getElementById('v1').textContent=d.today_visitors;document.getElementById('v2').textContent=d.queue_now;document.getElementById('v3').textContent=d.revenue_today;document.getElementById('v4').textContent=d.ai_actions_today;}catch(e){}
}
async function loadLog(){
  try{const d=await fetch('/api/log').then(r=>r.json());document.getElementById('log').innerHTML=d.map(l=>`<div class="log-item"><span class="log-t">${l.time}</span><span class="log-s">${l.action}</span><span class="log-r">${l.status}</span></div>`).join('');}catch(e){}
}
async function loadHealth(){
  try{
    const d=await fetch('/api/health').then(r=>r.json());
    const skills=Object.entries(d.skills||{}).map(([k,v])=>`<div class="health-item">${k}<br><b>${v}</b></div>`).join('');
    const claws=Object.entries(d.claws||{}).map(([k,v])=>`<div class="health-item">${k}<br><b>${v}</b></div>`).join('');
    document.getElementById('health').innerHTML=skills+claws;
  }catch(e){}
}
loadAll();setInterval(loadAll,30000);
</script>
</body>
</html>"""

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
