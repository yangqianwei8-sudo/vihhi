"""
发文跟踪服务
支持邮件、快递、现场送达、易签宝、短信等多种报送方式的跟踪
"""
import logging
import json
from typing import Dict, Optional, Tuple
from django.utils import timezone
from django.core.mail import send_mail, EmailMessage
from django.conf import settings

from .models import OutgoingDocumentTracking, DeliveryMethod
from .express_service import query_express_tracking

logger = logging.getLogger(__name__)


class TrackingService:
    """跟踪服务基类"""
    
    @staticmethod
    def update_tracking_status(tracking: OutgoingDocumentTracking, status: str, **kwargs):
        """更新跟踪状态"""
        tracking.status = status
        tracking.updated_at = timezone.now()
        
        # 根据状态更新时间戳
        if status == 'sent':
            tracking.sent_at = timezone.now()
        elif status == 'received':
            tracking.received_at = timezone.now()
        elif status == 'confirmed':
            tracking.confirmed_at = timezone.now()
        elif status == 'completed':
            tracking.completed_at = timezone.now()
        
        # 更新其他字段
        for key, value in kwargs.items():
            if hasattr(tracking, key):
                setattr(tracking, key, value)
        
        tracking.save()
        logger.info(f"跟踪记录 {tracking.id} 状态已更新为: {status}")


class EmailTrackingService(TrackingService):
    """邮件跟踪服务"""
    
    COMPANY_EMAIL = 'whkj@vihgroup.com.cn'
    
    @staticmethod
    def send_email(tracking: OutgoingDocumentTracking) -> Tuple[bool, str]:
        """
        发送邮件并创建跟踪记录
        
        Args:
            tracking: 跟踪记录对象
            
        Returns:
            (success, message)
        """
        try:
            document = tracking.document
            
            # 构建邮件内容
            subject = tracking.email_subject or f"【发文】{document.title}"
            
            # 收件人邮箱列表 - 优先从notes解析获取所有收件人，如果为空则从tracking.email_to获取
            recipient_emails = []
            import json
            
            # 尝试从notes字段解析收件人信息（EMAIL_RECIPIENTS_JSON格式）
            if tracking.notes and 'EMAIL_RECIPIENTS_JSON:' in tracking.notes:
                try:
                    json_part = tracking.notes.split('EMAIL_RECIPIENTS_JSON:')[1].strip()
                    if '\n' in json_part:
                        json_part = json_part.split('\n')[0].strip()
                    recipients_list = json.loads(json_part)
                    if recipients_list:
                        # 提取所有收件人的邮箱
                        for recipient in recipients_list:
                            email = recipient.get('email', '').strip()
                            if email and email not in recipient_emails:
                                recipient_emails.append(email)
                except (json.JSONDecodeError, ValueError, IndexError, KeyError) as e:
                    logger.warning(f"解析EMAIL_RECIPIENTS_JSON失败: {str(e)}")
            
            # 如果没有从JSON中获取到，尝试从 EMAIL_RECIPIENTS 获取（旧格式，逗号分隔）
            if not recipient_emails and tracking.notes and 'EMAIL_RECIPIENTS:' in tracking.notes:
                try:
                    emails_part = tracking.notes.split('EMAIL_RECIPIENTS:')[1].strip()
                    if '\n' in emails_part:
                        emails_part = emails_part.split('\n')[0].strip()
                    emails = [e.strip() for e in emails_part.split(',') if e.strip()]
                    recipient_emails = emails
                except (IndexError, AttributeError) as e:
                    logger.warning(f"解析EMAIL_RECIPIENTS失败: {str(e)}")
            
            # 如果还是为空，使用tracking.email_to作为备选
            if not recipient_emails and tracking.email_to:
                recipient_emails = [tracking.email_to]
            
            # 如果还是为空，使用document.recipient_email作为最后的备选
            if not recipient_emails and document.recipient_email:
                recipient_emails = [document.recipient_email]
            
            if not recipient_emails:
                return False, "收件人邮箱为空，请检查跟踪记录的收件人配置"
            
            # 使用第一个收件人邮箱作为主要收件人（用于日志和跟踪记录）
            recipient_email = recipient_emails[0]
            
            # 生成跟踪ID
            import hashlib
            import base64
            
            # 生成唯一的跟踪ID
            tracking_id = base64.urlsafe_b64encode(
                hashlib.md5(f"{tracking.id}_{document.id}_{timezone.now().isoformat()}".encode()).digest()
            ).decode('utf-8').rstrip('=')
            
            # 构建跟踪像素URL
            # 优先使用配置的SITE_URL，其次从ALLOWED_HOSTS推断，最后使用默认值
            site_url = getattr(settings, 'SITE_URL', None)
            if not site_url:
                # 从ALLOWED_HOSTS中获取第一个非localhost的域名
                allowed_hosts = getattr(settings, 'ALLOWED_HOSTS', [])
                if allowed_hosts:
                    # 过滤掉localhost和127.0.0.1以及内网IP
                    public_hosts = [h for h in allowed_hosts if h not in ['localhost', '127.0.0.1'] and not h.startswith('10.')]
                    if public_hosts:
                        # 优先使用Sealos域名（生产环境）
                        sealos_domains = [h for h in public_hosts if 'sealosbja.site' in h]
                        if sealos_domains:
                            domain = sealos_domains[0]
                        else:
                            # 如果没有Sealos域名，使用第一个公共域名
                            domain = public_hosts[0]
                        
                        # 判断是否使用HTTPS（根据CSRF_TRUSTED_ORIGINS或域名判断）
                        csrf_origins = getattr(settings, 'CSRF_TRUSTED_ORIGINS', [])
                        use_https = any('https://' in origin and domain in origin for origin in csrf_origins)
                        protocol = 'https' if use_https else 'http'
                        site_url = f"{protocol}://{domain}"
                        logger.info(f"从ALLOWED_HOSTS推断站点URL: {site_url} (域名: {domain})")
                    else:
                        # 如果没有公共域名，使用第一个allowed_host
                        domain = allowed_hosts[0]
                        site_url = f"http://{domain}"
                        logger.warning(f"使用本地域名: {site_url}，跟踪功能可能无法正常工作")
                else:
                    # 最后尝试从Site模型获取
                    try:
                        from django.contrib.sites.models import Site
                        current_site = Site.objects.get_current()
                        site_url = f"http://{current_site.domain}"
                        logger.info(f"从Site模型获取站点URL: {site_url}")
                    except:
                        # 如果都失败，使用默认值（但会记录警告）
                        site_url = 'http://localhost:8000'
                        logger.error(f"无法确定站点URL，使用默认值 {site_url}，跟踪功能将无法正常工作！")
            
            tracking_url = f"{site_url}/delivery/email-tracking/{tracking_id}/"
            logger.info(f"生成邮件跟踪URL: {tracking_url} (tracking_id={tracking_id}, 收件人={', '.join(recipient_emails)})")
            
            # 构建HTML格式的邮件内容（直接显示完整内容）
            html_message = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
