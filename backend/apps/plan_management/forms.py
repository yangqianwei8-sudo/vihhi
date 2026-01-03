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
    Plan, PlanProgressRecord, PlanIssue
)
from backend.apps.system_management.models import User, Department
from backend.apps.production_management.models import Project


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
            # 基本信息
            'goal_number', 'name', 'goal_type', 'goal_period', 'status',
            # 目标指标
            'indicator_name', 'indicator_type', 'indicator_unit', 'target_value', 'current_value',
            # 责任人信息
            'responsible_person', 'responsible_department',
            # 目标描述
            'description', 'background', 'significance',
            # 权重设置
            'weight', 'weight_description',
            # 时间信息
            'start_date', 'end_date',
            # 关联信息
            'parent_goal',
            'notes',
        ]
        widgets = {
            'goal_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '留空将自动生成，例如：GOAL-20250101-0001'
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '请输入目标名称',
                'maxlength': '200'
            }),
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
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': '4',
                'placeholder': '请输入目标描述',
                'maxlength': '2000'
            }),
            'background': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': '3',
                'placeholder': '请输入目标背景（可选）'
            }),
            'significance': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': '3',
                'placeholder': '请输入目标意义（可选）'
            }),
            'weight': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'max': '100',
                'placeholder': '范围0-100，同一周期内所有目标权重总和不能超过100'
            }),
            'weight_description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': '2',
                'placeholder': '权重说明（可选）'
            }),
            'start_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'end_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'parent_goal': forms.Select(attrs={
                'class': 'form-select',
                'title': '用于目标分解，选择上级目标后，当前目标将成为下级目标'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': '3',
                'placeholder': '备注（可选）'
            }),
        }
    
    participants = forms.ModelMultipleChoiceField(
        queryset=User.objects.filter(is_active=True),
        required=False,
        widget=forms.SelectMultiple(attrs={
            'class': 'form-select',
            'title': '可多选，按住 Ctrl 键或 Command 键选择多个'
        }),
        label='参与人员'
    )
    
    related_projects = forms.ModelMultipleChoiceField(
        queryset=Project.objects.all(),
        required=False,
        widget=forms.SelectMultiple(attrs={
            'class': 'form-select',
            'title': '可多选，按住 Ctrl 键或 Command 键选择多个'
        }),
        label='关联项目'
    )
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # 设置负责人和参与人员查询集（确保始终有查询集）
        self.fields['responsible_person'].queryset = User.objects.filter(is_active=True)
        self.fields['participants'].queryset = User.objects.filter(is_active=True)
        
        # 设置部门查询集
        self.fields['responsible_department'].queryset = Department.objects.filter(is_active=True)
        
        # 设置上级目标查询集（排除自己和自己的下级目标）
        if self.instance and self.instance.pk:
            exclude_ids = [self.instance.pk]
            exclude_ids.extend([g.pk for g in self.instance.get_all_descendants()])
            self.fields['parent_goal'].queryset = StrategicGoal.objects.exclude(pk__in=exclude_ids)
        else:
            self.fields['parent_goal'].queryset = StrategicGoal.objects.all()
        
        # 设置关联项目查询集
        self.fields['related_projects'].queryset = Project.objects.all()
        
        # 如果是编辑，设置初始值
        if self.instance and self.instance.pk:
            self.fields['participants'].initial = self.instance.participants.all()
            self.fields['related_projects'].initial = self.instance.related_projects.all()
        else:
            # 新建时，设置日期字段默认值为当天
            today = date.today()
            self.fields['start_date'].initial = today
            self.fields['end_date'].initial = today
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        target_value = cleaned_data.get('target_value')
        current_value = cleaned_data.get('current_value')
        indicator_type = cleaned_data.get('indicator_type')
        weight = cleaned_data.get('weight')
        goal_period = cleaned_data.get('goal_period')
        
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
            'new_end_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'placeholder': '新结束日期（可选）'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        self.goal = kwargs.pop('goal', None)
        super().__init__(*args, **kwargs)
    
    def clean(self):
        cleaned_data = super().clean()
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
            'plan_number', 'name', 'plan_type', 'plan_period',
            # 关联信息
            'related_goal', 'parent_plan', 'related_project',
            # 计划内容
            'content', 'plan_objective', 'description',
            # 协作信息
            'collaboration_plan',
            # 时间信息
            'start_time', 'end_time',
            # 责任人信息
            'responsible_person', 'responsible_department',
            # 优先级和预算
            'priority', 'budget',
            # 其他
            'notes',
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
            'plan_type': forms.Select(attrs={'class': 'form-select'}),
            'plan_period': forms.Select(attrs={'class': 'form-select'}),
            'related_goal': forms.Select(attrs={'class': 'form-select'}),
            'parent_plan': forms.Select(attrs={'class': 'form-select'}),
            'related_project': forms.Select(attrs={'class': 'form-select'}),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': '6',
                'placeholder': '请输入计划内容',
                'maxlength': '5000'
            }),
            'plan_objective': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': '4',
                'placeholder': '请输入计划目标',
                'maxlength': '1000'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': '3',
                'placeholder': '计划描述（可选）'
            }),
            'start_time': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'placeholder': '请选择计划开始日期'
            }),
            'end_time': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'placeholder': '请选择计划结束日期'
            }),
            'responsible_person': forms.Select(attrs={'class': 'form-select'}),
            'responsible_department': forms.Select(attrs={'class': 'form-select'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'budget': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '0.00'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': '3',
                'placeholder': '备注（可选）'
            }),
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
        super().__init__(*args, **kwargs)
        
        # 设置负责人和协作人员查询集
        self.fields['responsible_person'].queryset = User.objects.filter(is_active=True)
        self.fields['participants'].queryset = User.objects.filter(is_active=True)
        
        # 设置部门查询集
        self.fields['responsible_department'].queryset = Department.objects.filter(is_active=True)
        
        # 设置关联战略目标查询集
        self.fields['related_goal'].queryset = StrategicGoal.objects.filter(status__in=['published', 'in_progress'])
        
        # 设置父计划查询集（排除自己和自己的下级计划）
        if self.instance and self.instance.pk:
            exclude_ids = [self.instance.pk]
            exclude_ids.extend([p.pk for p in self.instance.get_all_descendants()])
            self.fields['parent_plan'].queryset = Plan.objects.exclude(pk__in=exclude_ids)
        else:
            self.fields['parent_plan'].queryset = Plan.objects.all()
        
        # 设置关联项目查询集
        self.fields['related_project'].queryset = Project.objects.all()
        
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
        
        # 如果是编辑，设置初始值
        if self.instance and self.instance.pk:
            self.fields['participants'].initial = self.instance.participants.all()
            # 将datetime字段转换为date显示
            if self.instance.start_time:
                self.fields['start_time'].initial = self.instance.start_time.date()
            if self.instance.end_time:
                self.fields['end_time'].initial = self.instance.end_time.date()
        else:
            # 新建时，设置日期字段默认值为当天
            today = date.today()
            self.fields['start_time'].initial = today
            self.fields['end_time'].initial = today
    
    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        budget = cleaned_data.get('budget')
        plan_number = cleaned_data.get('plan_number')
        participants = cleaned_data.get('participants')
        collaboration_plan = cleaned_data.get('collaboration_plan')
        
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
            if end_dt <= start_dt:
                raise ValidationError({'end_time': '结束日期必须晚于开始日期'})
        
        # 验证预算
        if budget is not None and budget < 0:
            raise ValidationError({'budget': '预算不能小于0'})
        
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

