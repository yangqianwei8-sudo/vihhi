"""
检查逾期账款管理命令
定期检查应收账款和应付账款的逾期情况，并自动更新状态
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Q
from backend.apps.financial_management.models import ReceivableAccount, PayableAccount


class Command(BaseCommand):
    help = '检查并更新逾期账款状态'

    def handle(self, *args, **options):
        today = timezone.now().date()
        
        # 检查逾期应收账款
        overdue_receivables = ReceivableAccount.objects.filter(
            Q(status__in=['pending', 'partial']) &
            Q(due_date__lt=today) &
            Q(remaining_amount__gt=0)
        )
        
        updated_receivables = 0
        for receivable in overdue_receivables:
            if receivable.status != 'overdue':
                receivable.status = 'overdue'
                receivable.save()
                updated_receivables += 1
        
        # 检查逾期应付账款
        overdue_payables = PayableAccount.objects.filter(
            Q(status__in=['pending', 'partial']) &
            Q(due_date__lt=today) &
            Q(remaining_amount__gt=0)
        )
        
        updated_payables = 0
        for payable in overdue_payables:
            if payable.status != 'overdue':
                payable.status = 'overdue'
                payable.save()
                updated_payables += 1
        
        self.stdout.write(
            self.style.SUCCESS(
                f'成功更新 {updated_receivables} 条逾期应收账款，'
                f'{updated_payables} 条逾期应付账款'
            )
        )

