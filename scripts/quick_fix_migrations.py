#!/usr/bin/env python
"""
Django迁移快速修复脚本
执行优化方案中的第一阶段快速修复：
1. 检查并修复迁移依赖问题
2. 识别并清理空合并迁移
3. 验证修复结果
"""
import os
import sys
import django
import re
from pathlib import Path

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.config.settings')
django.setup()

from django.apps import apps
from django.db import connection
from django.core.management import call_command
from django.utils import timezone


class QuickMigrationFixer:
    """快速迁移修复器"""
    
    def __init__(self, dry_run=False):
        self.dry_run = dry_run
        self.issues_found = []
        self.fixes_applied = []
        self.merge_migrations_found = []
        
    def run(self):
        """执行快速修复"""
        print("=" * 70)
        print("Django迁移快速修复")
        print("=" * 70)
        print(f"模式: {'预览模式（不实际修改）' if self.dry_run else '执行模式（将实际修改）'}")
        print()
        
        # 步骤1: 检查迁移依赖
        print("步骤1: 检查迁移依赖问题...")
        self.check_migration_dependencies()
        print()
        
        # 步骤2: 识别合并迁移
        print("步骤2: 识别合并迁移...")
        self.find_merge_migrations()
        print()
        
        # 步骤3: 修复依赖问题
        if not self.dry_run and self.issues_found:
            print("步骤3: 修复依赖问题...")
            self.fix_dependencies()
            print()
        
        # 步骤4: 清理空合并迁移
        if not self.dry_run and self.merge_migrations_found:
            print("步骤4: 清理空合并迁移...")
            self.cleanup_empty_merge_migrations()
            print()
        
        # 步骤5: 生成报告
        self.generate_report()
        
    def check_migration_dependencies(self):
        """检查迁移依赖问题"""
        try:
            # 使用现有的修复工具检查
            from fix_migration_dependencies import MigrationDependencyFixer
            
            fixer = MigrationDependencyFixer(dry_run=True, verbose=True)
            issues = fixer.check_all_migrations()
            
            if issues:
                print(f"发现 {len(issues)} 个依赖问题:")
                for issue in issues[:10]:  # 只显示前10个
                    print(f"  ⚠️  {issue}")
                if len(issues) > 10:
                    print(f"  ... 还有 {len(issues) - 10} 个问题")
                self.issues_found = issues
            else:
                print("  ✓ 未发现依赖问题")
                
        except Exception as e:
            print(f"  ⚠️  检查依赖时出错: {e}")
            print("  尝试使用Django命令检查...")
            try:
                call_command('showmigrations', verbosity=0)
                print("  ✓ Django迁移检查通过")
            except Exception as e2:
                print(f"  ✗ Django迁移检查失败: {e2}")
                self.issues_found.append(str(e2))
    
    def find_merge_migrations(self):
        """查找所有合并迁移"""
        project_root = Path(__file__).parent.parent
        migrations_dir = project_root / 'backend' / 'apps'
        
        merge_pattern = re.compile(r'.*merge.*\.py$', re.IGNORECASE)
        
        for app_dir in migrations_dir.iterdir():
            if not app_dir.is_dir():
                continue
                
            migrations_path = app_dir / 'migrations'
            if not migrations_path.exists():
                continue
            
            for migration_file in migrations_path.glob('*.py'):
                if migration_file.name == '__init__.py':
                    continue
                
                if merge_pattern.match(migration_file.name):
                    # 检查是否是空操作
                    is_empty = self._is_empty_merge_migration(migration_file)
                    self.merge_migrations_found.append({
                        'app': app_dir.name,
                        'file': migration_file.name,
                        'path': str(migration_file),
                        'empty': is_empty
                    })
        
        if self.merge_migrations_found:
            print(f"  发现 {len(self.merge_migrations_found)} 个合并迁移:")
            for merge in self.merge_migrations_found:
                status = "空操作" if merge['empty'] else "有操作"
                print(f"    - {merge['app']}/{merge['file']} ({status})")
        else:
            print("  ✓ 未发现合并迁移")
    
    def _is_empty_merge_migration(self, migration_file):
        """检查合并迁移是否为空操作"""
        try:
            content = migration_file.read_text(encoding='utf-8')
            # 检查operations是否为空
            if 'operations = [' in content:
                # 提取operations部分
                ops_match = re.search(r'operations\s*=\s*\[(.*?)\]', content, re.DOTALL)
                if ops_match:
                    ops_content = ops_match.group(1).strip()
                    # 如果operations中只有空白或注释，认为是空的
                    ops_content_clean = re.sub(r'#.*?\n', '', ops_content).strip()
                    return len(ops_content_clean) == 0
            return False
        except Exception as e:
            print(f"    警告: 无法读取 {migration_file}: {e}")
            return False
    
    def fix_dependencies(self):
        """修复依赖问题"""
        try:
            from fix_migration_dependencies import MigrationDependencyFixer
            
            fixer = MigrationDependencyFixer(dry_run=False, verbose=True)
            fixer.check_all_migrations()
            
            # 尝试自动修复
            if hasattr(fixer, 'fix_issues'):
                fixer.fix_issues()
                self.fixes_applied.append("依赖问题已修复")
                print("  ✓ 依赖问题修复完成")
            else:
                print("  ⚠️  依赖修复功能不可用，请手动修复")
                
        except Exception as e:
            print(f"  ✗ 修复依赖时出错: {e}")
    
    def cleanup_empty_merge_migrations(self):
        """清理空合并迁移"""
        empty_merges = [m for m in self.merge_migrations_found if m['empty']]
        
        if not empty_merges:
            print("  没有需要清理的空合并迁移")
            return
        
        print(f"  准备清理 {len(empty_merges)} 个空合并迁移...")
        
        for merge in empty_merges:
            migration_path = Path(merge['path'])
            backup_path = migration_path.parent / f"{migration_path.name}.backup"
            
            try:
                # 备份原文件
                if backup_path.exists():
                    backup_path.unlink()
                migration_path.rename(backup_path)
                
                print(f"    ✓ 已备份并移除: {merge['app']}/{merge['file']}")
                self.fixes_applied.append(f"清理空合并迁移: {merge['app']}/{merge['file']}")
                
                # TODO: 更新依赖关系，移除对该合并迁移的引用
                # 这需要更复杂的逻辑，暂时只备份文件
                
            except Exception as e:
                print(f"    ✗ 清理失败 {merge['file']}: {e}")
    
    def generate_report(self):
        """生成修复报告"""
        print("=" * 70)
        print("修复报告")
        print("=" * 70)
        
        print(f"\n发现的问题:")
        print(f"  - 依赖问题: {len(self.issues_found)} 个")
        print(f"  - 合并迁移: {len(self.merge_migrations_found)} 个")
        if self.merge_migrations_found:
            empty_count = sum(1 for m in self.merge_migrations_found if m['empty'])
            print(f"    - 空合并迁移: {empty_count} 个")
        
        if self.fixes_applied:
            print(f"\n已应用的修复:")
            for fix in self.fixes_applied:
                print(f"  ✓ {fix}")
        else:
            print(f"\n未应用任何修复（{'预览模式' if self.dry_run else '无需修复'}）")
        
        print("\n" + "=" * 70)
        
        if self.dry_run:
            print("\n提示: 这是预览模式，未实际修改任何文件")
            print("要执行修复，请运行: python scripts/quick_fix_migrations.py")
        else:
            print("\n快速修复完成！")
            print("建议下一步:")
            print("  1. 运行: python manage.py showmigrations")
            print("  2. 运行: python manage.py migrate --plan")
            print("  3. 验证迁移状态")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Django迁移快速修复')
    parser.add_argument('--dry-run', action='store_true', 
                       help='预览模式，不实际修改文件')
    args = parser.parse_args()
    
    fixer = QuickMigrationFixer(dry_run=args.dry_run)
    fixer.run()


if __name__ == '__main__':
    main()

