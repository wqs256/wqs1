-- 创建日程表
CREATE TABLE IF NOT EXISTS `user_schedule` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_phone` varchar(20) NOT NULL COMMENT '用户手机号',
  `title` varchar(200) NOT NULL COMMENT '日程标题',
  `content` text COMMENT '日程内容',
  `start_time` datetime NOT NULL COMMENT '开始时间',
  `end_time` datetime DEFAULT NULL COMMENT '结束时间',
  `reminder_type` varchar(20) DEFAULT 'message' COMMENT '提醒方式',
  `is_reminded` tinyint(1) DEFAULT 0 COMMENT '是否已提醒',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  KEY `idx_user_phone` (`user_phone`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户日程表';

-- 创建消费记录表
CREATE TABLE IF NOT EXISTS `user_expense` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_phone` varchar(20) NOT NULL COMMENT '用户手机号',
  `amount` decimal(10,2) NOT NULL COMMENT '金额',
  `category` varchar(50) DEFAULT '其他' COMMENT '分类',
  `description` text COMMENT '描述',
  `expense_date` date NOT NULL COMMENT '消费日期',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  KEY `idx_user_phone` (`user_phone`),
  KEY `idx_expense_date` (`expense_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户消费记录表';

-- 创建翻译记录表
CREATE TABLE IF NOT EXISTS `translation_record` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_phone` varchar(20) NOT NULL COMMENT '用户手机号',
  `source_text` text NOT NULL COMMENT '原文',
  `translated_text` text NOT NULL COMMENT '译文',
  `source_lang` varchar(10) DEFAULT 'zh' COMMENT '源语言',
  `target_lang` varchar(10) DEFAULT 'en' COMMENT '目标语言',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  KEY `idx_user_phone` (`user_phone`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='翻译记录表';
