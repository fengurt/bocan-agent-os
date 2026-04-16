"""
记忆系统
- 短时记忆：当前排队数、菜品状态等实时数据
- 长时记忆：VIP信息、历史数据、门店SOP
"""
from datetime import datetime, timedelta
from collections import deque
from typing import Any, Optional


class ShortTermMemory:
    """
    短时记忆 (STM)
    使用 deque 自动过期，保留最近 N 条
    """
    def __init__(self, max_items: int = 100, ttl_minutes: int = 60):
        self._queue = deque(maxlen=max_items)
        self._ttl = ttl_minutes  # 分钟
    
    def add(self, item: Any):
        """添加记忆"""
        self._queue.append({
            "data": item,
            "timestamp": datetime.now()
        })
    
    def get_all(self) -> list:
        """获取所有有效记忆"""
        cutoff = datetime.now() - timedelta(minutes=self._ttl)
        return [
            {"data": item["data"], "timestamp": item["timestamp"]}
            for item in self._queue
            if item["timestamp"] > cutoff
        ]
    
    def get_recent(self, n: int = 5) -> list:
        """获取最近N条"""
        return list(self._queue)[-n:]
    
    def query(self, key: str) -> Optional[Any]:
        """按 key 查询最新记忆"""
        for item in reversed(list(self._queue)):
            data = item["data"]
            if hasattr(data, key):
                return getattr(data, key)
            if isinstance(data, dict) and key in data:
                return data[key]
        return None


class LongTermMemory:
    """
    长时记忆 (LTM)
    基于文件的持久化存储（可升级为向量数据库）
    """
    
    def __init__(self, tenant_id: str, storage_path: str = "./memory"):
        self.tenant_id = tenant_id
        self.storage_path = f"{storage_path}/{tenant_id}"
        self._vip_file = f"{self.storage_path}/vip_customers.json"
        self._sop_file = f"{self.storage_path}/sop.json"
        self._history_file = f"{self.storage_path}/history.json"
        import os
        os.makedirs(self.storage_path, exist_ok=True)
    
    def get_vip(self, customer_id: str) -> Optional[dict]:
        """获取VIP信息"""
        import json
        try:
            with open(self._vip_file) as f:
                data = json.load(f)
                return data.get(customer_id)
        except (FileNotFoundError, json.JSONDecodeError):
            return None
    
    def save_vip(self, customer_id: str, info: dict):
        """保存VIP信息"""
        import json
        try:
            with open(self._vip_file) as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            data = {}
        
        data[customer_id] = info
        
        with open(self._vip_file, "w") as f:
            json.dump(data, f, ensure_ascii=False)
    
    def get_recent(self, n: int = 5) -> list:
        """获取最近N条历史记录"""
        import json
        try:
            with open(self._history_file) as f:
                data = json.load(f)
                return data[-n:]
        except (FileNotFoundError, json.JSONDecodeError):
            return []
    
    def append_history(self, event: dict):
        """追加历史记录"""
        import json
        try:
            with open(self._history_file) as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            data = []
        
        event["timestamp"] = datetime.now().isoformat()
        data.append(event)
        
        # 只保留最近1000条
        data = data[-1000:]
        
        with open(self._history_file, "w") as f:
            json.dump(data, f, ensure_ascii=False)
