"""
Bocan Agent OS - Web Dashboard
FastAPI 后端 + 简洁前端
"""
import os
import asyncio
from datetime import datetime
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from bocan.core.agent import BocanAgent
from bocan.core.manifest import TenantManifest, Persona, POSSystem, QueueSystem

# ==========================================
# Pydantic Models
# ==========================================

class ChatRequest(BaseModel):
    message: str
    tenant_id: Optional[str] = "demo"

class QueueStatusResponse(BaseModel):
    shop: str
    wait_count: int
    avg_wait_minutes: int
    last_updated: str

class OperationResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None
    requires_approval: bool = False
    draft: Optional[str] = None

# ==========================================
# Global State
# ==========================================

agent: Optional[BocanAgent] = None

# Demo tenant manifest (城厢古城主题餐厅)
DEMO_MANIFEST = TenantManifest(
    tenant_id="demo_chengxiang",
    tenant_name="城厢古城主题餐厅",
    location="成都青白江城厢古城",
    persona=Persona.WARM_SISTER,
    persona_greeting="欢迎光临！今天天气真好，来碗热乎的饺子吧~",
    pos_system=POSSystem.MEITUAN,
    queue_system=QueueSystem.MEITUAN_QUEUE,
    has_meituan=True,
    has_ele=True,
    has_douyin=True,
    hall_tables=15,
    private_rooms=4,
    total_seats=120,
    business_hours="10:00-22:00"
)

# ==========================================
# Lifespan
# ==========================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    global agent
    agent = BocanAgent(DEMO_MANIFEST)
    print("🏮 Bocan Agent OS 启动成功")
    yield
    print("👋 Bocan Agent OS 已关闭")

# ==========================================
# FastAPI App
# ==========================================

