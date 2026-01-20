# PostgreSQL 远程访问配置指南

## 问题描述

当使用 pgAdmin 或其他客户端连接 PostgreSQL 数据库时，如果遇到以下错误：
```
connection failed: connection to server at "192.168.0.14", port 5432 failed: 
no pg_hba.conf entry for host "客户端IP", user "weihai_user", database "postgres", no encryption
```

这表示 PostgreSQL 的 `pg_hba.conf` 文件没有允许来自该 IP 地址的连接。

## 解决方案

### 前置步骤：访问数据库服务器

**数据库服务器地址**：`192.168.0.14`

您需要先登录到这台服务器，然后才能修改配置。有以下几种方式：

#### 方式 1：SSH 远程登录（推荐）

在您的本地电脑上打开终端（Linux/Mac）或 PowerShell/CMD（Windows），使用 SSH 登录：

```bash
# 使用用户名和密码登录
ssh username@192.168.0.14

# 或使用密钥登录
ssh -i /path/to/your/key.pem username@192.168.0.14

# 示例（根据实际情况调整用户名）
ssh root@192.168.0.14
# 或
ssh postgres@192.168.0.14
# 或
ssh admin@192.168.0.14
```

**注意**：
- 需要知道服务器的登录用户名和密码（或 SSH 密钥）
- 需要网络能够访问 192.168.0.14
- 如果服务器在公司内网，您可能需要在公司网络环境中操作

**如果遇到 "Connection refused" 错误**，请参考下面的故障排查部分。

#### 方式 2：通过远程桌面（Windows 服务器）

如果数据库服务器是 Windows 系统：
- 使用远程桌面连接（RDP）工具
- 输入服务器地址：`192.168.0.14`
- 登录后打开 PowerShell 或命令提示符

#### 方式 3：通过服务器控制台

- 如果服务器在机房，可以直接在服务器前操作
- 或通过 KVM/IPMI 等远程管理工具访问

#### 方式 4：通过云平台控制台

如果服务器部署在云平台（如 Sealos、阿里云等）：
- 登录云平台控制台
- 找到对应的服务器实例
- 使用 Web SSH 或远程连接功能

---

### 步骤 1：找到 pg_hba.conf 文件位置

**在数据库服务器（192.168.0.14）上**执行以下命令：

```bash
# 方法 1：使用 psql 查询
sudo -u postgres psql -c "SHOW hba_file;"

# 方法 2：查找 PostgreSQL 数据目录
sudo -u postgres psql -c "SHOW data_directory;"
# 通常 pg_hba.conf 在数据目录下

# 方法 3：常见位置
# Linux: /etc/postgresql/13/main/pg_hba.conf
# 或: /var/lib/pgsql/13/data/pg_hba.conf
# 或: /usr/local/pgsql/data/pg_hba.conf
```

### 步骤 2：编辑 pg_hba.conf 文件

使用文本编辑器打开文件（需要 root 或 postgres 用户权限）：

```bash
sudo nano /etc/postgresql/13/main/pg_hba.conf
# 或根据实际路径调整
```

### 步骤 3：添加允许连接的规则

在文件末尾添加以下配置（根据安全需求选择）：

#### 选项 A：允许特定 IP 地址连接（推荐，更安全）

```conf
# 允许来自特定 IP 的连接（使用 md5 密码认证）
# 格式：TYPE  DATABASE        USER            ADDRESS                 METHOD
host    all                 all             192.168.0.0/24          md5
host    all                 all             10.0.0.0/8              md5
```

#### 选项 B：允许整个内网段连接

```conf
# 允许整个 192.168.0.x 网段连接
host    all                 all             192.168.0.0/24          md5
```

#### 选项 C：允许所有 IP 连接（仅用于测试，生产环境不推荐）

```conf
# 允许所有 IPv4 连接
host    all                 all             0.0.0.0/0               md5

# 允许所有 IPv6 连接
host    all                 all             ::/0                    md5
```

#### 选项 D：仅允许特定用户和数据库

```conf
# 仅允许 weihai_user 用户连接 weihai_tech 数据库
host    weihai_tech         weihai_user    192.168.0.0/24          md5
```

### 步骤 4：配置 PostgreSQL 监听地址

编辑 `postgresql.conf` 文件：

```bash
sudo nano /etc/postgresql/13/main/postgresql.conf
```

找到并修改以下配置：

```conf
# 允许监听所有网络接口（或指定 IP）
listen_addresses = '*'  # 或 'localhost,192.168.0.14'

# 确保端口正确
port = 5432
```

### 步骤 5：重启 PostgreSQL 服务

```bash
# Ubuntu/Debian
sudo systemctl restart postgresql
# 或
sudo systemctl restart postgresql@13-main

# CentOS/RHEL
sudo systemctl restart postgresql-13
# 或
sudo service postgresql restart
```

### 步骤 6：验证配置

```bash
# 检查 PostgreSQL 是否正在监听
sudo netstat -tlnp | grep 5432
# 或
sudo ss -tlnp | grep 5432

# 应该看到类似输出：
# 0.0.0.0:5432 或 192.168.0.14:5432
```

### 步骤 7：配置防火墙（如果需要）

如果服务器启用了防火墙，需要开放 5432 端口：

```bash
# Ubuntu/Debian (ufw)
sudo ufw allow 5432/tcp
sudo ufw reload

# CentOS/RHEL (firewalld)
sudo firewall-cmd --permanent --add-service=postgresql
sudo firewall-cmd --reload

# 或直接开放端口
sudo firewall-cmd --permanent --add-port=5432/tcp
sudo firewall-cmd --reload

# iptables
sudo iptables -A INPUT -p tcp --dport 5432 -j ACCEPT
sudo iptables-save
```

