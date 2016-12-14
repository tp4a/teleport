/*! ywl v1.0.1, (c)2016 eomsoft.net */
"use strict";

var USER_TYPE_TEAM_MEMBER = 1;
var USER_TYPE_TEAM_LEADER = 9;
var USER_TYPE_SYS_ADMIN = 99;

var AGENT_STAT_ONLINE = 1;
var AGENT_STAT_OFFLINE = 0;
// var AGENT_STAT_NOT_ACTIVE = 2;

var HOST_STAT_NOT_ACTIVE = 0;
var HOST_STAT_ACTIVE = 2;


var CACHE_TYPE_COMMAND = 1;
var CACHE_TYPE_TEAM_MEMBER = 2;
var CACHE_TYPE_TEAM = 3;
var CACHE_TYPE_COMMAND_VER = 4;
var CACHE_TYPE_GROUP = 5;
var CACHE_TYPE_COOKIE = 6;
var CACHE_TYPE_EVENT_CODE = 7;
var CACHE_TYPE_CONFIG = 8;


var KB = 1024;
var MB = 1048576;
var GB = 1073741824;
var TB = 1099511627776;
var PB = 1125899906842624;

var SECONDS_PER_DAY = 86400;
var SECONDS_PER_HOUR = 3600;
var SECONDS_PER_MINUTE = 60;


var system_group = [
	{id: 0, name: '全部'},
	{id: -1},
	{id: 1, name: 'Windows'},
	{id: -1},
	{id: 2, name: 'Linux'}
];

var paging_normal = {
	use_cookie: true,
	default_select: '25',
	selections: [
		{name: '10', val: 10},
		{name: "25", val: 25},
		{name: "50", val: 50},
		{name: "100", val: 100}]
};

var paging_big = {
	use_cookie: false,
	default_select: '100',
	selections: [{name: "100", val: 100}]
};


