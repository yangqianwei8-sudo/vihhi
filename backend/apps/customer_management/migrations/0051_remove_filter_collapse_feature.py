# Generated manually - 删除筛选条件展开/折叠功能
# 此功能为前端功能，使用localStorage存储状态，不涉及数据库模型
# 此迁移文件用于记录功能删除，实际不执行任何数据库操作

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('customer_management', '0050_remove_contact_info_change'),
    ]

    operations = [
        # 展开/折叠功能为前端功能，使用localStorage存储状态
        # 不涉及数据库模型，因此无需执行数据库操作
        # 前端代码已从 customer_list.html 中删除
        # localStorage 数据将在用户下次访问页面时自动清理（通过JavaScript）
    ]