## pg_hba.conf 配置说明

### 配置格式

```
TYPE    DATABASE    USER        ADDRESS         METHOD
```

- **TYPE**: 连接类型
  - `local`: Unix 域套接字连接
  - `host`: TCP/IP 连接
  - `hostssl`: SSL 加密的 TCP/IP 连接
  - `hostnossl`: 非 SSL 的 TCP/IP 连接

- **DATABASE**: 数据库名
  - `all`: 所有数据库
  - `sameuser`: 与用户名同名的数据库
  - `samerole`: 与角色同名的数据库
  - 具体数据库名

- **USER**: 用户名
  - `all`: 所有用户
  - 具体用户名

- **ADDRESS**: 客户端地址
  - `0.0.0.0/0`: 所有 IPv4 地址
  - `::/0`: 所有 IPv6 地址
  - `192.168.0.0/24`: 192.168.0.x 网段
  - 具体 IP 地址

- **METHOD**: 认证方法
  - `trust`: 无密码（不安全，仅用于本地）
  - `md5`: MD5 密码认证（推荐）
  - `scram-sha-256`: SCRAM-SHA-256 认证（更安全）
  - `password`: 明文密码（不安全）
  - `peer`: 使用操作系统用户名（仅 Unix 域套接字）

## 安全建议

1. **最小权限原则**：只允许必要的 IP 地址和用户连接
2. **使用强密码**：确保数据库用户使用强密码
3. **启用 SSL**：生产环境建议使用 SSL 连接
4. **定期审查**：定期检查 `pg_hba.conf` 配置，移除不必要的规则
5. **网络隔离**：如果可能，使用 VPN 或专用网络

## 示例配置（生产环境推荐）

```conf
# 本地连接（Unix 域套接字）
local   all             all                                     peer

# IPv4 本地连接
host    all             all             127.0.0.1/32            md5

# 允许内网特定网段连接
host    weihai_tech     weihai_user    192.168.0.0/24          md5
host    weihai_tech     weihai_user    10.0.0.0/8               md5

# 拒绝其他所有连接（默认）
host    all             all             0.0.0.0/0               reject
```

## 故障排查

### 问题 0：SSH 连接被拒绝（Connection refused）

如果执行 `ssh username@192.168.0.14` 时出现 "Connection refused" 错误：

#### 可能原因和解决方案：

**1. 服务器是 Windows 系统**
- Windows 默认不安装 SSH 服务
- 使用远程桌面（RDP）连接：
  ```bash
  # 在 Windows 上按 Win+R，输入：
  mstsc
  
  # 或使用命令行
  mstsc /v:192.168.0.14
  ```
- 或在 Windows 服务器上安装 OpenSSH Server

**2. SSH 服务未启动（Linux 服务器）**
- 需要在服务器上启动 SSH 服务（需要物理访问或通过其他方式）
- 或联系服务器管理员启动 SSH 服务

**3. SSH 服务监听在其他端口**
- 尝试其他常见端口：
  ```bash
  ssh -p 2222 username@192.168.0.14
  ssh -p 22222 username@192.168.0.14
  ```

**4. 防火墙阻止了 SSH 端口**
- 需要服务器管理员开放 22 端口（或 SSH 使用的其他端口）

**5. 网络不通**
- 检查是否能 ping 通服务器：
  ```bash
  ping 192.168.0.14
  ```
- 如果 ping 不通，检查网络连接和路由

**6. 替代方案：使用其他远程管理工具**
- **远程桌面（RDP）**：适用于 Windows 服务器
- **VNC**：图形界面远程控制
- **云平台控制台**：如果服务器在云平台，使用 Web SSH
- **KVM/IPMI**：服务器硬件级别的远程管理
- **TeamViewer/AnyDesk**：第三方远程工具

**7. 请 IT 管理员协助**
- 如果无法直接访问，请联系公司 IT 管理员：
  - 请他们协助配置 `pg_hba.conf`
  - 或提供服务器访问权限
  - 或提供远程访问方式

### 问题 1：修改后仍然无法连接

- 检查配置文件语法是否正确
- 确认已重启 PostgreSQL 服务
- 检查防火墙规则
- 查看 PostgreSQL 日志：`/var/log/postgresql/postgresql-13-main.log`

### 问题 2：连接被拒绝

- 检查 `listen_addresses` 配置
- 确认 PostgreSQL 服务正在运行
- 检查端口是否正确

### 问题 3：密码认证失败

- 确认用户名和密码正确
- 检查用户是否存在：`sudo -u postgres psql -c "\du"`
- 重置密码：`sudo -u postgres psql -c "ALTER USER weihai_user WITH PASSWORD '新密码';"`

## 相关命令

```bash
# 查看当前配置
sudo cat /etc/postgresql/13/main/pg_hba.conf

# 测试连接（从客户端）
psql -h 192.168.0.14 -U weihai_user -d weihai_tech

# 查看 PostgreSQL 日志
sudo tail -f /var/log/postgresql/postgresql-13-main.log

# 检查 PostgreSQL 状态
sudo systemctl status postgresql

# 重新加载配置（不重启服务，仅适用于某些配置更改）
sudo systemctl reload postgresql
```

## 注意事项

⚠️ **重要**：
- 修改 `pg_hba.conf` 后必须重启 PostgreSQL 服务才能生效
- 生产环境不要使用 `trust` 认证方法
- 不要允许 `0.0.0.0/0` 连接（除非有特殊需求）
- 定期备份配置文件

