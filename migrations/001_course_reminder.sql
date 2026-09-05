CREATE TABLE IF NOT EXISTS subscription (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    group_id VARCHAR(50) NOT NULL,
    subscription_type VARCHAR(50) NOT NULL,
    target VARCHAR(100) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_subscription (group_id, subscription_type, target)
);

CREATE TABLE IF NOT EXISTS course_reminder_log (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    group_id VARCHAR(50) NOT NULL,
    course_id VARCHAR(64) NOT NULL,
    class_date DATE NOT NULL,
    start_period TINYINT NOT NULL,
    sent_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_course_reminder (group_id, course_id, class_date, start_period)
);
