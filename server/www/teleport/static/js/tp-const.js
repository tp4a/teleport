"use strict";


var TP_LOGIN_AUTH_SYS_DEFAULT = 0;   // 系统默认
var TP_LOGIN_AUTH_USERNAME_PASSWORD = 0x0001;   // 用户名+密码
var TP_LOGIN_AUTH_USERNAME_PASSWORD_CAPTCHA = 0x0002;    // 用户名+密码+验证码
var TP_LOGIN_AUTH_USERNAME_OATH = 0x0004;  // 用户名+OATH
var TP_LOGIN_AUTH_USERNAME_PASSWORD_OATH = 0x0008;   // 用户名+密码+OATH

//=======================================================
// 远程连接认证方式
//=======================================================
var TP_AUTH_TYPE_NONE = 0;
var TP_AUTH_TYPE_PASSWORD = 1;
var TP_AUTH_TYPE_PRIVATE_KEY = 2;

//=======================================================
// 远程连接协议
//=======================================================
var TP_PROTOCOL_TYPE_RDP = 1;
var TP_PROTOCOL_TYPE_SSH = 2;
var TP_PROTOCOL_TYPE_TELNET = 3;

//=======================================================
// 远程连接子协议
//=======================================================
var TP_PROTOCOL_TYPE_RDP_DESKTOP = 100;
var TP_PROTOCOL_TYPE_SSH_SHELL = 200;
var TP_PROTOCOL_TYPE_SSH_SFTP = 201;
var TP_PROTOCOL_TYPE_TELNET_SHELL = 300;

//=======================================================
// 远程主机操作系统
//=======================================================
var TP_OS_TYPE_WINDOWS = 1;
var TP_OS_TYPE_LINUX = 2;

// =======================================================
// 远程连接会话状态
// =======================================================
var TP_SESS_STAT_RUNNING = 0; // 会话开始了，尚未结束，还在连接过程中
var TP_SESS_STAT_END = 9999; // 会话成功结束
var TP_SESS_STAT_ERR_AUTH_DENIED = 1; // 会话结束，因为认证失败
var TP_SESS_STAT_ERR_CONNECT = 2; // 会话结束，因为无法连接到远程主机
var TP_SESS_STAT_ERR_BAD_SSH_KEY = 3; // 会话结束，因为无法识别SSH私钥
var TP_SESS_STAT_ERR_INTERNAL = 4; // 会话结束，因为内部错误
var TP_SESS_STAT_ERR_UNSUPPORT_PROTOCOL = 5; // 会话结束，因为协议不支持(RDP)
var TP_SESS_STAT_ERR_BAD_PKG = 6; // 会话结束，因为收到错误的报文
var TP_SESS_STAT_ERR_RESET = 7; // 会话结束，因为teleport核心服务重置了
var TP_SESS_STAT_ERR_IO = 8; // 会话结束，因为网络中断
var TP_SESS_STAT_ERR_SESSION = 9; // 会话结束，因为无效的会话ID
var TP_SESS_STAT_ERR_AUTH_TYPE = 10; // // 会话结束，因为服务端不支持此认证方式
var TP_SESS_STAT_STARTED = 100; // 已经连接成功了，开始记录录像了
var TP_SESS_STAT_ERR_START_INTERNAL = 104; // 会话结束，因为内部错误
var TP_SESS_STAT_ERR_START_BAD_PKG = 106; // 会话结束，因为收到错误的报文
var TP_SESS_STAT_ERR_START_RESET = 107; // 会话结束，因为teleport核心服务重置了
var TP_SESS_STAT_ERR_START_IO = 108; // 会话结束，因为网络中断

// ==========================================================================
// 对象类型
// ==========================================================================
var TP_USER = 1;
var TP_GROUP_USER = 2;
var TP_ACCOUNT = 3;
var TP_GROUP_ACCOUNT = 4;
var TP_HOST = 5;
var TP_GROUP_HOST = 6;

// =======================================================
// 对象状态（用户/用户组/主机/主机组/账号/账号组/运维授权策略/审计授权策略/...）
// =======================================================
var TP_STATE_NORMAL = 1; // 正常
var TP_STATE_DISABLED = 2; // 禁用
var TP_STATE_LOCKED = 3; // 临时禁用（用于用户登录连续错误n次）

