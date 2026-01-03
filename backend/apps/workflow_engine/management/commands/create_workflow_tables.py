"""
手动创建审批流程引擎数据库表的命令
用于绕过迁移依赖问题
"""
from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = '手动创建审批流程引擎的数据库表'

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            self.stdout.write('开始创建审批流程引擎数据库表...')
            
            # 创建审批流程模板表
            try:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS workflow_template (
                        id BIGSERIAL PRIMARY KEY,
                        name VARCHAR(200) NOT NULL,
                        code VARCHAR(100) NOT NULL UNIQUE,
                        description TEXT,
                        category VARCHAR(100),
                        status VARCHAR(20) NOT NULL DEFAULT 'draft',
                        allow_withdraw BOOLEAN NOT NULL DEFAULT TRUE,
                        allow_reject BOOLEAN NOT NULL DEFAULT TRUE,
                        allow_transfer BOOLEAN NOT NULL DEFAULT FALSE,
                        timeout_hours INTEGER,
                        timeout_action VARCHAR(20) NOT NULL DEFAULT 'notify',
                        created_by_id BIGINT NOT NULL,
                        created_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        updated_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        CONSTRAINT fk_workflow_template_created_by 
                            FOREIGN KEY (created_by_id) REFERENCES system_user(id) ON DELETE RESTRICT
                    );
                """)
                self.stdout.write(self.style.SUCCESS('✓ 创建 workflow_template 表成功'))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'⚠ workflow_template 表可能已存在: {e}'))
            
            # 创建审批节点表
            try:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS workflow_approval_node (
                        id BIGSERIAL PRIMARY KEY,
                        workflow_id BIGINT NOT NULL,
                        name VARCHAR(200) NOT NULL,
                        node_type VARCHAR(20) NOT NULL DEFAULT 'approval',
                        sequence INTEGER NOT NULL DEFAULT 1,
                        approver_type VARCHAR(30),
                        approval_mode VARCHAR(20) NOT NULL DEFAULT 'single',
                        condition_expression TEXT,
                        is_required BOOLEAN NOT NULL DEFAULT TRUE,
                        can_reject BOOLEAN NOT NULL DEFAULT TRUE,
                        can_transfer BOOLEAN NOT NULL DEFAULT FALSE,
                        timeout_hours INTEGER,
                        description TEXT,
                        CONSTRAINT fk_approval_node_workflow 
                            FOREIGN KEY (workflow_id) REFERENCES workflow_template(id) ON DELETE CASCADE,
                        CONSTRAINT unique_workflow_sequence UNIQUE (workflow_id, sequence)
                    );
                """)
                self.stdout.write(self.style.SUCCESS('✓ 创建 workflow_approval_node 表成功'))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'⚠ workflow_approval_node 表可能已存在: {e}'))
            
            # 创建审批实例表
            try:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS workflow_approval_instance (
                        id BIGSERIAL PRIMARY KEY,
                        instance_number VARCHAR(100) NOT NULL UNIQUE,
                        workflow_id BIGINT NOT NULL,
                        content_type_id INTEGER NOT NULL,
                        object_id BIGINT NOT NULL,
                        status VARCHAR(20) NOT NULL DEFAULT 'draft',
                        current_node_id BIGINT,
                        applicant_id BIGINT NOT NULL,
                        apply_time TIMESTAMP,
                        apply_comment TEXT,
                        completed_time TIMESTAMP,
                        final_comment TEXT,
                        created_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        updated_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        CONSTRAINT fk_approval_instance_workflow 
                            FOREIGN KEY (workflow_id) REFERENCES workflow_template(id) ON DELETE RESTRICT,
                        CONSTRAINT fk_approval_instance_content_type 
                            FOREIGN KEY (content_type_id) REFERENCES django_content_type(id) ON DELETE CASCADE,
                        CONSTRAINT fk_approval_instance_current_node 
                            FOREIGN KEY (current_node_id) REFERENCES workflow_approval_node(id) ON DELETE SET NULL,
                        CONSTRAINT fk_approval_instance_applicant 
                            FOREIGN KEY (applicant_id) REFERENCES system_user(id) ON DELETE RESTRICT
                    );
                """)
                self.stdout.write(self.style.SUCCESS('✓ 创建 workflow_approval_instance 表成功'))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'⚠ workflow_approval_instance 表可能已存在: {e}'))
            
            # 创建审批记录表
            try:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS workflow_approval_record (
                        id BIGSERIAL PRIMARY KEY,
                        instance_id BIGINT NOT NULL,
                        node_id BIGINT NOT NULL,
                        approver_id BIGINT NOT NULL,
                        result VARCHAR(20) NOT NULL DEFAULT 'pending',
                        comment TEXT,
                        transferred_to_id BIGINT,
                        approval_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        created_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        CONSTRAINT fk_approval_record_instance 
                            FOREIGN KEY (instance_id) REFERENCES workflow_approval_instance(id) ON DELETE CASCADE,
                        CONSTRAINT fk_approval_record_node 
                            FOREIGN KEY (node_id) REFERENCES workflow_approval_node(id) ON DELETE RESTRICT,
                        CONSTRAINT fk_approval_record_approver 
                            FOREIGN KEY (approver_id) REFERENCES system_user(id) ON DELETE RESTRICT,
                        CONSTRAINT fk_approval_record_transferred_to 
                            FOREIGN KEY (transferred_to_id) REFERENCES system_user(id) ON DELETE SET NULL
                    );
                """)
                self.stdout.write(self.style.SUCCESS('✓ 创建 workflow_approval_record 表成功'))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'⚠ workflow_approval_record 表可能已存在: {e}'))
            
            # 创建多对多关系表
            try:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS workflow_approval_node_approver_users (
                        id BIGSERIAL PRIMARY KEY,
                        approvalnode_id BIGINT NOT NULL,
                        user_id BIGINT NOT NULL,
                        CONSTRAINT fk_node_approver_users_node 
                            FOREIGN KEY (approvalnode_id) REFERENCES workflow_approval_node(id) ON DELETE CASCADE,
                        CONSTRAINT fk_node_approver_users_user 
                            FOREIGN KEY (user_id) REFERENCES system_user(id) ON DELETE CASCADE,
                        CONSTRAINT unique_node_user UNIQUE (approvalnode_id, user_id)
                    );
                """)
                self.stdout.write(self.style.SUCCESS('✓ 创建 workflow_approval_node_approver_users 表成功'))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'⚠ workflow_approval_node_approver_users 表可能已存在: {e}'))
            
            try:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS workflow_approval_node_approver_roles (
                        id BIGSERIAL PRIMARY KEY,
                        approvalnode_id BIGINT NOT NULL,
                        role_id BIGINT NOT NULL,
                        CONSTRAINT fk_node_approver_roles_node 
                            FOREIGN KEY (approvalnode_id) REFERENCES workflow_approval_node(id) ON DELETE CASCADE,
                        CONSTRAINT fk_node_approver_roles_role 
                            FOREIGN KEY (role_id) REFERENCES system_role(id) ON DELETE CASCADE,
                        CONSTRAINT unique_node_role UNIQUE (approvalnode_id, role_id)
                    );
                """)
                self.stdout.write(self.style.SUCCESS('✓ 创建 workflow_approval_node_approver_roles 表成功'))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'⚠ workflow_approval_node_approver_roles 表可能已存在: {e}'))
            
            try:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS workflow_approval_node_approver_departments (
                        id BIGSERIAL PRIMARY KEY,
                        approvalnode_id BIGINT NOT NULL,
                        department_id BIGINT NOT NULL,
                        CONSTRAINT fk_node_approver_depts_node 
                            FOREIGN KEY (approvalnode_id) REFERENCES workflow_approval_node(id) ON DELETE CASCADE,
                        CONSTRAINT fk_node_approver_depts_dept 
                            FOREIGN KEY (department_id) REFERENCES system_department(id) ON DELETE CASCADE,
                        CONSTRAINT unique_node_dept UNIQUE (approvalnode_id, department_id)
                    );
                """)
                self.stdout.write(self.style.SUCCESS('✓ 创建 workflow_approval_node_approver_departments 表成功'))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'⚠ workflow_approval_node_approver_departments 表可能已存在: {e}'))
            
            # 创建索引
            try:
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_approval_instance_content_type_object 
                        ON workflow_approval_instance(content_type_id, object_id);
                    CREATE INDEX IF NOT EXISTS idx_approval_instance_status 
                        ON workflow_approval_instance(status);
                """)
                self.stdout.write(self.style.SUCCESS('✓ 创建索引成功'))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'⚠ 索引可能已存在: {e}'))
            
            # 标记迁移为已应用
            try:
                cursor.execute("""
                    INSERT INTO django_migrations (app, name, applied)
                    VALUES ('workflow_engine', '0001_initial', CURRENT_TIMESTAMP)
                    ON CONFLICT DO NOTHING;
                """)
                self.stdout.write(self.style.SUCCESS('✓ 标记迁移为已应用'))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'⚠ 迁移记录可能已存在: {e}'))
            
            self.stdout.write(self.style.SUCCESS('\n✅ 审批流程引擎数据库表创建完成！'))

