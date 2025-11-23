from django.urls import path
from . import views_pages

app_name = "personnel_pages"

urlpatterns = [
    # 人事管理主页
    path("", views_pages.personnel_home, name="personnel_home"),
    
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
    
    # 薪资管理
    path("salaries/create/", views_pages.salary_create, name="salary_create"),
    path("salaries/<int:salary_id>/edit/", views_pages.salary_update, name="salary_update"),
]