var TP_USER_TYPE_LOCAL = 1;
var TP_USER_TYPE_LDAP = 2;

// =======================================================
// 授权策略对象
// =======================================================
var TP_POLICY_OPERATOR = 0; // 授权（操作者：用户/用户组）
var TP_POLICY_ASSET = 1; // 被授权（资产：主机/主机组/账号/账号组）

// =======================================================
// 授权策略方式
// =======================================================
var TP_POLICY_AUTH_UNKNOWN = 0; // 0=未知
var TP_POLICY_AUTH_USER_ACC = 1; // 1=用户:账号
var TP_POLICY_AUTH_USER_gACC = 2; // 2=用户:账号组
var TP_POLICY_AUTH_USER_HOST = 3; // 3=用户:主机
var TP_POLICY_AUTH_USER_gHOST = 4; // 4=用户:主机组
var TP_POLICY_AUTH_gUSER_ACC = 5; // 5=用户组:账号
var TP_POLICY_AUTH_gUSER_gACC = 6; // 6=用户组:账号组
var TP_POLICY_AUTH_gUSER_HOST = 7; // 7=用户组:主机
var TP_POLICY_AUTH_gUSER_gHOST = 8; // 8=用户组:主机组

// =======================================================
// 全局配置
// =======================================================
var TP_ASSIST_STARTUP_URLPROTO = 1; // 启用urlprotocol功能

// =======================================================
// 授权标记
// =======================================================
var TP_FLAG_ALL = 0xFFFFFFFF;
// 会话记录相关
var TP_FLAG_RECORD_REPLAY = 0x0001; // 允许记录历史（录像回放）
var TP_FLAG_RECORD_REAL_TIME = 0x0002; // 允许实时监控
// RDP相关
var TP_FLAG_RDP_DESKTOP = 0x0001; // 0x1=允许远程桌面
var TP_FLAG_RDP_CLIPBOARD = 0x0002; // 0x2=允许剪贴板
var TP_FLAG_RDP_DISK = 0x0004; // 0x4=允许磁盘映射
var TP_FLAG_RDP_APP = 0x0008; // 0x8=允许远程APP（尚未实现）
var TP_FLAG_RDP_CONSOLE = 0x1000; // 0x1000=允许连接到管理员会话（RDP的console选项）
// SSH相关
var TP_FLAG_SSH_SHELL = 0x0001; // 0x1=允许SHELL
var TP_FLAG_SSH_SFTP = 0x0002; // 0x2=允许SFTP
var TP_FLAG_SSH_X11 = 0x0004; // 0x4=允许X11转发（尚未实现）
var TP_FLAG_SSH_EXEC = 0x0008; // 0x8=允许exec执行远程命令（尚未实现）
var TP_FLAG_SSH_TUNNEL = 0x0010; // 0x10=allow ssh tunnel. (not impl.)

// ==========================================================================
// 权限定义（因为权限是可以组合的，所以使用按位或的方式，目前最多能够支持32个权限粒度）
// ==========================================================================
var TP_PRIVILEGE_NONE = 0;
var TP_PRIVILEGE_ALL = 0xFFFFFFFF;//  # 具有所有权限（仅限系统管理员角色）

var TP_PRIVILEGE_LOGIN_WEB = 0x00000001;//  # 允许登录WEB

var TP_PRIVILEGE_USER_CREATE = 0x00000002;//  # 创建/编辑用户
var TP_PRIVILEGE_USER_DELETE = 0x00000004;//  # 删除用户
var TP_PRIVILEGE_USER_LOCK = 0x00000008;//  # 锁定/解锁用户
var TP_PRIVILEGE_USER_GROUP = 0x00000010;//  # 用户分组管理

var TP_PRIVILEGE_ASSET_CREATE = 0x00000020;//  # 创建/编辑资产
var TP_PRIVILEGE_ASSET_DELETE = 0x00000040;//  # 删除资产
var TP_PRIVILEGE_ASSET_LOCK = 0x00000080;//  # 锁定/解锁资产
var TP_PRIVILEGE_ASSET_GROUP = 0x00000100;//  # 资产分组管理

