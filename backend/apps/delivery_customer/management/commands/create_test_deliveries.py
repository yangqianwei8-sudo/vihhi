"""
创建测试交付记录的管理命令
用法: python manage.py create_test_deliveries
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import models
from datetime import timedelta
import random

from backend.apps.delivery_customer.models import DeliveryRecord
from backend.apps.production_management.models import Project
from backend.apps.customer_management.models import Client

User = get_user_model()


class Command(BaseCommand):
    help = '创建10条测试交付记录，包含不同状态、交付方式和优先级'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=10,
            help='要创建的交付记录数量（默认：10）',
        )

    def handle(self, *args, **options):
        count = options['count']
        self.stdout.write(self.style.SUCCESS(f'开始创建 {count} 条测试交付记录...'))

        # 获取用户
        users = User.objects.all()
        if not users.exists():
            self.stdout.write(self.style.ERROR('错误：系统中没有用户，请先创建用户'))
            return

        # 获取项目
        projects = Project.objects.all()
        if not projects.exists():
            self.stdout.write(self.style.WARNING('警告：系统中没有项目，交付记录将不关联项目'))

        # 获取客户
        clients = Client.objects.all()
        if not clients.exists():
            self.stdout.write(self.style.WARNING('警告：系统中没有客户，交付记录将不关联客户'))

        # 测试数据模板
        titles = [
            '项目设计图纸交付',
            '施工方案文档交付',
            '成本预算报告交付',
            '技术规范文档交付',
            '项目进度报告交付',
            '质量检测报告交付',
            '竣工验收资料交付',
            '变更设计图纸交付',
            '材料清单文档交付',
            '安全评估报告交付',
        ]

        descriptions = [
            '包含建筑、结构、给排水、电气等专业设计图纸',
            '详细的施工组织设计方案和技术措施',
            '项目全过程的成本预算和费用分析报告',
            '技术规范和标准要求文档',
            '项目各阶段进度情况汇总报告',
            '质量检测和验收相关报告',
            '竣工验收所需的所有资料文件',
            '设计变更后的更新图纸',
            '项目所需材料清单和规格说明',
            '安全评估和风险分析报告',
        ]

        # 收件人信息模板
        recipient_names = [
            '张工程师', '李经理', '王主任', '刘总工', '陈设计师',
            '赵主管', '孙工程师', '周经理', '吴主任', '郑总工'
        ]

        recipient_emails = [
            'zhang@example.com', 'li@example.com', 'wang@example.com',
            'liu@example.com', 'chen@example.com', 'zhao@example.com',
            'sun@example.com', 'zhou@example.com', 'wu@example.com',
            'zheng@example.com'
        ]

        recipient_phones = [
            '13800138001', '13800138002', '13800138003', '13800138004',
            '13800138005', '13800138006', '13800138007', '13800138008',
            '13800138009', '13800138010'
        ]

        recipient_addresses = [
            '北京市朝阳区建国路88号',
            '上海市浦东新区世纪大道1000号',
            '广州市天河区天河路123号',
            '深圳市南山区科技园南路2000号',
            '杭州市西湖区文三路259号',
            '成都市锦江区红星路三段1号',
            '武汉市武昌区中南路99号',
            '西安市雁塔区科技路10号',
            '南京市鼓楼区中山路321号',
            '重庆市渝中区解放碑步行街88号'
        ]

        # 快递公司列表
        express_companies = ['顺丰', '圆通', '申通', '中通', '韵达', 'EMS', '德邦', '京东']

        # 创建交付记录
        created_count = 0
        for i in range(count):
            try:
                # 随机选择用户、项目、客户
                created_by = random.choice(users)
                project = random.choice(projects) if projects.exists() else None
                client = None
                if project and project.client:
                    client = project.client
                elif clients.exists():
                    client = random.choice(clients)

                # 随机选择交付方式
                delivery_method = random.choice(['email', 'express', 'hand_delivery'])

                # 随机选择状态（确保有不同状态的记录）
                status_weights = {
                    'draft': 2,
                    'submitted': 1,
                    'pending_approval': 1,
                    'approved': 2,
                    'in_transit': 1,
                    'sent': 1,
                    'delivered': 1,
                    'confirmed': 1,
                }
                status = random.choices(
                    list(status_weights.keys()),
                    weights=list(status_weights.values())
                )[0]

                # 随机选择优先级
                priority = random.choice(['low', 'normal', 'high', 'urgent'])

                # 创建交付记录
                delivery = DeliveryRecord(
                    title=titles[i % len(titles)],
                    description=descriptions[i % len(descriptions)],
                    delivery_method=delivery_method,
                    status=status,
                    priority=priority,
                    project=project,
                    client=client,
                    created_by=created_by,
                    recipient_name=recipient_names[i % len(recipient_names)],
                    recipient_email=recipient_emails[i % len(recipient_emails)],
                    recipient_phone=recipient_phones[i % len(recipient_phones)],
                    recipient_address=recipient_addresses[i % len(recipient_addresses)],
                )

                # 根据交付方式设置特定字段
                if delivery_method == 'email':
                    delivery.email_subject = f'{delivery.title} - 交付通知'
                    delivery.email_message = f'<p>您好，</p><p>请查收附件：{delivery.title}</p><p>{delivery.description}</p>'
                    delivery.cc_emails = 'manager@example.com'
                    if status in ['sent', 'delivered', 'received']:
                        delivery.sent_at = timezone.now() - timedelta(days=random.randint(1, 7))
                        delivery.sent_by = created_by

                elif delivery_method == 'express':
                    delivery.express_company = random.choice(express_companies)
                    delivery.express_number = f'{delivery.express_company[:2].upper()}{random.randint(1000000000, 9999999999)}'
                    delivery.express_fee = round(random.uniform(10, 50), 2)
                    if status in ['in_transit', 'delivered']:
                        delivery.sent_at = timezone.now() - timedelta(days=random.randint(1, 5))
                        delivery.sent_by = created_by
                    if status == 'delivered':
                        delivery.delivered_at = timezone.now() - timedelta(days=random.randint(1, 3))

                elif delivery_method == 'hand_delivery':
                    delivery.delivery_person = random.choice(users)
                    delivery.delivery_notes = '现场送达，已签收'
                    if status in ['delivered', 'confirmed']:
                        delivery.delivered_at = timezone.now() - timedelta(days=random.randint(1, 5))
                        delivery.sent_by = delivery.delivery_person

                # 设置时间字段
                now = timezone.now()
                delivery.created_at = now - timedelta(days=random.randint(0, 30))
                
                if status in ['submitted', 'pending_approval', 'approving', 'approved', 'rejected']:
                    delivery.submitted_at = delivery.created_at + timedelta(hours=random.randint(1, 24))
                
                if status in ['received', 'confirmed']:
                    delivery.received_at = now - timedelta(days=random.randint(1, 7))
                
                if status == 'confirmed':
                    delivery.confirmed_at = now - timedelta(days=random.randint(1, 5))

                # 设置交付期限（部分记录设置期限，部分不设置）
                if random.choice([True, False]):
                    days_ahead = random.randint(-5, 10)  # 可能已逾期或未到期
                    delivery.deadline = now + timedelta(days=days_ahead)
                    delivery.scheduled_delivery_time = delivery.deadline - timedelta(days=1)

                # 保存（会自动生成交付单号）
                delivery.save()

                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'  [{created_count}/{count}] 创建交付记录：{delivery.delivery_number} - {delivery.title} '
                        f'({delivery.get_delivery_method_display()}, {delivery.get_status_display()})'
                    )
                )

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'  创建第 {i+1} 条交付记录失败：{str(e)}')
                )
                continue

        self.stdout.write(self.style.SUCCESS(f'\n成功创建 {created_count} 条交付记录！'))
        self.stdout.write(self.style.SUCCESS('\n交付记录统计：'))
        
        # 统计各状态的记录数
        status_counts = DeliveryRecord.objects.values('status').annotate(
            count=models.Count('id')
        ).order_by('status')
        
        for item in status_counts:
            status_display = dict(DeliveryRecord.STATUS_CHOICES).get(item['status'], item['status'])
            self.stdout.write(f'  {status_display}: {item["count"]} 条')

