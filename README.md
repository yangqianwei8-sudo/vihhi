# 维海科技生产信息化管理系统

## 项目介绍
维海科技生产信息化管理系统是为建筑设计优化服务提供商打造的综合性管理平台，涵盖项目管理、资源标准、任务协作、生产质量、交付客户、结算管理、客户成功和风险控制等核心业务模块。

## 技术栈
- 后端：Django + Django REST Framework
- 前端：Vue.js + Element UI
- 数据库：PostgreSQL
- 部署：Docker + Kubernetes (Sealos云平台)

## 项目结构




# 创建 requirements.txt
cat > /home/devbox/project/vihhi/weihai_tech_production_system/requirements.txt << 'EOF'
Django==4.2.7
djangorestframework==3.14.0
django-cors-headers==4.3.1
psycopg2-binary==2.9.7
Pillow==10.0.1
celery==5.3.4
redis==5.0.1
django-redis==5.3.0
django-filter==23.3
drf-yasg==1.21.7
python-dotenv==1.0.0
gunicorn==21.2.0
whitenoise==6.6.0
django-cleanup==8.0.0
openpyxl==3.1.2
reportlab==4.0.6
python-multipart==0.0.6