app = FastAPI(
    title="博餐 Agent OS",
    description="餐饮智能体操作系统 Web Dashboard",
    version="0.1.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# Routes
# ==========================================

@app.get("/", response_class=HTMLResponse)
async def root():
    """Web Dashboard 首页"""
    return get_dashboard_html()

@app.post("/api/chat", response_model=OperationResponse)
async def chat(req: ChatRequest):
    """自然语言对话入口"""
    if not agent:
        raise HTTPException(status_code=500, detail="Agent 未初始化")
    
    from bocan.core.types import Task
    task = Task(id=f"task_{datetime.now().timestamp()}", intent=req.message)
    result = await agent.execute_task(task)
    
    return OperationResponse(
        success=result.success,
        message=result.message,
        data=result.data,
        requires_approval=result.requires_approval,
        draft=result.draft_content
    )

@app.get("/api/queue", response_model=QueueStatusResponse)
async def get_queue():
    """获取排队状态（模拟数据）"""
    return QueueStatusResponse(
        shop="城厢古城主题餐厅",
        wait_count=8,
        avg_wait_minutes=25,
        last_updated=datetime.now().strftime("%H:%M:%S")
    )

@app.get("/api/stats")
async def get_stats():
    """获取实时统计数据"""
    return {
        "today_visitors": 127,
        "today_orders": 89,
        "queue_now": 8,
        "revenue_today": 4523,
        "ai_actions_today": 23,
        "active_customers": 15,
        "bad_reviews_flagged": 0
    }

@app.get("/api/actions/recent")
async def get_recent_actions():
    """最近AI操作记录"""
    return [
        {"time": "09:32", "action": "自动发放等位券", "target": "张先生", "status": "✅"},
        {"time": "09:28", "action": "回复差评", "target": "大众点评#4521", "status": "✅"},
        {"time": "09:15", "action": "库存同步", "target": "美团/饿了么", "status": "✅"},
        {"time": "09:02", "action": "舆情检查", "target": "3平台监控", "status": "✅"},
        {"time": "08:45", "action": "天气营销", "target": "私域客户87人", "status": "✅"},
    ]

# ==========================================
# Dashboard HTML
# ==========================================

def get_dashboard_html() -> str:
    return """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>博餐 Agent OS - 城厢古城主题餐厅</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f5f6fa; 
            color: #2c3e50;
            min-height: 100vh;
        }
        
        /* Header */
        .header {
            background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%);
            color: white;
            padding: 20px 30px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .header h1 { font-size: 24px; font-weight: 600; }
        .header .subtitle { opacity: 0.9; font-size: 14px; margin-top: 4px; }
        
        /* Stats Grid */
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
            gap: 15px;
            padding: 20px;
        }
        .stat-card {
            background: white;
            border-radius: 12px;
            padding: 20px;
            text-align: center;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        }
        .stat-value { font-size: 32px; font-weight: 700; color: #e74c3c; }
        .stat-label { font-size: 12px; color: #7f8c8d; margin-top: 4px; }
        
        /* Main Content */
        .main-content {
            display: grid;
            grid-template-columns: 1fr 380px;
            gap: 20px;
            padding: 0 20px 20px;
            height: calc(100vh - 200px);
        }
        
        @media (max-width: 900px) {
            .main-content { grid-template-columns: 1fr; }
        }
        
        /* Chat Panel */
        .chat-panel {
            background: white;
            border-radius: 12px;
            display: flex;
            flex-direction: column;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        }
        .chat-header {
            padding: 15px 20px;
            border-bottom: 1px solid #eee;
            font-weight: 600;
        }
        .chat-messages {
            flex: 1;
            overflow-y: auto;
            padding: 20px;
            display: flex;
            flex-direction: column;
            gap: 12px;
        }
        .msg {
            max-width: 80%;
            padding: 12px 16px;
            border-radius: 16px;
            font-size: 14px;
            line-height: 1.5;
        }
        .msg.bot {
            background: #f8f9fa;
            align-self: flex-start;
            border-bottom-left-radius: 4px;
        }
        .msg.user {
            background: #e74c3c;
            color: white;
            align-self: flex-end;
            border-bottom-right-radius: 4px;
        }
        .msg.error {
            background: #fee;
            color: #c00;
            border: 1px solid #fcc;
        }
        .msg.approval {
            background: #fff3cd;
            border: 1px solid #ffc;
            border-radius: 8px;
            padding: 15px;
        }
        
        .chat-input-area {
            padding: 15px 20px;
            border-top: 1px solid #eee;
            display: flex;
            gap: 10px;
        }
        .chat-input {
            flex: 1;
            padding: 12px 16px;
            border: 1px solid #ddd;
            border-radius: 24px;
            font-size: 14px;
            outline: none;
        }
        .chat-input:focus { border-color: #e74c3c; }
        .send-btn {
            padding: 12px 24px;
            background: #e74c3c;
            color: white;
            border: none;
            border-radius: 24px;
            cursor: pointer;
            font-weight: 600;
        }
        .send-btn:hover { background: #c0392b; }
        
        /* Side Panel */
        .side-panel {
            display: flex;
            flex-direction: column;
            gap: 15px;
        }
        .panel-card {
            background: white;
            border-radius: 12px;
            padding: 15px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        }
        .panel-title {
            font-size: 14px;
            font-weight: 600;
            margin-bottom: 12px;
            color: #2c3e50;
        }
        
        /* Quick Actions */
        .quick-actions {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 8px;
        }
        .action-btn {
            padding: 10px;
            background: #f8f9fa;
            border: none;
            border-radius: 8px;
            font-size: 12px;
            cursor: pointer;
            transition: all 0.2s;
        }
        .action-btn:hover { background: #e74c3c; color: white; }
        
        /* Activity Log */
        .activity-list { display: flex; flex-direction: column; gap: 8px; }
        .activity-item {
            display: flex;
            align-items: center;
            gap: 10px;
            font-size: 12px;
            padding: 8px;
            background: #f8f9fa;
            border-radius: 6px;
        }
        .activity-time { color: #95a5a6; min-width: 40px; }
        .activity-text { flex: 1; }
        .activity-status { font-size: 14px; }
        
        /* Loading */
        .loading {
            display: inline-block;
            animation: spin 1s linear infinite;
        }
        @keyframes spin {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🏮 博餐 Agent OS</h1>
        <div class="subtitle">城厢古城主题餐厅 · AI 店长控制台</div>
    </div>
    
    <div class="stats-grid">
        <div class="stat-card">
            <div class="stat-value" id="stat-visitors">--</div>
            <div class="stat-label">今日客流</div>
        </div>
        <div class="stat-card">
            <div class="stat-value" id="stat-queue">--</div>
            <div class="stat-label">当前排队</div>
        </div>
        <div class="stat-card">
            <div class="stat-value" id="stat-revenue">--</div>
            <div class="stat-label">今日营收(¥)</div>
        </div>
        <div class="stat-card">
            <div class="stat-value" id="stat-ai">--</div>
            <div class="stat-label">AI执行次数</div>
        </div>
    </div>
    
    <div class="main-content">
        <div class="chat-panel">
            <div class="chat-header">💬 AI 店长对话</div>
            <div class="chat-messages" id="chat-messages">
                <div class="msg bot">
                    👋 你好！我是博餐 AI 店长。有什么需要帮忙的？
                </div>
            </div>
            <div class="chat-input-area">
                <input class="chat-input" id="chat-input" placeholder="输入指令，例如：查看排队人数 / 虾仁水饺下架 / 回复差评" onkeypress="if(event.key==='Enter')sendMessage()">
                <button class="send-btn" onclick="sendMessage()">发送</button>
            </div>
        </div>
        
        <div class="side-panel">
            <div class="panel-card">
                <div class="panel-title">⚡ 快捷指令</div>
                <div class="quick-actions">
                    <button class="action-btn" onclick="quickCmd('查看当前排队人数')">📊 排队人数</button>
                    <button class="action-btn" onclick="quickCmd('查看今日营收')">💰 今日营收</button>
                    <button class="action-btn" onclick="quickCmd('虾仁水饺估清')">📦 估清下架</button>
                    <button class="action-btn" onclick="quickCmd('检查最新评价')">🛡️ 检查舆情</button>
                    <button class="action-btn" onclick="quickCmd('发放雨天外卖券')">🌧️ 雨天营销</button>
                    <button class="action-btn" onclick="quickCmd('VIP客户优惠')">👑 VIP营销</button>
                </div>
            </div>
            
            <div class="panel-card">
                <div class="panel-title">📜 最近操作记录</div>
                <div class="activity-list" id="activity-list">
                    <div class="activity-item">
                        <span class="activity-time">09:32</span>
                        <span class="activity-text">自动发放等位券</span>
                        <span class="activity-status">✅</span>
                    </div>
                    <div class="activity-item">
                        <span class="activity-time">09:28</span>
                        <span class="activity-text">回复差评</span>
                        <span class="activity-status">✅</span>
                    </div>
                    <div class="activity-item">
                        <span class="activity-time">09:15</span>
                        <span class="activity-text">库存同步</span>
                        <span class="activity-status">✅</span>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        async function sendMessage() {
            const input = document.getElementById('chat-input');
            const msg = input.value.trim();
            if (!msg) return;
            
            // Add user message
            addMsg(msg, 'user');
            input.value = '';
            
            // Add loading
            const loadingId = addMsg('<span class="loading">⚙️</span> 处理中...', 'bot');
            
            try {
                const res = await fetch('/api/chat', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({message: msg})
                });
                const data = await res.json();
                
                // Remove loading
                document.getElementById(loadingId)?.remove();
                
                if (data.requires_approval) {
                    addMsg(data.draft || data.message, 'approval');
                    if (confirm('操作需要审批，确认执行吗？')) {
                        // Handle approval
                    }
                } else if (data.success) {
                    addMsg(data.message + (data.data ? '\\n' + JSON.stringify(data.data, null, 2) : ''), 'bot');
                } else {
                    addMsg('❌ ' + (data.message || '操作失败'), 'error');
                }
                
                // Refresh stats
                loadStats();
                loadActivity();
            } catch (e) {
                document.getElementById(loadingId)?.remove();
                addMsg('❌ 网络错误: ' + e.message, 'error');
            }
        }
        
        function quickCmd(cmd) {
            document.getElementById('chat-input').value = cmd;
            sendMessage();
        }
        
        function addMsg(html, type='bot') {
            const div = document.createElement('div');
            div.className = 'msg ' + type;
            div.innerHTML = html;
            document.getElementById('chat-messages').appendChild(div);
            div.scrollIntoView({behavior: 'smooth'});
            return div.id = 'msg-' + Date.now();
        }
        
        async function loadStats() {
            try {
                const res = await fetch('/api/stats');
                const data = await res.json();
                document.getElementById('stat-visitors').textContent = data.today_visitors;
                document.getElementById('stat-queue').textContent = data.queue_now;
                document.getElementById('stat-revenue').textContent = data.revenue_today;
                document.getElementById('stat-ai').textContent = data.ai_actions_today;
            } catch (e) {}
        }
        
        async function loadActivity() {
            try {
                const res = await fetch('/api/actions/recent');
                const data = await res.json();
                const list = document.getElementById('activity-list');
                list.innerHTML = data.map(a => `
                    <div class="activity-item">
                        <span class="activity-time">${a.time}</span>
                        <span class="activity-text">${a.action}</span>
                        <span class="activity-status">${a.status}</span>
                    </div>
                `).join('');
            } catch (e) {}
        }
        
        // Initial load
        loadStats();
        setInterval(loadStats, 30000); // Refresh every 30s
    </script>
</body>
</html>
"""

# ==========================================
# Entry Point
# ==========================================

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
