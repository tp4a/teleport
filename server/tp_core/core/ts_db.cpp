#include "ts_db.h"
#include "ts_env.h"
#include "ts_http_client.h"

#include "../common/ts_const.h"

#include <ex/ex_str.h>

#include <algorithm>
#include <functional>

typedef std::map<ex_astr, ex_astr> mapStringKey;

TsDB g_db;

TsDB::TsDB()
{
}

TsDB::~TsDB()
{
// 	ExThreadSmartLock locker(m_lock);
// 	sqlite3Map::iterator it;
// 	for (it = m_sqlite3Map.begin(); it != m_sqlite3Map.end(); it++)
// 	{
// 		if (it->second != NULL)
// 		{
// 			sqlite3_close(it->second);
// 			it->second = NULL;
// 		}
// 	}
// 	m_sqlite3Map.clear();
}

// sqlite3* TsDB::get_db()
// {
// 	ex_astr db_path;
// 	ex_wstr2astr(g_env.m_db_file, db_path);
// 
// 	ex_u64 _tid = ex_get_thread_id();
// 
// 	{
// 		ExThreadSmartLock locker(m_lock);
// 		long tid = (long)_tid;
// 		sqlite3Map::iterator it = m_sqlite3Map.find(tid);
// 		if (it != m_sqlite3Map.end())
// 			return it->second;
// 
// 		sqlite3* sql_db = NULL;
// 		int ret = sqlite3_open(db_path.c_str(), &sql_db);
// 		if (SQLITE_OK != ret)
// 		{
// 			EXLOGE("[core-db] can not open database: %s\n", sqlite3_errmsg(sql_db));
// 			sqlite3_close(sql_db);
// 			sql_db = NULL;
// 			return NULL;
// 		}
// 
// 		m_sqlite3Map[tid] = sql_db;
// 		return sql_db;
// 	}
// 
// 	return NULL;
// }

bool TsDB::get_auth_info(int auth_id, Json::Value& jret)
{
	Json::FastWriter json_writer;
	Json::Value jreq;
	jreq["method"] = "get_auth_info";
	jreq["param"]["authid"] = auth_id;

	ex_astr json_param;
	json_param = json_writer.write(jreq);

	ex_astr param;
	ts_url_encode(json_param.c_str(), param);
	ex_astr url = "http://127.0.0.1:7190/rpc?";
	url += param;

	ex_astr body;
	if (!ts_http_get(url, body))
	{
// 		EXLOGV("request `get_auth_info` from web return: ");
// 		EXLOGV(body.c_str());
// 		EXLOGV("\n");
		return false;
	}

	Json::Reader jreader;

	if (!jreader.parse(body.c_str(), jret))
		return false;
	if (!jret.isObject())
		return false;
	if (!jret["data"].isObject())
		return false;

	Json::Value& _jret = jret["data"];

	if (
		!_jret["host_ip"].isString()
		|| !_jret["host_port"].isInt()
		|| !_jret["sys_type"].isInt()
		|| !_jret["protocol"].isInt()
		|| !_jret["auth_mode"].isInt()
		|| !_jret["account_lock"].isInt()
		|| !_jret["user_name"].isString()
		|| !_jret["user_auth"].isString()
		|| !_jret["user_param"].isString()
		|| !_jret["account_name"].isString()
		)
	{
		return false;
	}

	return true;
}

