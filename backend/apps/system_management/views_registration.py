from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.hashers import make_password
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from .forms import (
    RegistrationRequestForm,
    RegistrationAuditForm,
    ProfileCompletionForm,
    SERVICE_CATEGORY_CHOICES,
)
from backend.apps.system_management.models import RegistrationRequest
from .services_registration import assign_roles, create_user_from_request


def is_staff_user(user):
    return user.is_staff or user.is_superuser


def register(request):
    if request.method == 'POST':
        form = RegistrationRequestForm(request.POST)
        if form.is_valid():
            reg_request = form.save(commit=False)
            reg_request.encoded_password = make_password(form.cleaned_data['password'])
            reg_request.status = RegistrationRequest.STATUS_PENDING
            reg_request.save()
            messages.success(request, '注册申请已提交，待管理员审核。')
            return redirect('registration_submitted')
    else:
        form = RegistrationRequestForm()
    return render(request, 'registration/register.html', {'form': form})


def registration_submitted(request):
    return render(request, 'registration/submitted.html')


@login_required
@user_passes_test(is_staff_user)
def registration_list(request):
    status_filter = request.GET.get('status', RegistrationRequest.STATUS_PENDING)
    requests = RegistrationRequest.objects.all()
    if status_filter:
        requests = requests.filter(status=status_filter)
    return render(request, 'system_management/registration_list.html', {
        'requests': requests,
        'status_filter': status_filter,
    })


@login_required
@user_passes_test(is_staff_user)
def registration_detail(request, pk):
    reg_request = get_object_or_404(RegistrationRequest, pk=pk)
    if request.method == 'POST' and reg_request.status == RegistrationRequest.STATUS_PENDING:
        form = RegistrationAuditForm(request.POST)
        if form.is_valid():
            status = form.cleaned_data['status']
            feedback = form.cleaned_data['feedback']
            reg_request.status = status
            reg_request.feedback = feedback
            reg_request.processed_time = timezone.now()
            reg_request.processed_by = request.user

            if status == RegistrationRequest.STATUS_APPROVED:
                user, created = create_user_from_request(reg_request)
                if user:
                    assign_roles(user, reg_request)
                    if created:
                        messages.success(request, f'已批准注册，并创建用户 {user.username}')
                    else:
                        messages.success(request, f'已更新用户 {user.username} 的权限')
                else:
                    messages.warning(request, '审批通过，但未能创建对应的用户。')
            else:
                messages.info(request, '已拒绝该注册申请')

            reg_request.save()
            return redirect('admin_registration_list')
    else:
        form = RegistrationAuditForm()

    return render(request, 'system_management/registration_detail.html', {
        'request_obj': reg_request,
        'form': form,
    })


@login_required
def complete_profile(request):
    user = request.user
    if user.profile_completed:
        return redirect('admin:index')

    if request.method == 'POST':
        form = ProfileCompletionForm(request.POST, user=user)
        if form.is_valid():
            form.save()
            messages.success(request, '个人资料已完善')
            return redirect('admin:index')
    else:
        form = ProfileCompletionForm(user=user)

    current_category = form.initial.get('service_category', user.user_type or 'internal')
    service_category_label = dict(SERVICE_CATEGORY_CHOICES).get(current_category, '服务单位')

    return render(request, 'registration/complete_profile.html', {
        'form': form,
        'service_category': current_category,
        'service_category_label': service_category_label,
        'service_options': form.get_service_options(),
        'department_group_map': form.get_department_group_map(),
    })

