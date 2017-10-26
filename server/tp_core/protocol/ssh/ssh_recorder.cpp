#include "ssh_recorder.h"
//#include <teleport_const.h>

static ex_u8 TPP_RECORD_MAGIC[4] = { 'T', 'P', 'P', 'R' };

TppSshRec::TppSshRec()
{
	m_cmd_cache.reserve(MAX_SIZE_PER_FILE);

	memset(&m_head, 0, sizeof(TS_RECORD_HEADER));
	memcpy((ex_u8*)(&m_head.info.magic), TPP_RECORD_MAGIC, sizeof(ex_u32));
	m_head.info.ver = 0x03;

    m_file_info = NULL;
    m_file_data = NULL;
    m_file_cmd = NULL;
}

TppSshRec::~TppSshRec()
{
}

bool TppSshRec::_on_begin(const TPP_CONNECT_INFO* info)
{
	if (NULL == info)
		return false;
	m_head.basic.timestamp = (ex_u64)time(NULL);
	m_head.basic.protocol_type = (ex_u16)info->protocol_type;
	m_head.basic.protocol_sub_type = (ex_u16)info->protocol_sub_type;
	m_head.basic.conn_port = (ex_u16)info->conn_port;
	// 	memcpy(m_head.account, info.acc_username.c_str(), info.acc_username.length() > 15 ? 15 : info.acc_username.length());
	// 	memcpy(m_head.username, info.user_username.c_str(), info.user_username.length() > 15 ? 15 : info.user_username.length());
	// 	memcpy(m_head.ip, info.host_ip.c_str(), info.host_ip.length() > 17 ? 17 : info.host_ip.length());

	memcpy(m_head.basic.acc_username, info->acc_username, strlen(info->acc_username) >= 63 ? 63 : strlen(info->acc_username));
	memcpy(m_head.basic.user_username, info->user_username, strlen(info->user_username) >= 63 ? 63 : strlen(info->user_username));
	memcpy(m_head.basic.host_ip, info->host_ip, strlen(info->host_ip) >= 39 ? 39 : strlen(info->host_ip));
	memcpy(m_head.basic.conn_ip, info->conn_ip, strlen(info->conn_ip) >= 39 ? 39 : strlen(info->conn_ip));



    ex_wstr fname_info = m_base_path;
    ex_path_join(fname_info, false, m_base_fname.c_str(), NULL);
    fname_info += L".tpr";
    ex_wstr fname_data = m_base_path;
    ex_path_join(fname_data, false, m_base_fname.c_str(), NULL);
    fname_data += L".dat";
    ex_wstr fname_cmd = m_base_path;
    ex_path_join(fname_cmd, false, m_base_fname.c_str(), NULL);
    fname_cmd += L"-cmd.txt";

    m_file_info = ex_fopen(fname_info, L"wb");
    if (NULL == m_file_info)
    {
        EXLOGE("[ssh] can not open record info-file for write.\n");
        return false;
    }
    m_file_data = ex_fopen(fname_data, L"wb");
    if (NULL == m_file_data)
    {
        EXLOGE("[ssh] can not open record data-file for write.\n");
        return false;
    }
    m_file_cmd = ex_fopen(fname_cmd, L"wb");
    if (NULL == m_file_cmd)
    {
        EXLOGE("[ssh] can not open record cmd-file for write.\n");
        return false;
    }

    return true;
}

bool TppSshRec::_on_end()
{
	// 如果还有剩下未写入的数据，写入文件中。
	if (m_cache.size() > 0)
		_save_to_data_file();
	if (m_cmd_cache.size() > 0)
		_save_to_cmd_file();

//	// 更新头信息
//	//m_head.timestamp = m_start_time;
//	m_head.info.time_ms = (ex_u32)(m_last_time - m_start_time);
//
//	ex_wstr fname = m_base_path;
//	ex_path_join(fname, false, m_base_fname.c_str(), NULL);
//	fname += L".tpr";
//
//	FILE* f = ex_fopen(fname, L"wb");
//	if (NULL == f)
//	{
//		EXLOGE("[ssh] can not open record file for write.\n");
//		return false;
//	}
//
//	fwrite(&m_head, sizeof(TS_RECORD_HEADER), 1, f);
//	fflush(f);
//	fclose(f);

    fclose(m_file_info);
    fclose(m_file_data);
    fclose(m_file_cmd);

    return true;
}

