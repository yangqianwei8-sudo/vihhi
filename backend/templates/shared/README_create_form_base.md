# 共享创建表单模板使用指南

## 概述

`create_form_base.html` 是一个共享的创建表单模板，继承自 `module_base.html`，为所有创建类表单提供统一的结构和样式。

## 固定字段

模板固定了前三个字段，按顺序显示：

1. **所属部门** (`responsible_department`)
   - 默认值：当前用户所在部门
   - 字段类型：下拉选择框
   - 必填：根据表单定义

2. **负责人** (`responsible_person`)
   - 默认值：当前用户
   - 字段类型：下拉选择框
   - 必填：根据表单定义

3. **表单编号** (`form_number` 或自定义字段名)
   - 默认值：根据业务模块自动生成
   - 字段类型：文本输入框（只读）
   - 必填：否（系统自动生成）

## 使用方式

### 1. 基础使用

```django
{% extends "shared/create_form_base.html" %}
{% load static %}

{% block form_title %}创建计划{% endblock %}
{% block form_subtitle %}请填写计划基本信息{% endblock %}

{% block form_fields %}
  {# 其他表单字段 #}
  <div class="row mb-3">
    <div class="col-md-3">
      <label for="{{ form.name.id_for_label }}" class="form-label">
        {{ form.name.label }}
      </label>
    </div>
    <div class="col-md-9">
      {{ form.name }}
      {% if form.name.errors %}
      <div class="text-danger small">{{ form.name.errors }}</div>
      {% endif %}
    </div>
  </div>
{% endblock %}

{% block form_actions %}
  <button type="submit" class="btn btn-primary">创建</button>
  <a href="{% url 'plan_pages:plan_list' %}" class="btn btn-secondary">取消</a>
{% endblock %}
```

### 2. 自定义表单编号字段名

如果表单中的编号字段名不是 `form_number`，需要在视图中设置：

```python
# views.py
def my_create_view(request):
    form = MyForm(user=request.user)
    context = {
        'form': form,
        'form_number_field': 'plan_number',  # 自定义字段名
        'business_module': 'plan',  # 业务模块名称
    }
    return render(request, 'my_app/my_form.html', context)
```

然后在模板中使用：

```django
{% block form_fields %}
  {# 如果字段名不是 form_number，需要手动添加 #}
  <div class="row mb-3">
    <div class="col-md-3">
      <label for="{{ form.plan_number.id_for_label }}" class="form-label">
        {{ form.plan_number.label }}
      </label>
    </div>
    <div class="col-md-9">
      {{ form.plan_number }}
      {% if form.plan_number.errors %}
      <div class="text-danger small">{{ form.plan_number.errors }}</div>
      {% endif %}
    </div>
  </div>
  
  {# 其他字段 #}
{% endblock %}
```

### 3. 表单字段设置要求

在表单类中，需要确保以下字段存在：

```python
# forms.py
from django import forms
from backend.apps.system_management.models import User, Department

class MyForm(forms.ModelForm):
    class Meta:
        model = MyModel
        fields = [
            'responsible_department',  # 所属部门
            'responsible_person',      # 负责人
            'form_number',             # 表单编号（或自定义名称）
            # ... 其他字段
        ]
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # 设置部门查询集
        self.fields['responsible_department'].queryset = Department.objects.filter(is_active=True)
        
        # 设置负责人查询集
        self.fields['responsible_person'].queryset = User.objects.filter(is_active=True)
        
        # 设置默认值
        if user and not self.instance.pk:
            self.fields['responsible_person'].initial = user
            # 设置部门默认值
            if hasattr(user, 'department') and user.department:
                self.fields['responsible_department'].initial = user.department
        
        # 表单编号字段设置为只读
        if 'form_number' in self.fields:
            self.fields['form_number'].widget.attrs['readonly'] = True
            self.fields['form_number'].required = False
            self.fields['form_number'].widget.attrs['placeholder'] = '系统自动生成'
```

### 4. 后端自动生成表单编号

表单编号应该在模型保存时自动生成，而不是在前端生成：

```python
# models.py
from django.db import models
from django.db.models import Max
from django.db import transaction
from django.utils import timezone

class MyModel(models.Model):
    form_number = models.CharField(max_length=50, unique=True, verbose_name='表单编号')
    responsible_department = models.ForeignKey(Department, ...)
    responsible_person = models.ForeignKey(User, ...)
    
    def generate_form_number(self, prefix='FORM'):
        """生成表单编号：PREFIX-YYYYMMDD-XXXX"""
        date_str = timezone.now().strftime('%Y%m%d')
        pattern = f"{prefix}-{date_str}-"
        
        with transaction.atomic():
            max_number = MyModel.objects.filter(
                form_number__startswith=pattern
            ).aggregate(max_num=Max('form_number'))['max_num']
            
            if max_number:
                try:
                    seq = int(max_number.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    seq = 1
            else:
                seq = 1
            
            return f"{pattern}{seq:04d}"
    
    def save(self, *args, **kwargs):
        if not self.form_number:
            self.form_number = self.generate_form_number('FORM')
        super().save(*args, **kwargs)
```

## 可覆盖的 Block

- `form_title` - 表单标题（默认：创建表单）
- `form_subtitle` - 表单副标题（默认：请填写表单信息）
- `form_header_actions` - 表单头部操作按钮区域
- `form_fields` - 其他表单字段内容
- `form_actions` - 表单底部操作按钮（默认：创建和取消按钮）

## 样式定制

模板使用统一的样式系统，可以通过覆盖 `module_extra_css` block 来自定义样式：

```django
{% block module_extra_css %}
{{ block.super }}
<style>
  .form-card {
    /* 自定义样式 */
  }
</style>
{% endblock %}
```

## 注意事项

1. **字段名必须匹配**：确保表单中的字段名与模板中使用的字段名一致
2. **默认值设置**：在表单的 `__init__` 方法中设置默认值
3. **编号生成**：表单编号应在后端模型保存时生成，前端只是显示
4. **业务模块**：通过 `business_module` 上下文变量传入业务模块名称，用于编号前缀

## 示例

完整示例请参考：
- `plan_management/forms.py` - PlanForm
- `plan_management/views_pages.py` - plan_create
- `plan_management/models.py` - Plan.generate_plan_number
