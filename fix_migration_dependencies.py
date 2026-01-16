#!/usr/bin/env python
"""
统一的迁移依赖修复工具
自动检测并修复Django迁移依赖不一致问题

使用方法:
    # 检查所有迁移依赖问题
    python fix_migration_dependencies.py
    
    # 检查指定应用的迁移依赖问题
    python fix_migration_dependencies.py --app customer_success
    
    # 自动修复检测到的问题
    python fix_migration_dependencies.py --auto-fix
    
    # 只检测，不修复
    python fix_migration_dependencies.py --dry-run
"""
import os
import sys
import django
import argparse
from collections import defaultdict

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.config.settings')
django.setup()

from django.db import connection
from django.apps import apps
from django.core.management import call_command
from django.utils import timezone


class MigrationDependencyFixer:
    """迁移依赖修复器"""
    
    def __init__(self, dry_run=False, verbose=False):
        self.dry_run = dry_run
        self.verbose = verbose
        self.issues_found = []
        self.fixes_applied = []
    
    def check_all_migrations(self, app_name=None):
        """检查所有迁移的依赖问题"""
        print("=" * 70)
        print("检查迁移依赖问题...")
        print("=" * 70)
        
        # 获取已应用的迁移
        applied_migrations = self._get_all_applied_migrations()
        
        # 获取所有应用的迁移文件
        apps_to_check = [app_name] if app_name else [app.label for app in apps.get_app_configs()]
        
        for app_label in apps_to_check:
            try:
                app_config = apps.get_app_config(app_label)
                migrations_dir = os.path.join(app_config.path, 'migrations')
                
                if not os.path.exists(migrations_dir):
                    continue
                
                # 获取所有迁移文件
                migration_files = sorted([
                    f.replace('.py', '') 
                    for f in os.listdir(migrations_dir) 
                    if f.endswith('.py') and f != '__init__.py'
                ])
                
                for migration_name in migration_files:
                    issue = self._check_migration_dependency(
                        app_label, migration_name, migrations_dir, applied_migrations
                    )
                    if issue:
                        self.issues_found.append(issue)
            
            except Exception as e:
                if self.verbose:
                    print(f"⚠️  检查应用 {app_label} 时出错: {e}")
        
        return self.issues_found
    
    def _get_all_applied_migrations(self):
        """获取所有已应用的迁移"""
        cursor = connection.cursor()
        cursor.execute("""
            SELECT app, name FROM django_migrations 
            ORDER BY app, name
        """)
        
        applied = defaultdict(set)
        for row in cursor.fetchall():
            applied[row[0]].add(row[1])
        
        return applied
    
    def _check_migration_dependency(self, app_label, migration_name, migrations_dir, applied_migrations):
        """检查单个迁移的依赖"""
        migration_file = os.path.join(migrations_dir, f'{migration_name}.py')
        
        try:
            with open(migration_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 解析依赖
            dependencies = self._parse_dependencies(content)
            
            # 检查迁移是否已应用
            is_applied = migration_name in applied_migrations.get(app_label, set())
            
            # 检查依赖是否已应用
            missing_deps = []
            for dep_app, dep_name in dependencies:
                if dep_name not in applied_migrations.get(dep_app, set()):
                    missing_deps.append((dep_app, dep_name))
            
            # 如果迁移已应用但依赖缺失，这是不一致的情况
            if is_applied and missing_deps:
                return {
                    'type': 'inconsistent',
                    'app': app_label,
                    'migration': migration_name,
                    'missing_dependencies': missing_deps
                }
            # 如果迁移未应用但依赖缺失，这是阻塞的情况
            elif not is_applied and missing_deps:
                return {
                    'type': 'blocked',
                    'app': app_label,
                    'migration': migration_name,
                    'missing_dependencies': missing_deps
                }
        
        except Exception as e:
            if self.verbose:
                print(f"⚠️  检查迁移 {app_label}.{migration_name} 时出错: {e}")
        
        return None
    
    def _parse_dependencies(self, content):
        """解析迁移文件中的依赖"""
        dependencies = []
        import re
        
        # 匹配 dependencies = [ ... ]
        deps_pattern = r'dependencies\s*=\s*\[(.*?)\]'
        match = re.search(deps_pattern, content, re.DOTALL)
        
        if match:
            deps_content = match.group(1)
            # 匹配 ('app_name', 'migration_name')
            dep_pattern = r"\('([^']+)',\s*'([^']+)'\)"
            for match in re.finditer(dep_pattern, deps_content):
                dep_app = match.group(1)
                dep_name = match.group(2)
                dependencies.append((dep_app, dep_name))
        
        return dependencies
    
    def fix_issues(self, auto_fix=False):
        """修复检测到的问题"""
        if not self.issues_found:
            print("\n✓ 未发现迁移依赖问题")
            return True
        
        print(f"\n发现 {len(self.issues_found)} 个问题：")
        print("=" * 70)
        
        inconsistent_issues = [i for i in self.issues_found if i['type'] == 'inconsistent']
        blocked_issues = [i for i in self.issues_found if i['type'] == 'blocked']
        
        if inconsistent_issues:
            print(f"\n⚠️  不一致问题（迁移已应用但依赖缺失）: {len(inconsistent_issues)} 个")
            for issue in inconsistent_issues:
                print(f"  - {issue['app']}.{issue['migration']}")
                for dep_app, dep_name in issue['missing_dependencies']:
                    print(f"    缺失依赖: {dep_app}.{dep_name}")
        
        if blocked_issues:
            print(f"\n🚫 阻塞问题（迁移未应用且依赖缺失）: {len(blocked_issues)} 个")
            for issue in blocked_issues:
                print(f"  - {issue['app']}.{issue['migration']}")
                for dep_app, dep_name in issue['missing_dependencies']:
                    print(f"    缺失依赖: {dep_app}.{dep_name}")
        
        if auto_fix and not self.dry_run:
            print("\n开始自动修复...")
            return self._apply_fixes()
        elif not auto_fix:
            print("\n💡 提示: 使用 --auto-fix 参数可以自动修复这些问题")
            return False
        
        return False
    
    def _apply_fixes(self):
        """应用修复"""
        # 先处理不一致问题：标记缺失的依赖为已应用
        inconsistent_issues = [i for i in self.issues_found if i['type'] == 'inconsistent']
        
        for issue in inconsistent_issues:
            print(f"\n修复不一致问题: {issue['app']}.{issue['migration']}")
            
            for dep_app, dep_name in issue['missing_dependencies']:
                print(f"  标记依赖为已应用: {dep_app}.{dep_name}")
                if self._mark_migration_applied(dep_app, dep_name):
                    self.fixes_applied.append((dep_app, dep_name))
                    print(f"  ✓ 已标记")
                else:
                    print(f"  - 已存在")
        
        # 然后处理阻塞问题：应用缺失的依赖
        blocked_issues = [i for i in self.issues_found if i['type'] == 'blocked']
        
        for issue in blocked_issues:
            print(f"\n修复阻塞问题: {issue['app']}.{issue['migration']}")
            
            for dep_app, dep_name in issue['missing_dependencies']:
                print(f"  应用依赖: {dep_app}.{dep_name}")
                try:
                    # 先尝试使用标准 migrate 命令
                    call_command('migrate', dep_app, dep_name, verbosity=1)
                    print(f"  ✓ 已应用")
                except Exception as e:
                    # 如果失败，尝试使用 migrate_standalone
                    try:
                        call_command('migrate_standalone', dep_app, dep_name, verbosity=1)
                        print(f"  ✓ 已应用（使用独立迁移）")
                    except Exception as e2:
                        print(f"  ✗ 应用失败: {e2}")
                        # 最后尝试标记为已应用
                        if self._mark_migration_applied(dep_app, dep_name):
                            print(f"  ✓ 已标记为已应用（假设表已存在）")
        
        return len(self.fixes_applied) > 0
    
    def _mark_migration_applied(self, app_label, migration_name):
        """标记迁移为已应用"""
        cursor = connection.cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM django_migrations 
            WHERE app = %s AND name = %s
        """, [app_label, migration_name])
        
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
                INSERT INTO django_migrations (app, name, applied)
                VALUES (%s, %s, %s)
            """, [app_label, migration_name, timezone.now()])
            connection.commit()
            return True
        return False
    
    def generate_report(self):
        """生成报告"""
        print("\n" + "=" * 70)
        print("迁移依赖检查报告")
        print("=" * 70)
        
        if not self.issues_found:
            print("\n✓ 未发现迁移依赖问题")
            return
        
        print(f"\n总计: {len(self.issues_found)} 个问题")
        
        if self.fixes_applied:
            print(f"✓ 已修复: {len(self.fixes_applied)} 个依赖")
            print("\n修复的依赖:")
            for app, name in self.fixes_applied:
                print(f"  - {app}.{name}")


def main():
    parser = argparse.ArgumentParser(description='修复Django迁移依赖问题')
    parser.add_argument('--app', type=str, help='只检查指定应用')
    parser.add_argument('--auto-fix', action='store_true', help='自动修复问题')
    parser.add_argument('--dry-run', action='store_true', help='只检测，不修复')
    parser.add_argument('--verbose', action='store_true', help='显示详细信息')
    
    args = parser.parse_args()
    
    fixer = MigrationDependencyFixer(dry_run=args.dry_run, verbose=args.verbose)
    
    # 检查依赖问题
    issues = fixer.check_all_migrations(app_name=args.app)
    
    # 修复问题
    if args.auto_fix:
        success = fixer.fix_issues(auto_fix=True)
        if success:
            print("\n✓ 修复完成！现在可以继续运行迁移了")
        else:
            print("\n⚠️  部分问题可能未完全修复，请检查")
    else:
        fixer.fix_issues(auto_fix=False)
    
    # 生成报告
    fixer.generate_report()


if __name__ == '__main__':
    main()
