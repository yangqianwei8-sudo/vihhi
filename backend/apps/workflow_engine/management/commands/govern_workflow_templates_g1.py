"""
审批模板治理命令（G1-1 & G1-2）

G1-1: 冻结无实例的废弃模板
G1-2: 统一 applicable_models 格式

治理原则：
- 不删除记录
- 不动历史数据
- 所有操作可回滚
"""
from django.core.management.base import BaseCommand
from backend.apps.workflow_engine.models import WorkflowTemplate


class Command(BaseCommand):
    help = '审批模板治理：冻结废弃模板 + 统一绑定格式'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='仅显示将要执行的操作，不实际修改',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('=== DRY RUN 模式：不会实际修改数据 ===\n'))
        
        # ========== G1-1: 冻结废弃模板 ==========
        self.stdout.write(self.style.SUCCESS('=== G1-1: 冻结无实例的废弃模板 ==='))
        
        templates_to_freeze = [
            'administrative_general_approval',
            'goal_creation_approval',
            'goal_adjustment_approval',
        ]
        
        frozen_count = 0
        for code in templates_to_freeze:
            try:
                workflow = WorkflowTemplate.objects.get(code=code)
                instance_count = workflow.instances.count()
                
                if instance_count > 0:
                    self.stdout.write(
                        self.style.WARNING(
                            f'  ⚠ {code}: 有 {instance_count} 个实例，跳过冻结'
                        )
                    )
                    continue
                
                if workflow.status == 'inactive':
                    self.stdout.write(f'  ✓ {code}: 已经是 inactive 状态，跳过')
                    continue
                
                self.stdout.write(f'  ❄ {code}: 状态 {workflow.status} -> inactive')
                
                if not dry_run:
                    workflow.status = 'inactive'
                    workflow.save(update_fields=['status'])
                    frozen_count += 1
                else:
                    self.stdout.write('    [DRY RUN] 将设置为 inactive')
                    frozen_count += 1
                    
            except WorkflowTemplate.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'  ❌ {code}: 模板不存在'))
        
        self.stdout.write(self.style.SUCCESS(f'\n✓ G1-1 完成：冻结 {frozen_count} 个模板\n'))
        
        # ========== G1-2: 统一 applicable_models 格式 ==========
        self.stdout.write(self.style.SUCCESS('=== G1-2: 统一 applicable_models 格式 ==='))
        
        # 需要修复的模板
        fixes = [
            {
                'code': 'seal_borrowing_approval',
                'current': ['{sealborrowing}', 'sealborrowing'],
                'target': ['sealborrowing'],
            },
            {
                'code': 'seal_usage_approval',
                'current': ['{sealusage}'],
                'target': ['sealusage'],
            },
        ]
        
        fixed_count = 0
        for fix in fixes:
            try:
                workflow = WorkflowTemplate.objects.get(code=fix['code'])
                current = list(workflow.applicable_models) if workflow.applicable_models else []
                
                # 检查是否需要修复
                needs_fix = False
                if current != fix['target']:
                    needs_fix = True
                
                if not needs_fix:
                    self.stdout.write(f'  ✓ {fix["code"]}: 格式已正确 {current}')
                    continue
                
                self.stdout.write(f'  🔧 {fix["code"]}: {current} -> {fix["target"]}')
                
                if not dry_run:
                    workflow.applicable_models = fix['target']
                    workflow.save(update_fields=['applicable_models'])
                    fixed_count += 1
                else:
                    self.stdout.write('    [DRY RUN] 将更新 applicable_models')
                    fixed_count += 1
                    
            except WorkflowTemplate.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'  ❌ {fix["code"]}: 模板不存在'))
        
        self.stdout.write(self.style.SUCCESS(f'\n✓ G1-2 完成：修复 {fixed_count} 个模板的绑定格式\n'))
        
        # ========== 验证结果 ==========
        self.stdout.write(self.style.SUCCESS('=== 验证结果 ==='))
        
        active_templates = WorkflowTemplate.objects.filter(status='active')
        self.stdout.write(f'Active 模板数量: {active_templates.count()}')
        
        for workflow in active_templates.order_by('code'):
            models = list(workflow.applicable_models) if workflow.applicable_models else []
            instance_count = workflow.instances.count()
            self.stdout.write(
                f'  - {workflow.code}: applicable_models={models}, instances={instance_count}'
            )
        
        if dry_run:
            self.stdout.write(self.style.WARNING('\n=== DRY RUN 完成，未实际修改数据 ==='))
        else:
            self.stdout.write(self.style.SUCCESS('\n=== 治理完成 ==='))
