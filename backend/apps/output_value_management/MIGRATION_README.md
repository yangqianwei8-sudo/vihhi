# 产值口径迁移说明（OutputValuePolicy）

## 1. 工作目录

**所有 `python manage.py` 必须在「项目根目录」执行**（即包含 `manage.py` 的那一层），不是 `backend/` 下：

```bash
cd /home/devbox/project/vihhi/weihai_tech_production_system
# 或你本机项目路径，例如：cd D:\project\vihhi\weihai_tech_production_system
```

## 2. 若报错「No space left on device」

说明当前环境（如 devbox）磁盘满了。可先尝试腾出空间再执行下面步骤，例如：

```bash
# 删除 Python 缓存（可释放一定空间）
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null
find . -name "*.pyc" -delete 2>/dev/null
```

或在**本机/其它有空间的机器**上拉代码后执行下面的 3、4、5 步。

## 3. 创建 migrations 目录并放入迁移文件

```bash
# 在项目根目录下执行
mkdir -p backend/apps/output_value_management/migrations
mv backend/apps/output_value_management/0001_outputvaluepolicy.py \
   backend/apps/output_value_management/migrations/0001_outputvaluepolicy.py
```

若 `migrations` 目录已存在但没有 `__init__.py`，补一个空文件即可：

```bash
touch backend/apps/output_value_management/migrations/__init__.py
```

## 4. 执行迁移

```bash
python manage.py migrate output_value_management
```

## 5. 创建默认产值口径（可选，建议执行一次）

```bash
python manage.py seed_output_value_policy
```

---

**说明**：未执行迁移并 seed 时，调用产值计算会报错「未配置产值口径」，按上述步骤完成后即可正常使用。
