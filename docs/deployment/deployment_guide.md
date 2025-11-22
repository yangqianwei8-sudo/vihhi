## 部署清单（Deployment Checklist）

1. **环境准备**
   - 操作系统：Ubuntu 20.04+/CentOS 8+（已安装 `python3.10+`、`git`、`nginx`、`systemd`）
   - 创建应用目录：`/opt/weihai-app`
   - 创建 Python 虚拟环境：`python3 -m venv /opt/weihai-app/venv`
   - 克隆代码：`git clone https://.../vihhi_weihai_tech_production_system.git /opt/weihai-app/src`

2. **配置文件**
   - 拷贝示例 `.env.example` -> `.env`，根据环境填写数据库、Redis、邮件等配置
   - 确认 `backend/settings/production.py` 中的 `ALLOWED_HOSTS`、`DATABASES`、`CACHES` 等已指向生产资源

3. **依赖安装**
   ```bash
   source /opt/weihai-app/venv/bin/activate
   pip install --upgrade pip
   pip install -r requirements.txt
   npm install --production
   npm run build   # 如果前端资源需要打包
   ```

4. **数据库与静态资源**
   ```bash
   python manage.py migrate
   python manage.py collectstatic --noinput
   python manage.py loaddata initial_roles.json   # 若有种子数据
   ```

5. **Gunicorn/Nginx**
   - Gunicorn Unit 文件：`/etc/systemd/system/weihai-app.service`
   - Nginx 站点配置：`/etc/nginx/sites-available/weihai-app.conf` 并软链接到 `sites-enabled`
   - 启动并设置自启：
     ```bash
     sudo systemctl daemon-reload
     sudo systemctl enable weihai-app
     sudo systemctl start weihai-app
     sudo systemctl restart nginx
     ```

6. **验证**
   - 健康检查：`curl http://127.0.0.1:8000/health/`
   - 管理后台：`http://域名/admin/`
   - 日志：`journalctl -u weihai-app -f`

---

## 一键部署脚本（deployment/scripts/deploy.sh）

```bash
#!/usr/bin/env bash
set -euo pipefail

APP_DIR=/opt/weihai-app
SRC_DIR=$APP_DIR/src
VENV=$APP_DIR/venv

echo \"[1/6] 更新代码\"
cd \"$SRC_DIR\"
git fetch --all
git reset --hard origin/main

echo \"[2/6] 安装依赖\"
source \"$VENV/bin/activate\"
pip install --upgrade pip
pip install -r requirements.txt

echo \"[3/6] 数据库迁移\"
python manage.py migrate

echo \"[4/6] 收集静态文件\"
python manage.py collectstatic --noinput

echo \"[5/6] 重启应用服务\"
sudo systemctl restart weihai-app

echo \"[6/6] 重载 Nginx\"
sudo systemctl reload nginx

echo \"部署完成\"
```

> 如需执行请确保：1) 脚本有执行权限 `chmod +x deploy.sh`; 2) 运行账号具备 `sudo` 权限；3) 已正确配置 `.env`。
> 质量任务脚本：`chmod +x deployment/scripts/run_quality_jobs.sh`。

---

## 质量统计与提醒调度

| 项目 | 推荐频率 | 配置示例 |
| --- | --- | --- |
| `run_quality_jobs` (推荐) | 每日 07:30 (全局 + 项目) | `30 7 * * * APP_DIR=/opt/weihai-app PROJECT_IDS=11,22 /opt/weihai-app/src/deployment/scripts/run_quality_jobs.sh >> /var/log/weihai-app/quality.log 2>&1` |
| `capture_opinion_stats` | 仅统计、不发提醒的备用任务 | `30 7 * * * /opt/weihai-app/venv/bin/python /opt/weihai-app/src/manage.py capture_opinion_stats --type quality >> /var/log/weihai-app/stats.log 2>&1` |
| `issue_quality_alerts` | 手动或备用提醒 | `0 9 * * 1-5 /opt/weihai-app/venv/bin/python /opt/weihai-app/src/manage.py issue_quality_alerts >> /var/log/weihai-app/alerts.log 2>&1` |

> 建议：
> 1. 单独的 `cron` 用户或 `systemd timer` 运行，避免与 Web 进程权限混用。
> 2. `run_quality_jobs` 会保证“先统计后提醒”，PROJECT_IDS 支持逗号分隔的项目列表。
> 3. Log 文件建议纳入 logrotate，示例：`/etc/logrotate.d/weihai-app-jobs`。

### 手动执行 / 回滚
```bash
source /opt/weihai-app/venv/bin/activate
python manage.py run_quality_jobs --stat-type quality --project 11 --project 22
python manage.py capture_opinion_stats --type quality            # 全局快照
python manage.py capture_opinion_stats --type quality --project 12
python manage.py issue_quality_alerts                            # 立即触发提醒
```

常见异常排查：
1. **数据库连接失败**：确认 VPN / 安全组开放，使用 `psql` 验证；必要时加 `--settings backend.settings.production`。
2. **WeCom 推送失败**：检查系统配置表中的 webhook/secret 是否过期，本地执行命令查看控制台输出。
3. **消息重复**：`issue_quality_alerts` 会去重未读提醒，如需重置，手动标记历史通知为已读。

### 企业微信提醒模板示例
```json
{
  "touser": "@all",
  "msgtype": "markdown",
  "agentid": 1000003,
  "markdown": {
    "content": "【质量提醒】\n项目：{{project_number}} {{project_name}}\n部位：{{location_name}}\n待处理状态：{{pending_status}}\nSLA：首响 {{response_within_24h_rate}}%，结案 {{cycle_within_7d_rate}}%\n未读提醒：{{pending_alerts}} 条\n请在 {{action_url}} 查看详情。"
  }
}
```
> 模板变量说明：
> - `response_within_24h_rate` / `cycle_within_7d_rate`：来源于统计快照 `payload.sla.compliance`。
> - `pending_alerts`：`payload.reminders.pending_total`。
> - `action_url`：详情页链接，默认指向 `production_quality/pages/opinion_review_detail`。

---

## 部署常见问题

| 场景 | 排查建议 |
| --- | --- |
| `ModuleNotFoundError` | 确认虚拟环境已激活并安装了 requirements |
| 静态资源 404 | 检查 `collectstatic` 是否成功输出到 `STATIC_ROOT`，Nginx 是否配置静态路径 |
| Gunicorn 启动失败 | 查看 `journalctl -u weihai-app`，确认 `.env` 中数据库/缓存配置、文件权限 |
| 数据库连接失败 | 检查防火墙、安全组、数据库账号密码，使用 `psql`/`mysql` 测试连接 |


