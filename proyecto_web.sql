DROP DATABASE IF EXISTS proyecto_web;

CREATE DATABASE IF NOT EXISTS proyecto_web
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE proyecto_web;

-- =========================
-- USUARIOS (login futuro)
-- =========================
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('admin','user') DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =========================
-- DISPOSITIVOS (switches/routers)
-- =========================
CREATE TABLE IF NOT EXISTS devices (
  id INT AUTO_INCREMENT PRIMARY KEY,
  hostname VARCHAR(100) NOT NULL,
  mgmt_ip VARCHAR(45) NOT NULL,             -- IPv4 o IPv6
  device_type ENUM('switch','router','unknown') NOT NULL DEFAULT 'unknown',
  model VARCHAR(100) NOT NULL DEFAULT 'UNKNOWN',
  serial VARCHAR(100) NOT NULL DEFAULT 'UNKNOWN',
  ios_version VARCHAR(100) NOT NULL DEFAULT 'UNKNOWN',
  last_seen TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uq_devices_mgmt_ip (mgmt_ip),
  KEY idx_devices_serial (serial),
  KEY idx_devices_hostname (hostname)
);

-- =========================
-- INTERFACES CON IP (solo las que NO sean NO_IP)
-- =========================
CREATE TABLE IF NOT EXISTS device_interfaces (
  id INT AUTO_INCREMENT PRIMARY KEY,
  device_id INT NOT NULL,
  interface_name VARCHAR(80) NOT NULL,
  ip_address VARCHAR(45) NOT NULL,
  prefix_len TINYINT UNSIGNED NULL,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

  CONSTRAINT fk_if_device
    FOREIGN KEY (device_id) REFERENCES devices(id)
    ON DELETE CASCADE,

  UNIQUE KEY uq_device_if_ip (device_id, interface_name, ip_address),
  KEY idx_if_ip (ip_address),
  KEY idx_if_name (interface_name)
);

-- =========================
-- ERRORES DE CONEXIÓN / RECOLECCIÓN
-- =========================
CREATE TABLE IF NOT EXISTS device_errors (
  id INT AUTO_INCREMENT PRIMARY KEY,
  mgmt_ip VARCHAR(45) NOT NULL,
  hostname VARCHAR(100) NULL,
  error_text TEXT NOT NULL,
  seen_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  KEY idx_err_ip (mgmt_ip)
);
