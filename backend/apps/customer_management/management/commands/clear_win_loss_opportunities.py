"""
清除赢单与输单测试数据的管理命令

此命令会：
1. 清除所有状态为 'won'（赢单）或 'lost'（输单）的商机及其关联数据
2. 清除所有SET_NULL关联的商机字段（设为NULL）

关联数据包括：
- CASCADE删除：跟进记录、报价、审批记录、状态日志、备案记录、商务洽谈、投标报价、需求沟通
- SET_NULL处理：合同、拜访计划、活动、联系人跟踪、授权书
"""
from django.core.management.base import BaseCommand
from django.db import transaction

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
    ContactTracking,
    AuthorizationLetter,
)
from backend.apps.production_management.models import BusinessContract

# 尝试导入可能不存在的模型
try:
    from backend.apps.customer_management.models import Activity
    HAS_ACTIVITY = True
except ImportError:
    HAS_ACTIVITY = False
    Activity = None

try:
    from backend.apps.customer_management.models import CustomerCommunicationChecklist
    HAS_COMMUNICATION_CHECKLIST = True
except ImportError:
    HAS_COMMUNICATION_CHECKLIST = False
    CustomerCommunicationChecklist = None


class Command(BaseCommand):
    help = '清除所有赢单与输单的测试数据及其关联数据'

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
        self.stdout.write(self.style.WARNING('清除赢单与输单测试数据统计'))
        self.stdout.write(self.style.WARNING('=' * 70))
        self.stdout.write('')

        # 显示统计信息
        self._display_statistics(stats)

        if dry_run:
            self.stdout.write(self.style.WARNING('\n[DRY RUN模式] 仅显示统计，不会实际删除数据'))
            return

        # 确认操作
        if not confirm:
            self.stdout.write(self.style.ERROR('\n⚠️  警告：此操作将永久删除所有赢单与输单的测试数据！'))
            response = input('请输入 "YES" 确认删除: ')
            if response != 'YES':
                self.stdout.write(self.style.SUCCESS('操作已取消'))
                return

        # 执行删除
        try:
            with transaction.atomic():
                self._clear_win_loss_opportunity_data()
                self.stdout.write(self.style.SUCCESS('\n✅ 所有赢单与输单测试数据已成功清除！'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n❌ 删除失败: {str(e)}'))
            raise

    def _get_statistics(self):
        """获取数据统计"""
        # 只统计状态为 'won' 或 'lost' 的商机
        win_loss_opportunities = BusinessOpportunity.objects.filter(status__in=['won', 'lost'])
        opportunity_ids = list(win_loss_opportunities.values_list('id', flat=True))
        
        stats = {
            'opportunities': win_loss_opportunities.count(),
            'won_count': win_loss_opportunities.filter(status='won').count(),
            'lost_count': win_loss_opportunities.filter(status='lost').count(),
            'followups': OpportunityFollowUp.objects.filter(opportunity_id__in=opportunity_ids).count() if opportunity_ids else 0,
            'quotations': OpportunityQuotation.objects.filter(opportunity_id__in=opportunity_ids).count() if opportunity_ids else 0,
            'approvals': OpportunityApproval.objects.filter(opportunity_id__in=opportunity_ids).count() if opportunity_ids else 0,
            'status_logs': OpportunityStatusLog.objects.filter(opportunity_id__in=opportunity_ids).count() if opportunity_ids else 0,
            'filings': OpportunityFiling.objects.filter(opportunity_id__in=opportunity_ids).count() if opportunity_ids else 0,
            'negotiations': BusinessNegotiation.objects.filter(opportunity_id__in=opportunity_ids).count() if opportunity_ids else 0,
            'bidding_quotations': BiddingQuotation.objects.filter(opportunity_id__in=opportunity_ids).count() if opportunity_ids else 0,
            'requirement_communications': CustomerRequirementCommunication.objects.filter(opportunity_id__in=opportunity_ids).count() if opportunity_ids else 0,
            'contracts_with_opportunity': BusinessContract.objects.filter(opportunity_id__in=opportunity_ids).count() if opportunity_ids else 0,
            'visit_plans_with_opportunity': VisitPlan.objects.filter(related_opportunity_id__in=opportunity_ids).count() if opportunity_ids else 0,
            'contact_trackings_with_opportunity': ContactTracking.objects.filter(related_opportunity_id__in=opportunity_ids).count() if opportunity_ids else 0,
            'authorization_letters_with_opportunity': AuthorizationLetter.objects.filter(opportunity_id__in=opportunity_ids).count() if opportunity_ids else 0,
        }
        # 如果存在Activity，统计其关联数据
        if HAS_ACTIVITY and opportunity_ids:
            try:
                stats['activities_with_opportunity'] = Activity.objects.filter(related_opportunity_id__in=opportunity_ids).count()
            except Exception:
                stats['activities_with_opportunity'] = 0
        else:
            stats['activities_with_opportunity'] = 0
        # 如果存在CommunicationChecklist，统计其关联数据
        if HAS_COMMUNICATION_CHECKLIST and opportunity_ids:
            try:
                stats['communication_checklists_with_opportunity'] = CustomerCommunicationChecklist.objects.filter(opportunity_id__in=opportunity_ids).count()
            except Exception:
                stats['communication_checklists_with_opportunity'] = 0
        else:
            stats['communication_checklists_with_opportunity'] = 0
        return stats

    def _display_statistics(self, stats):
        """显示统计信息"""
        self.stdout.write('📊 赢单与输单相关数据统计：')
        self.stdout.write('')
        
        self.stdout.write('【将删除的数据（CASCADE关联）】')
        self.stdout.write(f'  赢单商机: {stats["won_count"]} 条')
        self.stdout.write(f'  输单商机: {stats["lost_count"]} 条')
        self.stdout.write(f'  总计商机: {stats["opportunities"]} 条')
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
            stats.get("activities_with_opportunity", 0) + 
            stats["contact_trackings_with_opportunity"] + 
            stats["authorization_letters_with_opportunity"] +
            stats["communication_checklists_with_opportunity"]
        )
        self.stdout.write(self.style.WARNING(f'总计将清除关联: {total_to_clear} 条记录的关联'))

    def _clear_win_loss_opportunity_data(self):
        """清除赢单与输单商机数据"""
        self.stdout.write('\n开始清除赢单与输单测试数据...')
        self.stdout.write('')

        # 获取所有赢单和输单的商机ID
        win_loss_opportunities = BusinessOpportunity.objects.filter(status__in=['won', 'lost'])
        opportunity_ids = list(win_loss_opportunities.values_list('id', flat=True))
        
        if not opportunity_ids:
            self.stdout.write(self.style.WARNING('  没有找到赢单或输单的商机数据'))
            return

        # 1. 先处理SET_NULL的关联（将关联字段设为NULL）
        self.stdout.write('步骤 1/2: 清除SET_NULL关联...')
        
        contracts_updated = BusinessContract.objects.filter(opportunity_id__in=opportunity_ids).update(opportunity=None)
        if contracts_updated > 0:
            self.stdout.write(f'  ✓ 已清除 {contracts_updated} 个合同的商机关联')
        
        visit_plans_updated = VisitPlan.objects.filter(related_opportunity_id__in=opportunity_ids).update(related_opportunity=None)
        if visit_plans_updated > 0:
            self.stdout.write(f'  ✓ 已清除 {visit_plans_updated} 个拜访计划的商机关联')
        
        # 处理Activity（如果存在）
        if HAS_ACTIVITY:
            try:
                activities_updated = Activity.objects.filter(related_opportunity_id__in=opportunity_ids).update(related_opportunity=None)
                if activities_updated > 0:
                    self.stdout.write(f'  ✓ 已清除 {activities_updated} 个活动的商机关联')
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'  ⚠️  处理活动时出错: {str(e)}'))
        
        contact_trackings_updated = ContactTracking.objects.filter(related_opportunity_id__in=opportunity_ids).update(related_opportunity=None)
        if contact_trackings_updated > 0:
            self.stdout.write(f'  ✓ 已清除 {contact_trackings_updated} 个联系人跟踪的商机关联')
        
        authorization_letters_updated = AuthorizationLetter.objects.filter(opportunity_id__in=opportunity_ids).update(opportunity=None)
        if authorization_letters_updated > 0:
            self.stdout.write(f'  ✓ 已清除 {authorization_letters_updated} 个授权书的商机关联')
        
        # 处理CommunicationChecklist（如果存在）
        if HAS_COMMUNICATION_CHECKLIST:
            try:
                communication_checklists_updated = CustomerCommunicationChecklist.objects.filter(opportunity_id__in=opportunity_ids).update(opportunity=None)
                if communication_checklists_updated > 0:
                    self.stdout.write(f'  ✓ 已清除 {communication_checklists_updated} 个沟通清单的商机关联')
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'  ⚠️  处理沟通清单时出错: {str(e)}'))
        
        self.stdout.write('')

        # 2. 删除所有赢单和输单商机（CASCADE关联会自动删除）
        self.stdout.write('步骤 2/2: 删除赢单与输单商机及其CASCADE关联数据...')
        
        # 统计删除前的数量
        before_counts = {
            'opportunities': win_loss_opportunities.count(),
            'followups': OpportunityFollowUp.objects.filter(opportunity_id__in=opportunity_ids).count(),
            'quotations': OpportunityQuotation.objects.filter(opportunity_id__in=opportunity_ids).count(),
            'approvals': OpportunityApproval.objects.filter(opportunity_id__in=opportunity_ids).count(),
            'status_logs': OpportunityStatusLog.objects.filter(opportunity_id__in=opportunity_ids).count(),
            'filings': OpportunityFiling.objects.filter(opportunity_id__in=opportunity_ids).count(),
            'negotiations': BusinessNegotiation.objects.filter(opportunity_id__in=opportunity_ids).count(),
            'bidding_quotations': BiddingQuotation.objects.filter(opportunity_id__in=opportunity_ids).count(),
            'requirement_communications': CustomerRequirementCommunication.objects.filter(opportunity_id__in=opportunity_ids).count(),
        }
        
        # 删除所有赢单和输单商机（CASCADE会自动删除关联数据）
        deleted_info = win_loss_opportunities.delete()
        deleted_count = deleted_info[0]
        
        self.stdout.write(f'  ✓ 已删除 {deleted_count} 条赢单/输单商机记录')
        if before_counts["followups"] > 0:
            self.stdout.write(f'  ✓ 已自动删除 {before_counts["followups"]} 条跟进记录')
        if before_counts["quotations"] > 0:
            self.stdout.write(f'  ✓ 已自动删除 {before_counts["quotations"]} 条报价记录')
        if before_counts["approvals"] > 0:
            self.stdout.write(f'  ✓ 已自动删除 {before_counts["approvals"]} 条审批记录')
        if before_counts["status_logs"] > 0:
            self.stdout.write(f'  ✓ 已自动删除 {before_counts["status_logs"]} 条状态日志')
        if before_counts["filings"] > 0:
            self.stdout.write(f'  ✓ 已自动删除 {before_counts["filings"]} 条备案记录')
        if before_counts["negotiations"] > 0:
            self.stdout.write(f'  ✓ 已自动删除 {before_counts["negotiations"]} 条商务洽谈记录')
        if before_counts["bidding_quotations"] > 0:
            self.stdout.write(f'  ✓ 已自动删除 {before_counts["bidding_quotations"]} 条投标报价记录')
        if before_counts["requirement_communications"] > 0:
            self.stdout.write(f'  ✓ 已自动删除 {before_counts["requirement_communications"]} 条需求沟通记录')
        
        # 验证删除结果
        self.stdout.write('')
        self.stdout.write('验证删除结果...')
        remaining_win_loss = BusinessOpportunity.objects.filter(status__in=['won', 'lost']).count()
        
        if remaining_win_loss == 0:
            self.stdout.write(self.style.SUCCESS('  ✓ 所有赢单与输单测试数据已成功清除'))
        else:
            self.stdout.write(self.style.WARNING(f'  ⚠️  仍有 {remaining_win_loss} 条赢单/输单商机数据残留'))

