#ifndef __TELEPORT_CONST_H__
#define __TELEPORT_CONST_H__

// 注意同步更新三个不同语言的const文件

// 本文件设定teleport各个模块之间通讯时的错误值（JSON数据），包括：
//  - WEB界面与助手
//  - WEB界面与WEB后台
//  - WEB后台与CORE核心服务

//=======================================================
// Urlprotocol相关
//=======================================================
#define TP_URLPROTO_APP_NAME		"teleport"

//=======================================================
// 远程连接认证方式
//=======================================================
#define TP_AUTH_TYPE_NONE			0
#define TP_AUTH_TYPE_PASSWORD		1
#define TP_AUTH_TYPE_PRIVATE_KEY	2

//=======================================================
// 远程连接协议
//=======================================================
#define TP_PROTOCOL_TYPE_RDP		1
#define TP_PROTOCOL_TYPE_SSH		2
#define TP_PROTOCOL_TYPE_TELNET		3

//=======================================================
// 远程连接子协议
//=======================================================
#define TP_PROTOCOL_TYPE_RDP_DESKTOP		100
#define TP_PROTOCOL_TYPE_SSH_SHELL		    200
#define TP_PROTOCOL_TYPE_SSH_SFTP	    	201
#define TP_PROTOCOL_TYPE_TELNET_SHELL		300


//=======================================================
// 远程主机操作系统
//=======================================================
#define TP_OS_TYPE_WINDOWS	1
#define TP_OS_TYPE_LINUX	2

//=======================================================
// 远程连接会话状态
//=======================================================
#define TP_SESS_STAT_RUNNING				0		// 会话开始了，正在连接
#define TP_SESS_STAT_END					9999	// 会话成功结束
#define TP_SESS_STAT_ERR_AUTH_DENIED		1		// 会话结束，因为认证失败
#define TP_SESS_STAT_ERR_CONNECT			2		// 会话结束，因为无法连接到远程主机
#define TP_SESS_STAT_ERR_BAD_SSH_KEY		3		// 会话结束，因为无法识别SSH私钥
#define TP_SESS_STAT_ERR_INTERNAL			4		// 会话结束，因为内部错误
#define TP_SESS_STAT_ERR_UNSUPPORT_PROTOCOL	5		// 会话结束，因为协议不支持(RDP)
#define TP_SESS_STAT_ERR_BAD_PKG			6		// 会话结束，因为收到错误的报文
#define TP_SESS_STAT_ERR_RESET				7		// 会话结束，因为teleport核心服务重置了
#define TP_SESS_STAT_ERR_IO					8		// 会话结束，因为网络中断
#define TP_SESS_STAT_ERR_SESSION			9		// 会话结束，因为无效的会话ID
#define TP_SESS_STAT_ERR_AUTH_TYPE			10		// 会话结束，因为不被允许的认证方式
#define TP_SESS_STAT_STARTED                100     // 已经连接成功了，开始记录录像了
#define TP_SESS_STAT_ERR_START_INTERNAL     104     // 会话结束，因为内部错误
#define TP_SESS_STAT_ERR_START_BAD_PKG      106     // 会话结束，因为收到错误的报文
#define TP_SESS_STAT_ERR_START_RESET        107     // 会话结束，因为teleport核心服务重置了
#define TP_SESS_STAT_ERR_START_IO           108     // 会话结束，因为网络中断


//=======================================================
// 授权标记
//=======================================================
#define TP_FLAG_ALL					0xFFFFFFFF
// 会话记录相关
#define TP_FLAG_RECORD_REPLAY		0x00000001	// 允许记录历史（录像回放）
#define TP_FLAG_RECORD_REAL_TIME	0x00000002	// 允许实时监控
// RDP相关
#define TP_FLAG_RDP_DESKTOP			0x00000001	// 允许远程桌面
#define TP_FLAG_RDP_CLIPBOARD		0x00000002	// 允许剪贴板
#define TP_FLAG_RDP_DISK			0x00000004	// 允许磁盘映射
#define TP_FLAG_RDP_APP				0x00000008	// 允许远程APP（尚未实现）
#define TP_FLAG_RDP_CONSOLE			0x00001000	//允许连接到管理员会话（RDP的console选项）
// SSH相关
#define TP_FLAG_SSH_SHELL			0x00000001	// 允许SHELL
#define TP_FLAG_SSH_SFTP			0x00000002	// 允许SFTP
#define TP_FLAG_SSH_X11				0x00000004	// 允许X11转发（尚未实现）
#define TP_FLAG_SSH_EXEC			0x00000008	// 允许exec执行远程命令（尚未实现）
#define TP_FLAG_SSH_TUNNEL			0x00000010	// allow ssh tunnel. (not impl.)


//=======================================================
// 错误值
//=======================================================
#define TPE_OK						0		// 成功
//-------------------------------------------------------
// 通用错误值
//-------------------------------------------------------
#define TPE_NEED_MORE_DATA			1		// 需要更多数据（不一定是错误）
#define TPE_NEED_LOGIN				2		// 需要登录
#define TPE_PRIVILEGE				3		// 没有操作权限
#define TPE_NOT_IMPLEMENT			7		// 功能尚未实现
#define TPE_EXISTS					8		// 目标已经存在
#define TPE_NOT_EXISTS              9		// 目标不存在

// 100~299是通用错误值

#define TPE_FAILED					100		// 内部错误
#define TPE_NETWORK					101		// 网络错误
#define TPE_DATABASE				102		// 数据库操作失败

// HTTP请求相关错误
#define TPE_HTTP_METHOD				120		// 无效的请求方法（不是GET/POST等），或者错误的请求方法（例如需要POST，却使用GET方式请求）
#define TPE_HTTP_URL_ENCODE			121		// URL编码错误（无法解码）
//#define TPE_HTTP_URI				122		// 无效的URI

#define TPE_UNKNOWN_CMD				124		// 未知的命令
#define TPE_JSON_FORMAT				125		// 错误的JSON格式（需要JSON格式数据，但是却无法按JSON格式解码）
#define TPE_PARAM					126		// 参数错误
#define TPE_DATA					127		// 数据错误

// #define TPE_OPENFILE_ERROR			0x1007	// 无法打开文件
// #define TPE_GETTEMPPATH_ERROR		0x1007
#define TPE_OPENFILE				300


//-------------------------------------------------------
// WEB服务专用错误值
//-------------------------------------------------------
#define TPE_CAPTCHA_EXPIRED			10000	// 验证码已过期
#define TPE_CAPTCHA_MISMATCH		10001	// 验证码错误
#define TPE_OATH_MISMATCH			10002	// 身份验证器动态验证码错误
#define TPE_SYS_MAINTENANCE			10003	// 系统维护中

#define TPE_USER_LOCKED				10100	// 用户已经被锁定（连续多次错误密码）
#define TPE_USER_DISABLED			10101	// 用户已经被禁用
#define TPE_USER_AUTH				10102	// 身份验证失败

//-------------------------------------------------------
// 助手程序专用错误值
//-------------------------------------------------------
#define TPE_NO_ASSIST				100000	// 未能检测到助手程序
#define TPE_OLD_ASSIST				100001	// 助手程序版本太低
#define TPE_START_CLIENT			100002	// 无法启动客户端程序（无法创建进程）



//-------------------------------------------------------
// 核心服务专用错误值
//-------------------------------------------------------
#define TPE_NO_CORE_SERVER			200000	// 未能检测到核心服务



#endif // __TELEPORT_CONST_H__
