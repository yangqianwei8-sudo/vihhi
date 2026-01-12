"""
模板配置示例
提供各种详情页的配置示例
"""
from .field_types import (
    FieldConfig,
    SectionConfig,
    TabConfig,
    ActionConfig,
    DetailPageConfig,
)

# 收文详情配置示例
INCOMING_DOCUMENT_DETAIL_CONFIG = DetailPageConfig(
    title="收文详情",
    layout="standard",
    sections=[
        SectionConfig(
            id="basic-info",
            title="基本信息",
            layout="grid",
            columns=2,
            fields=[
                FieldConfig(id="document_number", label="收文编号", type="text", span=6),
                FieldConfig(id="title", label="文件标题", type="text", span=12),
                FieldConfig(id="sender", label="发文单位", type="text", span=6),
                FieldConfig(id="sender_contact", label="联系人", type="text", span=6),
                FieldConfig(id="sender_phone", label="联系电话", type="phone", span=6),
                FieldConfig(id="document_type", label="文件类型", type="text", span=6),
                FieldConfig(id="document_date", label="文件日期", type="date", span=6, format="date"),
                FieldConfig(id="receive_date", label="收文日期", type="date", span=6, format="date"),
                FieldConfig(id="get_status_display", label="状态", type="status", span=6),
                FieldConfig(id="get_priority_display", label="优先级", type="status", span=6),
            ]
        ),
        SectionConfig(
            id="content-info",
            title="内容",
            layout="list",
            fields=[
                FieldConfig(id="summary", label="摘要", type="text", span=12),
                FieldConfig(id="content", label="文件内容", type="text", span=12),
            ]
        ),
        SectionConfig(
            id="handle-info",
            title="处理信息",
            layout="grid",
            columns=2,
            fields=[
                FieldConfig(id="handler.get_full_name", label="处理人", type="text", span=6),
                FieldConfig(id="completed_at", label="完成时间", type="datetime", span=6, format="datetime"),
                FieldConfig(id="handle_notes", label="处理意见", type="text", span=12),
            ]
        ),
        SectionConfig(
            id="attachment-info",
            title="附件",
            layout="list",
            fields=[
                FieldConfig(id="attachment.url", label="附件", type="link", span=12),
            ]
        ),
        SectionConfig(
            id="notes-info",
            title="备注",
            layout="list",
            fields=[
                FieldConfig(id="notes", label="备注", type="text", span=12),
            ]
        ),
    ],
    actions=[
        ActionConfig(
            id="edit",
            label="编辑",
            type="primary",
            icon="pencil",
            url_name="delivery_customer:incoming_document_edit",
        ),
    ],
    timeline_enabled=True,
)

# 客户详情配置示例
CUSTOMER_DETAIL_CONFIG = DetailPageConfig(
    title="客户详情",
    layout="tabbed",
    sections=[
        # 基本信息区块
        SectionConfig(
            id="basic-info",
            title="基本信息",
            layout="grid",
            columns=2,
            fields=[
                FieldConfig(id="name", label="客户名称", type="text", span=12),
                FieldConfig(id="code", label="客户编码", type="text", span=6),
                FieldConfig(id="unified_credit_code", label="统一信用代码", type="text", span=6),
            ]
        ),
        # 企业信息区块
        SectionConfig(
            id="company-info",
            title="企业信息",
            layout="grid",
            columns=2,
            fields=[
                FieldConfig(id="legal_representative", label="法定代表人", type="text", span=6),
                FieldConfig(id="established_date", label="成立日期", type="date", span=6, format="date"),
                FieldConfig(id="company_phone", label="联系电话", type="phone", span=6),
                FieldConfig(id="company_email", label="邮箱", type="email", span=6),
                FieldConfig(id="company_address", label="地址", type="text", span=12),
            ]
        ),
        # 客户分类区块
        SectionConfig(
            id="category-info",
            title="客户分类",
            layout="grid",
            columns=2,
            fields=[
                FieldConfig(id="get_client_level_display", label="客户等级", type="status", span=6),
                FieldConfig(id="get_grade_display", label="客户分级", type="status", span=6),
                FieldConfig(id="get_client_type_display", label="客户类型", type="text", span=6),
                FieldConfig(id="region", label="所属区域", type="text", span=6),
                FieldConfig(id="get_source_display", label="客户来源", type="text", span=6),
            ]
        ),
        # 财务信息区块
        SectionConfig(
            id="financial-info",
            title="财务信息",
            layout="grid",
            columns=2,
            fields=[
                FieldConfig(id="score", label="客户评分", type="text", span=6),
                FieldConfig(id="health_score", label="健康度评分", type="text", span=6),
                FieldConfig(id="total_contract_amount", label="累计合同金额", type="currency", span=6, format="currency"),
                FieldConfig(id="total_payment_amount", label="累计回款金额", type="currency", span=6, format="currency"),
            ]
        ),
        # 负责人信息区块
        SectionConfig(
            id="responsible-info",
            title="负责人信息",
            layout="grid",
            columns=2,
            fields=[
                FieldConfig(id="responsible_user.get_full_name", label="负责人", type="text", span=6),
                FieldConfig(id="public_sea_entry_time", label="进入公海时间", type="datetime", span=6, format="datetime"),
                FieldConfig(id="get_public_sea_reason_display", label="进入公海原因", type="text", span=6),
            ]
        ),
        # 关联联系人 - 使用自定义组件
        SectionConfig(
            id="contacts-info",
            title="关联联系人",
            render_mode="custom",
            component="customer_management/components/_contacts_table.html",
        ),
        # 被执行信息 - 使用自定义组件
        SectionConfig(
            id="execution-info",
            title="被执行信息",
            render_mode="custom",
            component="customer_management/components/_execution_table.html",
        ),
    ],
    tabs=[
        TabConfig(
            id="basic",
            title="基本信息",
            section_ids=["basic-info", "company-info", "category-info", "financial-info", "responsible-info"]
        ),
        TabConfig(
            id="contacts",
            title="关联联系人",
            section_ids=["contacts-info"]
        ),
        TabConfig(
            id="executions",
            title="被执行信息",
            section_ids=["execution-info"]
        ),
    ],
    actions=[
        ActionConfig(
            id="edit",
            label="编辑客户",
            type="primary",
            icon="pencil",
            url_name="business_pages:customer_edit",
        ),
        ActionConfig(
            id="submit_approval",
            label="提交审批",
            type="warning",
            icon="send",
            url_name="business_pages:customer_submit_approval",
            conditions={"can_submit": True},  # 需要根据权限动态显示
        ),
    ],
    timeline_enabled=True,
)
