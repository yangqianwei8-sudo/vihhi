# 🔒 SSL 协议错误解决方案

## ❌ 错误信息
```
Failed to load resource: net::ERR_SSL_PROTOCOL_ERROR
```

## 🔍 问题原因

Django 开发服务器（`runserver`）**默认只支持 HTTP，不支持 HTTPS**。

如果您在浏览器中使用 `https://localhost:8000` 访问，会出现 SSL 协议错误。

## ✅ 解决方案

### 方案1：使用 HTTP 访问（推荐）

**正确的访问地址**：
- ✅ http://localhost:8000/
- ✅ http://127.0.0.1:8000/
- ❌ https://localhost:8000/ （会导致 SSL 错误）

### 方案2：清除浏览器缓存

如果浏览器缓存了 HTTPS 配置，需要清除：

1. **Chrome/Edge**:
   - 按 `F12` 打开开发者工具
   - 右键点击刷新按钮
   - 选择"清空缓存并硬性重新加载"
   - 或者在地址栏输入：`chrome://settings/clearBrowserData`

2. **Firefox**:
   - 按 `Ctrl+Shift+Delete`
   - 选择"缓存"
   - 点击"立即清除"

3. **清除特定网站的缓存**:
   - Chrome: 设置 → 隐私和安全 → 网站设置 → 查看所有网站数据 → 搜索 localhost → 删除
   - Firefox: 设置 → 隐私与安全 → Cookie 和网站数据 → 管理数据 → 搜索 localhost → 删除

### 方案3：使用无痕模式

打开浏览器的无痕/隐私模式访问：
- Chrome: `Ctrl+Shift+N`
- Firefox: `Ctrl+Shift+P`
- Edge: `Ctrl+Shift+N`

### 方案4：配置 HTTPS（仅用于开发测试）

如果需要 HTTPS，可以使用 Django 的 `runserver_plus` 或配置反向代理：

```bash
# 安装 django-extensions
pip install django-extensions werkzeug pyOpenSSL

# 使用 runserver_plus（支持 HTTPS）
python manage.py runserver_plus 0.0.0.0:8000 --cert-file cert.pem --key-file key.pem
```

## 🔧 验证服务器状态

### 检查服务器是否运行
```bash
curl http://localhost:8000/
```

### 检查端口监听
```bash
netstat -tlnp | grep :8000
# 或
ss -tlnp | grep :8000
```

### 查看服务器日志
如果使用后台运行：
```bash
tail -f /tmp/django_server.log
```

## 📋 正确的访问地址

### 本地访问
- **首页**: http://localhost:8000/
- **登录页**: http://localhost:8000/login/
- **交付管理**: http://localhost:8000/delivery/
- **Django Admin**: http://localhost:8000/admin/

### API 接口
- **交付记录**: http://localhost:8000/api/delivery/delivery/
- **交付文件**: http://localhost:8000/api/delivery/files/
- **交付统计**: http://localhost:8000/api/delivery/delivery/statistics/
- **交付预警**: http://localhost:8000/api/delivery/delivery/warnings/

## ⚠️ 注意事项

1. **开发环境**: Django `runserver` 只支持 HTTP，这是正常的
2. **生产环境**: 生产环境应该使用 Nginx/Apache + Gunicorn + HTTPS
3. **浏览器警告**: 如果浏览器显示"不安全连接"，这是正常的，点击"高级" → "继续访问"即可

## 🚀 快速修复步骤

1. **确认使用 HTTP 协议**:
   ```
   http://localhost:8000/  ✅
   https://localhost:8000/ ❌
   ```

2. **清除浏览器缓存**:
   - 按 `Ctrl+Shift+Delete`
   - 清除缓存和 Cookie

3. **使用无痕模式测试**:
   - 打开无痕窗口
   - 访问 http://localhost:8000/

4. **如果仍有问题**:
   ```bash
   # 重启服务器
   pkill -f "runserver.*8000"
   cd /home/devbox/project/vihhi/weihai_tech_production_system
   source venv/bin/activate
   python manage.py runserver 0.0.0.0:8000
   ```

---

**总结**: 使用 `http://` 而不是 `https://` 访问本地开发服务器即可解决问题。

