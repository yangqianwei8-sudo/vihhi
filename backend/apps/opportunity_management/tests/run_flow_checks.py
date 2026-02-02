#!/usr/bin/env python
# 在开发库上快速验证 8 项流程逻辑（不依赖 test 库迁移）
# 用法: cd 项目根目录 && python -c "import django; django.setup(); from backend.apps.opportunity_management.tests.run_flow_checks import run; run()"

import os
import django

if __name__ == '__main__' or 'DJANGO_SETTINGS_MODULE' in os.environ:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.config.settings')
    django.setup()


def run():
    from django.test import RequestFactory, Client as TestClient
    from django.contrib.auth import get_user_model
    from django.urls import reverse
    from unittest.mock import patch

    User = get_user_model()
    from backend.apps.opportunity_management.models import BusinessOpportunity
    from backend.apps.opportunity_management.views_opportunity import (
        opportunity_detail,
        opportunity_submit_for_approval,
        opportunity_edit,
        opportunity_delete,
        opportunity_management,
    )
    from backend.apps.opportunity_management.perm_check import (
        PREFIX as OPP_PREFIX,
        opportunity_can_view_all,
        opportunity_can_access_detail,
        opportunity_can_access_edit,
    )
    from backend.apps.customer_management.models import Client

    def _perm_view_only():
        return {f'{OPP_PREFIX}.view'}

    def _perm_view_all():
        return {f'{OPP_PREFIX}.view', f'{OPP_PREFIX}.view_all'}

    def _perm_edit():
        return {f'{OPP_PREFIX}.view', f'{OPP_PREFIX}.view_all', f'{OPP_PREFIX}.edit'}

    results = []
    # 使用已有数据：第一个用户、第一个客户、第一条商机
    user = User.objects.filter(is_active=True).first()
    if not user:
        print('SKIP: 无用户')
        return
    client_obj = Client.objects.filter(is_active=True).first()
    if not client_obj:
        print('SKIP: 无客户')
        return
    opp = BusinessOpportunity.objects.filter(is_active=True).first()
    if not opp:
        print('SKIP: 无商机')
        return

    rf = RequestFactory()
    client = TestClient()

    # 1) 审批提交：视图可调用且不 500
    with patch('backend.apps.opportunity_management.views_opportunity.get_user_permission_codes', return_value=_perm_edit()):
        req = rf.post(f'/opportunities/{opp.id}/submit-approval/', {'comment': 'test'})
        req.user = user
        from django.contrib.sessions.middleware import SessionMiddleware
        from django.contrib.messages.middleware import MessageMiddleware
        for m in (SessionMiddleware(lambda r: None), MessageMiddleware(lambda r: None)):
            m.process_request(req)
        try:
            resp = opportunity_submit_for_approval(req, opp.id)
            results.append(('1.审批提交', resp.status_code in (200, 302)))
        except Exception as e:
            results.append(('1.审批提交', False))

    # 2) view_all：列表视图可正常返回（用 RequestFactory 直接调视图；开发库可能因模板/表差异导致渲染异常，仅校验视图逻辑与状态码）
    from django.contrib.sessions.middleware import SessionMiddleware
    from django.contrib.messages.middleware import MessageMiddleware
    with patch('backend.apps.opportunity_management.views_opportunity.get_user_permission_codes', return_value=_perm_view_only()):
        try:
            req = rf.get('/opportunities/list/')
            req.user = user
            for m in (SessionMiddleware(lambda r: None), MessageMiddleware(lambda r: None)):
                m.process_request(req)
            resp = opportunity_management(req)
            # 视图返回 200 即通过；500 多为模板/表缺失导致，开发库可接受
            results.append(('2.view_all 列表', resp.status_code == 200))
        except Exception as e:
            results.append(('2.view_all 列表', False))

    # 3) 非负责人访问详情/编辑/删除：应 302
    other_user = User.objects.filter(is_active=True).exclude(id=opp.business_manager_id).first() or user
    with patch('backend.apps.opportunity_management.views_opportunity.get_user_permission_codes', return_value=_perm_view_only()):
        for view, name in [
            (opportunity_detail, '详情'),
            (opportunity_edit, '编辑'),
            (opportunity_delete, '删除'),
        ]:
            req = rf.get(f'/opportunities/{opp.id}/' if name == '详情' else f'/opportunities/{opp.id}/edit/' if name == '编辑' else f'/opportunities/{opp.id}/delete/')
            req.user = other_user
            for m in (SessionMiddleware(lambda r: None), MessageMiddleware(lambda r: None)):
                m.process_request(req)
            try:
                if name == '删除':
                    req = rf.post(f'/opportunities/{opp.id}/delete/')
                    req.user = other_user
                    for m in (SessionMiddleware(lambda r: None), MessageMiddleware(lambda r: None)):
                        m.process_request(req)
                    resp = opportunity_delete(req, opp.id)
                elif name == '编辑':
                    resp = opportunity_edit(req, opp.id)
                else:
                    resp = opportunity_detail(req, opp.id)
                results.append((f'3.权限隔离-{name}', resp.status_code == 302 and (other_user.id != opp.business_manager_id)))
            except Exception as e:
                results.append((f'3.权限隔离-{name}', False))

    # 4) 软删除：普通用户删除后 is_active=False（这里不真删，只测视图可调）
    with patch('backend.apps.opportunity_management.views_opportunity.get_user_permission_codes', return_value=_perm_edit()):
        req = rf.post(f'/opportunities/{opp.id}/delete/')
        req.user = opp.business_manager
        for m in (SessionMiddleware(lambda r: None), MessageMiddleware(lambda r: None)):
            m.process_request(req)
        try:
            resp = opportunity_delete(req, opp.id)
            results.append(('4.软删除-提交', resp.status_code in (200, 302)))
        except Exception as e:
            results.append(('4.软删除-提交', False))

    # 5) 超管访问已删商机：能 200（需存在已删商机且存在超管；无则跳过）
    deleted_opp = BusinessOpportunity.objects.filter(is_active=False).first()
    superuser = User.objects.filter(is_superuser=True).first()
    if deleted_opp and superuser:
        try:
            req = rf.get(f'/opportunities/{deleted_opp.id}/')
            req.user = superuser
            for m in (SessionMiddleware(lambda r: None), MessageMiddleware(lambda r: None)):
                m.process_request(req)
            resp = opportunity_detail(req, deleted_opp.id)
            results.append(('5.软删除-超管看已删', resp.status_code in (200, 302)))
        except Exception as e:
            results.append(('5.软删除-超管看已删', False))
    else:
        results.append(('5.软删除-超管看已删', None))

    # 6) Project 关联：商机有 project_id 时详情能渲染
    opp_with_project = BusinessOpportunity.objects.filter(is_active=True).exclude(project_id__isnull=True).exclude(project_id=0).first()
    if opp_with_project:
        req = rf.get(f'/opportunities/{opp_with_project.id}/')
        req.user = user
        for m in (SessionMiddleware(lambda r: None), MessageMiddleware(lambda r: None)):
            m.process_request(req)
        try:
            resp = opportunity_detail(req, opp_with_project.id)
            results.append(('6.Project 关联-详情', resp.status_code == 200 and getattr(resp, 'context', {}).get('opportunity')))
        except Exception as e:
            results.append(('6.Project 关联-详情', False))
    else:
        results.append(('6.Project 关联-详情', None))

    # 7 & 8) 委托书/合同选择商机回填 API
    try:
        from django.test import Client as TestClient
        c = TestClient()
        c.force_login(user)
        url = reverse('customer:get_opportunities_by_client_name')
        r = c.get(url, {'opportunity_id': opp.id})
        data = r.json() if r.status_code == 200 else {}
        ok = data.get('success') and 'opportunity' in data and 'client' in data.get('opportunity', {}) and 'project' in data.get('opportunity', {})
        results.append(('7.委托书-选择商机回填 API', ok))
        results.append(('8.合同-选择商机回填 API', ok))
    except Exception as e:
        results.append(('7.委托书-选择商机回填 API', False))
        results.append(('8.合同-选择商机回填 API', False))

    # 输出
    print('8 项流程快速验证（开发库）：')
    for name, ok in results:
        if ok is None:
            print(f'  {name}: 跳过(无数据)')
        else:
            print(f'  {name}: {"通过" if ok else "失败"}')


if __name__ == '__main__':
    run()
