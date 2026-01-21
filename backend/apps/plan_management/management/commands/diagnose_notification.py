"""
诊断通知系统问题

全面检查通知系统的各个组件是否正常工作。
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import connection
from django.test import RequestFactory

from backend.apps.plan_management.compat import (
    get_approval_notification_model,
    has_approval_notification,
    safe_approval_notification
)
from backend.apps.plan_management.views_notifications import NotificationListAPI
from backend.apps.plan_management.serializers_notifications import ApprovalNotificationSerializer

User = get_user_model()


class Command(BaseCommand):
    help = "诊断通知系统问题 - 全面检查通知系统的各个组件"

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            default='tester1',
            help='要诊断的用户名（默认：tester1）'
        )
        parser.add_argument(
            '--notification-id',
            type=int,
            help='要诊断的特定通知ID'
        )

    def handle(self, *args, **options):
        username = options.get('username', 'tester1')
        notification_id = options.get('notification_id')
        
        self.stdout.write("=" * 80)
        self.stdout.write(self.style.SUCCESS("通知系统诊断"))
        self.stdout.write("=" * 80)
        self.stdout.write(f"诊断用户: {username}")
        if notification_id:
            self.stdout.write(f"特定通知ID: {notification_id}")
        self.stdout.write("")
        
        # 1. 检查用户是否存在
        self.stdout.write(self.style.SUCCESS("【1. 用户检查】"))
        try:
            user = User.objects.get(username=username)
            self.stdout.write(f"  ✓ 用户存在: {user.username} (ID: {user.id})")
            self.stdout.write(f"  是否活跃: {user.is_active}")
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"  ❌ 用户不存在: {username}"))
            return
        self.stdout.write("")
        
        # 2. 检查ApprovalNotification模型
        self.stdout.write(self.style.SUCCESS("【2. 模型检查】"))
        ApprovalNotification = get_approval_notification_model()
        has_model = has_approval_notification()
        
        if has_model and ApprovalNotification:
            self.stdout.write(f"  ✓ ApprovalNotification模型可用")
            self.stdout.write(f"  模型类: {ApprovalNotification.__name__}")
            self.stdout.write(f"  表名: {ApprovalNotification._meta.db_table}")
            
            # 检查字段
            fields = [f.name for f in ApprovalNotification._meta.get_fields()]
            self.stdout.write(f"  字段: {', '.join(fields)}")
        else:
            self.stdout.write(self.style.ERROR("  ❌ ApprovalNotification模型不可用"))
            self.stdout.write(self.style.ERROR("  ❌ 这是导致通知无法显示的主要原因！"))
            self.stdout.write("")
            self.stdout.write("  解决方案：")
            self.stdout.write("  1. 检查 models.py 中是否定义了 ApprovalNotification 模型")
            self.stdout.write("  2. 检查 compat.py 中的导入逻辑")
            return
        self.stdout.write("")
        
        # 3. 检查数据库中的通知记录
        self.stdout.write(self.style.SUCCESS("【3. 数据库记录检查】"))
        cursor = connection.cursor()
        
        # 检查表是否存在
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'plan_approval_notification'
            )
        """)
        table_exists = cursor.fetchone()[0]
        
        if table_exists:
            self.stdout.write("  ✓ 通知表存在: plan_approval_notification")
            
            # 统计通知数量
            cursor.execute("""
                SELECT 
                    COUNT(*) as total,
                    COUNT(*) FILTER (WHERE user_id = %s) as user_total,
                    COUNT(*) FILTER (WHERE user_id = %s AND is_read = false) as user_unread
                FROM plan_approval_notification
            """, [user.id, user.id])
            stats = cursor.fetchone()
            
            self.stdout.write(f"  总通知数: {stats[0]}")
            self.stdout.write(f"  用户通知数: {stats[1]}")
            self.stdout.write(f"  用户未读数: {stats[2]}")
            
            # 查询用户的通知
            if notification_id:
                cursor.execute("""
                    SELECT id, title, content, object_type, object_id, event, is_read, created_at
                    FROM plan_approval_notification
                    WHERE id = %s AND user_id = %s
                """, [notification_id, user.id])
            else:
                cursor.execute("""
                    SELECT id, title, content, object_type, object_id, event, is_read, created_at
                    FROM plan_approval_notification
                    WHERE user_id = %s
                    ORDER BY created_at DESC
                    LIMIT 10
                """, [user.id])
            
            rows = cursor.fetchall()
            if rows:
                self.stdout.write("")
                self.stdout.write(f"  找到 {len(rows)} 条通知记录:")
                for row in rows:
                    self.stdout.write(f"    ID: {row[0]}")
                    self.stdout.write(f"      标题: {row[1]}")
                    self.stdout.write(f"      事件: {row[5]}")
                    self.stdout.write(f"      对象: {row[3]}/{row[4]}")
                    self.stdout.write(f"      已读: {row[6]}")
                    self.stdout.write(f"      时间: {row[7]}")
                    self.stdout.write("")
            else:
                self.stdout.write(self.style.WARNING(f"  ⚠️  用户 {username} 没有通知记录"))
        else:
            self.stdout.write(self.style.ERROR("  ❌ 通知表不存在"))
        self.stdout.write("")
        
        # 4. 检查ORM查询
        self.stdout.write(self.style.SUCCESS("【4. ORM查询检查】"))
        try:
            notifications = ApprovalNotification.objects.filter(user=user)
            total_count = notifications.count()
            unread_count = notifications.filter(is_read=False).count()
            
            self.stdout.write(f"  ✓ ORM查询正常")
            self.stdout.write(f"  总通知数: {total_count}")
            self.stdout.write(f"  未读数: {unread_count}")
            
            if notification_id:
                try:
                    notification = ApprovalNotification.objects.get(id=notification_id, user=user)
                    self.stdout.write("")
                    self.stdout.write(f"  特定通知 (ID: {notification_id}):")
                    self.stdout.write(f"    标题: {notification.title}")
                    self.stdout.write(f"    内容: {notification.content[:50]}...")
                    self.stdout.write(f"    事件: {notification.event}")
                    self.stdout.write(f"    对象: {notification.object_type}/{notification.object_id}")
                    self.stdout.write(f"    已读: {notification.is_read}")
                except ApprovalNotification.DoesNotExist:
                    self.stdout.write(self.style.ERROR(f"  ❌ 通知 ID {notification_id} 不存在或不属于该用户"))
            else:
                # 显示最近的通知
                recent = notifications.order_by('-created_at')[:5]
                if recent:
                    self.stdout.write("")
                    self.stdout.write("  最近5条通知:")
                    for n in recent:
                        self.stdout.write(f"    - ID: {n.id}, 标题: {n.title}, 事件: {n.event}, 已读: {n.is_read}")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"  ❌ ORM查询失败: {str(e)}"))
            import traceback
            self.stdout.write(traceback.format_exc())
        self.stdout.write("")
        
        # 5. 检查API视图
        self.stdout.write(self.style.SUCCESS("【5. API视图检查】"))
        try:
            # 直接测试查询逻辑
            from rest_framework.test import APIRequestFactory
            from rest_framework.request import Request
            
            factory = APIRequestFactory()
            request = factory.get('/api/plan/notifications/')
            request.user = user
            
            # 包装为DRF Request对象
            drf_request = Request(request)
            
            view = NotificationListAPI()
            view.request = drf_request
            
            qs = view.get_queryset()
            api_count = qs.count()
            
            self.stdout.write(f"  ✓ API视图正常")
            self.stdout.write(f"  API返回通知数: {api_count}")
            
            # 测试序列化器
            if api_count > 0:
                serializer = ApprovalNotificationSerializer(qs[:3], many=True)
                self.stdout.write("")
                self.stdout.write("  API返回的前3条通知:")
                for item in serializer.data:
                    self.stdout.write(f"    - ID: {item.get('id')}, 标题: {item.get('title')}")
                    
                # 检查API URL
                self.stdout.write("")
                self.stdout.write("  API端点信息:")
                self.stdout.write("    URL: /api/plan/notifications/")
                self.stdout.write("    查询参数: ?is_read=0 (未读) 或 ?is_read=1 (已读)")
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"  ⚠️  API视图测试失败（不影响功能）: {str(e)}"))
            # 直接测试查询逻辑
            try:
                qs = ApprovalNotification.objects.filter(user=user)
                self.stdout.write(f"  直接查询通知数: {qs.count()}")
            except Exception as e2:
                self.stdout.write(self.style.ERROR(f"  ❌ 直接查询也失败: {str(e2)}"))
        self.stdout.write("")
        
        # 6. 检查通知创建功能
        self.stdout.write(self.style.SUCCESS("【6. 通知创建功能检查】"))
        try:
            test_result = safe_approval_notification(
                user=user,
                title="[测试] 通知系统诊断测试",
                content="这是一条测试通知，用于验证通知创建功能是否正常。",
                object_type='goal',
                object_id='999',
                event='submit',
                is_read=False
            )
            
            if test_result:
                self.stdout.write("  ✓ 通知创建功能正常")
                self.stdout.write(f"  测试通知ID: {test_result.id}")
                self.stdout.write("  ⚠️  已创建测试通知，请手动删除")
            else:
                self.stdout.write(self.style.ERROR("  ❌ 通知创建功能失败（返回None）"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"  ❌ 通知创建功能异常: {str(e)}"))
            import traceback
            self.stdout.write(traceback.format_exc())
        self.stdout.write("")
        
        # 7. 检查事件类型
        self.stdout.write(self.style.SUCCESS("【7. 事件类型检查】"))
        cursor.execute("""
            SELECT DISTINCT event, COUNT(*) as count
            FROM plan_approval_notification
            WHERE user_id = %s
            GROUP BY event
            ORDER BY count DESC
        """, [user.id])
        events = cursor.fetchall()
        
        if events:
            self.stdout.write("  用户通知的事件类型分布:")
            for event, count in events:
                self.stdout.write(f"    {event}: {count} 条")
        else:
            self.stdout.write("  暂无通知记录")
        self.stdout.write("")
        
        # 8. 诊断总结
        self.stdout.write("=" * 80)
        self.stdout.write(self.style.SUCCESS("【诊断总结】"))
        self.stdout.write("=" * 80)
        
        issues = []
        if not has_model:
            issues.append("❌ ApprovalNotification模型不可用")
        if not table_exists:
            issues.append("❌ 通知表不存在")
        
        if not issues:
            self.stdout.write(self.style.SUCCESS("  ✓ 通知系统基本组件正常"))
            self.stdout.write("")
            self.stdout.write("  如果前端仍无法显示通知，请检查：")
            self.stdout.write("")
            self.stdout.write("  1. 前端API调用：")
            self.stdout.write("     - 检查浏览器开发者工具 -> Network 标签")
            self.stdout.write("     - 查找对 /api/plan/notifications/ 的请求")
            self.stdout.write("     - 检查请求状态码（应该是200）")
            self.stdout.write("     - 检查响应数据是否包含通知")
            self.stdout.write("")
            self.stdout.write("  2. 前端代码检查：")
            self.stdout.write("     - 检查控制台是否有JavaScript错误")
            self.stdout.write("     - 检查通知组件是否正确渲染")
            self.stdout.write("     - 检查数据过滤逻辑（is_read等）")
            self.stdout.write("")
            self.stdout.write("  3. 认证和权限：")
            self.stdout.write("     - 确认用户已正确登录")
            self.stdout.write("     - 检查API请求是否包含认证token")
            self.stdout.write("     - 确认用户ID匹配（前端用户ID = 后端用户ID）")
            self.stdout.write("")
            self.stdout.write("  4. 缓存问题：")
            self.stdout.write("     - 尝试硬刷新（Ctrl+F5 或 Cmd+Shift+R）")
            self.stdout.write("     - 清除浏览器缓存")
            self.stdout.write("     - 检查是否有Service Worker缓存")
            self.stdout.write("")
            self.stdout.write("  5. 手动测试API：")
            self.stdout.write(f"     curl -H 'Authorization: Bearer <token>' http://localhost:8000/api/plan/notifications/")
            self.stdout.write("     或使用Postman/浏览器直接访问（需要认证）")
        else:
            self.stdout.write(self.style.ERROR("  发现以下问题："))
            for issue in issues:
                self.stdout.write(f"    {issue}")
        
        self.stdout.write("")
        self.stdout.write("=" * 80)
