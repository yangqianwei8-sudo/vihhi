from django.urls import path
from . import views_pages

app_name = "personnel_pages"

urlpatterns = [
    # 人事管理主页
    path("", views_pages.personnel_home, name="personnel_home"),
    path("home/", views_pages.personnel_home, name="personnel_home"),
    
    # 员工档案
    path("employees/", views_pages.employee_management, name="employee_management"),
    path("employees/create/", views_pages.employee_create, name="employee_create"),
    path("employees/<int:employee_id>/", views_pages.employee_detail, name="employee_detail"),
    path("employees/<int:employee_id>/edit/", views_pages.employee_update, name="employee_update"),
    
    # 考勤管理
    path("attendance/", views_pages.attendance_management, name="attendance_management"),
    
    # 请假管理
    path("leaves/", views_pages.leave_management, name="leave_management"),
    path("leaves/create/", views_pages.leave_create, name="leave_create"),
    path("leaves/<int:leave_id>/", views_pages.leave_detail, name="leave_detail"),
    path("leaves/<int:leave_id>/edit/", views_pages.leave_update, name="leave_update"),
    
    # 培训管理
    path("trainings/", views_pages.training_management, name="training_management"),
    path("trainings/create/", views_pages.training_create, name="training_create"),
    path("trainings/<int:training_id>/", views_pages.training_detail, name="training_detail"),
    path("trainings/<int:training_id>/edit/", views_pages.training_update, name="training_update"),
    
    # 绩效考核
    path("performances/", views_pages.performance_management, name="performance_management"),
    path("performances/create/", views_pages.performance_create, name="performance_create"),
    path("performances/<int:performance_id>/", views_pages.performance_detail, name="performance_detail"),
    path("performances/<int:performance_id>/edit/", views_pages.performance_update, name="performance_update"),
    
    # 薪资管理
    path("salaries/", views_pages.salary_management, name="salary_management"),
    
    # 劳动合同
    path("contracts/", views_pages.contract_management, name="contract_management"),
    path("contracts/create/", views_pages.contract_create, name="contract_create"),
    path("contracts/<int:contract_id>/", views_pages.contract_detail, name="contract_detail"),
    path("contracts/<int:contract_id>/edit/", views_pages.contract_update, name="contract_update"),
    
    # 考勤管理
    path("attendance/create/", views_pages.attendance_create, name="attendance_create"),
    # path("attendance/<int:attendance_id>/", views_pages.attendance_detail, name="attendance_detail"),  # TODO: 视图函数尚未实现
    
    # 薪资管理
    path("salaries/create/", views_pages.salary_create, name="salary_create"),
    # path("salaries/<int:salary_id>/", views_pages.salary_detail, name="salary_detail"),  # TODO: 视图函数 salary_detail 尚未实现
    path("salaries/<int:salary_id>/edit/", views_pages.salary_update, name="salary_update"),
    
    # 组织架构管理
    # path("organization/", views_pages.organization_management, name="organization_management"),  # TODO: 视图函数 organization_management 尚未实现
    # path("departments/", views_pages.department_management, name="department_management"),  # TODO: 视图函数 department_management 尚未实现
    # path("positions/", views_pages.position_management, name="position_management"),  # TODO: 视图函数 position_management 尚未实现
    # path("org-chart/", views_pages.org_chart, name="org_chart"),  # TODO: 视图函数 org_chart 尚未实现
    
    # 员工档案管理
    # path("employee-archives/", views_pages.employee_archive_management, name="employee_archive_management"),  # TODO: 视图函数 employee_archive_management 尚未实现
    # path("employee-archives/create/", views_pages.employee_archive_create, name="employee_archive_create"),  # TODO: 视图函数 employee_archive_create 尚未实现
    
    # 员工异动管理
    # path("employee-movements/", views_pages.employee_movement_management, name="employee_movement_management"),  # TODO: 视图函数 employee_movement_management 尚未实现
    # path("employee-movements/create/", views_pages.employee_movement_create, name="employee_movement_create"),  # TODO: 视图函数 employee_movement_create 尚未实现
    # path("employee-movements/<int:movement_id>/", views_pages.employee_movement_detail, name="employee_movement_detail"),  # TODO: 视图函数 employee_movement_detail 尚未实现
    # path("employee-movements/<int:movement_id>/approve/", views_pages.employee_movement_approve, name="employee_movement_approve"),  # TODO: 视图函数 employee_movement_approve 尚未实现
    
    # 福利管理
    # path("welfare/", views_pages.welfare_management, name="welfare_management"),  # TODO: 视图函数 welfare_management 尚未实现
    # path("welfare/project/create/", views_pages.welfare_project_create, name="welfare_project_create"),  # TODO: 视图函数 welfare_project_create 尚未实现
    # path("welfare/distribution/create/", views_pages.welfare_distribution_create, name="welfare_distribution_create"),  # TODO: 视图函数 welfare_distribution_create 尚未实现
    
    # 招聘管理
    # path("recruitment/", views_pages.recruitment_management, name="recruitment_management"),  # TODO: 视图函数 recruitment_management 尚未实现
    # path("recruitment/requirement/create/", views_pages.recruitment_requirement_create, name="recruitment_requirement_create"),  # TODO: 视图函数 recruitment_requirement_create 尚未实现
    # path("recruitment/resume/create/", views_pages.resume_create, name="resume_create"),  # TODO: 视图函数 resume_create 尚未实现
    # path("recruitment/interview/create/", views_pages.interview_create, name="interview_create"),  # TODO: 视图函数 interview_create 尚未实现
    
    # 员工关系管理
    # path("employee-relations/", views_pages.employee_relations_management, name="employee_relations_management"),  # TODO: 视图函数 employee_relations_management 尚未实现
    # path("employee-relations/communication/create/", views_pages.employee_communication_create, name="employee_communication_create"),  # TODO: 视图函数 employee_communication_create 尚未实现
    # path("employee-relations/care/create/", views_pages.employee_care_create, name="employee_care_create"),  # TODO: 视图函数 employee_care_create 尚未实现
    # path("employee-relations/activity/create/", views_pages.employee_activity_create, name="employee_activity_create"),  # TODO: 视图函数 employee_activity_create 尚未实现
    # path("employee-relations/complaint/create/", views_pages.employee_complaint_create, name="employee_complaint_create"),  # TODO: 视图函数 employee_complaint_create 尚未实现
    # path("employee-relations/suggestion/create/", views_pages.employee_suggestion_create, name="employee_suggestion_create"),  # TODO: 视图函数 employee_suggestion_create 尚未实现
]

