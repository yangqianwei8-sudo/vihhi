from django.urls import path

from . import views

app_name = "resource_standard"

urlpatterns = [
    path("standards/", views.standard_list, name="standard_list"),
    path("standards/create/", views.standard_create, name="standard_create"),
    path("standards/<int:pk>/", views.standard_detail, name="standard_detail"),
    path("standards/<int:pk>/edit/", views.standard_edit, name="standard_edit"),

    path("materials/", views.material_price_list, name="material_price_list"),
    path("materials/create/", views.material_price_create, name="material_price_create"),
    path("materials/<int:pk>/edit/", views.material_price_edit, name="material_price_edit"),

    path("cost-indicators/", views.cost_indicator_list, name="cost_indicator_list"),
    path("cost-indicators/create/", views.cost_indicator_create, name="cost_indicator_create"),
    path("cost-indicators/<int:pk>/edit/", views.cost_indicator_edit, name="cost_indicator_edit"),

    path("report-templates/", views.report_template_list, name="report_template_list"),
    path("report-templates/create/", views.report_template_create, name="report_template_create"),
    path("report-templates/<int:pk>/edit/", views.report_template_edit, name="report_template_edit"),

    path("opinion-templates/", views.opinion_template_list, name="opinion_template_list"),
    path("opinion-templates/create/", views.opinion_template_create, name="opinion_template_create"),
    path("opinion-templates/<int:pk>/edit/", views.opinion_template_edit, name="opinion_template_edit"),

    path("knowledge/tags/", views.knowledge_tag_list, name="knowledge_tag_list"),
    path("knowledge/tags/create/", views.knowledge_tag_create, name="knowledge_tag_create"),
    path("knowledge/tags/<int:pk>/edit/", views.knowledge_tag_edit, name="knowledge_tag_edit"),

    path("knowledge/risk-cases/", views.risk_case_list, name="risk_case_list"),
    path("knowledge/risk-cases/create/", views.risk_case_create, name="risk_case_create"),
    path("knowledge/risk-cases/<int:pk>/edit/", views.risk_case_edit, name="risk_case_edit"),
    path("knowledge/risk-cases/export/", views.risk_case_export, name="risk_case_export"),

    path("knowledge/technical-solutions/", views.technical_solution_list, name="technical_solution_list"),
    path("knowledge/technical-solutions/create/", views.technical_solution_create, name="technical_solution_create"),
    path("knowledge/technical-solutions/<int:pk>/edit/", views.technical_solution_edit, name="technical_solution_edit"),

    path("maintenance/professional-categories/", views.professional_category_list, name="professional_category_list"),
    path("maintenance/professional-categories/create/", views.professional_category_create, name="professional_category_create"),
    path("maintenance/professional-categories/<int:pk>/edit/", views.professional_category_edit, name="professional_category_edit"),

    path("maintenance/system-parameters/", views.system_parameter_list, name="system_parameter_list"),
    path("maintenance/system-parameters/create/", views.system_parameter_create, name="system_parameter_create"),
    path("maintenance/system-parameters/<int:pk>/edit/", views.system_parameter_edit, name="system_parameter_edit"),
]
