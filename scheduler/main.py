import schedule
import time
import threading
import json
from typing import Dict, List, Any, Optional
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from skills.trade_customer_skill.main import TradeCustomerSkill
from utils.logger import logger

class TaskScheduler:
    def __init__(self):
        self.skill = TradeCustomerSkill()
        self.scheduled_tasks = {}
        self.running = False
    
    def add_task(self, task_id: str, instruction: str, cron_expression: str, **kwargs) -> bool:
        try:
            schedule.every().day.at(cron_expression).do(
                self._execute_task,
                task_id=task_id,
                instruction=instruction,
                **kwargs
            )
            
            self.scheduled_tasks[task_id] = {
                "instruction": instruction,
                "cron_expression": cron_expression,
                "kwargs": kwargs,
                "last_run": None,
                "next_run": None,
                "status": "active"
            }
            
            logger.info(f"任务添加成功: {task_id} - {cron_expression}")
            return True
        except Exception as e:
            logger.error(f"添加任务失败 {task_id}: {e}")
            return False
    
    def remove_task(self, task_id: str) -> bool:
        if task_id in self.scheduled_tasks:
            del self.scheduled_tasks[task_id]
            schedule.clear()
            self._rebuild_schedule()
            logger.info(f"任务删除成功: {task_id}")
            return True
        return False
    
    def pause_task(self, task_id: str) -> bool:
        if task_id in self.scheduled_tasks:
            self.scheduled_tasks[task_id]["status"] = "paused"
            logger.info(f"任务暂停: {task_id}")
            return True
        return False
    
    def resume_task(self, task_id: str) -> bool:
        if task_id in self.scheduled_tasks:
            self.scheduled_tasks[task_id]["status"] = "active"
            logger.info(f"任务恢复: {task_id}")
            return True
        return False
    
    def list_tasks(self) -> List[Dict[str, Any]]:
        tasks = []
        for task_id, info in self.scheduled_tasks.items():
            tasks.append({
                "task_id": task_id,
                "instruction": info["instruction"],
                "cron_expression": info["cron_expression"],
                "status": info["status"],
                "last_run": info["last_run"],
                "next_run": info["next_run"]
            })
        return tasks
    
    def run_task_now(self, task_id: str) -> Dict[str, Any]:
        if task_id in self.scheduled_tasks:
            task_info = self.scheduled_tasks[task_id]
            return self._execute_task(task_id, task_info["instruction"], **task_info["kwargs"])
        return {"status": "failed", "error": "任务不存在"}
    
    def start(self):
        self.running = True
        logger.info("定时调度器启动")
        
        scheduler_thread = threading.Thread(target=self._run_scheduler)
        scheduler_thread.daemon = True
        scheduler_thread.start()
    
    def stop(self):
        self.running = False
        logger.info("定时调度器停止")
    
    def _run_scheduler(self):
        while self.running:
            schedule.run_pending()
            time.sleep(60)
    
    def _rebuild_schedule(self):
        for task_id, info in self.scheduled_tasks.items():
            if info["status"] == "active":
                schedule.every().day.at(info["cron_expression"]).do(
                    self._execute_task,
                    task_id=task_id,
                    instruction=info["instruction"],
                    **info["kwargs"]
                )
    
    def _execute_task(self, task_id: str, instruction: str, **kwargs) -> Dict[str, Any]:
        logger.info(f"开始执行任务: {task_id} - {instruction}")
        
        try:
            result = self.skill.execute(instruction, **kwargs)
            
            if task_id in self.scheduled_tasks:
                self.scheduled_tasks[task_id]["last_run"] = time.strftime("%Y-%m-%d %H:%M:%S")
                self.scheduled_tasks[task_id]["next_run"] = str(schedule.next_run())
            
            logger.info(f"任务执行完成: {task_id}")
            logger.info(f"执行结果: {result.get('summary', '')}")
            
            return result
        except Exception as e:
            logger.error(f"任务执行失败 {task_id}: {e}")
            return {"status": "failed", "error": str(e)}

if __name__ == "__main__":
    scheduler = TaskScheduler()
    
    scheduler.add_task(
        task_id="daily_trade_develop",
        instruction="帮我开发5个医疗客户",
        cron_expression="09:00"
    )
    
    scheduler.add_task(
        task_id="follow_up_emails",
        instruction="给待开发客户发送跟进邮件",
        cron_expression="14:00"
    )
    
    print("定时任务列表:")
    for task in scheduler.list_tasks():
        print(json.dumps(task, ensure_ascii=False, indent=2))
    
    scheduler.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        scheduler.stop()
        print("调度器已停止")