void TppSshRec::flush_record() {
    if (m_cache.size() > 0)
        _save_to_data_file();
    if (m_cmd_cache.size() > 0)
        _save_to_cmd_file();
}

void TppSshRec::record(ex_u8 type, const ex_u8* data, size_t size)
{
	if (data == NULL || 0 == size)
		return;
	m_head.info.packages++;
    m_head.info.time_ms = (ex_u32)(m_last_time - m_start_time);

	if (sizeof(TS_RECORD_PKG) + size + m_cache.size() > m_cache.buffer_size())
		_save_to_data_file();

	TS_RECORD_PKG pkg = {0};
	//memset(&pkg, 0, sizeof(TS_RECORD_PKG));
	pkg.type = type;
	pkg.size = (ex_u32)size;

	if (m_start_time > 0)
	{
		m_last_time = ex_get_tick_count();
		pkg.time_ms = (ex_u32)(m_last_time - m_start_time);
	}

	m_cache.append((ex_u8*)&pkg, sizeof(TS_RECORD_PKG));
	m_cache.append(data, size);
}

void TppSshRec::record_win_size_startup(int width, int height)
{
	m_head.basic.width = (ex_u16)width;
	m_head.basic.height = (ex_u16)height;
}

void TppSshRec::record_win_size_change(int width, int height)
{
	TS_RECORD_WIN_SIZE pkg = {0};
	pkg.width = (ex_u16)width;
	pkg.height = (ex_u16)height;
	record(TS_RECORD_TYPE_SSH_TERM_SIZE, (ex_u8*)&pkg, sizeof(TS_RECORD_WIN_SIZE));
}

void TppSshRec::record_command(const ex_astr& cmd)
{
	char szTime[100] = { 0 };
#ifdef EX_OS_WIN32
	SYSTEMTIME st;
	GetLocalTime(&st);
	sprintf_s(szTime, 100, "[%04d-%02d-%02d %02d:%02d:%02d] ", st.wYear, st.wMonth, st.wDay, st.wHour, st.wMinute, st.wSecond);
#else
	time_t timep;
	struct tm *p;
	time(&timep);
	p = localtime(&timep);
	if (p == NULL)
		return;
	sprintf(szTime, "[%04d-%02d-%02d %02d:%02d:%02d] ", p->tm_year + 1900, p->tm_mon + 1, p->tm_mday, p->tm_hour, p->tm_min, p->tm_sec);
#endif
	size_t lenTime = strlen(szTime);


	if (m_cmd_cache.size() + cmd.length() + lenTime > m_cache.buffer_size())
		_save_to_cmd_file();

	m_cmd_cache.append((ex_u8*)szTime, lenTime);
	m_cmd_cache.append((ex_u8*)cmd.c_str(), cmd.length());
}

bool TppSshRec::_save_to_data_file()
{
//	wchar_t _str_file_id[24] = { 0 };
//	ex_wcsformat(_str_file_id, 24, L".%03d", 0);// m_head.file_count);
//
//	ex_wstr fname = m_base_path;
//	ex_path_join(fname, false, m_base_fname.c_str(), NULL);
//	fname += _str_file_id;
//
//	FILE* f = ex_fopen(fname, L"wb");
//
//	if (NULL == f)
//	{
//		EXLOGE("[ssh] can not open record data-file for write.\n");
//		m_cache.empty();
//		return false;
//	}

	ex_u32 size = m_cache.size();
	fwrite(&size, sizeof(ex_u32), 1, m_file_data);
	fwrite(m_cache.data(), m_cache.size(), 1, m_file_data);
//	fflush(f);
//	fclose(f);

	//m_head.file_count++;
	//m_head.file_size += m_cache.size();

	m_cache.empty();
	return true;
}

bool TppSshRec::_save_to_cmd_file()
{
	ex_wstr fname = m_base_path;
	ex_path_join(fname, false, m_base_fname.c_str(), NULL);
	fname += L"-cmd.txt";

	FILE* f = ex_fopen(fname, L"ab");
	if (NULL == f)
	{
		m_cmd_cache.empty();
		return false;
	}

	fwrite(m_cmd_cache.data(), m_cmd_cache.size(), 1, f);
	fflush(f);
	fclose(f);

	m_cmd_cache.empty();

	return true;
}
