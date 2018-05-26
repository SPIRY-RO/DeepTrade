/*
Navicat MySQL Data Transfer

Source Server         : 阿里云
Source Server Version : 50639
Source Host           : 47.94.199.58:3306
Source Database       : market_strategy_test

Target Server Type    : MYSQL
Target Server Version : 50639
File Encoding         : 65001

Date: 2018-03-21 10:28:41
*/

SET FOREIGN_KEY_CHECKS=0;

-- ----------------------------
-- Table structure for order
-- ----------------------------
DROP TABLE IF EXISTS `order`;
CREATE TABLE `order` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `bid_order_id` varchar(45) DEFAULT NULL COMMENT '下单id',
  `ask_order_id` varchar(45) DEFAULT NULL,
  `type` tinyint(1) DEFAULT NULL COMMENT '类型（0：买单 1：卖单）',
  `buy_price` decimal(20,8) DEFAULT NULL COMMENT '买入价格',
  `buy_fee` float(20,8) DEFAULT NULL,
  `sell_price` decimal(20,8) DEFAULT NULL COMMENT '卖出价格',
  `sell_fee` float(20,8) DEFAULT NULL,
  `status` int(1) DEFAULT NULL COMMENT '成交的状态(0:撤单 1：买单未完成 2：买单完成 3：卖单未完成 4：卖单完成)',
  `start_date` datetime DEFAULT NULL,
  `end_date` datetime DEFAULT NULL,
  `update_date` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `east8_date` datetime DEFAULT NULL COMMENT '北京时间',
  `amount` float(10,2) DEFAULT NULL COMMENT '下单总量',
  `profit_rate` float(20,8) DEFAULT NULL,
  `profit` float(20,8) DEFAULT NULL,
  `achieve_amount` float(10,2) DEFAULT NULL,
  `coin_type` varchar(45) DEFAULT NULL COMMENT '兑换币品种',
  `time_type` varchar(11) DEFAULT NULL,
  `close_rate` float(20,8) DEFAULT NULL COMMENT '收盘价的加速度',
  `average_rate` float(20,8) DEFAULT NULL COMMENT '平均线的加速度',
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique` (`coin_type`,`time_type`) USING BTREE
) ENGINE=InnoDB AUTO_INCREMENT=2367 DEFAULT CHARSET=utf8;