var TP_PRIVILEGE_OPS = 0x00000200;//  # 远程主机运维
var TP_PRIVILEGE_ACCOUNT = 0x00000400;//  # 远程主机账号管理（增删改查）
var TP_PRIVILEGE_ACCOUNT_GROUP = 0x00000800;//  # 远程主机账号分组管理
var TP_PRIVILEGE_OPS_AUZ = 0x00001000;//  # 远程主机运维授权管理
var TP_PRIVILEGE_SESSION_BLOCK = 0x00002000;//  # 阻断在线会话
var TP_PRIVILEGE_SESSION_VIEW = 0x00004000;//  # 查看在线会话

var TP_PRIVILEGE_AUDIT = 0x00008000;//  # 审计（查看历史会话）
var TP_PRIVILEGE_AUDIT_AUZ = 0x00010000;//  # 审计策略授权管理
//var TP_PRIVILEGE_AUDIT_SYSLOG = 0x00020000;//  # 查看系统日志

var TP_PRIVILEGE_SYS_ROLE = 0x00040000;//  # 角色管理
var TP_PRIVILEGE_SYS_CONFIG = 0x00080000;//  # 系统配置维护
//var TP_PRIVILEGE_SYS_OPS_HISTORY = 0x00100000;//  # 历史会话管理（例如删除历史会话、设定多长时间之前的历史会话自动删除等）
var TP_PRIVILEGE_SYS_LOG = 0x00200000;//  # 查看系统日志

var TP_PRIVILEGES = [
    TP_PRIVILEGE_LOGIN_WEB,
    TP_PRIVILEGE_USER_CREATE,
    TP_PRIVILEGE_USER_DELETE,
    TP_PRIVILEGE_USER_LOCK,
    TP_PRIVILEGE_USER_GROUP,
    TP_PRIVILEGE_ASSET_CREATE,
    TP_PRIVILEGE_ASSET_DELETE,
    TP_PRIVILEGE_ASSET_LOCK,
    TP_PRIVILEGE_ASSET_GROUP,
    TP_PRIVILEGE_OPS,
    TP_PRIVILEGE_ACCOUNT,
    TP_PRIVILEGE_ACCOUNT_GROUP,
    TP_PRIVILEGE_OPS_AUZ,
    TP_PRIVILEGE_SESSION_BLOCK,
    TP_PRIVILEGE_SESSION_VIEW,
    TP_PRIVILEGE_AUDIT,
    TP_PRIVILEGE_AUDIT_AUZ,
    //TP_PRIVILEGE_AUDIT_SYSLOG,
    TP_PRIVILEGE_SYS_ROLE,
    TP_PRIVILEGE_SYS_CONFIG,
    //TP_PRIVILEGE_SYS_OPS_HISTORY,
    TP_PRIVILEGE_SYS_LOG
];

//========================================================
// 错误值（请参考源代码/common/teleport/teleport_const.h）
//========================================================
var TPE_OK = 0;

//-------------------------------------------------------
// 通用错误值
//-------------------------------------------------------
var TPE_NEED_MORE_DATA = 1; // 需要更多数据（不一定是错误）

var TPE_NEED_LOGIN = 2;
var TPE_PRIVILEGE = 3;

var TPE_NOT_IMPLEMENT = 7;  // 尚未实现
var TPE_EXISTS = 8;
var TPE_NOT_EXISTS = 9;

// 100~299是通用错误值

var TPE_FAILED = 100;	// 内部错误
var TPE_NETWORK = 101;	// 网络错误
var TPE_DATABASE = 102; // 数据库操作失败
var TPE_EXPIRED = 103;  // 数据/操作等已过期

// HTTP请求相关错误
var TPE_HTTP_METHOD = 120;	// 无效的请求方法（不是GET/POST等），或者错误的请求方法（例如需要POST，却使用GET方式请求）
var TPE_HTTP_URL_ENCODE = 121;	// URL编码错误（无法解码）

var TPE_UNKNOWN_CMD = 124;	// 未知的命令
var TPE_JSON_FORMAT = 125;	// 错误的JSON格式（需要JSON格式数据，但是却无法按JSON格式解码）
var TPE_PARAM = 126;	// 参数错误
var TPE_DATA = 127;	// 数据错误


