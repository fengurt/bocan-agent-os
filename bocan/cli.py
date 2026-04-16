"""
博餐 Agent OS CLI
命令行入口
"""
import argparse
import asyncio
import json
import sys

from bocan.core.agent import BocanAgent
from bocan.core.manifest import TenantManifest, Persona


def onboarding() -> TenantManifest:
    """
    交互式 Onboarding
    向店长询问灵魂问题，生成 TenantManifest
    """
    print("\n🏮 博餐 Agent OS - 初始化向导")
    print("=" * 40)
    print("正在为您的门店创建 AI 店长...\n")
    
    # 基础信息
    tenant_name = input("1. 门店名称（如：金谷园饺子馆）: ").strip()
    location = input("2. 门店地址: ").strip()
    tenant_id = input("3. 简短ID（如：jinguYuan）: ").strip().lower().replace(" ", "_")
    
    # 人设选择
    print("\n4. AI店长人设风格:")
    print("   1. 热情接地的老板娘")
    print("   2. 严谨克制的米其林大堂经理")
    print("   3. 幽默风趣的邻家大叔")
    print("   4. 年轻时尚的网红店长")
    persona_map = {
        "1": Persona.WARM_SISTER,
        "2": Persona.ELEGANT_MANAGER,
        "3": Persona.HUMOR_UNCLE,
        "4": Persona.YOUNG_TRENDY,
    }
    persona_choice = input("选择 (1-4): ").strip()
    persona = persona_map.get(persona_choice, Persona.WARM_SISTER)
    
    # 平台配置
    print("\n5. 已接入的平台（逗号分隔）: ")
    print("   meituan=美团, ele=饿了么, douyin=抖音, xiancheng=闲鱼")
    platforms_str = input("   例如: meituan,ele,douyin: ").strip()
    platforms = []
    for p in platforms_str.replace(" ", "").split(","):
        if p:
            platforms.append({"platform": p, "enabled": True, "shop_id": "", "credentials_stored": False})
    
    # 创建 Manifest
    manifest = TenantManifest(
        tenant_id=tenant_id,
        tenant_name=tenant_name,
        location=location,
        persona=persona,
        platforms=platforms,
        has_meituan="meituan" in platforms_str,
        has_ele="ele" in platforms_str,
        has_douyin="douyin" in platforms_str,
    )
    
    print("\n✅ 初始化完成！")
    print(f"   门店: {manifest.tenant_name}")
    print(f"   人设: {manifest.persona.value}")
    print(f"   平台: {', '.join(manifest.get_active_platforms())}")
    
    return manifest


def chat_mode(agent: BocanAgent):
    """对话模式"""
    print("\n🏮 博餐 Agent OS - 对话模式")
    print("=" * 40)
    print(f"AI店长: {agent.manifest.persona_greeting}")
    print("（输入 'quit' 退出）\n")
    
    while True:
        try:
            user_input = input("你: ").strip()
            if user_input.lower() in ["quit", "exit", "退出"]:
                print("再见！👋")
                break
            
            if not user_input:
                continue
            
            response = agent.chat(user_input)
            print(f"\nAI店长: {response}\n")
        
        except KeyboardInterrupt:
            print("\n\n再见！👋")
            break


def main():
    parser = argparse.ArgumentParser(description="博餐 Agent OS")
    subparsers = parser.add_subparsers(dest="command")
    
    # init 子命令
    init_parser = subparsers.add_parser("init", help="初始化门店配置")
    init_parser.add_argument("--name", help="门店名称")
    init_parser.add_argument("--output", default="./tenant_manifest.json", help="输出文件")
    
    # run 子命令
    run_parser = subparsers.add_parser("run", help="运行Agent")
    run_parser.add_argument("--manifest", default="./tenant_manifest.json", help="配置文件路径")
    
    # skill 子命令
    skill_parser = subparsers.add_parser("skills", help="列出可用技能")
    
    args = parser.parse_args()
    
    if args.command == "init":
        manifest = onboarding()
        output_path = args.output
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(manifest.model_dump(), f, ensure_ascii=False, indent=2)
        print(f"\n📁 配置已保存至: {output_path}")
    
    elif args.command == "run":
        # 加载配置
        try:
            with open(args.manifest, encoding="utf-8") as f:
                data = json.load(f)
                manifest = TenantManifest(**data)
        except FileNotFoundError:
            print(f"❌ 配置文件不存在: {args.manifest}")
            print("请先运行: bocan init")
            return
        
        agent = BocanAgent(manifest)
        chat_mode(agent)
    
    elif args.command == "skills":
        from bocan.skill_hub.hub import SkillHub
        hub = SkillHub()
        
        # 加载内置Skills
        from bocan.skills.meituan_queue import MeituanQueueSkill
        hub.register(MeituanQueueSkill())
        
        print("\n📋 可用 Skills:")
        for name in hub.list_all():
            skill = hub.get(name)
            print(f"  • {name}: {skill.description}")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
