# 业务委托书路由重定向（已迁移至 contract_management，保留 /business/ 旧路径兼容）
from django.shortcuts import redirect

from .common import login_required


@login_required
def authorization_letter_list_redirect(request):
    return redirect('contract_pages:authorization_letter_list')


@login_required
def authorization_letter_create_redirect(request):
    return redirect('contract_pages:authorization_letter_create')


@login_required
def authorization_letter_detail_redirect(request, letter_id):
    return redirect('contract_pages:authorization_letter_detail', letter_id=letter_id)


@login_required
def authorization_letter_edit_redirect(request, letter_id):
    return redirect('contract_pages:authorization_letter_edit', letter_id=letter_id)


@login_required
def authorization_letter_delete_redirect(request, letter_id):
    return redirect('contract_pages:authorization_letter_delete', letter_id=letter_id)


@login_required
def authorization_letter_status_transition_redirect(request, letter_id):
    return redirect('contract_pages:authorization_letter_status_transition', letter_id=letter_id)


@login_required
def authorization_letter_template_list_redirect(request):
    return redirect('contract_pages:authorization_letter_template_list')


@login_required
def authorization_letter_template_create_redirect(request):
    return redirect('contract_pages:authorization_letter_template_create')


@login_required
def authorization_letter_template_edit_redirect(request, template_id):
    return redirect('contract_pages:authorization_letter_template_edit', template_id=template_id)


@login_required
def authorization_letter_template_delete_redirect(request, template_id):
    return redirect('contract_pages:authorization_letter_template_delete', template_id=template_id)


@login_required
def authorization_letter_create_from_template_redirect(request, template_id):
    return redirect('contract_pages:authorization_letter_create_from_template', template_id=template_id)


@login_required
def authorization_letter_template_file_preview_redirect(request, template_id):
    return redirect('contract_pages:authorization_letter_template_file_preview', template_id=template_id)


@login_required
def authorization_letter_template_file_download_redirect(request, template_id):
    return redirect('contract_pages:authorization_letter_template_file_download', template_id=template_id)
