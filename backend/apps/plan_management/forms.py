"""
计划管理模块表单定义
"""
from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db.models import Sum
from datetime import datetime, date
from .models import (
    StrategicGoal, GoalProgressRecord, GoalAdjustment,
    Plan, PlanProgressRecord, PlanIssue, PlanAdjustment
)
from backend.apps.system_management.models import User, Department
from backend.apps.production_management.models import Project
from backend.apps.customer_management.models import BusinessOpportunity


def set_date_fields_default_today(form_instance):
    """
    为表单中所有日期字段设置默认值为当天
    仅在新建时（没有instance.pk）设置默认值
    """
    if form_instance.instance and form_instance.instance.pk:
        return  # 编辑时，不设置默认值
    
    today = date.today()
    for field_name, field in form_instance.fields.items():
        # 检查是否是日期输入字段
        if isinstance(field.widget, forms.DateInput):
            # 如果字段还没有初始值，设置为今天
            if field_name not in form_instance.initial:
                form_instance.fields[field_name].initial = today


class StrategicGoalForm(forms.ModelForm):
    """战略目标表单"""
    
    class Meta:
        model = StrategicGoal
        fields = [
            # 固定字段（前三个）：所属部门、负责人、表单编号
            'responsible_department', 'responsible_person', 'goal_number',
            # 基本信息
            'name', 'level', 'goal_type', 'goal_period', 'status',  # P2-2: 添加 level
            # 目标指标
            'indicator_name', 'indicator_type', 'indicator_unit', 'target_value', 'current_value',
            # 时间信息
            'start_date', 'end_date',
            # 关联信息
            'parent_goal',
        ]
        widgets = {
            'goal_number': forms.TextInput(attrs={
                'class': 'form-control',
                'readonly': True,
                'placeholder': '系统自动生成'
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '请输入目标名称',
                'maxlength': '200'
            }),
            'level': forms.Select(attrs={'class': 'form-select'}),
            'goal_type': forms.Select(attrs={'class': 'form-select'}),
            'goal_period': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'indicator_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '请输入目标指标名称',
                'maxlength': '100'
            }),
            'indicator_type': forms.Select(attrs={'class': 'form-select'}),
            'indicator_unit': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '如：万元、%、个、次等'
            }),
            'target_value': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '0.00'
            }),
            'current_value': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'value': '0',
                'placeholder': '默认0，可在跟踪页面更新'
            }),
            'responsible_person': forms.Select(attrs={'class': 'form-select'}),
            'responsible_department': forms.Select(attrs={'class': 'form-select'}),
            'start_date': forms.DateInput(
                format='%Y-%m-%d',
                attrs={
                    'class': 'form-control',
                    'type': 'date'
                }
            ),
            'end_date': forms.DateInput(
                format='%Y-%m-%d',
                attrs={
                    'class': 'form-control',
                    'type': 'date'
                }
            ),
            'parent_goal': forms.Select(attrs={
                'class': 'form-select',
                'title': '用于目标分解，选择上级目标后，当前目标将成为下级目标'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        # 获取is_draft参数，判断是否是草稿模式
        self.is_draft = kwargs.pop('is_draft', False)
        # 从POST数据中检查action参数
        if 'data' in kwargs and hasattr(kwargs['data'], 'get'):
            action = kwargs['data'].get('action', '')
            if action == 'draft':
                self.is_draft = True
        super().__init__(*args, **kwargs)
        
        # 设置负责人查询集（确保始终有查询集）
        self.fields['responsible_person'].queryset = User.objects.filter(is_active=True)
        
        # 设置部门查询集
        self.fields['responsible_department'].queryset = Department.objects.filter(is_active=True)
        
        # 设置上级目标查询集（排除自己和自己的下级目标）
        if self.instance and self.instance.pk:
            exclude_ids = [self.instance.pk]
            exclude_ids.extend([g.pk for g in self.instance.get_all_descendants()])
            self.fields['parent_goal'].queryset = StrategicGoal.objects.exclude(pk__in=exclude_ids)
        else:
            self.fields['parent_goal'].queryset = StrategicGoal.objects.all()
        
        # 目标编号字段处理：完全由系统自动生成，不允许修改
        self.fields['goal_number'].widget.attrs['readonly'] = True
        self.fields['goal_number'].required = False
        if self.instance and self.instance.pk:
            # 编辑时：显示已有编号，不允许修改
            self.fields['goal_number'].widget.attrs['placeholder'] = '系统自动生成，不可修改'
        else:
            # 新建时：显示提示信息，系统会自动生成
            self.fields['goal_number'].widget.attrs['placeholder'] = '系统将自动生成'
        
        # 如果是草稿模式，将必填字段设置为非必填
        if self.is_draft:
            # 草稿模式下，允许字段为空
            if 'name' in self.fields:
                self.fields['name'].required = False
            if 'goal_type' in self.fields:
                self.fields['goal_type'].required = False
            if 'goal_period' in self.fields:
                self.fields['goal_period'].required = False
            if 'start_date' in self.fields:
                self.fields['start_date'].required = False
            if 'end_date' in self.fields:
                self.fields['end_date'].required = False
            # 草稿模式下，所属部门和负责人也允许为空（虽然通常有默认值）
            if 'responsible_department' in self.fields:
                self.fields['responsible_department'].required = False
            if 'responsible_person' in self.fields:
                self.fields['responsible_person'].required = False
        
        # P2-2: 设置 level 字段的初始值和逻辑
        if self.instance and self.instance.pk:
            # 编辑时：使用现有值
            pass
        else:
            # 新建时：设置默认值
            # 设置所属部门和负责人为只读（默认值，不可修改）
            if user:
                # 先设置默认值
                self.fields['responsible_person'].initial = user
                # 所属部门默认为当前用户所在部门
                user_department = None
                if hasattr(user, 'department') and user.department:
                    user_department = user.department
                elif hasattr(user, 'profile') and hasattr(user.profile, 'department') and user.profile.department:
                    user_department = user.profile.department
                if user_department:
                    self.fields['responsible_department'].initial = user_department
                
                # 然后设置为只读和禁用
                self.fields['responsible_department'].widget.attrs['disabled'] = True
                self.fields['responsible_department'].label = '所属部门（默认，不可修改）'
                self.fields['responsible_person'].widget.attrs['disabled'] = True
                self.fields['responsible_person'].label = '负责人（默认，不可修改）'
            
            # 根据是否有 parent_goal 设置 level
            parent_goal_id = self.data.get('parent_goal') or self.initial.get('parent_goal')
            if parent_goal_id:
                # 有父目标，说明是个人目标
                self.fields['level'].initial = 'personal'
            else:
                # 没有父目标，说明是公司目标
                self.fields['level'].initial = 'company'
            
            # 设置开始日期默认为当天
            today = date.today()
            # 确保初始值正确设置，并且格式化为 YYYY-MM-DD 格式（HTML5 date input 需要的格式）
            self.fields['start_date'].initial = today
            # 同时在 widget 的 attrs 中设置 value，确保 HTML 正确显示
            self.fields['start_date'].widget.attrs['value'] = today.strftime('%Y-%m-%d')
            
            # 根据目标周期自动计算结束日期
            goal_period = self.data.get('goal_period') or self.initial.get('goal_period')
            if goal_period:
                end_date = self._calculate_end_date_by_period(today, goal_period)
                self.fields['end_date'].initial = end_date
                self.fields['end_date'].widget.attrs['value'] = end_date.strftime('%Y-%m-%d')
            else:
                # 如果没有选择目标周期，默认设置为当天（用户选择周期后会通过JavaScript更新）
                self.fields['end_date'].initial = today
                self.fields['end_date'].widget.attrs['value'] = today.strftime('%Y-%m-%d')
    
    def _calculate_end_date_by_period(self, start_date, goal_period):
        """根据目标周期计算结束日期"""
        from datetime import timedelta
        from calendar import monthrange
        
        if goal_period == 'annual':
            # 年度目标：开始日期后1年减1天
            try:
                end_year = start_date.year + 1
                end_month = start_date.month
                end_day = start_date.day
                # 处理2月29日的情况
                if end_month == 2 and end_day == 29:
                    end_day = 28
                return date(end_year, end_month, end_day) - timedelta(days=1)
            except ValueError:
                # 如果日期无效，返回开始日期后365天
                return start_date + timedelta(days=365) - timedelta(days=1)
        elif goal_period == 'half_year':
            # 半年目标：开始日期后6个月减1天
            try:
                end_year = start_date.year
                end_month = start_date.month + 6
                if end_month > 12:
                    end_year += 1
                    end_month -= 12
                # 确保日期有效（处理月末日期）
                max_day = monthrange(end_year, end_month)[1]
                end_day = min(start_date.day, max_day)
                return date(end_year, end_month, end_day) - timedelta(days=1)
            except ValueError:
                # 如果日期无效，返回开始日期后180天
                return start_date + timedelta(days=180) - timedelta(days=1)
        elif goal_period == 'quarterly':
            # 季度目标：开始日期后3个月减1天
            try:
                end_year = start_date.year
                end_month = start_date.month + 3
                if end_month > 12:
                    end_year += 1
                    end_month -= 12
                # 确保日期有效（处理月末日期）
                max_day = monthrange(end_year, end_month)[1]
                end_day = min(start_date.day, max_day)
                return date(end_year, end_month, end_day) - timedelta(days=1)
            except ValueError:
                # 如果日期无效，返回开始日期后90天
                return start_date + timedelta(days=90) - timedelta(days=1)
        else:
            # 默认返回开始日期
            return start_date
    
    def clean(self):
        cleaned_data = super().clean()
        
        # 如果是草稿模式，跳过大部分验证，只做基本的数据处理
        if self.is_draft:
            # 处理 disabled 字段：如果字段被禁用，从 initial 值获取
            if not self.instance or not self.instance.pk:
                # 新建时，如果字段被禁用，使用 initial 值
                if 'responsible_person' in self.fields:
                    if self.fields['responsible_person'].widget.attrs.get('disabled'):
                        if not cleaned_data.get('responsible_person') and self.fields['responsible_person'].initial:
                            cleaned_data['responsible_person'] = self.fields['responsible_person'].initial
                if 'responsible_department' in self.fields:
                    if self.fields['responsible_department'].widget.attrs.get('disabled'):
                        if not cleaned_data.get('responsible_department') and self.fields['responsible_department'].initial:
                            cleaned_data['responsible_department'] = self.fields['responsible_department'].initial
            return cleaned_data
        
        # 处理 disabled 字段：如果字段被禁用，从 initial 值获取
        if not self.instance or not self.instance.pk:
            # 新建时，如果字段被禁用，使用 initial 值
            if self.fields['responsible_person'].widget.attrs.get('disabled'):
                if not cleaned_data.get('responsible_person') and self.fields['responsible_person'].initial:
                    cleaned_data['responsible_person'] = self.fields['responsible_person'].initial
            if self.fields['responsible_department'].widget.attrs.get('disabled'):
                if not cleaned_data.get('responsible_department') and self.fields['responsible_department'].initial:
                    cleaned_data['responsible_department'] = self.fields['responsible_department'].initial
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        target_value = cleaned_data.get('target_value')
        current_value = cleaned_data.get('current_value')
        indicator_type = cleaned_data.get('indicator_type')
        weight = cleaned_data.get('weight')
        goal_period = cleaned_data.get('goal_period')
        goal_number = cleaned_data.get('goal_number')
        
        # 编辑时，确保目标编号不被修改
        if self.instance and self.instance.pk:
            if goal_number and goal_number != self.instance.goal_number:
                # 如果用户尝试修改目标编号，恢复为原值
                cleaned_data['goal_number'] = self.instance.goal_number
        
        # 验证日期范围
        if start_date and end_date:
            if end_date < start_date:
                raise ValidationError({'end_date': '结束日期不能早于开始日期'})
        
        # 验证目标值
        if target_value is not None and target_value <= 0:
            raise ValidationError({'target_value': '目标值必须大于0'})
        
        # 验证当前值
        if current_value is not None and current_value < 0:
            raise ValidationError({'current_value': '当前值不能小于0'})
        
        # 验证百分比型指标
        if indicator_type == 'percentage' and target_value:
            if target_value > 100:
                raise ValidationError({'target_value': '百分比型指标的目标值不能超过100'})
        
        # 验证权重
        if weight is not None:
            if weight < 0 or weight > 100:
                raise ValidationError({'weight': '权重必须在0-100之间'})
            
            # 检查同一周期内权重总和
            if self.instance and self.instance.pk:
                # 编辑时，排除自己
                other_goals = StrategicGoal.objects.filter(
                    goal_period=goal_period
                ).exclude(pk=self.instance.pk)
            else:
                # 新建时
                other_goals = StrategicGoal.objects.filter(goal_period=goal_period)
            
            total_weight = other_goals.aggregate(
                total=Sum('weight')
            )['total'] or 0
            
            if total_weight + weight > 100:
                raise ValidationError({
                    'weight': f'同一周期内所有目标权重总和不能超过100，当前已有{total_weight}，剩余可用{100 - total_weight}'
                })
        
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # 新建时，如果目标编号为空，系统会自动生成（在模型的save方法中）
        # 编辑时，目标编号不可修改，保持原值
        
        if commit:
            instance.save()
            
            # 保存多对多关系
            if 'participants' in self.cleaned_data:
                instance.participants.set(self.cleaned_data['participants'])
            if 'related_projects' in self.cleaned_data:
                instance.related_projects.set(self.cleaned_data['related_projects'])
        
        return instance


class GoalProgressUpdateForm(forms.ModelForm):
    """目标进度更新表单"""
    
    class Meta:
        model = GoalProgressRecord
        fields = ['current_value', 'progress_description', 'notes']
        widgets = {
            'current_value': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '0.00'
            }),
            'progress_description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': '4',
                'placeholder': '请输入进度说明',
                'required': True
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': '2',
                'placeholder': '备注（可选）'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        self.goal = kwargs.pop('goal', None)
        super().__init__(*args, **kwargs)
        
        if self.goal:
            self.fields['current_value'].initial = self.goal.current_value
    
    def clean_current_value(self):
        current_value = self.cleaned_data.get('current_value')
        if current_value is not None and current_value < 0:
            raise ValidationError('当前值不能小于0')
        return current_value
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.goal:
            instance.goal = self.goal
            # 更新目标的当前值
            self.goal.current_value = instance.current_value
            self.goal.save()
        if commit:
            instance.save()
        return instance


class GoalAdjustmentForm(forms.ModelForm):
    """目标调整申请表单"""
    
    class Meta:
        model = GoalAdjustment
        fields = ['adjustment_reason', 'adjustment_content', 'new_target_value', 'new_end_date']
        widgets = {
            'adjustment_reason': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': '3',
                'placeholder': '请输入调整原因',
                'required': True
            }),
            'adjustment_content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': '4',
                'placeholder': '请输入调整内容',
                'required': True
            }),
            'new_target_value': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '新目标值（可选）'
            }),
            'new_end_date': forms.DateInput(
                format='%Y-%m-%d',
                attrs={
                    'class': 'form-control',
                    'type': 'date',
                    'placeholder': '新结束日期（可选）'
                }
            ),
        }
    
    def __init__(self, *args, **kwargs):
        self.goal = kwargs.pop('goal', None)
        super().__init__(*args, **kwargs)
    
    def clean(self):
        cleaned_data = super().clean()
        
        # 处理 disabled 字段：如果字段被禁用，从 initial 值获取
        if not self.instance or not self.instance.pk:
            # 新建时，如果字段被禁用，使用 initial 值
            if self.fields['responsible_person'].widget.attrs.get('disabled'):
                if not cleaned_data.get('responsible_person') and self.fields['responsible_person'].initial:
                    cleaned_data['responsible_person'] = self.fields['responsible_person'].initial
            if self.fields['responsible_department'].widget.attrs.get('disabled'):
                if not cleaned_data.get('responsible_department') and self.fields['responsible_department'].initial:
                    cleaned_data['responsible_department'] = self.fields['responsible_department'].initial
        new_target_value = cleaned_data.get('new_target_value')
        new_end_date = cleaned_data.get('new_end_date')
        
        if new_target_value is not None and new_target_value <= 0:
            raise ValidationError({'new_target_value': '新目标值必须大于0'})
        
        if self.goal and new_end_date:
            if new_end_date < self.goal.start_date:
                raise ValidationError({'new_end_date': '新结束日期不能早于开始日期'})
        
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.goal:
            instance.goal = self.goal
        if commit:
            instance.save()
        return instance


