#!/bin/bash

# 创建模块首页模板文件脚本
# 使用方法: bash scripts/create_module_home_templates.sh

# 模块列表
modules=(
    "settlement_center"
    "production_management"
    "plan_management"
    "task_collaboration"
    "delivery_customer"
    "archive_management"
    "resource_standard"
    "workflow_engine"
    "system_management"
    "api_management"
    "risk_management"
)

# 模板内容
TEMPLATE='{% load static %}
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ page_title }} - 维海科技信息化管理平台</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="{% static "css/common.css" %}">
    <link rel="stylesheet" href="{% static "css/modules/module-home.css" %}">
</head>
<body>
    <div class="container-fluid">
        <div class="module-home-container">
            <div class="module-home-header">
                <h1 class="module-home-title">
                    <span class="module-home-icon">{{ page_icon }}</span>
                    {{ page_title }}
                </h1>
                {% if description %}<p class="module-home-description">{{ description }}</p>{% endif %}
            </div>
            {% if summary_cards %}
            <div class="summary-cards-section">
                <div class="row g-3">
                    {% for card in summary_cards %}
                    <div class="col-12 col-sm-6 col-md-4 col-lg-3">
                        <div class="summary-card summary-card-{{ card.variant|default:"default" }}">
                            <a href="{{ card.url }}" class="summary-card-link">
                                <div class="summary-card-icon">{{ card.icon }}</div>
                                <div class="summary-card-content">
                                    <div class="summary-card-label">{{ card.label }}</div>
                                    <div class="summary-card-value">{{ card.value }}</div>
                                    {% if card.subvalue %}<div class="summary-card-subvalue">{{ card.subvalue }}</div>{% endif %}
                                    {% if card.extra %}<div class="summary-card-extra">{{ card.extra }}</div>{% endif %}
                                </div>
                            </a>
                        </div>
                    </div>
                    {% endfor %}
                </div>
            </div>
            {% endif %}
            {% if sections %}
            {% for section in sections %}
            <div class="module-section">
                <div class="module-section-header">
                    <h2 class="module-section-title">{{ section.title }}</h2>
                    {% if section.description %}<p class="module-section-description">{{ section.description }}</p>{% endif %}
                </div>
                <div class="module-section-content">
                    {% if section.layout == "grid" %}
                    <div class="row g-3">
                        {% for item in section.items %}
                        <div class="col-12 col-sm-6 col-md-4">
                            <div class="module-action-card">
                                <div class="module-action-icon">{{ item.icon }}</div>
                                <div class="module-action-content">
                                    <h3 class="module-action-title">{{ item.label }}</h3>
                                    <p class="module-action-description">{{ item.description }}</p>
                                    <a href="{{ item.url }}" class="module-action-link">{{ item.link_label|default:"查看详情 →" }}</a>
                                </div>
                            </div>
                        </div>
                        {% endfor %}
                    </div>
                    {% else %}
                    <ul class="module-action-list">
                        {% for item in section.items %}
                        <li class="module-action-item">
                            <a href="{{ item.url }}" class="module-action-link">
                                <span class="module-action-icon">{{ item.icon }}</span>
                                <span class="module-action-label">{{ item.label }}</span>
                                <span class="module-action-arrow">→</span>
                            </a>
                        </li>
                        {% endfor %}
                    </ul>
                    {% endif %}
                </div>
            </div>
            {% endfor %}
            {% endif %}
        </div>
    </div>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>'

# 获取脚本所在目录的父目录（项目根目录）
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

# 创建模板文件
for module in "${modules[@]}"; do
    template_dir="$PROJECT_ROOT/backend/templates/${module}"
    template_file="${template_dir}/home.html"
    
    # 创建目录（如果不存在）
    mkdir -p "$template_dir"
    
    # 创建模板文件
    echo "$TEMPLATE" > "$template_file"
    echo "✅ 已创建: $template_file"
done

echo ""
echo "🎉 所有模板文件创建完成！"
echo ""
echo "已创建的模板文件："
for module in "${modules[@]}"; do
    echo "  - backend/templates/${module}/home.html"
done

