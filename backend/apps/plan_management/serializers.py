"""
计划管理模块序列化器
"""
from rest_framework import serializers
from .models import Plan, StrategicGoal, GoalAlignmentRecord, PlanDecision


class StrategicGoalSerializer(serializers.ModelSerializer):
    """战略目标序列化器"""
    parent_goal = serializers.PrimaryKeyRelatedField(
        queryset=StrategicGoal.objects.all(),
        required=False,
        allow_null=True,
        write_only=True
    )
    
    class Meta:
        model = StrategicGoal
        fields = '__all__'
        read_only_fields = ('goal_number', 'created_time', 'updated_time', 'completion_rate', 'status')
    
    def _save_parent(self, goal, parent):
        if parent:
            GoalAlignmentRecord.objects.update_or_create(
                child_goal=goal,
                defaults={"parent_goal": parent}
            )
        else:
            GoalAlignmentRecord.objects.filter(child_goal=goal).delete()
    
    def create(self, validated_data):
        parent = validated_data.pop("parent_goal", None)
        obj = super().create(validated_data)
        if "parent_goal" in self.initial_data:
            self._save_parent(obj, parent)
        return obj
    
    def update(self, instance, validated_data):
        parent = validated_data.pop("parent_goal", None)
        obj = super().update(instance, validated_data)
        if "parent_goal" in self.initial_data:
            self._save_parent(obj, parent)
        return obj
    
    def validate(self, attrs):
        """
        W1-Fix-1: 禁止在 update/partial_update 中直接修改 status
        """
        if 'status' in getattr(self, 'initial_data', {}):
            raise serializers.ValidationError({
                'status': '不允许直接修改 status，请使用状态流转 action（submit_approval/approve/reject/cancel_approval/change_status）'
            })
        return attrs


class PlanSerializer(serializers.ModelSerializer):
    """计划序列化器"""
    # 修复：plan_type是只读属性（property），不是数据库字段
    # 将其显式声明为只读字段，并支持向后兼容
    plan_type = serializers.CharField(source='plan_type', read_only=True)
    
    class Meta:
        model = Plan
        fields = '__all__'
        read_only_fields = ('plan_number', 'created_time', 'updated_time', 'duration_days', 'alignment_score', 'status', 'plan_type')
    
    def validate_related_goal(self, goal):
        """
        W1-Fix-2: 禁止关联 draft 或 pending_approval 状态的目标（白名单方式）
        """
        if goal is None:
            return goal
        
        # 白名单：只允许已发布/执行中的目标
        allowed_statuses = {'published', 'in_progress'}
        if goal.status not in allowed_statuses:
            raise serializers.ValidationError(
                f"关联目标必须为已发布/执行中的目标，当前目标状态为：{goal.get_status_display()}"
            )
        
        return goal
    
    def validate(self, attrs):
        """
        P1: 禁止在 update/partial_update 中直接修改 status
        status 只能通过裁决接口修改（start-request/cancel-request + decide）
        P2: 支持向后兼容，将plan_type参数映射到level字段
        """
        if 'status' in getattr(self, 'initial_data', {}):
            raise serializers.ValidationError({
                'status': 'status 禁止直接修改，请使用裁决接口（start-request/cancel-request + decide）'
            })
        
        # 修复：向后兼容处理plan_type输入，映射到level字段
        initial_data = getattr(self, 'initial_data', {})
        if 'plan_type' in initial_data and 'level' not in attrs:
            plan_type_value = initial_data.get('plan_type')
            plan_type_to_level_map = {
                'company': 'company',
                'personal': 'personal',
                'department': 'company',  # 部门计划映射为公司计划
                'project': 'company',     # 项目计划映射为公司计划
            }
            mapped_level = plan_type_to_level_map.get(plan_type_value)
            if mapped_level:
                attrs['level'] = mapped_level
        
        return attrs


class PlanDecisionSerializer(serializers.ModelSerializer):
    """计划决策序列化器"""
    plan_number = serializers.CharField(source='plan.plan_number', read_only=True)
    plan_name = serializers.CharField(source='plan.name', read_only=True)
    requested_by_username = serializers.CharField(source='requested_by.username', read_only=True)
    decided_by_username = serializers.CharField(source='decided_by.username', read_only=True, allow_null=True)
    
    class Meta:
        model = PlanDecision
        fields = [
            'id', 'plan', 'plan_number', 'plan_name',
            'request_type', 'decision',
            'requested_by', 'requested_by_username', 'requested_at',
            'decided_by', 'decided_by_username', 'decided_at',
            'reason',
        ]
        read_only_fields = [
            'id', 'plan_number', 'plan_name',
            'requested_by_username', 'requested_at',
            'decided_by_username', 'decided_at',
        ]

