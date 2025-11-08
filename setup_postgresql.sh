#!/bin/bash
# PostgreSQL 快速设置脚本

set -e

echo "=========================================="
echo "PostgreSQL 数据库设置和部门数据创建"
echo "=========================================="
echo ""

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 步骤 1：检查 PostgreSQL 是否安装
echo "步骤 1: 检查 PostgreSQL 安装..."
if command -v psql &> /dev/null; then
    echo -e "${GREEN}✓ PostgreSQL 已安装${NC}"
    psql --version
else
    echo -e "${YELLOW}⚠ PostgreSQL 未安装${NC}"
    echo "请先安装 PostgreSQL："
    echo "  Ubuntu/Debian: sudo apt install postgresql postgresql-contrib"
    echo "  CentOS/RHEL: sudo yum install postgresql-server postgresql-contrib"
    echo "  macOS: brew install postgresql"
    exit 1
fi

# 步骤 2：检查 PostgreSQL 服务是否运行
echo ""
echo "步骤 2: 检查 PostgreSQL 服务..."
if systemctl is-active --quiet postgresql 2>/dev/null || pg_isready -h localhost -p 5432 &> /dev/null; then
    echo -e "${GREEN}✓ PostgreSQL 服务正在运行${NC}"
else
    echo -e "${YELLOW}⚠ PostgreSQL 服务未运行，尝试启动...${NC}"
    if sudo systemctl start postgresql 2>/dev/null; then
        echo -e "${GREEN}✓ PostgreSQL 服务已启动${NC}"
        sleep 2
    else
        echo -e "${RED}✗ 无法启动 PostgreSQL 服务${NC}"
        echo "请手动启动：sudo systemctl start postgresql"
        exit 1
    fi
fi

# 步骤 3：创建数据库和用户
echo ""
echo "步骤 3: 创建数据库和用户..."
DB_NAME="weihai_tech"
DB_USER="weihai_user"
DB_PASSWORD="password123"

# 检查数据库是否存在
if sudo -u postgres psql -lqt | cut -d \| -f 1 | grep -qw $DB_NAME; then
    echo -e "${GREEN}✓ 数据库 $DB_NAME 已存在${NC}"
else
    echo "创建数据库 $DB_NAME..."
    sudo -u postgres psql << EOF
CREATE DATABASE $DB_NAME;
CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';
GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;
ALTER USER $DB_USER CREATEDB;
\q
EOF
    echo -e "${GREEN}✓ 数据库和用户创建成功${NC}"
fi

# 步骤 4：配置环境变量
echo ""
echo "步骤 4: 配置环境变量..."
export DATABASE_URL="postgres://$DB_USER:$DB_PASSWORD@localhost:5432/$DB_NAME"
echo "DATABASE_URL=$DATABASE_URL" >> .env
echo -e "${GREEN}✓ 环境变量已配置${NC}"

# 步骤 5：运行数据库迁移
echo ""
echo "步骤 5: 运行数据库迁移..."
cd "$(dirname "$0")"
source venv/bin/activate
python manage.py migrate
echo -e "${GREEN}✓ 数据库迁移完成${NC}"

# 步骤 6：创建部门数据
echo ""
echo "步骤 6: 创建部门数据..."
python manage.py shell << 'EOF'
from backend.apps.system_management.models import Department

departments = [
    {'name': '总经理办公室', 'code': 'GM_OFFICE', 'description': '总经理办公室，负责公司整体战略规划和管理决策', 'order': 1},
    {'name': '造价部', 'code': 'COST', 'description': '造价部门，负责项目造价审核、成本控制等工作', 'order': 2},
    {'name': '技术部', 'code': 'TECH', 'description': '技术部门，负责技术研发和项目执行', 'order': 3},
    {'name': '商务部', 'code': 'BUSINESS', 'description': '商务部门，负责商务洽谈和客户管理', 'order': 4},
]

created_count = 0
existing_count = 0

for dept_data in departments:
    dept, created = Department.objects.get_or_create(
        code=dept_data['code'],
        defaults={
            'name': dept_data['name'],
            'description': dept_data['description'],
            'order': dept_data['order'],
            'is_active': True
        }
    )
    if created:
        created_count += 1
        print(f'✓ 创建部门：{dept.name} ({dept.code})')
    else:
        existing_count += 1
        dept.name = dept_data['name']
        dept.description = dept_data['description']
        dept.order = dept_data['order']
        dept.is_active = True
        dept.save()
        print(f'→ 部门已存在，已更新：{dept.name} ({dept.code})')

print(f'\n部门创建完成！新建：{created_count} 个，已存在：{existing_count} 个')
print('\n当前所有部门列表：')
for dept in Department.objects.all().order_by('order', 'id'):
    status = '✓' if dept.is_active else '✗'
    print(f'  {status} [{dept.code}] {dept.name}')
EOF

echo ""
echo "=========================================="
echo -e "${GREEN}✓ 所有步骤完成！${NC}"
echo "=========================================="
echo ""
echo "数据库连接信息："
echo "  数据库：$DB_NAME"
echo "  用户：$DB_USER"
echo "  主机：localhost:5432"
echo ""
echo "环境变量已保存到 .env 文件"
echo "下次使用时，设置：export DATABASE_URL=\"postgres://$DB_USER:$DB_PASSWORD@localhost:5432/$DB_NAME\""

