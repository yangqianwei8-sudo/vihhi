-- Add collaboration_plan field to plan_plan table
-- This field is missing from the database but exists in the model

-- Check if column exists before adding
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'plan_plan' 
        AND column_name = 'collaboration_plan'
    ) THEN
        ALTER TABLE plan_plan 
        ADD COLUMN collaboration_plan TEXT NULL;
        
        COMMENT ON COLUMN plan_plan.collaboration_plan IS '协作计划，如果选择了协作人员，必须填写协作计划';
    END IF;
END $$;
















