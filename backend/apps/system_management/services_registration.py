from __future__ import annotations

from typing import Optional, Tuple

from django.contrib.auth import get_user_model
from django.utils import timezone

from backend.apps.system_management.models import RegistrationRequest, Role

# Default role mapping based on the client type selected during registration.
CLIENT_TYPE_DEFAULT_ROLE = {
    'service_provider': 'technical_assistant',
    'client_owner': 'client_engineer',
    'design_partner': 'design_engineer',
}

# Mapping between position codes collected in the profile form and system roles.
POSITION_ROLE_MAP = {
    'general_manager': 'general_manager',
    'technical_manager': 'technical_manager',
    'project_manager': 'project_manager',
    'professional_lead': 'professional_lead',
    'professional_engineer': 'professional_engineer',
    'technical_assistant': 'technical_assistant',
    'business_manager': 'business_team',
    'business_assistant': 'business_assistant',
    'cost_engineer': 'cost_engineer',
    'cost_auditor': 'cost_team',
    'admin_office': 'admin_office',
    'finance_supervisor': 'finance_supervisor',
    'client_engineer': 'client_engineer',
    'client_professional_lead': 'client_professional_lead',
    'client_project_lead': 'client_project_lead',
    'design_engineer': 'design_engineer',
    'design_professional_lead': 'design_professional_lead',
    'design_project_lead': 'design_project_lead',
    'control_civil_auditor': 'control_civil_auditor',
    'control_install_auditor': 'control_install_auditor',
    'control_project_lead': 'control_project_lead',
}


def assign_role_by_position(user, position_code: Optional[str]) -> None:
    """
    Assign a role to the user based on the provided position code, if a mapping exists.
    This is mainly used after profile completion.
    """
    if not position_code:
        return
    role_code = POSITION_ROLE_MAP.get(position_code)
    if not role_code:
        return
    role = Role.objects.filter(code=role_code, is_active=True).first()
    if not role:
        return
    user.roles.set([role])


def create_user_from_request(reg_request: RegistrationRequest) -> Tuple[Optional[object], bool]:
    """
    Create a Django user from the registration request if it does not already exist.

    Returns a tuple of (user, created) where `created` indicates whether a new user was created.
    """
    User = get_user_model()
    existing_user = User.objects.filter(username=reg_request.username).first()
    if existing_user:
        return existing_user, False

    user_type = 'internal' if reg_request.client_type == 'service_provider' else reg_request.client_type
    user = User(
        username=reg_request.username,
        user_type=user_type,
        phone=reg_request.phone,
        client_type=reg_request.client_type,
        is_active=True,
    )
    user.password = reg_request.encoded_password
    user.save()
    return user, True


def assign_roles(user, reg_request: RegistrationRequest) -> None:
    """
    Assign default roles to the user based on the client type of the registration request.
    """
    role_code = CLIENT_TYPE_DEFAULT_ROLE.get(reg_request.client_type, 'professional_engineer')
    role = Role.objects.filter(code=role_code, is_active=True).first()
    if role:
        user.roles.set([role])
    else:
        user.roles.clear()


def finalize_approval(reg_request: RegistrationRequest, processed_by=None) -> Optional[object]:
    """
    Ensure the registration request has an associated user once it transitions to APPROVED.
    Also records the processor and processed_time if they are missing.
    """
    if reg_request.status != RegistrationRequest.STATUS_APPROVED:
        return None

    user, _created = create_user_from_request(reg_request)
    if user:
        assign_roles(user, reg_request)

    update_fields = []
    if reg_request.processed_time is None:
        reg_request.processed_time = timezone.now()
        update_fields.append('processed_time')
    if processed_by and reg_request.processed_by_id is None:
        reg_request.processed_by = processed_by
        update_fields.append('processed_by')
    if update_fields:
        reg_request.save(update_fields=update_fields)
    return user

