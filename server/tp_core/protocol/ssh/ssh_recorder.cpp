#include "ssh_recorder.h"

static ex_u8 TPP_RECORD_MAGIC[4] = { 'T', 'P', 'P', 'R' };

TppSshRec::TppSshRec()
{
	m_cmd_cache.reserve(MAX_SIZE_PER_FILE);

	memset(&m_head, 0, sizeof(TS_RECORD_HEADER));
	memcpy((ex_u8*)(&m_head.magic), TPP_RECORD_MAGIC, sizeof(ex_u32));
	m_head.ver = 0x02;
	m_head.protocol = TS_PROXY_PROTOCOL_SSH;
}

TppSshRec::~TppSshRec()
{
	end();
}

void TppSshRec::_on_begin(const TPP_SESSION_INFO* info)
{
	if (NULL == info)
		return;
	m_head.timestamp = time(NULL);
	m_head.port = info->host_port;
	// 	memcpy(m_head.account, info.account_name.c_str(), info.account_name.length() > 15 ? 15 : info.account_name.length());
	// 	memcpy(m_head.username, info.user_name.c_str(), info.user_name.length() > 15 ? 15 : info.user_name.length());
	// 	memcpy(m_head.ip, info.host_ip.c_str(), info.host_ip.length() > 17 ? 17 : info.host_ip.length());

	memcpy(m_head.account, info->account_name, strlen(info->account_name) > 15 ? 15 : strlen(info->account_name));
	memcpy(m_head.username, info->user_name, strlen(info->user_name) > 15 ? 15 : strlen(info->user_name));
	memcpy(m_head.ip, info->host_ip, strlen(info->host_ip) > 17 ? 17 : strlen(info->host_ip));
}

void TppSshRec::_on_end(void)
{
	// 如果还有剩下未写入的数据，写入文件中。
	if (m_cache.size() > 0)
		_save_to_data_file();
	if (m_cmd_cache.size() > 0)
		_save_to_cmd_file();

	// 更新头信息
	//m_head.timestamp = m_start_time;
	m_head.time_ms = (ex_u32)(m_last_time - m_start_time);

	ex_wstr fname = m_base_path;
	ex_path_join(fname, false, m_base_fname.c_str(), NULL);
	fname += L".tpr";

	FILE* f = ex_fopen(fname, L"wb");
	if (NULL == f)
	{
		EXLOGE("[ssh] can not open record file for write.\n");
		return;
	}

	fwrite(&m_head, sizeof(TS_RECORD_HEADER), 1, f);
	fflush(f);
	fclose(f);
}

void TppSshRec::record(ex_u8 type, const ex_u8* data, size_t size)
{
	if (data == NULL || 0 == size)
		return;
	m_head.packages++;

	if (sizeof(TS_RECORD_PKG) + size + m_cache.size() > m_cache.buffer_size())
		_save_to_data_file();

	TS_RECORD_PKG pkg;
	memset(&pkg, 0, sizeof(TS_RECORD_PKG));
	pkg.type = type;
	pkg.size = size;

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
	m_head.width = width;
	m_head.height = height;
}

void TppSshRec::record_win_size_change(int width, int height)
{
	TS_RECORD_WIN_SIZE pkg;
	pkg.width = (ex_u16)width;
	pkg.height = (ex_u16)height;
	record(TS_RECORD_TYPE_SSH_TERM_SIZE, (ex_u8*)&pkg, sizeof(TS_RECORD_WIN_SIZE));
}

void TppSshRec::record_command(const ex_astr cmd)
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
	int lenTime = strlen(szTime);


	if (m_cmd_cache.size() + cmd.length() + lenTime > m_cache.buffer_size())
		_save_to_cmd_file();

	m_cmd_cache.append((ex_u8*)szTime, lenTime);
	m_cmd_cache.append((ex_u8*)cmd.c_str(), cmd.length());
}

bool TppSshRec::_save_to_data_file(void)
{
	wchar_t _str_file_id[24] = { 0 };
	ex_wcsformat(_str_file_id, 24, L".%03d", m_head.file_count);

	ex_wstr fname = m_base_path;
	ex_path_join(fname, false, m_base_fname.c_str(), NULL);
	fname += _str_file_id;

	FILE* f = ex_fopen(fname, L"wb");

	if (NULL == f)
	{
		EXLOGE("[ssh] can not open record data-file for write.\n");
		m_cache.empty();
		return false;
	}

	ex_u32 size = m_cache.size();
	fwrite(&size, sizeof(ex_u32), 1, f);
	fwrite(m_cache.data(), m_cache.size(), 1, f);
	fflush(f);
	fclose(f);

	m_head.file_count++;
	m_head.file_size += m_cache.size();

	m_cache.empty();
	return true;
}

bool TppSshRec::_save_to_cmd_file(void)
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
