-- 为 user_expense 表添加 income_type 字段
ALTER TABLE `user_expense` 
ADD COLUMN `income_type` varchar(10) DEFAULT 'expense' COMMENT '收入类型: expense-支出, income-收入' 
AFTER `amount`;

-- 更新现有数据默认为支出
UPDATE `user_expense` SET `income_type` = 'expense' WHERE `income_type` IS NULL;
