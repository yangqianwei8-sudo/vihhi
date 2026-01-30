from django.db import models
from django.utils import timezone
import logging
from backend.apps.system_management.models import User

logger = logging.getLogger(__name__)

# ==================== 回款管理模块模型 =====================

class PaymentRecord(models.Model):
    """回款记录（实际回款）"""
    PAYMENT_METHOD_CHOICES = [
        ('bank_transfer', '银行转账'),
        ('cash', '现金'),
        ('check', '支票'),
        ('acceptance', '承兑汇票'),
        ('other', '其他'),
    ]
    
    # 关联回款计划（支持项目回款计划和商务回款计划）
    payment_plan_id = models.IntegerField(verbose_name='回款计划ID')
    payment_plan_type = models.CharField(
        max_length=50, 
        choices=[
            ('project', '项目回款计划'),
            ('business', '商务回款计划'),
        ],
        verbose_name='回款计划类型'
    )
    
    # 回款信息
    payment_number = models.CharField(max_length=100, unique=True, verbose_name='回款单号')
    payment_amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='回款金额')
    payment_date = models.DateField(verbose_name='回款日期')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, verbose_name='回款方式')
    
    # 财务信息
    invoice_number = models.CharField(max_length=100, blank=True, verbose_name='发票号码')
    bank_account = models.CharField(max_length=200, blank=True, verbose_name='收款账户')
    receipt_voucher = models.FileField(upload_to='payment_receipts/', null=True, blank=True, verbose_name='收款凭证')
    
    # 状态和审核
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', '待确认'),
            ('confirmed', '已确认'),
            ('rejected', '已拒绝'),
        ],
        default='pending',
        verbose_name='状态'
    )
    confirmed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='confirmed_payments', verbose_name='确认人')
    confirmed_time = models.DateTimeField(null=True, blank=True, verbose_name='确认时间')
    
    # 备注
    notes = models.TextField(blank=True, verbose_name='备注')
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='created_payments', verbose_name='创建人')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    
    class Meta:
        db_table = 'settlement_payment_record'
        verbose_name = '回款记录'
        verbose_name_plural = verbose_name
        ordering = ['-payment_date', '-created_time']
        indexes = [
            models.Index(fields=['payment_plan_type', 'payment_plan_id']),
            models.Index(fields=['payment_number']),
            models.Index(fields=['payment_date']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.payment_number} - ¥{self.payment_amount}"
    
    def save(self, *args, **kwargs):
        # 自动生成回款单号
        if not self.payment_number:
            from django.db.models import Max
            from datetime import datetime
            current_year = datetime.now().year
            max_payment = PaymentRecord.objects.filter(
                payment_number__startswith=f'PAY-{current_year}-'
            ).aggregate(max_num=Max('payment_number'))['max_num']
            
            if max_payment:
                try:
                    seq = int(max_payment.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    seq = 1
            else:
                seq = 1
            
            self.payment_number = f'PAY-{current_year}-{seq:04d}'
        
        super().save(*args, **kwargs)
    
    def get_payment_plan(self):
        """获取关联的回款计划对象"""
        if self.payment_plan_type == 'project':
            # 项目回款计划模型已删除，返回None
            return None
        elif self.payment_plan_type == 'business':
            from backend.apps.production_management.models import BusinessPaymentPlan
            try:
                return BusinessPaymentPlan.objects.get(id=self.payment_plan_id)
            except BusinessPaymentPlan.DoesNotExist:
                return None
        return None