class PlanForm(forms.ModelForm):
    """计划表单"""
    
    class Meta:
        model = Plan
        fields = [
            # 基本信息
            'plan_number', 'name', 'level',
            # 关联信息
            'related_goal', 'plan_period', 'parent_plan', 'related_project',
            # 计划内容
            'content', 'plan_objective',
            # 协作信息
            'collaboration_plan',
            # 时间信息
            'start_time', 'end_time',
            # 责任人信息
            'responsible_person', 'responsible_department',
        ]
        widgets = {
            'plan_number': forms.TextInput(attrs={
                'class': 'form-control',
                'readonly': True,
                'placeholder': '系统自动生成'
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '请输入计划名称',
                'maxlength': '200'
            }),
            'level': forms.Select(attrs={'class': 'form-select'}),
            'plan_period': forms.Select(attrs={'class': 'form-select'}),
            'related_goal': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'parent_plan': forms.Select(attrs={'class': 'form-select'}),
            'content': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '请输入计划内容',
                'maxlength': '5000'
            }),
            'plan_objective': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '请输入计划目标',
                'maxlength': '1000'
            }),
            'start_time': forms.DateInput(
                format='%Y-%m-%d',
                attrs={
                    'class': 'form-control',
                    'type': 'date',
                    'placeholder': '请选择计划开始日期'
                }
            ),
            'end_time': forms.DateInput(
                format='%Y-%m-%d',
                attrs={
                    'class': 'form-control',
                    'type': 'date',
                    'placeholder': '请选择计划结束日期'
                }
            ),
            'responsible_person': forms.Select(attrs={'class': 'form-select'}),
            'responsible_department': forms.Select(attrs={'class': 'form-select'}),
            'collaboration_plan': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': '4',
                'placeholder': '请输入协作计划内容',
                'maxlength': '2000'
            }),
        }
    
    participants = forms.ModelMultipleChoiceField(
        queryset=User.objects.filter(is_active=True),
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-select'}),
        label='协作人员'
    )
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        # 获取is_draft参数，判断是否是草稿模式
        self.is_draft = kwargs.pop('is_draft', False)
        # 从POST数据中检查action参数
        if 'data' in kwargs and hasattr(kwargs['data'], 'get'):
            action = kwargs['data'].get('action', '')
            if action == 'draft':
                self.is_draft = True
        super().__init__(*args, **kwargs)
        
        # 确保删除可能存在的 related_opportunity 字段（如果迁移后仍有残留）
        if 'related_opportunity' in self.fields:
            del self.fields['related_opportunity']
        
        # 设置负责人和协作人员查询集
        self.fields['responsible_person'].queryset = User.objects.filter(is_active=True)
        self.fields['participants'].queryset = User.objects.filter(is_active=True)
        
        # 设置部门查询集
        self.fields['responsible_department'].queryset = Department.objects.filter(is_active=True)
        
        # 新建时：设置所属部门和负责人为只读（默认值，不可修改）
        if not self.instance or not self.instance.pk:
            if user:
                # 先设置默认值
                self.fields['responsible_person'].initial = user
                # 所属部门默认为当前用户所在部门
                user_department = None
                if hasattr(user, 'department') and user.department:
                    user_department = user.department
                elif hasattr(user, 'profile') and hasattr(user.profile, 'department') and user.profile.department:
                    user_department = user.profile.department
                if user_department:
                    self.fields['responsible_department'].initial = user_department
                
                # 然后设置为只读和禁用
                self.fields['responsible_department'].widget.attrs['disabled'] = True
                self.fields['responsible_department'].label = '所属部门（默认，不可修改）'
                self.fields['responsible_person'].widget.attrs['disabled'] = True
                self.fields['responsible_person'].label = '负责人（默认，不可修改）'
        
        # 设置关联战略目标查询集：只显示当前用户负责的目标
        # 状态必须是已发布或进行中，且负责人必须是当前用户
        if user:
            self.fields['related_goal'].queryset = StrategicGoal.objects.filter(
                status__in=['published', 'in_progress'],
                responsible_person=user
            )
        else:
            # 如果没有传入用户，返回空查询集
            self.fields['related_goal'].queryset = StrategicGoal.objects.none()
        # 关联战略目标为必填
        self.fields['related_goal'].required = True
        
        # 设置父计划查询集（只显示公司计划，排除自己和自己的下级计划）
        base_queryset = Plan.objects.filter(level='company')  # 只显示公司计划
        if self.instance and self.instance.pk:
            exclude_ids = [self.instance.pk]
            exclude_ids.extend([p.pk for p in self.instance.get_all_descendants()])
            self.fields['parent_plan'].queryset = base_queryset.exclude(pk__in=exclude_ids)
        else:
            self.fields['parent_plan'].queryset = base_queryset
        
        # 设置关联项目字段：从商机中获取项目信息
        # 获取所有有项目名称的商机，提取项目信息作为选项
        opportunities_with_projects = BusinessOpportunity.objects.filter(
            project_name__isnull=False
        ).exclude(project_name='').select_related('client').order_by('-created_time')
        
        # 创建项目选项列表（从商机中提取）
        project_choices = [('', '-------')]  # 空选项
        seen_projects = set()  # 用于去重
        
        for opp in opportunities_with_projects:
            project_name = opp.project_name.strip() if opp.project_name else ''
            if project_name and project_name not in seen_projects:
                # 显示格式：项目名称（商机：商机名称）
                display_text = project_name
                if opp.name:
                    display_text += f"（商机：{opp.name}）"
                project_choices.append((project_name, display_text))
                seen_projects.add(project_name)
        
        # 如果没有找到有项目名称的商机，尝试显示所有商机（使用商机名称作为项目名称）
        if len(project_choices) == 1:  # 只有空选项
            all_opportunities = BusinessOpportunity.objects.filter(is_active=True).select_related('client').order_by('-created_time')[:50]
            for opp in all_opportunities:
                # 如果没有项目名称，使用商机名称作为项目名称
                project_name = opp.project_name.strip() if opp.project_name else opp.name
                if project_name and project_name not in seen_projects:
                    display_text = project_name
                    if opp.name and opp.name != project_name:
                        display_text += f"（商机：{opp.name}）"
                    project_choices.append((project_name, display_text))
                    seen_projects.add(project_name)
        
        # 将 related_project 改为 ChoiceField，使用商机中的项目数据
        self.fields['related_project'] = forms.ChoiceField(
            choices=project_choices,
            required=False,
            widget=forms.Select(attrs={'class': 'form-select'}),
            label='关联项目',
            help_text='项目信息来源于商机管理'
        )
        
        # 计划编号字段处理：完全由系统自动生成，但必须显示
        # 新建和编辑时都显示，但都是只读的
        self.fields['plan_number'].widget.attrs['readonly'] = True
        self.fields['plan_number'].required = False
        if self.instance and self.instance.pk:
            # 编辑时：显示已有编号
            self.fields['plan_number'].widget.attrs['placeholder'] = '系统自动生成，不可修改'
        else:
            # 新建时：显示提示信息
            self.fields['plan_number'].widget.attrs['placeholder'] = '系统将自动生成'
        
        # 如果是草稿模式，将必填字段设置为非必填
        if self.is_draft:
            # 草稿模式下，允许字段为空
            if 'name' in self.fields:
                self.fields['name'].required = False
            if 'related_goal' in self.fields:
                self.fields['related_goal'].required = False
            if 'plan_period' in self.fields:
                self.fields['plan_period'].required = False
            if 'start_time' in self.fields:
                self.fields['start_time'].required = False
            if 'end_time' in self.fields:
                self.fields['end_time'].required = False
            # 草稿模式下，所属部门和负责人也允许为空（虽然通常有默认值）
            if 'responsible_department' in self.fields:
                self.fields['responsible_department'].required = False
            if 'responsible_person' in self.fields:
                self.fields['responsible_person'].required = False
        
        # 如果是编辑，设置初始值
        if self.instance and self.instance.pk:
            self.fields['participants'].initial = self.instance.participants.all()
            # 将datetime字段转换为date显示
            if self.instance.start_time:
                self.fields['start_time'].initial = self.instance.start_time.date()
            if self.instance.end_time:
                self.fields['end_time'].initial = self.instance.end_time.date()
        else:
            # 新建时，设置默认值
            
            # 设置开始日期默认为当天
            today = date.today()
            self.fields['start_time'].initial = today
            # 同时在 widget 的 attrs 中设置 value，确保 HTML 正确显示
            self.fields['start_time'].widget.attrs['value'] = today.strftime('%Y-%m-%d')
            
            # 根据计划周期自动计算结束日期
            plan_period = self.data.get('plan_period') or self.initial.get('plan_period')
            if plan_period:
                end_date = self._calculate_end_date_by_period(today, plan_period)
                self.fields['end_time'].initial = end_date
                self.fields['end_time'].widget.attrs['value'] = end_date.strftime('%Y-%m-%d')
            else:
                # 如果没有选择计划周期，默认设置为当天（用户选择周期后会通过JavaScript更新）
                self.fields['end_time'].initial = today
                self.fields['end_time'].widget.attrs['value'] = today.strftime('%Y-%m-%d')
    
    def _calculate_end_date_by_period(self, start_date, plan_period):
        """根据计划周期计算结束日期"""
        from datetime import timedelta
        from calendar import monthrange
        
        if plan_period == 'yearly':
            # 年计划：开始日期后1年减1天
            try:
                end_year = start_date.year + 1
                end_month = start_date.month
                end_day = start_date.day
                # 处理2月29日的情况
                if end_month == 2 and end_day == 29:
                    end_day = 28
                return date(end_year, end_month, end_day) - timedelta(days=1)
            except ValueError:
                # 如果日期无效，返回开始日期后365天
                return start_date + timedelta(days=365) - timedelta(days=1)
        elif plan_period == 'quarterly':
            # 季度计划：开始日期后3个月减1天
            try:
                end_year = start_date.year
                end_month = start_date.month + 3
                if end_month > 12:
                    end_year += 1
                    end_month -= 12
                # 确保日期有效（处理月末日期）
                max_day = monthrange(end_year, end_month)[1]
                end_day = min(start_date.day, max_day)
                return date(end_year, end_month, end_day) - timedelta(days=1)
            except ValueError:
                # 如果日期无效，返回开始日期后90天
                return start_date + timedelta(days=90) - timedelta(days=1)
        elif plan_period == 'monthly':
            # 月计划：开始日期后1个月减1天
            try:
                end_year = start_date.year
                end_month = start_date.month + 1
                if end_month > 12:
                    end_year += 1
                    end_month -= 12
                # 确保日期有效（处理月末日期）
                max_day = monthrange(end_year, end_month)[1]
                end_day = min(start_date.day, max_day)
                return date(end_year, end_month, end_day) - timedelta(days=1)
            except ValueError:
                # 如果日期无效，返回开始日期后30天
                return start_date + timedelta(days=30) - timedelta(days=1)
        elif plan_period == 'weekly':
            # 周计划：开始日期后7天减1天（即6天后）
            return start_date + timedelta(days=6)
        elif plan_period == 'daily':
            # 日计划：开始日期当天（即结束日期等于开始日期）
            return start_date
        else:
            # 默认返回开始日期
            return start_date
    
    def clean(self):
        cleaned_data = super().clean()
        
        # 如果是草稿模式，跳过大部分验证，只做基本的数据处理
        if self.is_draft:
            # 处理 disabled 字段：如果字段被禁用，从 initial 值获取
            if not self.instance or not self.instance.pk:
                # 新建时，如果字段被禁用，使用 initial 值
                if 'responsible_person' in self.fields:
                    if self.fields['responsible_person'].widget.attrs.get('disabled'):
                        if not cleaned_data.get('responsible_person') and self.fields['responsible_person'].initial:
                            cleaned_data['responsible_person'] = self.fields['responsible_person'].initial
                if 'responsible_department' in self.fields:
                    if self.fields['responsible_department'].widget.attrs.get('disabled'):
                        if not cleaned_data.get('responsible_department') and self.fields['responsible_department'].initial:
                            cleaned_data['responsible_department'] = self.fields['responsible_department'].initial
            # 草稿模式下，如果有日期数据，仍然需要转换格式
            start_time = cleaned_data.get('start_time')
            end_time = cleaned_data.get('end_time')
            if start_time:
                if isinstance(start_time, datetime):
                    cleaned_data['start_time'] = datetime.combine(start_time.date(), datetime.min.time())
                    cleaned_data['start_time'] = timezone.make_aware(cleaned_data['start_time'])
                elif hasattr(start_time, 'date'):
                    cleaned_data['start_time'] = datetime.combine(start_time, datetime.min.time())
                    cleaned_data['start_time'] = timezone.make_aware(cleaned_data['start_time'])
            if end_time:
                if isinstance(end_time, datetime):
                    cleaned_data['end_time'] = datetime.combine(end_time.date(), datetime.max.time().replace(microsecond=0))
                    cleaned_data['end_time'] = timezone.make_aware(cleaned_data['end_time'])
                elif hasattr(end_time, 'date'):
                    cleaned_data['end_time'] = datetime.combine(end_time, datetime.max.time().replace(microsecond=0))
                    cleaned_data['end_time'] = timezone.make_aware(cleaned_data['end_time'])
            return cleaned_data
        
        # 处理 disabled 字段：如果字段被禁用，从 initial 值获取
        if not self.instance or not self.instance.pk:
            # 新建时，如果字段被禁用，使用 initial 值
            if self.fields['responsible_person'].widget.attrs.get('disabled'):
                if not cleaned_data.get('responsible_person') and self.fields['responsible_person'].initial:
                    cleaned_data['responsible_person'] = self.fields['responsible_person'].initial
            if self.fields['responsible_department'].widget.attrs.get('disabled'):
                if not cleaned_data.get('responsible_department') and self.fields['responsible_department'].initial:
                    cleaned_data['responsible_department'] = self.fields['responsible_department'].initial
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        plan_number = cleaned_data.get('plan_number')
        participants = cleaned_data.get('participants')
        collaboration_plan = cleaned_data.get('collaboration_plan')
        related_goal = cleaned_data.get('related_goal')
        
        # 验证关联战略目标为必填
        if not related_goal:
            raise ValidationError({'related_goal': '关联战略目标为必填项，请选择关联的战略目标'})
        
        # 编辑时，确保计划编号不被修改
        if self.instance and self.instance.pk:
            if plan_number and plan_number != self.instance.plan_number:
                # 如果用户尝试修改计划编号，恢复为原值
                cleaned_data['plan_number'] = self.instance.plan_number
        
        # 将日期转换为datetime（设置为当天的开始时间 00:00:00）
        if start_time:
            if isinstance(start_time, datetime):
                # 如果已经是datetime，只保留日期部分，时间设为00:00:00
                cleaned_data['start_time'] = datetime.combine(start_time.date(), datetime.min.time())
                cleaned_data['start_time'] = timezone.make_aware(cleaned_data['start_time'])
            elif hasattr(start_time, 'date'):
                # 如果是date对象，转换为datetime
                cleaned_data['start_time'] = datetime.combine(start_time, datetime.min.time())
                cleaned_data['start_time'] = timezone.make_aware(cleaned_data['start_time'])
        
        if end_time:
            if isinstance(end_time, datetime):
                # 如果已经是datetime，只保留日期部分，时间设为23:59:59（结束日期包含整天）
                cleaned_data['end_time'] = datetime.combine(end_time.date(), datetime.max.time().replace(microsecond=0))
                cleaned_data['end_time'] = timezone.make_aware(cleaned_data['end_time'])
            elif hasattr(end_time, 'date'):
                # 如果是date对象，转换为datetime
                cleaned_data['end_time'] = datetime.combine(end_time, datetime.max.time().replace(microsecond=0))
                cleaned_data['end_time'] = timezone.make_aware(cleaned_data['end_time'])
        
        # 验证时间范围
        if start_time and end_time:
            start_dt = cleaned_data.get('start_time')
            end_dt = cleaned_data.get('end_time')
            if end_dt < start_dt:
                self.add_error('end_time', '结束时间不能早于开始时间。')
        
        # 注意：周计划重复检查已在视图层面处理，使用messages.error显示弹窗提示
        # 此处不再进行验证，避免重复提示
        
        # 验证协作计划：如果选择了协作人员，必须填写协作计划
        if participants and len(participants) > 0:
            if not collaboration_plan or not collaboration_plan.strip():
                raise ValidationError({'collaboration_plan': '如果选择了协作人员，必须填写协作计划'})
        
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # 设置创建人
        if not instance.pk:
            instance.created_by = self.initial.get('user') or instance.responsible_person
        
        # 新建时，如果计划编号为空，系统会自动生成（在模型的save方法中）
        # 编辑时，计划编号不可修改，保持原值
        
        if commit:
            instance.save()
            
            # 保存多对多关系
            if 'participants' in self.cleaned_data:
                instance.participants.set(self.cleaned_data['participants'])
        
        return instance


