import argparse
import json
import sys

from skills.trade_customer_skill.main import TradeCustomerSkill
from skills.google_maps_whatsapp_skill.main import GoogleMapsWhatsAppSkill, search_businesses
from scheduler.main import TaskScheduler
from utils.logger import logger

def main():
    parser = argparse.ArgumentParser(description="Agent外贸获客 - 全自动外贸客户开发系统")
    parser.add_argument("--mode", choices=["skill", "scheduler", "gmaps"], default="skill", help="运行模式: skill=通用获客, scheduler=定时任务, gmaps=谷歌地图商家采集")
    parser.add_argument("--instruction", type=str, help="自然语言指令")
    parser.add_argument("--task-id", type=str, help="任务ID")
    parser.add_argument("--action", choices=["add", "remove", "list", "run"], help="调度器操作")
    parser.add_argument("--cron", type=str, help="Cron表达式")
    parser.add_argument("--count", type=int, default=5, help="客户数量")
    parser.add_argument("--industry", type=str, help="目标行业")
    parser.add_argument("--region", type=str, help="目标地区")
    parser.add_argument("--export", choices=["table", "csv"], default="table", help="gmaps模式输出格式: table=Markdown表格, csv=CSV纯文本")

    args = parser.parse_args()

    if args.mode == "gmaps":
        # 谷歌地图商家采集 + WhatsApp建联模式
        if not args.instruction:
            print("错误: --instruction 参数是必需的")
            print("示例: python main.py --mode gmaps --instruction '美国洛杉矶服装批发商家，最多10条'")
            sys.exit(1)

        skill = GoogleMapsWhatsAppSkill()
        if args.export == "csv":
            result = skill.export_csv(args.instruction)
        else:
            result = skill.search_only(args.instruction)

        if isinstance(result, dict) and result.get("output"):
            print(result["output"])
        elif isinstance(result, str):
            print(result)
        else:
            print(json.dumps(result, ensure_ascii=False, indent=2))

    elif args.mode == "skill":
        if not args.instruction:
            print("错误: --instruction 参数是必需的")
            sys.exit(1)

        skill = TradeCustomerSkill()
        result = skill.execute(
            instruction=args.instruction,
            count=args.count,
            industry=args.industry,
            region=args.region
        )

        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    elif args.mode == "scheduler":
        scheduler = TaskScheduler()
        
        if args.action == "add":
            if not args.task_id or not args.instruction or not args.cron:
                print("错误: 添加任务需要 --task-id, --instruction 和 --cron 参数")
                sys.exit(1)
            
            success = scheduler.add_task(
                task_id=args.task_id,
                instruction=args.instruction,
                cron_expression=args.cron
            )
            print(f"任务添加{'成功' if success else '失败'}")
        
        elif args.action == "remove":
            if not args.task_id:
                print("错误: 删除任务需要 --task-id 参数")
                sys.exit(1)
            
            success = scheduler.remove_task(args.task_id)
            print(f"任务删除{'成功' if success else '失败'}")
        
        elif args.action == "list":
            tasks = scheduler.list_tasks()
            print(json.dumps(tasks, ensure_ascii=False, indent=2))
        
        elif args.action == "run":
            if not args.task_id:
                print("错误: 运行任务需要 --task-id 参数")
                sys.exit(1)
            
            result = scheduler.run_task_now(args.task_id)
            print(json.dumps(result, ensure_ascii=False, indent=2))
        
        else:
            print("启动定时调度器...")
            scheduler.start()
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                scheduler.stop()
                print("调度器已停止")

if __name__ == "__main__":
    main()