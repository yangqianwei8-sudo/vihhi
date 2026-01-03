-- 添加统一社会信用代码和法定代表人字段到contract_party表

ALTER TABLE contract_party
ADD COLUMN credit_code VARCHAR(50) DEFAULT '' NOT NULL,
ADD COLUMN legal_representative VARCHAR(100) DEFAULT '' NOT NULL;

COMMENT ON COLUMN contract_party.credit_code IS '统一社会信用代码';
COMMENT ON COLUMN contract_party.legal_representative IS '法定代表人';

