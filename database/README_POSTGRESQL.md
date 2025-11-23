# PostgreSQL 数据库设置和部门数据创建指南

## 步骤 1：安装 PostgreSQL

### Ubuntu/Debian 系统：
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
```

### CentOS/RHEL 系统：
```bash
sudo yum install postgresql-server postgresql-contrib
sudo postgresql-setup initdb
```

### macOS (使用 Homebrew)：
```bash
brew install postgresql
brew services start postgresql
```

## 步骤 2：启动 PostgreSQL 服务

```bash
# Ubuntu/Debian
sudo systemctl start postgresql
sudo systemctl enable postgresql

# CentOS/RHEL
sudo systemctl start postgresql
sudo systemctl enable postgresql

# macOS
brew services start postgresql
```

## 步骤 3：创建数据库和用户

```bash
# 切换到 postgres 用户
sudo -u postgres psql

# 在 PostgreSQL 命令行中执行：
CREATE DATABASE weihai_tech;
CREATE USER weihai_user WITH PASSWORD 'password123';
GRANT ALL PRIVILEGES ON DATABASE weihai_tech TO weihai_user;
ALTER USER weihai_user CREATEDB;
\q
```

## 步骤 4：配置 Django 连接 PostgreSQL

编辑 `.env` 文件，取消注释并修改 DATABASE_URL：

```bash
cd /home/devbox/project/vihhi/weihai_tech_production_system
nano .env
```

添加或修改：
```
DATABASE_URL=postgres://weihai_user:password123@localhost:5432/weihai_tech
```

## 步骤 5：运行数据库迁移

```bash
source venv/bin/activate
export DATABASE_URL="postgres://weihai_user:password123@localhost:5432/weihai_tech"
python manage.py migrate
```

## 步骤 6：创建部门数据

### 方法 1：使用 Django Shell（推荐）

```bash
source venv/bin/activate
export DATABASE_URL="postgres://weihai_user:password123@localhost:5432/weihai_tech"
python manage.py shell
```

然后在 shell 中执行：
```python
from backend.apps.system_management.models import Department

departments = [
    {'name': '总经理办公室', 'code': 'GM_OFFICE', 'description': '总经理办公室，负责公司整体战略规划和管理决策', 'order': 1},
    {'name': '造价部', 'code': 'COST', 'description': '造价部门，负责项目造价审核、成本控制等工作', 'order': 2},
    {'name': '技术部', 'code': 'TECH', 'description': '技术部门，负责技术研发和项目执行', 'order': 3},
    {'name': '商务部', 'code': 'BUSINESS', 'description': '商务部门，负责商务洽谈和客户管理', 'order': 4},
]

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
        print(f'✓ 创建部门：{dept.name} ({dept.code})')
    else:
        print(f'→ 部门已存在：{dept.name} ({dept.code})')
```

### 方法 2：使用 SQL 脚本

```bash
psql -h localhost -U weihai_user -d weihai_tech -f database/seeds/create_departments.sql
```

## 步骤 7：验证数据

```bash
psql -h localhost -U weihai_user -d weihai_tech -c "SELECT id, code, name, \"order\" FROM system_department ORDER BY \"order\";"
```

## 快速一键脚本

如果你已经安装了 PostgreSQL，可以使用以下脚本快速设置：

```bash
#!/bin/bash
# 设置数据库连接
export DATABASE_URL="postgres://weihai_user:password123@localhost:5432/weihai_tech"

# 运行迁移
cd /home/devbox/project/vihhi/weihai_tech_production_system
source venv/bin/activate
python manage.py migrate

# 创建部门数据
python manage.py shell << 'EOF'
from backend.apps.system_management.models import Department

departments = [
    {'name': '总经理办公室', 'code': 'GM_OFFICE', 'description': '总经理办公室，负责公司整体战略规划和管理决策', 'order': 1},
    {'name': '造价部', 'code': 'COST', 'description': '造价部门，负责项目造价审核、成本控制等工作', 'order': 2},
    {'name': '技术部', 'code': 'TECH', 'description': '技术部门，负责技术研发和项目执行', 'order': 3},
    {'name': '商务部', 'code': 'BUSINESS', 'description': '商务部门，负责商务洽谈和客户管理', 'order': 4},
]

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
    print(f'✓ 创建部门：{dept.name} ({dept.code})' if created else f'→ 部门已存在：{dept.name} ({dept.code})')
EOF
```

## 故障排除

### 连接被拒绝
- 检查 PostgreSQL 服务是否运行：`sudo systemctl status postgresql`
- 检查端口是否开放：`sudo netstat -tlnp | grep 5432`

### 认证失败
- 检查 `pg_hba.conf` 配置
- 确认用户名和密码正确

### 数据库不存在
- 运行步骤 3 创建数据库和用户

