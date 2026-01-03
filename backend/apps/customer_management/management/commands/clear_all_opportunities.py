"""
清除所有商机数据的管理命令

此命令会：
1. 清除所有SET_NULL关联的商机字段（设为NULL）
2. 删除所有商机及其CASCADE关联的数据

关联数据包括：
- CASCADE删除：跟进记录、报价、审批记录、状态日志、备案记录、商务洽谈、投标报价、需求沟通
- SET_NULL处理：合同、拜访计划、活动、联系人跟踪、授权书
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Count

from backend.apps.customer_management.models import (
    BusinessOpportunity,
    OpportunityFollowUp,
    OpportunityQuotation,
    OpportunityApproval,
    OpportunityStatusLog,
    OpportunityFiling,
    BusinessNegotiation,
    BiddingQuotation,
    CustomerRequirementCommunication,
    VisitPlan,
    Activity,
    ContactTracking,
    AuthorizationLetter,
)
from backend.apps.production_management.models import BusinessContract

# 尝试导入CommunicationChecklist（如果存在）
try:
    from backend.apps.customer_management.models import CustomerCommunicationChecklist
    HAS_COMMUNICATION_CHECKLIST = True
except ImportError:
    HAS_COMMUNICATION_CHECKLIST = False
    CustomerCommunicationChecklist = None


class Command(BaseCommand):
    help = '清除所有商机数据及其关联数据'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='仅显示将要删除的数据统计，不实际删除',
        )
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='跳过确认提示，直接执行删除',
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        confirm = options.get('confirm', False)

        # 统计数据
        stats = self._get_statistics()

        self.stdout.write(self.style.WARNING('=' * 70))
        self.stdout.write(self.style.WARNING('清除商机数据统计'))
        self.stdout.write(self.style.WARNING('=' * 70))
        self.stdout.write('')

        # 显示统计信息
        self._display_statistics(stats)

        if dry_run:
            self.stdout.write(self.style.WARNING('\n[DRY RUN模式] 仅显示统计，不会实际删除数据'))
            return

        # 确认操作
        if not confirm:
            self.stdout.write(self.style.ERROR('\n⚠️  警告：此操作将永久删除所有商机数据！'))
            response = input('请输入 "YES" 确认删除: ')
            if response != 'YES':
                self.stdout.write(self.style.SUCCESS('操作已取消'))
                return

        # 执行删除
        try:
            with transaction.atomic():
                self._clear_opportunity_data()
                self.stdout.write(self.style.SUCCESS('\n✅ 所有商机数据已成功清除！'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n❌ 删除失败: {str(e)}'))
            raise

    def _get_statistics(self):
        """获取数据统计"""
        stats = {
            'opportunities': BusinessOpportunity.objects.count(),
            'followups': OpportunityFollowUp.objects.count(),
            'quotations': OpportunityQuotation.objects.count(),
            'approvals': OpportunityApproval.objects.count(),
            'status_logs': OpportunityStatusLog.objects.count(),
            'filings': OpportunityFiling.objects.count(),
            'negotiations': BusinessNegotiation.objects.count(),
            'bidding_quotations': BiddingQuotation.objects.count(),
            'requirement_communications': CustomerRequirementCommunication.objects.count(),
            'contracts_with_opportunity': BusinessContract.objects.filter(opportunity__isnull=False).count(),
            'visit_plans_with_opportunity': VisitPlan.objects.filter(related_opportunity__isnull=False).count(),
            'activities_with_opportunity': Activity.objects.filter(related_opportunity__isnull=False).count(),
            'contact_trackings_with_opportunity': ContactTracking.objects.filter(related_opportunity__isnull=False).count(),
            'authorization_letters_with_opportunity': AuthorizationLetter.objects.filter(opportunity__isnull=False).count(),
        }
        # 如果存在CommunicationChecklist，统计其关联数据
        if HAS_COMMUNICATION_CHECKLIST:
            try:
                stats['communication_checklists_with_opportunity'] = CustomerCommunicationChecklist.objects.filter(opportunity__isnull=False).count()
            except Exception:
                stats['communication_checklists_with_opportunity'] = 0
        else:
            stats['communication_checklists_with_opportunity'] = 0
        return stats

    def _display_statistics(self, stats):
        """显示统计信息"""
        self.stdout.write('📊 商机相关数据统计：')
        self.stdout.write('')
        
        self.stdout.write('【将删除的数据（CASCADE关联）】')
        self.stdout.write(f'  商机: {stats["opportunities"]} 条')
        self.stdout.write(f'  跟进记录: {stats["followups"]} 条')
        self.stdout.write(f'  报价记录: {stats["quotations"]} 条')
        self.stdout.write(f'  审批记录: {stats["approvals"]} 条')
        self.stdout.write(f'  状态日志: {stats["status_logs"]} 条')
        self.stdout.write(f'  备案记录: {stats["filings"]} 条')
        self.stdout.write(f'  商务洽谈: {stats["negotiations"]} 条')
        self.stdout.write(f'  投标报价: {stats["bidding_quotations"]} 条')
        self.stdout.write(f'  需求沟通: {stats["requirement_communications"]} 条')
        self.stdout.write('')

        self.stdout.write('【将清除关联的数据（SET_NULL处理）】')
        self.stdout.write(f'  合同关联: {stats["contracts_with_opportunity"]} 条（将设为NULL）')
        self.stdout.write(f'  拜访计划关联: {stats["visit_plans_with_opportunity"]} 条（将设为NULL）')
        self.stdout.write(f'  活动关联: {stats["activities_with_opportunity"]} 条（将设为NULL）')
        self.stdout.write(f'  联系人跟踪关联: {stats["contact_trackings_with_opportunity"]} 条（将设为NULL）')
        self.stdout.write(f'  授权书关联: {stats["authorization_letters_with_opportunity"]} 条（将设为NULL）')
        if stats["communication_checklists_with_opportunity"] > 0:
            self.stdout.write(f'  沟通清单关联: {stats["communication_checklists_with_opportunity"]} 条（将设为NULL）')
        self.stdout.write('')

        total_to_delete = (
            stats["opportunities"] +
            stats["followups"] +
            stats["quotations"] +
            stats["approvals"] +
            stats["status_logs"] +
            stats["filings"] +
            stats["negotiations"] +
            stats["bidding_quotations"] +
            stats["requirement_communications"]
        )
        self.stdout.write(self.style.WARNING(f'总计将删除: {total_to_delete} 条记录'))
        total_to_clear = (
            stats["contracts_with_opportunity"] + 
            stats["visit_plans_with_opportunity"] + 
            stats["activities_with_opportunity"] + 
            stats["contact_trackings_with_opportunity"] + 
            stats["authorization_letters_with_opportunity"] +
            stats["communication_checklists_with_opportunity"]
        )
        self.stdout.write(self.style.WARNING(f'总计将清除关联: {total_to_clear} 条记录的关联'))

    def _clear_opportunity_data(self):
        """清除商机数据"""
        self.stdout.write('\n开始清除商机数据...')
        self.stdout.write('')

        # 1. 先处理SET_NULL的关联（将关联字段设为NULL）
        self.stdout.write('步骤 1/2: 清除SET_NULL关联...')
        
        contracts_updated = BusinessContract.objects.filter(opportunity__isnull=False).update(opportunity=None)
        if contracts_updated > 0:
            self.stdout.write(f'  ✓ 已清除 {contracts_updated} 个合同的商机关联')
        
        visit_plans_updated = VisitPlan.objects.filter(related_opportunity__isnull=False).update(related_opportunity=None)
        if visit_plans_updated > 0:
            self.stdout.write(f'  ✓ 已清除 {visit_plans_updated} 个拜访计划的商机关联')
        
        activities_updated = Activity.objects.filter(related_opportunity__isnull=False).update(related_opportunity=None)
        if activities_updated > 0:
            self.stdout.write(f'  ✓ 已清除 {activities_updated} 个活动的商机关联')
        
        contact_trackings_updated = ContactTracking.objects.filter(related_opportunity__isnull=False).update(related_opportunity=None)
        if contact_trackings_updated > 0:
            self.stdout.write(f'  ✓ 已清除 {contact_trackings_updated} 个联系人跟踪的商机关联')
        
        authorization_letters_updated = AuthorizationLetter.objects.filter(opportunity__isnull=False).update(opportunity=None)
        if authorization_letters_updated > 0:
            self.stdout.write(f'  ✓ 已清除 {authorization_letters_updated} 个授权书的商机关联')
        
        # 处理CommunicationChecklist（如果存在）
        if HAS_COMMUNICATION_CHECKLIST:
            try:
                communication_checklists_updated = CustomerCommunicationChecklist.objects.filter(opportunity__isnull=False).update(opportunity=None)
                if communication_checklists_updated > 0:
                    self.stdout.write(f'  ✓ 已清除 {communication_checklists_updated} 个沟通清单的商机关联')
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'  ⚠️  处理沟通清单时出错: {str(e)}'))
        
        self.stdout.write('')

        # 2. 删除所有商机（CASCADE关联会自动删除）
        self.stdout.write('步骤 2/2: 删除商机及其CASCADE关联数据...')
        
        # 统计删除前的数量
        before_counts = {
            'opportunities': BusinessOpportunity.objects.count(),
            'followups': OpportunityFollowUp.objects.count(),
            'quotations': OpportunityQuotation.objects.count(),
            'approvals': OpportunityApproval.objects.count(),
            'status_logs': OpportunityStatusLog.objects.count(),
            'filings': OpportunityFiling.objects.count(),
            'negotiations': BusinessNegotiation.objects.count(),
            'bidding_quotations': BiddingQuotation.objects.count(),
            'requirement_communications': CustomerRequirementCommunication.objects.count(),
        }
        
        # 删除所有商机（CASCADE会自动删除关联数据）
        deleted_info = BusinessOpportunity.objects.all().delete()
        deleted_count = deleted_info[0]
        
        self.stdout.write(f'  ✓ 已删除 {deleted_count} 条商机记录')
        self.stdout.write(f'  ✓ 已自动删除 {before_counts["followups"]} 条跟进记录')
        self.stdout.write(f'  ✓ 已自动删除 {before_counts["quotations"]} 条报价记录')
        self.stdout.write(f'  ✓ 已自动删除 {before_counts["approvals"]} 条审批记录')
        self.stdout.write(f'  ✓ 已自动删除 {before_counts["status_logs"]} 条状态日志')
        self.stdout.write(f'  ✓ 已自动删除 {before_counts["filings"]} 条备案记录')
        self.stdout.write(f'  ✓ 已自动删除 {before_counts["negotiations"]} 条商务洽谈记录')
        self.stdout.write(f'  ✓ 已自动删除 {before_counts["bidding_quotations"]} 条投标报价记录')
        self.stdout.write(f'  ✓ 已自动删除 {before_counts["requirement_communications"]} 条需求沟通记录')
        
        # 验证删除结果
        self.stdout.write('')
        self.stdout.write('验证删除结果...')
        remaining_opportunities = BusinessOpportunity.objects.count()
        remaining_followups = OpportunityFollowUp.objects.count()
        remaining_quotations = OpportunityQuotation.objects.count()
        remaining_approvals = OpportunityApproval.objects.count()
        remaining_status_logs = OpportunityStatusLog.objects.count()
        remaining_filings = OpportunityFiling.objects.count()
        remaining_negotiations = BusinessNegotiation.objects.count()
        remaining_bidding_quotations = BiddingQuotation.objects.count()
        remaining_requirement_communications = CustomerRequirementCommunication.objects.count()
        
        if (remaining_opportunities == 0 and 
            remaining_followups == 0 and 
            remaining_quotations == 0 and 
            remaining_approvals == 0 and 
            remaining_status_logs == 0 and 
            remaining_filings == 0 and 
            remaining_negotiations == 0 and 
            remaining_bidding_quotations == 0 and 
            remaining_requirement_communications == 0):
            self.stdout.write(self.style.SUCCESS('  ✓ 所有商机数据已成功清除'))
        else:
            self.stdout.write(self.style.WARNING('  ⚠️  仍有残留数据：'))
            if remaining_opportunities > 0:
                self.stdout.write(f'     - 商机: {remaining_opportunities} 条')
            if remaining_followups > 0:
                self.stdout.write(f'     - 跟进记录: {remaining_followups} 条')
            if remaining_quotations > 0:
                self.stdout.write(f'     - 报价记录: {remaining_quotations} 条')
            if remaining_approvals > 0:
                self.stdout.write(f'     - 审批记录: {remaining_approvals} 条')
            if remaining_status_logs > 0:
                self.stdout.write(f'     - 状态日志: {remaining_status_logs} 条')
            if remaining_filings > 0:
                self.stdout.write(f'     - 备案记录: {remaining_filings} 条')
            if remaining_negotiations > 0:
                self.stdout.write(f'     - 商务洽谈: {remaining_negotiations} 条')
            if remaining_bidding_quotations > 0:
                self.stdout.write(f'     - 投标报价: {remaining_bidding_quotations} 条')
            if remaining_requirement_communications > 0:
                self.stdout.write(f'     - 需求沟通: {remaining_requirement_communications} 条')

