#!/usr/bin/env python3
"""
清理并完成所有迁移
使用方法：python cleanup_migrations.py
"""
import os
import sys
import django
import subprocess

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.config.settings')
django.setup()

from django.core.management import call_command
from django.db import connection

def cleanup_pycache():
    """清理迁移缓存文件"""
    print("1️⃣ 清理迁移缓存文件...")
    import shutil
    
    migrations_dirs = []
    for root, dirs, files in os.walk('backend/apps'):
        if 'migrations' in dirs:
            migrations_path = os.path.join(root, 'migrations')
            migrations_dirs.append(migrations_path)
            
            # 删除__pycache__
            pycache_path = os.path.join(migrations_path, '__pycache__')
            if os.path.exists(pycache_path):
                shutil.rmtree(pycache_path)
                print(f"   ✅ 已删除: {pycache_path}")
            
            # 删除.pyc文件
            for file in os.listdir(migrations_path):
                if file.endswith('.pyc'):
                    pyc_path = os.path.join(migrations_path, file)
                    os.remove(pyc_path)
                    print(f"   ✅ 已删除: {pyc_path}")
    
    print(f"✅ 已清理 {len(migrations_dirs)} 个迁移目录的缓存")

def check_unapplied_migrations():
    """检查未应用的迁移"""
    print("\n2️⃣ 检查未应用的迁移...")
    try:
        from django.db.migrations.recorder import MigrationRecorder
        recorder = MigrationRecorder(connection)
        applied = recorder.applied_migrations()
        
        # 获取所有迁移
        from django.apps import apps
        all_migrations = set()
        for app_config in apps.get_app_configs():
            if hasattr(app_config, 'get_models'):
                try:
                    migrations_module = app_config.get_migrations_module()
                    if migrations_module:
                        from importlib import import_module
                        mod = import_module(migrations_module)
                        for name in dir(mod):
                            obj = getattr(mod, name)
                            if isinstance(obj, type) and hasattr(obj, 'name'):
                                all_migrations.add((app_config.label, obj.name))
                except:
                    pass
        
        unapplied = all_migrations - applied
        print(f"   发现 {len(unapplied)} 个未应用的迁移")
        if unapplied:
            for app, migration in sorted(unapplied)[:10]:
                print(f"      - {app}.{migration}")
            if len(unapplied) > 10:
                print(f"      ... 还有 {len(unapplied) - 10} 个")
        
        return len(unapplied)
    except Exception as e:
        print(f"   ⚠️  检查失败: {e}")
        return -1

def make_migrations():
    """创建新迁移"""
    print("\n3️⃣ 检查是否需要创建新迁移...")
    try:
        call_command('makemigrations', '--dry-run', verbosity=0)
        print("   ✅ 没有需要创建的新迁移")
        return False
    except SystemExit:
        print("   ⚠️  检测到模型变更，需要创建新迁移")
        return True
    except Exception as e:
        print(f"   ⚠️  检查失败: {e}")
        return False

def apply_migrations():
    """应用所有迁移"""
    print("\n4️⃣ 应用所有迁移...")
    try:
        call_command('migrate', '--noinput', verbosity=1)
        print("✅ 所有迁移已应用")
        return True
    except Exception as e:
        print(f"❌ 迁移失败: {e}")
        return False

def main():
    print("=" * 60)
    print("🔧 开始清理并完成所有迁移")
    print("=" * 60)
    
    # 1. 清理缓存
    cleanup_pycache()
    
    # 2. 检查未应用的迁移
    unapplied_count = check_unapplied_migrations()
    
    # 3. 检查是否需要创建新迁移
    needs_makemigrations = make_migrations()
    
    if needs_makemigrations:
        print("\n⚠️  请先运行: python manage.py makemigrations")
        return
    
    # 4. 应用迁移
    if unapplied_count > 0:
        success = apply_migrations()
        if not success:
            print("\n❌ 迁移失败，请检查错误信息")
            return
    
    # 5. 最终验证
    print("\n5️⃣ 最终验证...")
    final_unapplied = check_unapplied_migrations()
    if final_unapplied == 0:
        print("✅ 所有迁移已成功应用")
    else:
        print(f"⚠️  仍有 {final_unapplied} 个未应用的迁移")
    
    print("\n" + "=" * 60)
    print("✅ 清理和迁移完成")
    print("=" * 60)

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"\n❌ 执行失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