</head>
<body>
    <div style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto;">
        <h2 style="color: #2c3e50; text-align: center;">【发文】{document.title}</h2>
        
        <div style="background-color: #f5f5f5; padding: 20px; margin: 20px 0; border-left: 4px solid #3498db; border-radius: 4px;">
            <p style="margin: 10px 0;"><strong>发文编号：</strong>{document.document_number}</p>
            <p style="margin: 10px 0;"><strong>文件标题：</strong>{document.title}</p>
            <p style="margin: 10px 0;"><strong>收文单位：</strong>{document.recipient}</p>
            <p style="margin: 10px 0;"><strong>联系人：</strong>{document.recipient_contact or '无'}</p>
            <p style="margin: 10px 0;"><strong>联系电话：</strong>{document.recipient_phone or '无'}</p>
        </div>
        
        <div style="margin: 30px 0;">
            <h3 style="color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px;">文件内容：</h3>
            <div style="background-color: #fdfdfd; padding: 20px; border: 1px solid #ddd; border-radius: 4px; white-space: pre-wrap; word-break: break-word;">
                {document.content or '无'}
            </div>
        </div>
        
        {f'''
        <div style="margin: 30px 0;">
            <h3 style="color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px;">摘要：</h3>
            <div style="background-color: #fdfdfd; padding: 20px; border: 1px solid #ddd; border-radius: 4px; white-space: pre-wrap; word-break: break-word;">
                {document.summary or '无'}
            </div>
        </div>
        ''' if document.summary else ''}
        
        <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">
        <p style="color: #7f8c8d; font-size: 11px; text-align: center;">
            此邮件由维海科技信息化管理平台自动发送 | 如有疑问，请联系发件人
        </p>
    </div>
    
    <!-- 邮件跟踪像素（1x1透明图片）
         注意：某些邮件客户端（如QQ邮箱、Gmail）默认阻止外部图片加载以保护隐私
         如果跟踪像素未触发，系统管理员可以在跟踪详情页面手动标记为已读 -->
    <img src="{tracking_url}" width="1" height="1" style="width: 1px; height: 1px; border: 0; position: absolute; left: -9999px;" alt="" />
</body>
</html>
            """
            
            # 纯文本版本（用于不支持HTML的邮件客户端）
            text_message = f"""
【发文】{document.title}

发文编号：{document.document_number}
文件标题：{document.title}
收文单位：{document.recipient}
联系人：{document.recipient_contact or '无'}
联系电话：{document.recipient_phone or '无'}

文件内容：
{document.content or '无'}