// bool TsDB::get_auth_info(int auth_id, TS_DB_AUTH_INFO& info)
// {
// 	int result = 0;
// 	char * errmsg = NULL;
// 	char **dbResult;
// 	int nRow, nColumn;
// 	int i, j;
// 	int index;
// 
// 	sqlite3* sql_exec = get_db();
// 	if (sql_exec == NULL)
// 		return false;
// 
// 	char szSQL[1024] = { 0 };
// 	ex_strformat(szSQL, 1024,
// 		"SELECT a.auth_id as auth_id, a.account_name as account_name, \
// a.host_auth_id as host_auth_id, a.host_id as host_id,host_lock, \
// b.host_sys_type as host_sys_type, host_ip, host_port, protocol, \
// c.user_pswd as user_pswd, c.cert_id as cert_id, c.user_name as user_name, \
// c.encrypt as encrypt, c.auth_mode as auth_mode,c.user_param as user_param, \
// d.account_lock as account_lock FROM ts_auth as a \
// LEFT JOIN ts_host_info as b ON a.host_id = b.host_id \
// LEFT JOIN ts_auth_info as c ON a.host_auth_id = c.id \
// LEFT JOIN ts_account as d ON a.account_name = d.account_name \
// WHERE a.auth_id=%d", auth_id);
// 
// 	result = sqlite3_get_table(sql_exec, szSQL, &dbResult, &nRow, &nColumn, &errmsg);
// 	if (result != 0)
// 		return false;
// 
// 	//查询是否存在表
// 	index = nColumn;
// 	bool bFind = false;
// 	for (i = 0; i < nRow; i++)
// 	{
// 		mapStringKey mapstringKey;
// 		for (j = 0; j < nColumn; j++)
// 		{
// 			ex_astr temp = dbResult[j];
// 			if (dbResult[index] == NULL)
// 			{
// 				mapstringKey[dbResult[j]] = "";
// 			}
// 			else
// 			{
// 				mapstringKey[dbResult[j]] = dbResult[index];
// 			}
// 
// 			++index;
// 		}
// 
// 		mapStringKey::iterator it = mapstringKey.find("host_ip");
// 		if (it != mapstringKey.end())
// 			info.host_ip = it->second;
// 
// 		it = mapstringKey.find("host_sys_type");
// 		if (it != mapstringKey.end())
// 			info.sys_type = atoi(it->second.c_str());
// 		else
// 			return false;
// 
// 		it = mapstringKey.find("account_name");
// 		if (it != mapstringKey.end())
// 			info.account_name = it->second;
// 		else
// 			return false;
// 
// 		it = mapstringKey.find("account_lock");
// 		if (it != mapstringKey.end())
// 			info.account_lock = atoi(it->second.c_str());
// 		else
// 			return false;
// 
// 		it = mapstringKey.find("host_lock");
// 		if (it != mapstringKey.end())
// 			info.host_lock = atoi(it->second.c_str());
// 		else
// 			return false;
// 
// 		it = mapstringKey.find("host_port");
// 		if (it != mapstringKey.end())
// 			info.host_port = atoi(it->second.c_str());
// 
// 		it = mapstringKey.find("protocol");
// 		if (it != mapstringKey.end())
// 		{
// 			info.protocol = atoi(it->second.c_str());
// 			it = mapstringKey.find("host_port");
// 		}
// 		else
// 		{
// 			return false;
// 		}
// 
// 		it = mapstringKey.find("encrypt");
// 		if (it != mapstringKey.end())
// 			info.is_encrypt = atoi(it->second.c_str());
// 		else
// 			return false;
// 
// 		it = mapstringKey.find("auth_mode");
// 		if (it != mapstringKey.end())
// 			info.auth_mode = atoi(it->second.c_str());
// 		else
// 			return false;
// 
// 		it = mapstringKey.find("user_name");
// 		if (it != mapstringKey.end())
// 			info.user_name = it->second;
// 		else
// 			return false;
// 
// 		it = mapstringKey.find("user_param");
// 		if (it != mapstringKey.end())
// 			info.user_param = it->second;
// 		else
// 			return false;
// 
// 		if (info.auth_mode == TS_AUTH_MODE_PASSWORD)
// 		{
// 			it = mapstringKey.find("user_pswd");
// 			if (it != mapstringKey.end())
// 				info.user_auth = it->second;
// 			else
// 				return false;
// 		}
// 		else if (info.auth_mode == TS_AUTH_MODE_PRIVATE_KEY)
// 		{
// 			it = mapstringKey.find("cert_id");
// 			if (it != mapstringKey.end())
// 			{
// 				int cert_id = atoi(it->second.c_str());
// 				ex_astr cert_pri;
// 				get_cert_pri(cert_id, cert_pri);
// 				info.user_auth = cert_pri;
// 			}
// 			else
// 			{
// 				return false;
// 			}
// 		}
// 		else if (info.auth_mode == TS_AUTH_MODE_NONE)
// 		{
// 		}
// 		else
// 		{
// 		}
// 
// 		bFind = true;
// 		break;
// 	}
// 
// 	sqlite3_free_table(dbResult);
// 	return bFind;
// }

