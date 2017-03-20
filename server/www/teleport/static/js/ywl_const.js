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


//========================================================
// 错误值（请参考源代码/common/teleport/teleport_const.h）
//========================================================
var TPE_OK = 0;

//-------------------------------------------------------
// 通用错误值
//-------------------------------------------------------
var TPE_NEED_MORE_DATA = 1; // 需要更多数据（不一定是错误）


// 100~299是通用错误值

var TPE_FAILED = 100;	// 内部错误
var TPE_NETWORK = 101;	// 网络错误

// HTTP请求相关错误
var TPE_HTTP_METHOD = 120;	// 无效的请求方法（不是GET/POST等），或者错误的请求方法（例如需要POST，却使用GET方式请求）
var TPE_HTTP_URL_ENCODE = 121;	// URL编码错误（无法解码）
//#define TPE_HTTP_URI				122	// 无效的URI

var TPE_UNKNOWN_CMD = 124;	// 未知的命令
var TPE_JSON_FORMAT = 125;	// 错误的JSON格式（需要JSON格式数据，但是却无法按JSON格式解码）
var TPE_PARAM = 126;	// 参数错误
var TPE_DATA = 127;	// 数据错误


// #define TPE_OPENFILE_ERROR			0x1007	// 无法打开文件
// #define TPE_GETTEMPPATH_ERROR		0x1007


//-------------------------------------------------------
// 助手程序专用错误值
//-------------------------------------------------------
var TPE_NO_ASSIST = 100000;	// 未能检测到助手程序
var TPE_OLD_ASSIST = 100001;	// 助手程序版本太低
var TPE_START_CLIENT = 100002;	// 无法启动客户端程序（无法创建进程）


//-------------------------------------------------------
// 核心服务专用错误值
//-------------------------------------------------------
var TPE_NO_CORE_SERVER = 200000;	// 未能检测到核心服务