{f'''
摘要：
{document.summary or '无'}

''' if document.summary else ''}
---
此邮件由维海科技信息化管理平台自动发送
            """
            
            # 更新跟踪记录
            tracking.email_subject = subject
            tracking.email_to = recipient_email
            tracking.email_tracking_id = tracking_id
            tracking.status = 'sending'
            tracking.save()
            
            # 更新文档的邮件跟踪ID
            document.email_tracking_id = tracking_id
            document.save(update_fields=['email_tracking_id'])
            
            # 发送邮件（使用公司对公邮箱）
            # 发送给所有收件人
            email = EmailMessage(
                subject=subject,
                body=text_message,
                from_email=EmailTrackingService.COMPANY_EMAIL,
                to=recipient_emails,
            )
            
            # 设置HTML内容
            email.content_subtype = "html"
            email.body = html_message
            
            # 注意：不添加已读回执请求（Disposition-Notification-To），因为：
            # 1. 收件人看到"对方希望接到你的已读回执"提示通常不会理会，体验不好
            # 2. 已使用跟踪像素（tracking pixel）来隐式检测邮件是否被打开，更友好
            # 3. 跟踪像素是1x1透明图片，收件人无感知，不会影响用户体验
            
            # 如果有附件，添加附件
            attachment_added = False
            if document.attachment:
                try:
                    import os
                    attachment_name = None
                    attachment_content = None
                    
                    # 方法1: 尝试从本地文件系统读取（适用于默认存储）
                    if hasattr(document.attachment, 'path'):
                        try:
                            attachment_path = document.attachment.path
                            if os.path.exists(attachment_path):
                                attachment_name = os.path.basename(document.attachment.name)
                                # 读取文件内容
                                with open(attachment_path, 'rb') as f:
                                    attachment_content = f.read()
                                logger.info(f"从本地文件系统读取附件: {attachment_name} (路径: {attachment_path}, 大小: {len(attachment_content)} 字节)")
                            else:
                                logger.warning(f"附件文件路径不存在: {attachment_path} (附件名: {document.attachment.name})")
                        except Exception as e:
                            logger.warning(f"从本地路径读取附件失败: {str(e)}")
                    
                    # 方法2: 如果方法1失败，尝试从存储后端读取
                    if not attachment_content and hasattr(document.attachment, 'storage'):
                        try:
                            if document.attachment.storage.exists(document.attachment.name):
                                attachment_name = os.path.basename(document.attachment.name)
                                with document.attachment.storage.open(document.attachment.name, 'rb') as f:
                                    attachment_content = f.read()
                                logger.info(f"从存储后端读取附件: {attachment_name} (大小: {len(attachment_content)} 字节)")
                            else:
                                logger.warning(f"存储后端中附件文件不存在: {document.attachment.name}")
                        except Exception as e:
                            logger.warning(f"从存储后端读取附件失败: {str(e)}")
                    
                    # 方法3: 如果前两种方法都失败，尝试直接读取文件对象
                    if not attachment_content and hasattr(document.attachment, 'read'):
                        try:
                            document.attachment.seek(0)  # 重置文件指针
                            attachment_content = document.attachment.read()
                            attachment_name = os.path.basename(document.attachment.name) if hasattr(document.attachment, 'name') else 'attachment'
                            logger.info(f"直接从文件对象读取附件: {attachment_name} (大小: {len(attachment_content)} 字节)")
                        except Exception as e:
                            logger.warning(f"从文件对象读取附件失败: {str(e)}")
                    
                    # 如果成功读取附件内容，添加到邮件
                    if attachment_content and attachment_name:
                        # 获取MIME类型
                        import mimetypes
                        mime_type, _ = mimetypes.guess_type(attachment_name)
                        if not mime_type:
                            mime_type = 'application/octet-stream'
                        
                        email.attach(attachment_name, attachment_content, mime_type)
                        attachment_added = True
                        logger.info(f"✅ 邮件附件已成功添加: {attachment_name} (MIME类型: {mime_type}, 大小: {len(attachment_content)} 字节)")
                    else:
                        logger.error(f"❌ 无法读取附件内容: {document.attachment.name if hasattr(document.attachment, 'name') else '未知'}")
                        
                except Exception as e:
                    logger.error(f"❌ 添加邮件附件失败: {str(e)}", exc_info=True)
                    # 附件添加失败不影响邮件发送，继续发送邮件
            else:
                logger.info("该发文没有附件，跳过附件添加")
            
            # 记录附件添加结果
            if not attachment_added and document.attachment:
                logger.warning(f"⚠️ 警告: 发文 {document.document_number} 有附件字段，但附件未能成功添加到邮件中")
            
            # 发送邮件
            email.send()
            
            # 更新跟踪记录
            tracking.status = 'sent'
            tracking.email_sent_at = timezone.now()
            tracking.email_message_id = email.message_id if hasattr(email, 'message_id') else ''
            tracking.sent_at = timezone.now()
            tracking.error_message = ''  # 清空之前的错误信息
            tracking.save()
            
            logger.info(f"邮件已发送: {subject} -> {', '.join(recipient_emails)}")
            return True, "邮件发送成功"
            
        except Exception as e:
            logger.error(f"发送邮件失败: {str(e)}", exc_info=True)
            tracking.status = 'failed'
            tracking.error_message = str(e)
            tracking.save()
            return False, f"发送失败：{str(e)}"
    
    @staticmethod
    def check_email_status(tracking: OutgoingDocumentTracking) -> Tuple[bool, str]:
        """
        检查邮件状态（读取状态等）
        
        注意：通过跟踪像素检测邮件是否被打开
        """
        # 如果邮件已被读取，返回成功
        if tracking.email_read_at:
            return True, f"邮件已于 {tracking.email_read_at.strftime('%Y-%m-%d %H:%M:%S')} 被读取"
        
        # 检查文档的邮件读取时间
        document = tracking.document
        if document.email_read_at:
            # 同步到跟踪记录
            tracking.email_read_at = document.email_read_at
            tracking.status = 'read'
            tracking.save()
            return True, f"邮件已于 {document.email_read_at.strftime('%Y-%m-%d %H:%M:%S')} 被读取"
        
        return False, "邮件尚未被读取"
    
    @staticmethod
    def mark_email_as_read(tracking_id: str) -> Tuple[bool, str]:
        """
        标记邮件为已读取（通过跟踪像素触发或手动标记）
        
        Args:
            tracking_id: 跟踪ID
            
        Returns:
            (success, message)
        """
        try:
            from .models import OutgoingDocumentTracking
            from django.utils import timezone
            from django.db import transaction
            
            # 验证跟踪ID格式
            if not tracking_id or len(tracking_id) < 10:
                logger.warning(f"标记邮件为已读：无效的跟踪ID格式: tracking_id={tracking_id}")
                return False, "无效的跟踪ID"
            
            # 使用事务确保数据一致性
            with transaction.atomic():
                # 查找跟踪记录（使用select_for_update防止并发问题）
                tracking = OutgoingDocumentTracking.objects.select_for_update().filter(
                    email_tracking_id=tracking_id
                ).select_related('document', 'delivery_method').first()
                
                if not tracking:
                    # 尝试通过文档查找
                    from .models import OutgoingDocument
                    document = OutgoingDocument.objects.filter(email_tracking_id=tracking_id).first()
                    if document:
                        # 创建或更新跟踪记录
                        tracking = OutgoingDocumentTracking.objects.select_for_update().filter(
                            document=document
                        ).select_related('document', 'delivery_method').first()
                        if tracking:
                            tracking.email_tracking_id = tracking_id
                            tracking.save(update_fields=['email_tracking_id'])
                
                if not tracking:
                    logger.warning(f"标记邮件为已读：未找到跟踪ID为 {tracking_id} 的跟踪记录")
                    return False, "未找到跟踪记录"
                
                # 检查是否为邮件方式
                if not tracking.delivery_method or tracking.delivery_method.code != 'email':
                    logger.warning(f"标记邮件为已读：跟踪记录 {tracking.id} 不是邮件方式")
                    return False, "此跟踪记录不是邮件方式"
                
                # 如果已经标记为已读，不重复处理（但返回成功，因为目标状态已达成）
                if tracking.email_read_at:
                    logger.debug(f"标记邮件为已读：跟踪记录 {tracking.id} 已标记为已读，跳过重复处理")
                    return True, "邮件已标记为已读"
                
                # 记录标记前状态（用于日志）
                old_status = tracking.status
                document_number = tracking.document.document_number if tracking.document else 'N/A'
                
                # 标记为已读
                read_time = timezone.now()
                tracking.email_read_at = read_time
                tracking.status = 'read'
                # 邮件已读 = 已接收
                if not tracking.received_at:
                    tracking.received_at = read_time
                tracking.save(update_fields=['email_read_at', 'status', 'received_at'])
                
                logger.info(f"✅ 邮件跟踪记录已标记为已读: tracking_id={tracking_id}, 跟踪记录ID={tracking.id}, 文档={document_number}, 状态={old_status}->read")
                
                # 同步到文档并处理状态流转
                document = tracking.document
                if document:
                    document.email_read_at = read_time
                    # 邮件已读 = 已接收
                    if not document.received_at:
                        document.received_at = read_time
                    
                    # 邮件已读 = 已完成（跳过确认步骤）
                    # 更新跟踪记录状态为已完成
                    tracking.status = 'completed'
                    tracking.completed_at = read_time
                    tracking.save(update_fields=['status', 'completed_at'])
                    
                    # 如果文档状态为 sent，自动流转到 completed（邮件已读表示已完成送达）
                    if document.status == 'sent':
                        try:
                            document.transition_to('completed', actor=None, comment='邮件已读，自动完成')
                            logger.info(f"✅ 邮件已读，文档状态自动流转到已完成: 文档={document.document_number}")
                        except ValueError as e:
                            # 如果状态流转失败（可能已经流转过），记录警告但不影响已读标记
                            logger.warning(f"⚠️ 邮件已读，但文档状态流转失败: 文档={document.document_number}, 错误={str(e)}")
                    
                    document.save()
                    logger.info(f"✅ 文档状态已同步: 文档={document.document_number}, email_read_at={read_time}, received_at={document.received_at}")
            
            return True, "邮件已标记为已读"
            
        except Exception as e:
            logger.error(f"❌ 标记邮件为已读失败: tracking_id={tracking_id}, error={str(e)}", exc_info=True)
            return False, f"处理失败：{str(e)}"


class ExpressTrackingService(TrackingService):
    """快递跟踪服务（使用快递100 API）"""
    
    @staticmethod
    def update_express_info(tracking: OutgoingDocumentTracking, company: str, number: str) -> Tuple[bool, str]:
        """
        更新快递信息并查询状态
        
        Args:
            tracking: 跟踪记录对象
            company: 快递公司名称
            number: 快递单号
            
        Returns:
            (success, message)
        """
        try:
            tracking.express_company = company
            tracking.express_number = number
            tracking.save()
            
            # 查询快递状态（如果查询失败，仍然返回成功，因为信息已保存）
            query_success, query_message = ExpressTrackingService.query_express_status(tracking)
            
            if query_success:
                return True, f"快递信息已更新，状态查询成功：{query_message}"
            else:
                # 如果查询失败，但信息已保存，返回部分成功
                # 常见错误："没该功能权限" 表示快递100账户未开通实时查询功能
                if "没该功能权限" in query_message or "权限" in query_message:
                    return True, f"快递信息已保存，但查询状态失败：{query_message}（提示：可能是快递100账户未开通实时查询功能，或需要检查API配置）"
                else:
                    return True, f"快递信息已保存，但查询状态失败：{query_message}"
            
        except Exception as e:
            logger.error(f"更新快递信息失败: {str(e)}")
            return False, f"更新失败：{str(e)}"
    
    @staticmethod
    def query_express_status(tracking: OutgoingDocumentTracking) -> Tuple[bool, str]:
        """
        查询快递状态（使用快递100 API）
        
        Args:
            tracking: 跟踪记录对象
            
        Returns:
            (success, message)
        """
        try:
            if not tracking.express_company or not tracking.express_number:
                return False, "快递公司或快递单号为空"
            
            # 调用快递100 API
            success, logistics_data, message = query_express_tracking(
                tracking.express_company,
                tracking.express_number
            )
            
            if success:
                # 更新跟踪记录
                tracking.express_status = logistics_data.get('status_text', '')
                tracking.express_tracking_data = logistics_data
                tracking.express_last_update = timezone.now()
                
                # 根据快递状态更新跟踪状态
                status_code = logistics_data.get('status', '0')
                if status_code == '0':  # 在途
                    tracking.status = 'in_transit'
                elif status_code == '3':  # 已签收 = 已接收 = 已完成（跳过确认步骤）
                    tracking.status = 'completed'
                    tracking.received_at = timezone.now()
                    tracking.completed_at = timezone.now()
                elif status_code in ['2', '4', '6', '14']:  # 疑难、退签、退回、拒签
                    tracking.status = 'rejected'
                    tracking.express_reject_time = timezone.now()
                    
                    # 从跟踪数据中提取退回原因和详情
                    tracks = logistics_data.get('tracks', [])
                    reject_detail_parts = []
                    
                    # 查找最新的退回/拒收相关记录（通常是最新的记录）
                    for track in tracks[:5]:  # 只检查最新的5条记录
                        context = track.get('context', '') or track.get('acceptStation', '') or ''
                        if context:
                            reject_detail_parts.append(context)
                    
                    # 合并所有详情文本用于分析
                    reject_text = ' '.join(reject_detail_parts).lower()
                    
                    # 根据状态码和跟踪信息判断退回原因
                    if status_code == '2':  # 疑难
                        # 默认原因
                        tracking.express_reject_reason = 'contact_failed'
                        if not reject_detail_parts:
                            reject_detail_parts.append('联系不到收件人')
                    elif status_code == '4':  # 退签
                        tracking.express_reject_reason = 'recipient_refused'
                        if not reject_detail_parts:
                            reject_detail_parts.append('收件人拒收')
                    elif status_code == '6':  # 退回
                        tracking.express_reject_reason = 'delivery_failed'
                        if not reject_detail_parts:
                            reject_detail_parts.append('快递退回')
                    elif status_code == '14':  # 收件人拒签
                        tracking.express_reject_reason = 'recipient_refused'
                        if not reject_detail_parts:
                            reject_detail_parts.append('收件人拒签')
                    
                    # 从跟踪信息中提取更具体的原因（覆盖默认原因）
                    if '联系' in reject_text or '电话' in reject_text or '无人' in reject_text or '无法联系' in reject_text:
                        tracking.express_reject_reason = 'contact_failed'
                    elif '地址' in reject_text or '不详' in reject_text or '错误' in reject_text or '地址不详' in reject_text:
                        tracking.express_reject_reason = 'address_error'
                    elif '拒' in reject_text or '不收' in reject_text or '拒收' in reject_text or '拒签' in reject_text:
                        tracking.express_reject_reason = 'recipient_refused'
                    elif '不存在' in reject_text or '无此人' in reject_text or '查无此人' in reject_text:
                        tracking.express_reject_reason = 'recipient_not_found'
                    
                    # 保存退回详情（取最新的3条记录）
                    if reject_detail_parts:
                        tracking.express_reject_detail = '\n'.join(reject_detail_parts[:3])
                    else:
                        tracking.express_reject_detail = logistics_data.get('status_text', '')
                    
                    logger.warning(f"快递退回/拒收: tracking_id={tracking.id}, 状态码={status_code}, 原因={tracking.get_express_reject_reason_display()}, 详情={tracking.express_reject_detail[:100]}")
                else:
                    tracking.status = 'in_transit'
                
                tracking.save()
                logger.info(f"快递状态已更新: {tracking.express_company} {tracking.express_number} -> {tracking.express_status}")
                return True, "查询成功"
            else:
                tracking.error_message = message
                tracking.save()
                return False, message
                
        except Exception as e:
            logger.error(f"查询快递状态失败: {str(e)}", exc_info=True)
            tracking.error_message = str(e)
            tracking.save()
            return False, f"查询失败：{str(e)}"


class HandDeliveryTrackingService(TrackingService):
    """现场送达跟踪服务"""
    
    @staticmethod
    def checkin(tracking: OutgoingDocumentTracking, location: str, latitude: float, 
                longitude: float, photo=None, user=None) -> Tuple[bool, str]:
        """
        现场送达打卡
        
        Args:
            tracking: 跟踪记录对象
            location: 送达地点
            latitude: 纬度
            longitude: 经度
            photo: 送达照片
            user: 送达人
            
        Returns:
            (success, message)
        """
        try:
            tracking.hand_delivery_location = location
            tracking.hand_delivery_latitude = latitude
            tracking.hand_delivery_longitude = longitude
            tracking.hand_delivery_checkin_at = timezone.now()
            tracking.hand_delivery_checkin_by = user
            
            if photo:
                tracking.hand_delivery_photo = photo
            
            # 更新状态：现场送达 = 已接收 = 已完成（跳过确认步骤）
            tracking.status = 'completed'
            tracking.received_at = timezone.now()
            tracking.completed_at = timezone.now()
            tracking.save()
            
            logger.info(f"现场送达打卡成功: {location} ({latitude}, {longitude})")
            return True, "打卡成功"
            
        except Exception as e:
            logger.error(f"现场送达打卡失败: {str(e)}")
            return False, f"打卡失败：{str(e)}"


class YisignTrackingService(TrackingService):
    """易签宝跟踪服务"""
    
    @staticmethod
    def create_contract(tracking: OutgoingDocumentTracking, contract_data: Dict) -> Tuple[bool, str]:
        """
        创建易签宝合同
        
        Args:
            tracking: 跟踪记录对象
            contract_data: 合同数据
            
        Returns:
            (success, message)
        """
        # TODO: 实现易签宝API集成
        # 需要根据易签宝的API文档来实现
        try:
            # 示例：创建合同
            # contract_id = yisign_api.create_contract(contract_data)
            # tracking.yisign_contract_id = contract_id
            # tracking.yisign_contract_url = f"https://yisign.com/contract/{contract_id}"
            # tracking.status = 'sent'
            # tracking.save()
            
            logger.warning("易签宝API集成待实现")
            return False, "易签宝API集成待实现"
            
        except Exception as e:
            logger.error(f"创建易签宝合同失败: {str(e)}")
            return False, f"创建失败：{str(e)}"
    
    @staticmethod
    def handle_callback(tracking: OutgoingDocumentTracking, callback_data: Dict) -> Tuple[bool, str]:
        """
        处理易签宝回调
        
        Args:
            tracking: 跟踪记录对象
            callback_data: 回调数据
            
        Returns:
            (success, message)
        """
        try:
            # 保存回调数据
            tracking.yisign_callback_data = callback_data
            tracking.yisign_status = callback_data.get('status', '')
            
            # 根据状态更新跟踪状态
            status = callback_data.get('status', '')
            if status == 'signed':
                tracking.status = 'confirmed'
                tracking.yisign_signed_at = timezone.now()
                tracking.yisign_signed_by = callback_data.get('signed_by', '')
                tracking.confirmed_at = timezone.now()
            elif status == 'rejected':
                tracking.status = 'rejected'
            elif status == 'expired':
                tracking.status = 'failed'
            
            tracking.save()
            logger.info(f"易签宝回调处理成功: {status}")
            return True, "回调处理成功"
            
        except Exception as e:
            logger.error(f"处理易签宝回调失败: {str(e)}")
            return False, f"处理失败：{str(e)}"


class SmsTrackingService(TrackingService):
    """短信跟踪服务（使用阿里云短信服务）"""
    
    @staticmethod
    def send_sms(tracking: OutgoingDocumentTracking) -> Tuple[bool, str]:
        """
        发送短信并创建跟踪记录（使用阿里云短信服务）
        
        Args:
            tracking: 跟踪记录对象
            
        Returns:
            (success, message)
        """
        try:
            document = tracking.document
            
            # 验证手机号
            if not tracking.sms_phone:
                return False, "收件人手机号为空，请检查跟踪记录的收件人配置"
            
            # 验证手机号格式（简单验证）
            import re
            phone_pattern = r'^1[3-9]\d{9}$'
            if not re.match(phone_pattern, tracking.sms_phone):
                return False, f"手机号格式不正确：{tracking.sms_phone}"
            
            # 验证短信内容
            if not tracking.sms_content:
                # 如果没有内容，使用默认格式
                tracking.sms_content = f"【发文通知】发文编号：{document.document_number}，文件标题：{document.title}。详情请查看邮件或联系我司。"
            
            # 检查阿里云短信配置
            access_key_id = getattr(settings, 'ALIYUN_SMS_ACCESS_KEY_ID', '')
            access_key_secret = getattr(settings, 'ALIYUN_SMS_ACCESS_KEY_SECRET', '')
            sign_name = getattr(settings, 'ALIYUN_SMS_SIGN_NAME', '维海科技')
            template_code = getattr(settings, 'ALIYUN_SMS_TEMPLATE_CODE', '')
            region = getattr(settings, 'ALIYUN_SMS_REGION', 'cn-hangzhou')
            
            if not access_key_id or not access_key_secret:
                logger.error("阿里云短信服务未配置：缺少 AccessKey ID 或 AccessKey Secret")
                return False, "短信服务未配置，请联系管理员配置阿里云短信服务"
            
            # 尝试导入阿里云SDK
            try:
                from alibabacloud_dysmsapi20170525.client import Client as DysmsapiClient
                from alibabacloud_tea_openapi import models as open_api_models
                from alibabacloud_dysmsapi20170525 import models as dysmsapi_models
                from alibabacloud_tea_util.client import Client as UtilClient
            except ImportError:
                logger.error("阿里云短信SDK未安装，请运行：pip install alibabacloud-dysmsapi20170525")
                return False, "短信服务SDK未安装，请联系管理员安装阿里云短信SDK"
            
            # 创建阿里云短信客户端
            # 根据阿里云官方文档，短信服务的endpoint固定为 dysmsapi.aliyuncs.com
            # 参考Java SDK示例：setEndpointOverride("dysmsapi.aliyuncs.com")
            # region_id 用于指定服务区域，但不影响endpoint
            config = open_api_models.Config(
                access_key_id=access_key_id.strip(),
                access_key_secret=access_key_secret.strip(),
                region_id=region,  # 设置区域ID，如：cn-hangzhou
                endpoint='dysmsapi.aliyuncs.com',  # 短信服务endpoint固定为dysmsapi.aliyuncs.com
                connect_timeout=10000,  # 连接超时：10秒（参考Java示例：connectionTimeout(Duration.ofSeconds(10))）
                read_timeout=10000,  # 读取超时：10秒（参考Java示例：responseTimeout(Duration.ofSeconds(10))）
                protocol='https'  # 使用HTTPS协议
            )
            client = DysmsapiClient(config)
            
            # 构建短信内容
            # 如果配置了模板代码，使用模板发送；否则使用内容发送
            if template_code:
                # 使用模板发送（推荐方式）
                # 模板变量：unit_name（企业/组织名称）、type（通知类型）、title（通知标题）
                # 模板内容：${unit_name}新增一则${type}通知，标题:《${title}》，请您及时查阅哦
                document = tracking.document
                
                # 构建模板参数
                # unit_name: 使用公司名称或收文单位
                unit_name = document.recipient or '维海科技'
                
                # type: 通知类型，根据文件类型或阶段判断
                if document.file_category:
                    type_value = document.file_category.name
                elif document.stage:
                    stage_names = {
                        'conversion': '转化',
                        'contract': '合同',
                        'production': '生产',
                        'settlement': '结算',
                        'payment': '回款',
                        'after_sales': '售后',
                        'litigation': '诉讼',
                    }
                    type_value = stage_names.get(document.stage, '文件')
                else:
                    type_value = '文件'
                
                # title: 文件标题
                title_value = document.title or '无标题'
                
                # 构建模板参数
                template_params = {
                    'unit_name': unit_name,
                    'type': type_value,
                    'title': title_value
                }
                
                request = dysmsapi_models.SendSmsRequest(
                    phone_numbers=tracking.sms_phone,
                    sign_name=sign_name,
                    template_code=template_code,
                    template_param=json.dumps(template_params)
                )
            else:
                # 如果没有配置模板，尝试直接发送（需要短信服务支持）
                # 注意：阿里云短信服务通常需要模板，直接发送可能不支持
                logger.warning("未配置短信模板代码，尝试使用默认方式发送")
                request = dysmsapi_models.SendSmsRequest(
                    phone_numbers=tracking.sms_phone,
                    sign_name=sign_name,
                    template_code='SMS_123456789',  # 默认模板，需要替换为实际模板
                    template_param=json.dumps({'content': tracking.sms_content})
                )
            
            # 发送短信
            response = client.send_sms(request)
            
            # 检查响应
            if response.status_code == 200 and response.body.code == 'OK':
                # 发送成功
                tracking.sms_message_id = response.body.biz_id or f"SMS_{tracking.id}_{int(timezone.now().timestamp())}"
                tracking.sms_sent_at = timezone.now()
                tracking.sms_status = '发送成功'
                tracking.sent_at = timezone.now()
                tracking.status = 'sent'
                tracking.error_message = ''  # 清空之前的错误信息
                tracking.save()
                
                logger.info(f"短信发送成功: tracking_id={tracking.id}, phone={tracking.sms_phone}, biz_id={tracking.sms_message_id}")
                return True, "短信发送成功"
            else:
                # 发送失败
                error_code = response.body.code if response.body else 'UNKNOWN'
                error_message = response.body.message if response.body else '发送失败'
                
                tracking.sms_status = '发送失败'
                tracking.error_message = f"{error_code}: {error_message}"
                tracking.status = 'failed'
                tracking.save()
                
                logger.error(f"短信发送失败: tracking_id={tracking.id}, phone={tracking.sms_phone}, error={error_code}: {error_message}")
                return False, f"短信发送失败：{error_message}（错误代码：{error_code}）"
            
        except ImportError as e:
            logger.error(f"导入阿里云SDK失败: {str(e)}")
            return False, f"短信服务SDK未安装：{str(e)}，请运行：pip install alibabacloud-dysmsapi20170525"
        except Exception as e:
            logger.error(f"发送短信失败: {str(e)}", exc_info=True)
            tracking.sms_status = '发送失败'
            tracking.error_message = str(e)
            tracking.status = 'failed'
            tracking.save()
            return False, f"发送失败：{str(e)}"
    
    @staticmethod
    def handle_callback(tracking: OutgoingDocumentTracking, callback_data: Dict) -> Tuple[bool, str]:
        """
        处理短信服务商回调（如送达状态回调）
        
        Args:
            tracking: 跟踪记录对象
            callback_data: 回调数据
            
        Returns:
            (success, message)
        """
        try:
            # 保存回调数据
            tracking.sms_callback_data = callback_data
            tracking.sms_status = callback_data.get('status', '')
            
            # 根据状态更新跟踪状态
            status = callback_data.get('status', '')
            if status == 'delivered' or status == 'success':
                # 短信已送达 = 已接收 = 已完成
                tracking.status = 'completed'
                tracking.received_at = timezone.now()
                tracking.completed_at = timezone.now()
            elif status == 'failed' or status == 'rejected':
                tracking.status = 'failed'
            
            tracking.save()
            logger.info(f"短信回调处理成功: status={status}")
            return True, "回调处理成功"
            
        except Exception as e:
            logger.error(f"处理短信回调失败: {str(e)}")
            return False, f"处理失败：{str(e)}"


class TrackingServiceFactory:
    """跟踪服务工厂"""
    
    @staticmethod
    def get_service(delivery_method_code: str):
        """
        根据报送方式代码获取对应的跟踪服务
        
        Args:
            delivery_method_code: 报送方式代码（如：email, express, hand_delivery, yisign, sms）
            
        Returns:
            跟踪服务实例
        """
        service_map = {
            'email': EmailTrackingService,
            'express': ExpressTrackingService,
            'hand_delivery': HandDeliveryTrackingService,
            'yisign': YisignTrackingService,
            'sms': SmsTrackingService,
        }
        
        service_class = service_map.get(delivery_method_code)
        if service_class:
            return service_class()
        else:
            raise ValueError(f"不支持的报送方式：{delivery_method_code}")