var TPE_OPENFILE = 300; // 无法打开文件

var TPE_HTTP_404_NOT_FOUND = 404;

var TPE_CAPTCHA_EXPIRED = 10000;
var TPE_CAPTCHA_MISMATCH = 10001;
var TPE_OATH_MISMATCH = 10002;
var TPE_SYS_MAINTENANCE = 10003;
var TPE_OATH_ALREADY_BIND = 10004;

var TPE_USER_LOCKED = 10100;
var TPE_USER_DISABLED = 10101;
var TPE_USER_AUTH = 10102;

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


// ==========================================================================
// 数据库类型
// ==========================================================================
var DB_TYPE_UNKNOWN = 0;
var DB_TYPE_SQLITE = 1;
var DB_TYPE_MYSQL = 2;

var PAGING_SELECTOR = {
    // use_cookie: true,
    default_select: '25',
    selections: [
        {name: '10', val: 10},
        {name: "25", val: 25},
        {name: "50", val: 50},
        {name: "100", val: 100}]
};

function tp_error_msg(error_code, message) {
    var msg = '';
    switch (error_code) {
        case TPE_NEED_LOGIN:
            msg = '需要刷新页面，重新登录';
            break;
        case TPE_PRIVILEGE:
            msg = '没有此操作权限';
            break;
        case TPE_NOT_IMPLEMENT:
            msg = '功能尚未实现';
            break;
        case TPE_EXISTS:
            msg = '已经存在';
            break;
        case TPE_NOT_EXISTS:
            msg = '不存在';
            break;
        case TPE_FAILED:
            msg = '内部错误';
            break;
        case TPE_NETWORK:
            msg = '网络错误';
            break;
        case TPE_DATABASE:
            msg = '数据库操作失败';
            break;

//-------------------------------------------------------
// HTTP请求相关错误
//-------------------------------------------------------
        case TPE_HTTP_METHOD:
            msg = '无效/错误的请求方法';
            break;
        case TPE_HTTP_URL_ENCODE:
            msg = 'URL编码错误（无法解码）';
            break;

        case  TPE_UNKNOWN_CMD:
            msg = '未知命令';
            break;
        case TPE_JSON_FORMAT:
            msg = '错误的JSON格式数据';
            break;
        case TPE_PARAM:
            msg = '参数错误';
            break;
        case  TPE_DATA:
            msg = '数据错误';
            break;


        case  TPE_OPENFILE:
            msg = '无法打开文件';
            break;


        case TPE_CAPTCHA_EXPIRED:
            msg = '验证码已失效';
            break;
        case  TPE_CAPTCHA_MISMATCH:
            msg = '验证码错误';
            break;
        case  TPE_OATH_MISMATCH:
            msg = '身份验证器动态验证码错误';
            break;
        case  TPE_SYS_MAINTENANCE:
            msg = '系统维护中';
            break;
        
        case TPE_OATH_ALREADY_BIND:
            msg = '该账号已经绑定了身份验证器，如无法使用，请联系管理员重置密码或更换登陆方式';
            break;

        case TPE_USER_LOCKED:
            msg = '账号已被锁定';
            break;
        case TPE_USER_DISABLED:
            msg = '账号已被禁用';
            break;
        case TPE_USER_AUTH :
            msg = '用户名/密码错误';
            break;


//-------------------------------------------------------
// 助手程序专用错误值
//-------------------------------------------------------
        case  TPE_NO_ASSIST:
            msg = '未能检测到助手程序';
            break;
        case TPE_OLD_ASSIST:
            msg = '助手程序版本太低';
            break;
        case TPE_START_CLIENT:
            msg = '无法启动客户端程序（无法创建进程）';
            break;

//-------------------------------------------------------
// 核心服务专用错误值
//-------------------------------------------------------
        case TPE_NO_CORE_SERVER:
            msg = '未能检测到核心服务';
            break;

        default:
            msg = '未知错误';
            break;
    }
    var ret_msg = message || msg;
    return ret_msg + ' (' + error_code + ')';
}
