# Generated manually to add missing models

from decimal import Decimal
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('personnel_management', '0001_initial'),
        ('system_management', '0006_alter_user_user_type'),
    ]

    operations = [
        # Position model
        migrations.CreateModel(
            name='Position',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='职位名称')),
                ('code', models.CharField(max_length=50, unique=True, verbose_name='职位编码')),
                ('level', models.IntegerField(default=1, verbose_name='职位级别')),
                ('description', models.TextField(blank=True, verbose_name='职位描述')),
                ('requirements', models.TextField(blank=True, verbose_name='任职要求')),
                ('min_salary', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='最低薪资')),
                ('max_salary', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='最高薪资')),
                ('is_active', models.BooleanField(default=True, verbose_name='是否启用')),
                ('created_time', models.DateTimeField(default=django.utils.timezone.now, verbose_name='创建时间')),
                ('updated_time', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('department', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='positions', to='system_management.department', verbose_name='所属部门')),
            ],
            options={
                'verbose_name': '职位',
                'verbose_name_plural': '职位',
                'db_table': 'personnel_position',
                'ordering': ['department', 'level', 'name'],
            },
        ),
        migrations.AddIndex(
            model_name='position',
            index=models.Index(fields=['code'], name='personnel_p_code_abc123_idx'),
        ),
        migrations.AddIndex(
            model_name='position',
            index=models.Index(fields=['department'], name='personnel_p_departm_def456_idx'),
        ),
        migrations.AddIndex(
            model_name='position',
            index=models.Index(fields=['is_active'], name='personnel_p_is_acti_ghi789_idx'),
        ),
        
        # EmployeeArchive model
        migrations.CreateModel(
            name='EmployeeArchive',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('category', models.CharField(choices=[('id_card', '身份证'), ('education', '学历证书'), ('qualification', '资格证书'), ('contract', '劳动合同'), ('health_report', '体检报告'), ('other', '其他')], max_length=50, verbose_name='档案分类')),
                ('file_name', models.CharField(max_length=255, verbose_name='文件名称')),
                ('file', models.FileField(upload_to='employee_archives/%Y/%m/', verbose_name='档案文件')),
                ('file_size', models.BigIntegerField(verbose_name='文件大小（字节）')),
                ('description', models.TextField(blank=True, verbose_name='档案描述')),
                ('expiry_date', models.DateField(blank=True, null=True, verbose_name='到期日期')),
                ('is_archived', models.BooleanField(default=False, verbose_name='是否归档')),
                ('created_time', models.DateTimeField(default=django.utils.timezone.now, verbose_name='创建时间')),
                ('updated_time', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_employee_archives', to=settings.AUTH_USER_MODEL, verbose_name='创建人')),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='archives', to='personnel_management.employee', verbose_name='员工')),
            ],
            options={
                'verbose_name': '员工档案文件',
                'verbose_name_plural': '员工档案文件',
                'db_table': 'personnel_employee_archive',
                'ordering': ['-created_time'],
            },
        ),
        migrations.AddIndex(
            model_name='employeearchive',
            index=models.Index(fields=['employee', 'category'], name='personnel_e_employe_jkl012_idx'),
        ),
        migrations.AddIndex(
            model_name='employeearchive',
            index=models.Index(fields=['category'], name='personnel_e_categor_mno345_idx'),
        ),
        migrations.AddIndex(
            model_name='employeearchive',
            index=models.Index(fields=['expiry_date'], name='personnel_e_expiry_pqr678_idx'),
        ),
        
        # EmployeeMovement model
        migrations.CreateModel(
            name='EmployeeMovement',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('movement_number', models.CharField(max_length=50, unique=True, verbose_name='异动编号')),
                ('movement_type', models.CharField(choices=[('entry', '入职'), ('transfer', '调岗'), ('promotion', '晋升'), ('demotion', '降职'), ('resignation', '离职'), ('suspension', '停职'), ('reinstatement', '复职'), ('other', '其他')], max_length=20, verbose_name='异动类型')),
                ('movement_date', models.DateField(verbose_name='异动日期')),
                ('old_position', models.CharField(blank=True, max_length=100, verbose_name='原职位')),
                ('old_salary', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='原薪资')),
                ('new_position', models.CharField(blank=True, max_length=100, verbose_name='新职位')),
                ('new_salary', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='新薪资')),
                ('reason', models.TextField(verbose_name='异动原因')),
                ('status', models.CharField(choices=[('pending', '待审批'), ('approved', '已批准'), ('rejected', '已拒绝'), ('completed', '已完成')], default='pending', max_length=20, verbose_name='状态')),
                ('approval_time', models.DateTimeField(blank=True, null=True, verbose_name='审批时间')),
                ('approval_comment', models.TextField(blank=True, verbose_name='审批意见')),
                ('created_time', models.DateTimeField(default=django.utils.timezone.now, verbose_name='创建时间')),
                ('updated_time', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('approver', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='approved_movements', to=settings.AUTH_USER_MODEL, verbose_name='审批人')),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_movements', to=settings.AUTH_USER_MODEL, verbose_name='创建人')),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='movements', to='personnel_management.employee', verbose_name='员工')),
                ('new_department', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='new_movements', to='system_management.department', verbose_name='新部门')),
                ('old_department', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='old_movements', to='system_management.department', verbose_name='原部门')),
            ],
            options={
                'verbose_name': '员工异动记录',
                'verbose_name_plural': '员工异动记录',
                'db_table': 'personnel_employee_movement',
                'ordering': ['-movement_date', '-created_time'],
            },
        ),
        migrations.AddIndex(
            model_name='employeemovement',
            index=models.Index(fields=['employee', 'movement_date'], name='personnel_e_employe_stu901_idx'),
        ),
        migrations.AddIndex(
            model_name='employeemovement',
            index=models.Index(fields=['movement_type'], name='personnel_e_movemen_vwx234_idx'),
        ),
        migrations.AddIndex(
            model_name='employeemovement',
            index=models.Index(fields=['status'], name='personnel_e_status_yza567_idx'),
        ),
        migrations.AddIndex(
            model_name='employeemovement',
            index=models.Index(fields=['movement_date'], name='personnel_e_movemen_bcd890_idx'),
        ),
        
        # WelfareProject model
        migrations.CreateModel(
            name='WelfareProject',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='福利项目名称')),
                ('welfare_type', models.CharField(choices=[('holiday', '节日福利'), ('birthday', '生日福利'), ('health', '健康福利'), ('training', '培训福利'), ('travel', '旅游福利'), ('meal', '餐饮福利'), ('housing', '住房福利'), ('other', '其他')], max_length=20, verbose_name='福利类型')),
                ('standard', models.TextField(verbose_name='福利标准')),
                ('target_employees', models.TextField(blank=True, verbose_name='福利对象描述')),
                ('cycle', models.CharField(choices=[('once', '一次性'), ('monthly', '每月'), ('quarterly', '每季度'), ('yearly', '每年')], default='once', max_length=20, verbose_name='福利周期')),
                ('is_active', models.BooleanField(default=True, verbose_name='是否启用')),
                ('created_time', models.DateTimeField(default=django.utils.timezone.now, verbose_name='创建时间')),
                ('updated_time', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
            ],
            options={
                'verbose_name': '福利项目',
                'verbose_name_plural': '福利项目',
                'db_table': 'personnel_welfare_project',
                'ordering': ['-created_time'],
            },
        ),
        
        # WelfareDistribution model
        migrations.CreateModel(
            name='WelfareDistribution',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('distribution_date', models.DateField(verbose_name='发放日期')),
                ('amount', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='发放金额')),
                ('payment_method', models.CharField(choices=[('cash', '现金'), ('bank_transfer', '银行转账'), ('voucher', '代金券'), ('goods', '实物'), ('other', '其他')], default='cash', max_length=20, verbose_name='发放方式')),
                ('description', models.TextField(blank=True, verbose_name='发放说明')),
                ('created_time', models.DateTimeField(default=django.utils.timezone.now, verbose_name='创建时间')),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_welfare_distributions', to=settings.AUTH_USER_MODEL, verbose_name='创建人')),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='welfare_distributions', to='personnel_management.employee', verbose_name='员工')),
                ('welfare_project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='distributions', to='personnel_management.welfareproject', verbose_name='福利项目')),
            ],
            options={
                'verbose_name': '福利发放记录',
                'verbose_name_plural': '福利发放记录',
                'db_table': 'personnel_welfare_distribution',
                'ordering': ['-distribution_date', '-created_time'],
            },
        ),
        migrations.AddIndex(
            model_name='welfaredistribution',
            index=models.Index(fields=['welfare_project', 'distribution_date'], name='personnel_w_welfare_efg123_idx'),
        ),
        migrations.AddIndex(
            model_name='welfaredistribution',
            index=models.Index(fields=['employee', 'distribution_date'], name='personnel_w_employe_hij456_idx'),
        ),
        
        # RecruitmentRequirement model
        migrations.CreateModel(
            name='RecruitmentRequirement',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('requirement_number', models.CharField(max_length=50, unique=True, verbose_name='需求编号')),
                ('position', models.CharField(max_length=100, verbose_name='需求职位')),
                ('required_count', models.IntegerField(verbose_name='需求人数')),
                ('requirements', models.TextField(verbose_name='岗位要求')),
                ('salary_range_min', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='薪资范围（最低）')),
                ('salary_range_max', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='薪资范围（最高）')),
                ('reason', models.TextField(verbose_name='需求原因')),
                ('publish_date', models.DateField(blank=True, null=True, verbose_name='发布日期')),
                ('deadline', models.DateField(blank=True, null=True, verbose_name='截止日期')),
                ('status', models.CharField(choices=[('draft', '草稿'), ('pending', '待审批'), ('approved', '已批准'), ('recruiting', '招聘中'), ('completed', '已完成'), ('cancelled', '已取消')], default='draft', max_length=20, verbose_name='状态')),
                ('approval_time', models.DateTimeField(blank=True, null=True, verbose_name='审批时间')),
                ('approval_comment', models.TextField(blank=True, verbose_name='审批意见')),
                ('created_time', models.DateTimeField(default=django.utils.timezone.now, verbose_name='创建时间')),
                ('updated_time', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('approver', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='approved_recruitment_requirements', to=settings.AUTH_USER_MODEL, verbose_name='审批人')),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_recruitment_requirements', to=settings.AUTH_USER_MODEL, verbose_name='创建人')),
                ('department', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='recruitment_requirements', to='system_management.department', verbose_name='需求部门')),
            ],
            options={
                'verbose_name': '招聘需求',
                'verbose_name_plural': '招聘需求',
                'db_table': 'personnel_recruitment_requirement',
                'ordering': ['-created_time'],
            },
        ),
        migrations.AddIndex(
            model_name='recruitmentrequirement',
            index=models.Index(fields=['department', 'status'], name='personnel_r_departm_klm789_idx'),
        ),
        migrations.AddIndex(
            model_name='recruitmentrequirement',
            index=models.Index(fields=['status'], name='personnel_r_status_nop012_idx'),
        ),
        migrations.AddIndex(
            model_name='recruitmentrequirement',
            index=models.Index(fields=['publish_date'], name='personnel_r_publish_qrs345_idx'),
        ),
        
        # Resume model
        migrations.CreateModel(
            name='Resume',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('resume_number', models.CharField(max_length=50, unique=True, verbose_name='简历编号')),
                ('name', models.CharField(max_length=100, verbose_name='姓名')),
                ('gender', models.CharField(choices=[('male', '男'), ('female', '女'), ('other', '其他')], max_length=10, verbose_name='性别')),
                ('phone', models.CharField(max_length=20, verbose_name='手机号')),
                ('email', models.EmailField(blank=True, max_length=254, verbose_name='邮箱')),
                ('education', models.CharField(blank=True, max_length=50, verbose_name='学历')),
                ('work_experience', models.IntegerField(default=0, verbose_name='工作经验（年）')),
                ('resume_file', models.FileField(upload_to='resumes/%Y/%m/', verbose_name='简历文件')),
                ('source', models.CharField(blank=True, max_length=100, verbose_name='简历来源')),
                ('status', models.CharField(choices=[('pending', '待处理'), ('screened', '已筛选'), ('interview', '待面试'), ('rejected', '已淘汰'), ('hired', '已录用')], default='pending', max_length=20, verbose_name='状态')),
                ('notes', models.TextField(blank=True, verbose_name='备注')),
                ('created_time', models.DateTimeField(default=django.utils.timezone.now, verbose_name='创建时间')),
                ('updated_time', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('recruitment_requirement', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='resumes', to='personnel_management.recruitmentrequirement', verbose_name='招聘需求')),
            ],
            options={
                'verbose_name': '简历',
                'verbose_name_plural': '简历',
                'db_table': 'personnel_resume',
                'ordering': ['-created_time'],
            },
        ),
        migrations.AddIndex(
            model_name='resume',
            index=models.Index(fields=['recruitment_requirement', 'status'], name='personnel_r_recruit_tuv678_idx'),
        ),
        migrations.AddIndex(
            model_name='resume',
            index=models.Index(fields=['status'], name='personnel_r_status_wxy901_idx'),
        ),
        
        # Interview model
        migrations.CreateModel(
            name='Interview',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('interview_number', models.CharField(max_length=50, unique=True, verbose_name='面试编号')),
                ('interview_date', models.DateTimeField(verbose_name='面试时间')),
                ('interview_location', models.CharField(blank=True, max_length=200, verbose_name='面试地点')),
                ('interview_method', models.CharField(default='onsite', max_length=50, verbose_name='面试方式')),
                ('evaluation', models.TextField(blank=True, verbose_name='面试评价')),
                ('result', models.CharField(blank=True, choices=[('pass', '通过'), ('fail', '未通过'), ('pending', '待定')], max_length=20, verbose_name='面试结果')),
                ('status', models.CharField(choices=[('scheduled', '已安排'), ('completed', '已完成'), ('cancelled', '已取消')], default='scheduled', max_length=20, verbose_name='状态')),
                ('created_time', models.DateTimeField(default=django.utils.timezone.now, verbose_name='创建时间')),
                ('updated_time', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('interviewer', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='conducted_interviews', to=settings.AUTH_USER_MODEL, verbose_name='面试官')),
                ('resume', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='interviews', to='personnel_management.resume', verbose_name='简历')),
            ],
            options={
                'verbose_name': '面试记录',
                'verbose_name_plural': '面试记录',
                'db_table': 'personnel_interview',
                'ordering': ['-interview_date'],
            },
        ),
        migrations.AddIndex(
            model_name='interview',
            index=models.Index(fields=['resume', 'interview_date'], name='personnel_i_resume__zab234_idx'),
        ),
        migrations.AddIndex(
            model_name='interview',
            index=models.Index(fields=['interviewer', 'interview_date'], name='personnel_i_intervi_cde567_idx'),
        ),
        
        # EmployeeCommunication model
        migrations.CreateModel(
            name='EmployeeCommunication',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('subject', models.CharField(max_length=200, verbose_name='沟通主题')),
                ('communication_date', models.DateTimeField(verbose_name='沟通时间')),
                ('content', models.TextField(verbose_name='沟通内容')),
                ('method', models.CharField(choices=[('online', '线上'), ('offline', '线下'), ('anonymous', '匿名')], default='offline', max_length=20, verbose_name='沟通方式')),
                ('feedback', models.TextField(blank=True, verbose_name='员工反馈')),
                ('result', models.TextField(blank=True, verbose_name='处理结果')),
                ('created_time', models.DateTimeField(default=django.utils.timezone.now, verbose_name='创建时间')),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_communications', to=settings.AUTH_USER_MODEL, verbose_name='创建人')),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='communications', to='personnel_management.employee', verbose_name='员工')),
            ],
            options={
                'verbose_name': '员工沟通记录',
                'verbose_name_plural': '员工沟通记录',
                'db_table': 'personnel_employee_communication',
                'ordering': ['-communication_date'],
            },
        ),
        migrations.AddIndex(
            model_name='employeecommunication',
            index=models.Index(fields=['employee', 'communication_date'], name='personnel_e_employe_fgh890_idx'),
        ),
        
        # EmployeeCare model
        migrations.CreateModel(
            name='EmployeeCare',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('care_type', models.CharField(choices=[('birthday', '生日关怀'), ('holiday', '节日关怀'), ('difficulty', '困难关怀'), ('achievement', '成就关怀'), ('other', '其他')], max_length=20, verbose_name='关怀类型')),
                ('care_date', models.DateField(verbose_name='关怀日期')),
                ('content', models.TextField(verbose_name='关怀内容')),
                ('created_time', models.DateTimeField(default=django.utils.timezone.now, verbose_name='创建时间')),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_cares', to=settings.AUTH_USER_MODEL, verbose_name='创建人')),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='cares', to='personnel_management.employee', verbose_name='员工')),
            ],
            options={
                'verbose_name': '员工关怀记录',
                'verbose_name_plural': '员工关怀记录',
                'db_table': 'personnel_employee_care',
                'ordering': ['-care_date'],
            },
        ),
        migrations.AddIndex(
            model_name='employeecare',
            index=models.Index(fields=['employee', 'care_date'], name='personnel_e_employe_ijk123_idx'),
        ),
        migrations.AddIndex(
            model_name='employeecare',
            index=models.Index(fields=['care_type'], name='personnel_e_care_ty_lmn456_idx'),
        ),
        
        # EmployeeActivity model
        migrations.CreateModel(
            name='EmployeeActivity',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('activity_number', models.CharField(max_length=50, unique=True, verbose_name='活动编号')),
                ('title', models.CharField(max_length=200, verbose_name='活动主题')),
                ('activity_date', models.DateTimeField(verbose_name='活动时间')),
                ('location', models.CharField(blank=True, max_length=200, verbose_name='活动地点')),
                ('max_participants', models.IntegerField(blank=True, null=True, verbose_name='最大参与人数')),
                ('budget', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='活动预算')),
                ('description', models.TextField(verbose_name='活动描述')),
                ('status', models.CharField(choices=[('planning', '策划中'), ('registration', '报名中'), ('ongoing', '进行中'), ('completed', '已完成'), ('cancelled', '已取消')], default='planning', max_length=20, verbose_name='状态')),
                ('created_time', models.DateTimeField(default=django.utils.timezone.now, verbose_name='创建时间')),
                ('updated_time', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_activities', to=settings.AUTH_USER_MODEL, verbose_name='创建人')),
            ],
            options={
                'verbose_name': '员工活动',
                'verbose_name_plural': '员工活动',
                'db_table': 'personnel_employee_activity',
                'ordering': ['-activity_date'],
            },
        ),
        migrations.AddIndex(
            model_name='employeeactivity',
            index=models.Index(fields=['status', 'activity_date'], name='personnel_e_status_opq789_idx'),
        ),
        
        # ActivityParticipant model
        migrations.CreateModel(
            name='ActivityParticipant',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('signed_in', models.BooleanField(default=False, verbose_name='是否签到')),
                ('signed_in_time', models.DateTimeField(blank=True, null=True, verbose_name='签到时间')),
                ('feedback', models.TextField(blank=True, verbose_name='活动反馈')),
                ('created_time', models.DateTimeField(default=django.utils.timezone.now, verbose_name='报名时间')),
                ('activity', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='activity_participants', to='personnel_management.employeeactivity', verbose_name='活动')),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='participated_activities', to='personnel_management.employee', verbose_name='员工')),
            ],
            options={
                'verbose_name': '活动参与记录',
                'verbose_name_plural': '活动参与记录',
                'db_table': 'personnel_activity_participant',
                'unique_together': {('activity', 'employee')},
            },
        ),
        migrations.AddIndex(
            model_name='activityparticipant',
            index=models.Index(fields=['activity', 'employee'], name='personnel_a_activit_rst012_idx'),
        ),
        
        # EmployeeComplaint model
        migrations.CreateModel(
            name='EmployeeComplaint',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('complaint_number', models.CharField(max_length=50, unique=True, verbose_name='投诉编号')),
                ('complaint_date', models.DateTimeField(verbose_name='投诉时间')),
                ('content', models.TextField(verbose_name='投诉内容')),
                ('complaint_type', models.CharField(blank=True, max_length=100, verbose_name='投诉类型')),
                ('status', models.CharField(choices=[('pending', '待处理'), ('processing', '处理中'), ('resolved', '已解决'), ('closed', '已关闭')], default='pending', max_length=20, verbose_name='状态')),
                ('handling_result', models.TextField(blank=True, verbose_name='处理结果')),
                ('handled_time', models.DateTimeField(blank=True, null=True, verbose_name='处理时间')),
                ('created_time', models.DateTimeField(default=django.utils.timezone.now, verbose_name='创建时间')),
                ('updated_time', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='complaints', to='personnel_management.employee', verbose_name='投诉人')),
                ('handler', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='handled_complaints', to=settings.AUTH_USER_MODEL, verbose_name='处理人')),
            ],
            options={
                'verbose_name': '员工投诉',
                'verbose_name_plural': '员工投诉',
                'db_table': 'personnel_employee_complaint',
                'ordering': ['-complaint_date'],
            },
        ),
        migrations.AddIndex(
            model_name='employeecomplaint',
            index=models.Index(fields=['employee', 'complaint_date'], name='personnel_e_employe_uvw345_idx'),
        ),
        migrations.AddIndex(
            model_name='employeecomplaint',
            index=models.Index(fields=['status'], name='personnel_e_status_xyz678_idx'),
        ),
        
        # EmployeeSuggestion model
        migrations.CreateModel(
            name='EmployeeSuggestion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('suggestion_number', models.CharField(max_length=50, unique=True, verbose_name='建议编号')),
                ('suggestion_date', models.DateTimeField(verbose_name='建议时间')),
                ('content', models.TextField(verbose_name='建议内容')),
                ('status', models.CharField(choices=[('pending', '待处理'), ('reviewing', '审核中'), ('adopted', '已采纳'), ('rejected', '已拒绝')], default='pending', max_length=20, verbose_name='状态')),
                ('review_result', models.TextField(blank=True, verbose_name='审核结果')),
                ('is_adopted', models.BooleanField(default=False, verbose_name='是否采纳')),
                ('reward', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='奖励金额')),
                ('reviewed_time', models.DateTimeField(blank=True, null=True, verbose_name='审核时间')),
                ('created_time', models.DateTimeField(default=django.utils.timezone.now, verbose_name='创建时间')),
                ('updated_time', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='suggestions', to='personnel_management.employee', verbose_name='建议人')),
                ('reviewer', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='reviewed_suggestions', to=settings.AUTH_USER_MODEL, verbose_name='审核人')),
            ],
            options={
                'verbose_name': '员工建议',
                'verbose_name_plural': '员工建议',
                'db_table': 'personnel_employee_suggestion',
                'ordering': ['-suggestion_date'],
            },
        ),
        migrations.AddIndex(
            model_name='employeesuggestion',
            index=models.Index(fields=['employee', 'suggestion_date'], name='personnel_e_employe_abc901_idx'),
        ),
        migrations.AddIndex(
            model_name='employeesuggestion',
            index=models.Index(fields=['status'], name='personnel_e_status_def234_idx'),
        ),
    ]