class PlanProgressUpdateForm(forms.ModelForm):
    """计划进度更新表单"""
    
    class Meta:
        model = PlanProgressRecord
        fields = ['progress', 'progress_description', 'execution_result', 'execution_issues', 'notes']
        widgets = {
            'progress': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'max': '100',
                'placeholder': '0.00'
            }),
            'progress_description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': '4',
                'placeholder': '请输入进度说明',
                'required': True
            }),
            'execution_result': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': '3',
                'placeholder': '执行结果（可选）'
            }),
            'execution_issues': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': '3',
                'placeholder': '执行问题（可选）'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': '2',
                'placeholder': '备注（可选）'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        self.plan = kwargs.pop('plan', None)
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if self.plan:
            self.fields['progress'].initial = self.plan.progress
    
    def clean_progress(self):
        progress = self.cleaned_data.get('progress')
        if progress is not None:
            if progress < 0 or progress > 100:
                raise ValidationError('进度必须在0-100之间')
        return progress
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.plan:
            instance.plan = self.plan
            # 更新计划的进度
            self.plan.progress = instance.progress
            self.plan.save()
        if self.user:
            instance.recorded_by = self.user
        if commit:
            instance.save()
        return instance


class PlanIssueForm(forms.ModelForm):
    """计划问题表单"""
    
    class Meta:
        model = PlanIssue
        fields = ['title', 'description', 'severity', 'status', 'solution', 'assigned_to']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '请输入问题标题',
                'maxlength': '200'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': '4',
                'placeholder': '请输入问题描述',
                'required': True
            }),
            'severity': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'solution': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': '4',
                'placeholder': '解决方案（可选）'
            }),
            'assigned_to': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.plan = kwargs.pop('plan', None)
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # 设置负责人查询集
        self.fields['assigned_to'].queryset = User.objects.filter(is_active=True)
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.plan:
            instance.plan = self.plan
        if self.user:
            instance.created_by = self.user
        if commit:
            instance.save()
        return instance


