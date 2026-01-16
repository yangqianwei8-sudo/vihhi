"""
创建测试收文记录的管理命令
用法: python manage.py create_test_incoming_documents
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta, date
import random

from backend.apps.delivery_customer.models import IncomingDocument

User = get_user_model()


class Command(BaseCommand):
    help = '创建10条测试收文记录，包含不同状态、优先级和阶段'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=10,
            help='要创建的收文记录数量（默认：10）',
        )

    def handle(self, *args, **options):
        count = options['count']
        self.stdout.write(self.style.SUCCESS(f'开始创建 {count} 条测试收文记录...'))

        # 获取用户
        users = User.objects.all()
        if not users.exists():
            self.stdout.write(self.style.ERROR('错误：系统中没有用户，请先创建用户'))
            return
        
        created_by = users.first()  # 使用第一个用户作为创建人
        handlers = list(users)  # 所有用户作为可能的处理人

        # 测试数据模板
        titles = [
            '关于项目设计方案的函',
            '技术规范文件通知',
            '合同补充协议',
            '项目进度报告',
            '质量检测报告',
            '竣工验收通知',
            '设计变更通知',
            '材料采购清单',
            '安全评估报告',
            '项目结算文件',
            '回款通知函',
            '售后服务协议',
            '诉讼相关文件',
            '客户反馈意见',
            '项目总结报告',
        ]

        senders = [
            '北京市建筑设计研究院',
            '上海市工程咨询公司',
            '广州市建设集团有限公司',
            '深圳市规划设计院',
            '杭州市工程管理公司',
            '成都市建筑装饰公司',
            '武汉市工程设计院',
            '西安市工程咨询有限公司',
            '南京市建设发展公司',
            '天津市工程设计研究院',
        ]

        sender_contacts = [
            '张工程师', '李经理', '王主任', '刘总工', '陈设计师',
            '赵主管', '孙工程师', '周经理', '吴主任', '郑总工'
        ]

        sender_phones = [
            '010-12345678', '021-87654321', '020-11223344',
            '0755-22334455', '0571-33445566', '028-44556677',
            '027-55667788', '029-66778899', '025-77889900',
            '022-88990011'
        ]

        document_types = [
            '通知', '函', '报告', '协议', '合同',
            '清单', '方案', '计划', '说明', '意见'
        ]

        contents = [
            '关于项目设计方案的详细说明，请查收。',
            '技术规范文件已更新，请按照新规范执行。',
            '合同补充协议内容详见附件。',
            '项目进度报告包含各阶段完成情况。',
            '质量检测报告显示各项指标均符合要求。',
            '竣工验收通知，请准备相关材料。',
            '设计变更通知，请及时更新相关图纸。',
            '材料采购清单包含所有所需材料明细。',
            '安全评估报告显示项目安全状况良好。',
            '项目结算文件包含所有费用明细。',
        ]

        summaries = [
            '项目设计方案相关文件',
            '技术规范更新通知',
            '合同补充协议',
            '项目进度情况汇报',
            '质量检测结果',
            '竣工验收安排',
            '设计变更说明',
            '材料采购需求',
            '安全评估结果',
            '项目结算明细',
        ]

        # 状态、优先级、阶段选项
        statuses = ['draft', 'registered', 'processing', 'completed', 'archived']
        priorities = ['low', 'normal', 'high', 'urgent']
        stages = ['conversion', 'contract', 'production', 'settlement', 'payment', 'after_sales', 'litigation']

        created_count = 0

        for i in range(count):
            try:
                # 生成收文编号
                today = timezone.now().date()
                year = today.strftime('%Y')
                existing_count = IncomingDocument.objects.filter(
                    document_number__startswith=f'SW{year}'
                ).count()
                document_number = f'SW{year}{(existing_count + i + 1):04d}'
                
                # 确保编号唯一
                while IncomingDocument.objects.filter(document_number=document_number).exists():
                    existing_count += 1
                    document_number = f'SW{year}{(existing_count + 1):04d}'

                # 随机选择数据
                title = random.choice(titles)
                sender = random.choice(senders)
                sender_contact = random.choice(sender_contacts)
                sender_phone = random.choice(sender_phones)
                document_type = random.choice(document_types)
                content = random.choice(contents)
                summary = random.choice(summaries)
                
                # 随机状态和优先级
                status = random.choice(statuses)
                priority = random.choice(priorities)
                stage = random.choice(stages) if random.random() > 0.3 else None  # 70%概率有阶段
                
                # 随机处理人
                handler = random.choice(handlers) if handlers and random.random() > 0.4 else None  # 60%概率有处理人
                
                # 随机日期（过去30天内）
                days_ago = random.randint(0, 30)
                document_date = today - timedelta(days=days_ago)
                receive_date = document_date + timedelta(days=random.randint(0, 5))  # 收文日期在文件日期后0-5天
                
                # 如果状态是已完成，设置完成时间
                completed_at = None
                if status == 'completed':
                    completed_at = timezone.now() - timedelta(days=random.randint(0, 10))
                
                # 创建收文记录
                document = IncomingDocument(
                    document_number=document_number,
                    title=title,
                    sender=sender,
                    sender_contact=sender_contact,
                    sender_phone=sender_phone,
                    document_date=document_date,
                    receive_date=receive_date,
                    document_type=document_type,
                    content=content,
                    summary=summary,
                    status=status,
                    priority=priority,
                    stage=stage,
                    handler=handler,
                    handle_notes=f'处理意见：{summary}' if handler else '',
                    completed_at=completed_at,
                    notes=f'备注：这是第{i+1}条测试收文记录',
                    created_by=created_by,
                )
                
                document.save()
                created_count += 1
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'  [{created_count}/{count}] 创建收文：{document.document_number} - {document.title} '
                        f'(状态: {document.get_status_display()}, 优先级: {document.get_priority_display()})'
                    )
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'  创建第 {i+1} 条收文记录失败：{str(e)}')
                )

        self.stdout.write(self.style.SUCCESS(f'\n成功创建 {created_count} 条收文记录！'))
        self.stdout.write(self.style.SUCCESS('\n收文记录统计：'))
        
        # 统计各状态数量
        for status_code, status_name in IncomingDocument.STATUS_CHOICES:
            count_by_status = IncomingDocument.objects.filter(status=status_code).count()
            self.stdout.write(f'  {status_name}: {count_by_status} 条')
        
        # 统计各优先级数量
        self.stdout.write(self.style.SUCCESS('\n优先级统计：'))
        for priority_code, priority_name in IncomingDocument.PRIORITY_CHOICES:
            count_by_priority = IncomingDocument.objects.filter(priority=priority_code).count()
            self.stdout.write(f'  {priority_name}: {count_by_priority} 条')


