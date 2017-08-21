#include "ts_session.h"
#include "ts_env.h"

#include <mbedtls/sha1.h>
#include <teleport_const.h>

TsSessionManager g_session_mgr;

TsSessionManager::TsSessionManager() :
	ExThreadBase("sid-mgr-thread")
{
}

TsSessionManager::~TsSessionManager()
{
	ts_connections::iterator it_conn = m_connections.begin();
	for (; it_conn != m_connections.end(); ++it_conn)
	{
		delete it_conn->second;
	}
	m_connections.clear();
}

void TsSessionManager::_thread_loop(void)
{
	for (;;)
	{
		ex_sleep_ms(1000);
		if (m_stop_flag)
			return;
		_check_connect_info();
	}
}

void TsSessionManager::_set_stop_flag(void)
{
	m_stop_flag = true;
}


void TsSessionManager::_check_connect_info(void)
{
	// 超过30秒未进行连接的connect-info会被移除

	ExThreadSmartLock locker(m_lock);

	ex_u64 _now = ex_get_tick_count();
	ts_connections::iterator it = m_connections.begin();
	for (; it != m_connections.end(); )
	{
#ifdef EX_DEBUG
		if (it->second->ref_count == 0 && _now - it->second->ticket_start >= 60*1000*60)
#else
		if (it->second->ref_count == 0 && _now - it->second->ticket_start >= 30000)
#endif
		{
			EXLOGV("[core] remove connection info: %s\n", it->first.c_str());
			delete it->second;
			m_connections.erase(it++);
		}
		else
		{
			++it;
		}
	}
}

ex_rv TsSessionManager::request_session(
	ex_astr& sid,	// 返回的session-id
	ex_astr account_name,
	int auth_id,
	const ex_astr& host_ip, // 要连接的主机IP
	int host_port,  // 要连接的主机端口
	int sys_type,
	int protocol,  // 要使用的协议，1=rdp, 2=ssh
	const ex_astr& user_name, // 认证信息中的用户名
	const ex_astr& user_auth, // 认证信息，密码或私钥
	const ex_astr& user_param, //
	int auth_mode // 认证方式，1=password，2=private-key
	)
{
	TS_SESSION_INFO* info = new TS_SESSION_INFO;
	info->account_name = account_name;
	info->auth_id = auth_id;
	info->host_ip = host_ip;
	info->host_port = host_port;
	info->sys_type = sys_type;
	info->protocol = protocol;
	info->user_name = user_name;
	info->user_auth = user_auth;
	info->auth_mode = auth_mode;
	info->user_param = user_param;
	if (protocol == TP_PROTOCOL_TYPE_RDP)
		info->ref_count = 2;
	else
		info->ref_count = 1;
	info->ticket_start = ex_get_tick_count();

	EXLOGD("[core] request session: user-name: [%s], protocol: [%d], auth-mode: [%d]\n", info->user_name.c_str(), info->protocol, info->auth_mode);

	if (_add_connect_info(sid, info))
		return EXRV_OK;

	delete info;
	return EXRV_FAILED;
}

bool TsSessionManager::get_connect_info(const ex_astr& sid, TS_CONNECT_INFO& info)
{
	ExThreadSmartLock locker(m_lock);

	ts_connections::iterator it = m_connections.find(sid);
	if (it == m_connections.end())
		return false;

	info.sid = it->second->sid;
	info.account_name = it->second->account_name;
	info.auth_id = it->second->auth_id;
	info.host_ip = it->second->host_ip;
	info.host_port = it->second->host_port;
	info.protocol = it->second->protocol;
	info.user_name = it->second->user_name;

	info.user_auth = it->second->user_auth;

	info.user_param = it->second->user_param;
	info.auth_mode = it->second->auth_mode;
	info.sys_type = it->second->sys_type;
	info.ref_count = it->second->ref_count;
	info.ticket_start = it->second->ticket_start;

	it->second->ref_count++;
// 	if (it->second->ref_count <= 0)
// 	{
// 		delete it->second;
// 		m_sessions.erase(it);
// 	}

	return true;
}

bool TsSessionManager::_add_connect_info(ex_astr& sid, TS_CONNECT_INFO* info)
{
	ExThreadSmartLock locker(m_lock);

	ex_astr _sid;
	int retried = 0;
	ts_connections::iterator it;
	for (;;)
	{
		_gen_session_id(_sid, info, 6);
		it = m_connections.find(_sid);
		if (it == m_connections.end())
			break;

		retried++;
		if (retried > 50)
			return false;
	}

	info->sid = _sid;
	m_connections.insert(std::make_pair(_sid, info));

	sid = _sid;
	if (info->protocol_type == TP_PROTOCOL_TYPE_RDP)
	{
		char szTmp[8] = { 0 };
		snprintf(szTmp, 8, "%02X", (unsigned char)(info->account_name.length() + info->account_secret.length()));
		sid += szTmp;
	}

	return true;
}

void TsSessionManager::_gen_session_id(ex_astr& sid, const TS_CONNECT_INFO* info, int len)
{
	mbedtls_sha1_context sha;
	ex_u8 sha_digist[20] = { 0 };

	ex_u64 _tick = ex_get_tick_count();
	ex_u64 _tid = ex_get_thread_id();

	mbedtls_sha1_init(&sha);
	mbedtls_sha1_starts(&sha);
	mbedtls_sha1_update(&sha, (const unsigned char*)&_tick, sizeof(ex_u64));
	mbedtls_sha1_update(&sha, (const unsigned char*)&_tid, sizeof(ex_u64));
	mbedtls_sha1_update(&sha, (const unsigned char*)info->remote_host_ip.c_str(), info->remote_host_ip.length());
	mbedtls_sha1_update(&sha, (const unsigned char*)info->client_ip.c_str(), info->client_ip.length());
	mbedtls_sha1_update(&sha, (const unsigned char*)info->account_name.c_str(), info->account_name.length());
	mbedtls_sha1_finish(&sha, sha_digist);
	mbedtls_sha1_free(&sha);

	char szTmp[64] = { 0 };
	int _len = len / 2 + 1;
	int i = 0;
	int offset = 0;
	for (i = 0; i < _len; ++i)
	{
		snprintf(szTmp + offset, 64 - offset, "%02X", sha_digist[i]);
		offset += 2;
	}

	sid.assign(szTmp, len);
}
