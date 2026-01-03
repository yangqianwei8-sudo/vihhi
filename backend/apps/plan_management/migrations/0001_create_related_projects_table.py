# Generated manually to fix missing plan_strategic_goal_related_projects table

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = []

    operations = [
        migrations.RunSQL(
            sql="""
            CREATE TABLE IF NOT EXISTS plan_strategic_goal_related_projects (
                id BIGSERIAL PRIMARY KEY,
                strategicgoal_id BIGINT NOT NULL,
                project_id BIGINT NOT NULL,
                CONSTRAINT plan_strategic_goal_related_projects_strategicgoal_id_fkey 
                    FOREIGN KEY (strategicgoal_id) 
                    REFERENCES plan_strategic_goal(id) 
                    ON DELETE CASCADE,
                CONSTRAINT plan_strategic_goal_related_projects_project_id_fkey 
                    FOREIGN KEY (project_id) 
                    REFERENCES production_management_project(id) 
                    ON DELETE CASCADE,
                CONSTRAINT plan_strategic_goal_related_projects_unique 
                    UNIQUE (strategicgoal_id, project_id)
            );
            CREATE INDEX IF NOT EXISTS plan_strategic_goal_related_projects_strategicgoal_id_idx 
                ON plan_strategic_goal_related_projects(strategicgoal_id);
            CREATE INDEX IF NOT EXISTS plan_strategic_goal_related_projects_project_id_idx 
                ON plan_strategic_goal_related_projects(project_id);
            """,
            reverse_sql="""
            DROP TABLE IF EXISTS plan_strategic_goal_related_projects;
            """
        ),
    ]

