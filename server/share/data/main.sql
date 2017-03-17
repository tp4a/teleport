
CREATE TABLE `ts_account` (
  `account_id` integer PRIMARY KEY AUTOINCREMENT,
  `account_type` int(11) DEFAULT 0,
  `account_name` varchar(32) DEFAULT NULL,
  `account_pwd` varchar(32) DEFAULT NULL,
  `account_status` int(11) DEFAULT 0,
  `account_lock` int(11) DEFAULT 0,
  `account_desc` varchar(255)
);

INSERT INTO `main`.`ts_account` VALUES (1, 100, 'admin', '8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918', 0, 0, '超级管理员');

CREATE TABLE `ts_auth`(
`auth_id`  INTEGER PRIMARY KEY AUTOINCREMENT,
`account_name`  varchar(256),
`host_id`  INTEGER,
`host_auth_id`  int(11) NOT NULL
);

CREATE TABLE `ts_cert` (
`cert_id`  integer PRIMARY KEY AUTOINCREMENT,
`cert_name`  varchar(256),
`cert_pub`  varchar(2048) DEFAULT '',
`cert_pri`  varchar(4096) DEFAULT '',
`cert_desc`  varchar(256)
);


CREATE TABLE `ts_config` (
`name`  varchar(256) NOT NULL,
`value`  varchar(256),
PRIMARY KEY (`name` ASC)
);


INSERT INTO `main`.`ts_config` VALUES ('ts_server_ip', '127.0.0.1');
INSERT INTO `main`.`ts_config` VALUES ('ts_server_rpc_port', 52080);
INSERT INTO `main`.`ts_config` VALUES ('ts_server_rdp_port', 52089);
INSERT INTO `main`.`ts_config` VALUES ('ts_server_ssh_port', 52189);
INSERT INTO `main`.`ts_config` VALUES ('ts_server_telnet_port', 52389);
INSERT INTO `main`.`ts_config` VALUES ('ts_server_rpc_ip', '127.0.0.1');

CREATE TABLE `ts_group` (
  `group_id` integer PRIMARY KEY AUTOINCREMENT,
  `group_name` varchar(255) DEFAULT''
);


CREATE TABLE `ts_host_info`(
`host_id`  integer PRIMARY KEY AUTOINCREMENT,
`group_id`  int(11) DEFAULT 0,
`host_sys_type`  int(11) DEFAULT 1,
`host_ip`  varchar(32) DEFAULT '',
`host_port`  int(11) DEFAULT 0,
`protocol`  int(11) DEFAULT 0,
`host_lock`  int(11) DEFAULT 0,
`host_desc`   DEFAULT ''
);

CREATE TABLE `ts_auth_info`(
`id`  INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
`host_id`  INTEGER,
`auth_mode`  INTEGER,
`user_name`  varchar(256),
`user_pswd`  varchar(256),
`user_param` varchar(256),
`cert_id`  INTEGER,
`encrypt`  INTEGER,
`log_time`  varchar(60)
);


CREATE TABLE `ts_log` (
`id`  INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
`session_id`  varchar(32),
`account_name`  varchar(64),
`host_ip`  varchar(32),
`host_port`  INTEGER,
`sys_type`  INTEGER DEFAULT 0,
`auth_type`  INTEGER,
`protocol` INTEGER,
`user_name`  varchar(64),
`ret_code`  INTEGER,
`begin_time`  INTEGER,
`end_time`  INTEGER,
`log_time`  varchar(64)
);
