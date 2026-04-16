"""
租户配置清单 (Tenant Manifest)
每个餐厅实例的配置，包含人设、平台拓扑、权限护栏
"""
from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class POSSystem(str, Enum):
    """收银POS系统"""
    MEITUAN = "meituan"          # 美团
    KEIRUYUN = "keiruyun"        # 客如云
    HALALA = "halala"            # 哗啦啦
    MEITUAN_POS = "meituan_pos"  # 美团收银
    XMD = "xmd"                  # 美味不用等
    OTHER = "other"


class QueueSystem(str, Enum):
    """排队系统"""
    MEITUAN_QUEUE = "meituan_queue"  # 美团排队
    XMD = "xmd"                    # 美味不用等
    KRRY_QUEUE = "krrY_queue"       # 客如云排队
    MANUAL = "manual"               # 手动叫号


class Persona(str, Enum):
    """AI店长人设"""
    WARM_SISTER = "热情接地的老板娘"
    ELEGANT_MANAGER = "严谨克制的米其林大堂经理"
    HUMOR_UNCLE = "幽默风趣的邻家大叔"
    YOUNG_TRENDY = "年轻时尚的网红店长"


class ApprovalPolicy(BaseModel):
    """审批权限策略"""
    auto_approve_below: float = 20.0  # 元，自动审批金额上限
    coupon_max_auto: float = 20.0     # 元，自动发券上限
    refund_max_auto: float = 50.0      # 元，自动退款上限
    can_reply_review: bool = True      # 是否可以回复评价
    can_modify_price: bool = False     # 是否可以改价
    can_cancel_order: bool = False      # 是否可以退单


class PlatformConfig(BaseModel):
    """单个平台配置"""
    platform: str                   # meituan / ele / douyin / keiruyun
    enabled: bool = True
    shop_id: Optional[str] = None    # 门店ID
    credentials_stored: bool = False   # 凭证是否已入库


class TenantManifest(BaseModel):
    """
    租户配置清单
    Onboarding 时通过对话生成，是每个餐厅 Agent 实例的"灵魂配置"
    """
    tenant_id: str
    tenant_name: str                     # "金谷园饺子馆"
    location: str                        # "成都青白江城厢古城"
    
    # AI店长人设
    persona: Persona = Persona.WARM_SISTER
    persona_greeting: str = "欢迎光临！今天想吃点什么？"  # 个性化开场白
    
    # 系统拓扑
    pos_system: POSSystem = POSSystem.OTHER
    queue_system: QueueSystem = QueueSystem.MANUAL
    platforms: list[PlatformConfig] = Field(default_factory=list)
    
    # 外卖平台
    has_meituan: bool = False
    has_ele: bool = False        # 饿了么
    has_douyin: bool = False     # 抖音团购
    has_xiancheng: bool = False   # 闲鱼
    
    # 桌台配置
    hall_tables: int = 10       # 大厅桌数
    private_rooms: int = 3      # 包间数
    total_seats: int = 100
    
    # 权限护栏
    approval_policy: ApprovalPolicy = Field(default_factory=ApprovalPolicy)
    
    # 营业时间
    business_hours: str = "10:00-22:00"
    is_24h: bool = False
    
    # 菜品SKU映射 (各平台SKU → 统一SKU)
    sku_mapping: dict[str, str] = Field(default_factory=dict)  # {platform_sku_id: unified_sku_id}
    
    # 长时记忆 (从历史数据导入)
    vip_customers: dict[str, dict] = Field(default_factory=dict)  # {customer_id: {name, preferences, ...}}
    
    # 元数据
    created_at: str = ""
    updated_at: str = ""
    version: str = "1.0"
    
    def get_active_platforms(self) -> list[str]:
        """获取已启用的平台列表"""
        return [p.platform for p in self.platforms if p.enabled]
    
    def needs_approval(self, operation_type: str, amount: float = 0) -> bool:
        """检查操作是否需要人工审批"""
        policy = self.approval_policy
        
        if operation_type == "coupon" and amount <= policy.coupon_max_auto:
            return False
        if operation_type == "refund" and amount <= policy.refund_max_auto:
            return False
        if operation_type == "reply_review" and policy.can_reply_review:
            return False
            
        return True