// bool TsDB::get_cert_pri(int cert_id, ex_astr& cert_pri)
// {
// 	int result = 0;
// 	char * errmsg = NULL;
// 	char **dbResult;
// 	int nRow, nColumn;
// 	int i, j;
// 	int index;
// 
// 	sqlite3* sql_exec = get_db();
// 	if (sql_exec == NULL)
// 		return false;
// 
// 	char szSQL[256] = { 0 };
// 	ex_strformat(szSQL, 256, "SELECT a.cert_pri as cert_pri FROM ts_cert as a WHERE a.cert_id=%d", cert_id);
// 
// 	result = sqlite3_get_table(sql_exec, szSQL, &dbResult, &nRow, &nColumn, &errmsg);
// 	if (result != 0)
// 		return false;
// 
// 	//查询是否存在表
// 	index = nColumn;
// 	for (i = 0; i < nRow; i++)
// 	{
// 		mapStringKey mapstringKey;
// 		for (j = 0; j < nColumn; j++)
// 		{
// 			ex_astr temp = dbResult[j];
// 			if (dbResult[index] == NULL)
// 				mapstringKey[dbResult[j]] = "";
// 			else
// 				mapstringKey[dbResult[j]] = dbResult[index];
// 
// 			++index;
// 		}
// 
// 		mapStringKey::iterator it = mapstringKey.find("cert_pri");
// 		if (it != mapstringKey.end())
// 			cert_pri = it->second.c_str();
// 	}
// 
// 	sqlite3_free_table(dbResult);
// 	return true;
// }

// bool TsDB::get_host_count(int& count)
// {
// 	int result;
// 	char * errmsg = NULL;
// 	char **dbResult; //是 char ** 类型，两个*号
// 	int nRow, nColumn;
// 	int index;
// 
// 	sqlite3* sql_exec = get_db();
// 	if (sql_exec == NULL)
// 		return false;
// 
// 	const char* szSQL = "select count(*) from ts_host_info;";
// 
// 	result = sqlite3_get_table(sql_exec, szSQL, &dbResult, &nRow, &nColumn, &errmsg);
// 	if (result != 0)
// 	{
// 		if (dbResult)
// 			sqlite3_free_table(dbResult);
// 		return false;
// 	}
// 
// 	index = nColumn;
// 	if (nColumn != 1)
// 	{
// 		if (dbResult)
// 			sqlite3_free_table(dbResult);
// 		return false;
// 	}
// 
// 	count = atoi(dbResult[index]);
// 
// 	sqlite3_free_table(dbResult);
// 
// 	return true;
// }

bool TsDB::update_reset_log()
{
	ex_astr param;
	ts_url_encode("{\"method\":\"session_fix\",\"param\":[]}", param);
	ex_astr url = "http://127.0.0.1:7190/rpc?";
	url += param;

	ex_astr body;
	return ts_http_get(url, body);
}

// bool TsDB::session_begin(TS_SESSION_INFO& info, int& sid)
// {
// 	int result;
// 	char * errmsg = NULL;
// 	char **dbResult;
// 	int nRow, nColumn;
// 	int index;
// 
// 	sqlite3* sql_exec = get_db();
// 	if (sql_exec == NULL)
// 		return false;
// 
// 	int ret_code = 0;
// 	int begin_time = 0;
// 	int end_time = 0;
// 
// 	struct tm _now;
// 	if (!ex_localtime_now(&begin_time, &_now))
// 		return false;
// 
// 	char szTime[64] = { 0 };
// 	ex_strformat(szTime, 64, "%04d-%02d-%02d %02d:%02d:%02d", (1900 + _now.tm_year), (1 + _now.tm_mon), _now.tm_mday, _now.tm_hour, _now.tm_min, _now.tm_sec);
// 
// 	char szSQL[1024] = { 0 };
// 	ex_strformat(szSQL, 1024,
// 		"INSERT INTO ts_log (session_id, account_name,host_ip,sys_type, host_port,auth_type,\
// user_name,ret_code,begin_time,end_time,log_time, protocol) \
// VALUES (\'%s\', \'%s\',\'%s\', %d,%d,%d,\'%s\', %d, %d,%d, \'%s\', %d);",
// 		info.sid.c_str(), info.account_name.c_str(), info.host_ip.c_str(), info.sys_type,
// 		info.host_port, info.auth_mode, info.user_name.c_str(), ret_code, begin_time, end_time,
// 		szTime, info.protocol);
// 
// 	result = sqlite3_exec(sql_exec, szSQL, NULL, NULL, &errmsg);
// 	if (result != 0)
// 	{
// 		EXLOGE("[db] insert new session failed: %s.\n", errmsg);
// 		return false;
// 	}
// 
// 	ex_strformat(szSQL, 1024, "SELECT last_insert_rowid() as id;");
// 	result = sqlite3_get_table(sql_exec, szSQL, &dbResult, &nRow, &nColumn, &errmsg);
// 	if (result != 0)
// 	{
// 		if (dbResult)
// 			sqlite3_free_table(dbResult);
// 		return false;
// 	}
// 
// 	index = nColumn;
// 	if (nColumn != 1)
// 	{
// 		if (dbResult)
// 			sqlite3_free_table(dbResult);
// 		return false;
// 	}
// 
// 	sid = atoi(dbResult[index]);
// 
// 	sqlite3_free_table(dbResult);
// 
// 	return true;
// }

