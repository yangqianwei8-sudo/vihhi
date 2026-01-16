# ==================== 商机完整性检查管理命令 ====================

from django.core.management.base import BaseCommand
from django.db.models import Q, Count
from backend.apps.customer_management.models import BusinessOpportunity


class Command(BaseCommand):
    help = '检查数据库中是否有完整的商机记录'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--detailed',
            action='store_true',
            help='显示详细的检查结果，包括不完整的商机列表',
        )
        parser.add_argument(
            '--min-health-score',
            type=int,
            default=60,
            help='最低健康度评分阈值（默认60分）',
        )
        parser.add_argument(
            '--status',
            type=str,
            help='按状态筛选（potential/initial_contact/requirement_confirmed/quotation/negotiation/won/lost/cancelled）',
        )
    
    def handle(self, *args, **options):
        detailed = options.get('detailed', False)
        min_health_score = options.get('min_health_score', 60)
        status_filter = options.get('status')
        
        self.stdout.write(self.style.SUCCESS('=' * 80))
        self.stdout.write(self.style.SUCCESS('商机完整性检查报告'))
        self.stdout.write(self.style.SUCCESS('=' * 80))
        
        # 基础统计
        total_count = BusinessOpportunity.objects.count()
        active_count = BusinessOpportunity.objects.filter(is_active=True).count()
        
        self.stdout.write(f'\n【基础统计】')
        self.stdout.write(f'  总商机数: {total_count}')
        self.stdout.write(f'  启用商机数: {active_count}')
        self.stdout.write(f'  禁用商机数: {total_count - active_count}')
        
        # 构建查询
        queryset = BusinessOpportunity.objects.all()
        if status_filter:
            queryset = queryset.filter(status=status_filter)
            self.stdout.write(f'\n【筛选条件】状态: {status_filter}')
        
        # 1. 检查必填字段完整性
        self.stdout.write(f'\n【1. 必填字段完整性检查】')
        missing_name = queryset.filter(name__isnull=True).count()
        missing_name_empty = queryset.filter(name='').count()
        missing_client = queryset.filter(client__isnull=True).count()
        missing_business_manager = queryset.filter(business_manager__isnull=True).count()
        missing_created_by = queryset.filter(created_by__isnull=True).count()
        
        complete_required = queryset.exclude(
            Q(name__isnull=True) | Q(name='') |
            Q(client__isnull=True) |
            Q(business_manager__isnull=True) |
            Q(created_by__isnull=True)
        ).count()
        
        self.stdout.write(f'  ✓ 必填字段完整: {complete_required}')
        if missing_name or missing_name_empty:
            self.stdout.write(self.style.WARNING(f'  ✗ 缺少商机名称: {missing_name + missing_name_empty}'))
        if missing_client:
            self.stdout.write(self.style.WARNING(f'  ✗ 缺少关联客户: {missing_client}'))
        if missing_business_manager:
            self.stdout.write(self.style.WARNING(f'  ✗ 缺少负责商务: {missing_business_manager}'))
        if missing_created_by:
            self.stdout.write(self.style.WARNING(f'  ✗ 缺少创建人: {missing_created_by}'))
        
        # 2. 检查重要字段完整性（影响健康度评分）
        self.stdout.write(f'\n【2. 重要字段完整性检查（影响健康度评分）】')
        missing_project_name = queryset.filter(
            Q(project_name__isnull=True) | Q(project_name='')
        ).count()
        missing_project_address = queryset.filter(
            Q(project_address__isnull=True) | Q(project_address='')
        ).count()
        missing_estimated_amount = queryset.filter(
            Q(estimated_amount__isnull=True) | Q(estimated_amount=0)
        ).count()
        missing_expected_sign_date = queryset.filter(
            expected_sign_date__isnull=True
        ).count()
        
        # 计算完整度
        complete_info_fields = queryset.filter(
            ~Q(project_name__isnull=True) & ~Q(project_name=''),
            ~Q(project_address__isnull=True) & ~Q(project_address=''),
            ~Q(estimated_amount__isnull=True) & ~Q(estimated_amount=0),
            expected_sign_date__isnull=False
        ).count()
        
        self.stdout.write(f'  ✓ 所有重要字段完整: {complete_info_fields}')
        if missing_project_name:
            self.stdout.write(self.style.WARNING(f'  ✗ 缺少项目名称: {missing_project_name}'))
        if missing_project_address:
            self.stdout.write(self.style.WARNING(f'  ✗ 缺少项目地址: {missing_project_address}'))
        if missing_estimated_amount:
            self.stdout.write(self.style.WARNING(f'  ✗ 缺少预计金额: {missing_estimated_amount}'))
        if missing_expected_sign_date:
            self.stdout.write(self.style.WARNING(f'  ✗ 缺少预计签约时间: {missing_expected_sign_date}'))
        
        # 3. 检查健康度评分
        self.stdout.write(f'\n【3. 健康度评分检查】')
        high_health = queryset.filter(health_score__gte=min_health_score).count()
        medium_health = queryset.filter(health_score__gte=40, health_score__lt=min_health_score).count()
        low_health = queryset.filter(health_score__lt=40).count()
        
        self.stdout.write(f'  ✓ 高健康度 (≥{min_health_score}分): {high_health}')
        self.stdout.write(f'  ⚠ 中等健康度 (40-{min_health_score-1}分): {medium_health}')
        self.stdout.write(f'  ✗ 低健康度 (<40分): {low_health}')
        
        # 4. 检查状态逻辑完整性
        self.stdout.write(f'\n【4. 状态逻辑完整性检查】')
        
        # 赢单状态检查
        won_opportunities = queryset.filter(status='won')
        won_count = won_opportunities.count()
        won_without_amount = won_opportunities.filter(
            Q(actual_amount__isnull=True) | Q(actual_amount=0)
        ).count()
        won_without_contract = won_opportunities.filter(
            Q(contract_number__isnull=True) | Q(contract_number='')
        ).count()
        won_without_reason = won_opportunities.filter(
            Q(win_reason__isnull=True) | Q(win_reason='')
        ).count()
        
        if won_count > 0:
            self.stdout.write(f'  赢单商机总数: {won_count}')
            if won_without_amount:
                self.stdout.write(self.style.WARNING(f'    ✗ 缺少实际签约金额: {won_without_amount}'))
            if won_without_contract:
                self.stdout.write(self.style.WARNING(f'    ✗ 缺少合同编号: {won_without_contract}'))
            if won_without_reason:
                self.stdout.write(self.style.WARNING(f'    ✗ 缺少赢单原因: {won_without_reason}'))
        
        # 输单状态检查
        lost_opportunities = queryset.filter(status='lost')
        lost_count = lost_opportunities.count()
        lost_without_reason = lost_opportunities.filter(
            Q(loss_reason__isnull=True) | Q(loss_reason='')
        ).count()
        
        if lost_count > 0:
            self.stdout.write(f'  输单商机总数: {lost_count}')
            if lost_without_reason:
                self.stdout.write(self.style.WARNING(f'    ✗ 缺少输单原因: {lost_without_reason}'))
        
        # 5. 检查外键关联有效性
        self.stdout.write(f'\n【5. 外键关联有效性检查】')
        
        # 检查关联客户是否有效
        invalid_clients = queryset.filter(client__isnull=False).exclude(
            client__is_active=True
        ).count()
        if invalid_clients:
            self.stdout.write(self.style.WARNING(f'  ✗ 关联了非启用状态的客户: {invalid_clients}'))
        
        # 检查负责商务是否有效
        invalid_business_managers = queryset.filter(business_manager__isnull=False).exclude(
            business_manager__is_active=True
        ).count()
        if invalid_business_managers:
            self.stdout.write(self.style.WARNING(f'  ✗ 负责商务处于非启用状态: {invalid_business_managers}'))
        
        # 6. 综合完整性评估
        self.stdout.write(f'\n【6. 综合完整性评估】')
        
        # 完全完整的商机：必填字段 + 所有重要字段 + 健康度达标
        fully_complete = queryset.exclude(
            Q(name__isnull=True) | Q(name='') |
            Q(client__isnull=True) |
            Q(business_manager__isnull=True) |
            Q(created_by__isnull=True) |
            Q(project_name__isnull=True) | Q(project_name='') |
            Q(project_address__isnull=True) | Q(project_address='') |
            Q(estimated_amount__isnull=True) | Q(estimated_amount=0) |
            Q(expected_sign_date__isnull=True) |
            Q(health_score__lt=min_health_score)
        ).count()
        
        # 基本完整的商机：必填字段完整
        basically_complete = complete_required
        
        # 不完整的商机
        incomplete = queryset.filter(
            Q(name__isnull=True) | Q(name='') |
            Q(client__isnull=True) |
            Q(business_manager__isnull=True) |
            Q(created_by__isnull=True)
        ).count()
        
        self.stdout.write(self.style.SUCCESS(f'  ✓ 完全完整（必填+重要字段+健康度≥{min_health_score}）: {fully_complete}'))
        self.stdout.write(f'  ✓ 基本完整（必填字段完整）: {basically_complete}')
        self.stdout.write(self.style.WARNING(f'  ✗ 不完整（缺少必填字段）: {incomplete}'))
        
        # 7. 详细列表（如果启用）
        if detailed:
            self.stdout.write(f'\n【7. 详细列表】')
            
            # 显示完全完整的商机
            if fully_complete > 0:
                self.stdout.write(f'\n完全完整的商机列表（前20条）:')
                complete_list = queryset.exclude(
                    Q(name__isnull=True) | Q(name='') |
                    Q(client__isnull=True) |
                    Q(business_manager__isnull=True) |
                    Q(created_by__isnull=True) |
                    Q(project_name__isnull=True) | Q(project_name='') |
                    Q(project_address__isnull=True) | Q(project_address='') |
                    Q(estimated_amount__isnull=True) | Q(estimated_amount=0) |
                    Q(expected_sign_date__isnull=True) |
                    Q(health_score__lt=min_health_score)
                ).select_related('client', 'business_manager', 'created_by')[:20]
                
                for opp in complete_list:
                    self.stdout.write(
                        f'  ✓ {opp.opportunity_number} - {opp.name} '
                        f'(客户: {opp.client.name if opp.client else "N/A"}, '
                        f'健康度: {opp.health_score}, '
                        f'状态: {opp.get_status_display()})'
                    )
            
            # 显示不完整的商机
            if incomplete > 0:
                self.stdout.write(f'\n不完整的商机列表（前20条）:')
                incomplete_list = queryset.filter(
                    Q(name__isnull=True) | Q(name='') |
                    Q(client__isnull=True) |
                    Q(business_manager__isnull=True) |
                    Q(created_by__isnull=True)
                ).select_related('client', 'business_manager', 'created_by')[:20]
                
                for opp in incomplete_list:
                    issues = []
                    if not opp.name:
                        issues.append('缺少商机名称')
                    if not opp.client:
                        issues.append('缺少关联客户')
                    if not opp.business_manager:
                        issues.append('缺少负责商务')
                    if not opp.created_by:
                        issues.append('缺少创建人')
                    
                    self.stdout.write(
                        self.style.WARNING(
                            f'  ✗ {opp.opportunity_number or "未编号"} - {opp.name or "未命名"} '
                            f'({", ".join(issues)})'
                        )
                    )
        
        # 8. 按状态统计
        self.stdout.write(f'\n【8. 按状态统计】')
        status_stats = queryset.values('status').annotate(
            count=Count('id')
        ).order_by('-count')
        
        for stat in status_stats:
            status_display = dict(BusinessOpportunity.STATUS_CHOICES).get(stat['status'], stat['status'])
            self.stdout.write(f'  {status_display}: {stat["count"]}')
        
        self.stdout.write(self.style.SUCCESS('\n' + '=' * 80))
        self.stdout.write(self.style.SUCCESS('检查完成'))
        self.stdout.write(self.style.SUCCESS('=' * 80))