class PlanAdjustmentForm(forms.ModelForm):
    """计划调整申请表单"""
    
    class Meta:
        model = PlanAdjustment
        fields = [
            'adjustment_reason',
            'adjustment_content',
            'new_end_time',
        ]
        widgets = {
            'adjustment_reason': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': '4',
                'placeholder': '请输入调整原因',
                'required': True
            }),
            'adjustment_content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': '4',
                'placeholder': '请输入调整内容',
                'required': True
            }),
            'new_end_time': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local',
                'placeholder': '请选择新的截止时间'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        self.plan = kwargs.pop('plan', None)
        super().__init__(*args, **kwargs)
        
        # 如果有关联的计划，设置默认的新截止时间
        if self.plan and self.plan.end_time:
            # 将datetime转换为datetime-local格式（YYYY-MM-DDTHH:mm）
            end_time = self.plan.end_time
            if timezone.is_aware(end_time):
                end_time = timezone.localtime(end_time)
            dt_str = end_time.strftime('%Y-%m-%dT%H:%M')
            self.fields['new_end_time'].initial = dt_str
    
    def clean(self):
        cleaned_data = super().clean()
        
        # 处理 disabled 字段：如果字段被禁用，从 initial 值获取
        if not self.instance or not self.instance.pk:
            # 新建时，如果字段被禁用，使用 initial 值
            if self.fields['responsible_person'].widget.attrs.get('disabled'):
                if not cleaned_data.get('responsible_person') and self.fields['responsible_person'].initial:
                    cleaned_data['responsible_person'] = self.fields['responsible_person'].initial
            if self.fields['responsible_department'].widget.attrs.get('disabled'):
                if not cleaned_data.get('responsible_department') and self.fields['responsible_department'].initial:
                    cleaned_data['responsible_department'] = self.fields['responsible_department'].initial
        new_end_time = cleaned_data.get('new_end_time')
        
        if not self.plan:
            raise ValidationError('计划信息缺失')
        
        # 验证新截止时间必须晚于原截止时间
        if new_end_time and self.plan.end_time:
            # 将datetime转换为timezone-aware进行比较
            if timezone.is_naive(new_end_time):
                new_end_time = timezone.make_aware(new_end_time)
            
            if new_end_time <= self.plan.end_time:
                raise ValidationError({
                    'new_end_time': '新截止时间必须晚于原截止时间'
                })
        
        # 验证计划状态：只有执行中的计划可以申请调整
        if self.plan.status != 'in_progress':
            raise ValidationError('只有执行中的计划可以申请调整')
        
        # 检查是否已有待审批的调整申请
        pending_adjustment = PlanAdjustment.objects.filter(
            plan=self.plan,
            status='pending'
        ).exists()
        
        if pending_adjustment:
            raise ValidationError('该计划已有待审批的调整申请，请等待审批完成后再提交新的申请')
        
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.plan:
            instance.plan = self.plan
            # 记录原截止时间
            instance.original_end_time = self.plan.end_time
        
        if commit:
            instance.save()
        
        return instance