bool TsDB::session_begin(TS_SESSION_INFO& info, int& record_id)
{
	Json::FastWriter json_writer;
	Json::Value jreq;

// 	ex_strformat(szSQL, 1024,
// 		"INSERT INTO ts_log (session_id, account_name,host_ip,sys_type, host_port,auth_type,\
// user_name,ret_code,begin_time,end_time,log_time, protocol) \
// VALUES (\'%s\', \'%s\',\'%s\', %d,%d,%d,\'%s\', %d, %d,%d, \'%s\', %d);",
// 		info.sid.c_str(), info.account_name.c_str(), info.host_ip.c_str(), info.sys_type,
// 		info.host_port, info.auth_mode, info.user_name.c_str(), ret_code, begin_time, end_time,
// 		szTime, info.protocol);

	jreq["method"] = "session_begin";
	jreq["param"]["sid"] = info.sid.c_str();
	jreq["param"]["account_name"] = info.account_name.c_str();
	jreq["param"]["host_ip"] = info.host_ip.c_str();
	jreq["param"]["sys_type"] = info.sys_type;
	jreq["param"]["host_port"] = info.host_port;
	jreq["param"]["auth_mode"] = info.auth_mode,
	jreq["param"]["user_name"] = info.user_name.c_str();
	jreq["param"]["protocol"] = info.protocol;

	ex_astr json_param;
	json_param = json_writer.write(jreq);

	ex_astr param;
	ts_url_encode(json_param.c_str(), param);
	ex_astr url = "http://127.0.0.1:7190/rpc?";
	url += param;

	ex_astr body;
	if (!ts_http_get(url, body))
	{
		// 		EXLOGV("request `get_auth_info` from web return: ");
		// 		EXLOGV(body.c_str());
		// 		EXLOGV("\n");
		return false;
	}

	Json::Reader jreader;
	Json::Value jret;

	if (!jreader.parse(body.c_str(), jret))
		return false;
	if (!jret.isObject())
		return false;
	if (!jret["data"].isObject())
		return false;
	if (!jret["data"]["rid"].isUInt())
		return false;

	record_id = jret["data"]["rid"].asUInt();

	return true;
}

//session 结束
bool TsDB::session_end(int record_id, int ret_code)
{
// 	int result = 0;
// 	char * errmsg = NULL;
// 
// 	sqlite3* sql_exec = get_db();
// 	if (sql_exec == NULL)
// 		return false;
// 
// 	int end_time = 0;
// 	if (!ex_localtime_now(&end_time, NULL))
// 	{
// 		EXLOGE("[db] can not local time.\n");
// 		return false;
// 	}
// 
// 	char szSQL[256] = { 0 };
// 	ex_strformat(szSQL, 256, "UPDATE ts_log SET ret_code=%d, end_time=%d WHERE id=%d;", ret_code, end_time, id);
// 
// 	result = sqlite3_exec(sql_exec, szSQL, 0, 0, &errmsg);
// 	if (result != 0)
// 	{
// 		EXLOGE("[db] update log failed: %s.\n", errmsg);
// 		return false;
// 	}
// 
// 	return true;

	Json::FastWriter json_writer;
	Json::Value jreq;
	jreq["method"] = "session_end";
	jreq["param"]["rid"] = record_id;
	jreq["param"]["code"] = ret_code;

	ex_astr json_param;
	json_param = json_writer.write(jreq);

	ex_astr param;
	ts_url_encode(json_param.c_str(), param);
	ex_astr url = "http://127.0.0.1:7190/rpc?";
	url += param;

// 	ex_astr param;
// 	ts_url_encode("{\"method\":\"session_end\",\"param\":[]}", param);
// 	ex_astr url = "http://127.0.0.1:7190/rpc?";
// 	url += param;

	ex_astr body;
	return ts_http_get(url, body);
}

