-- Run this script once in MySQL to create DebugMate's database and table.
CREATE DATABASE IF NOT EXISTS debugmate_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE debugmate_db;

CREATE TABLE IF NOT EXISTS debug_history (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  error_type VARCHAR(100) NULL,
  error_text MEDIUMTEXT NOT NULL,
  explanation TEXT NOT NULL,
  suggested_fix TEXT NOT NULL,
  status VARCHAR(20) NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  INDEX idx_debug_history_created_at (created_at),
  INDEX idx_debug_history_error_type (error_type)
) ENGINE=InnoDB;
