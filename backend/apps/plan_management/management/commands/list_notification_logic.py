"""
列出系统中所有通知逻辑

用于查看系统中配置了哪些通知规则。
"""
from django.core.management.base import BaseCommand
import inspect
from backend.apps.plan_management import notifications


class Command(BaseCommand):
    help = "列出系统中所有通知逻辑"

    def handle(self, *args, **options):
        self.stdout.write("=" * 80)
        self.stdout.write(self.style.SUCCESS("系统通知逻辑清单"))
        self.stdout.write("=" * 80)
        self.stdout.write("")
        
        # 获取所有通知函数
        notification_functions = [
            name for name, obj in inspect.getmembers(notifications)
            if inspect.isfunction(obj) and name.startswith('notify_')
        ]
        
        notification_functions.sort()
        
        for func_name in notification_functions:
            func = getattr(notifications, func_name)
            doc = inspect.getdoc(func) or "无文档说明"
            
            # 提取函数描述
            lines = doc.split('\n')
            description = lines[0] if lines else "无描述"
            
            self.stdout.write(self.style.SUCCESS(f"【{func_name}】"))
            self.stdout.write(f"  描述: {description}")
            
            # 显示参数
            sig = inspect.signature(func)
            params = list(sig.parameters.keys())
            if params:
                self.stdout.write(f"  参数: {', '.join(params)}")
            
            # 显示详细文档
            if len(lines) > 1:
                self.stdout.write("  详细说明:")
                for line in lines[1:]:
                    if line.strip():
                        self.stdout.write(f"    {line.strip()}")
            
            self.stdout.write("")
        
        self.stdout.write("=" * 80)
        self.stdout.write(self.style.SUCCESS("通知事件类型汇总"))
        self.stdout.write("=" * 80)
        self.stdout.write("")
        
        events = {
            'submit': '提交审批',
            'approve': '审批通过',
            'reject': '审批驳回',
            'draft_timeout': '草稿超时（7天）',
            'approval_timeout': '审批超时（3天）',
            'company_goal_published': '公司目标发布',
            'personal_goal_published': '个人目标发布',
            'goal_accepted': '目标被接收',
            'company_plan_published': '公司计划发布',
            'personal_plan_published': '个人计划发布',
            'plan_accepted': '计划被接收',
        }
        
        for event, desc in sorted(events.items()):
            self.stdout.write(f"  {event:25s} - {desc}")
        
        self.stdout.write("")
        self.stdout.write("=" * 80)
