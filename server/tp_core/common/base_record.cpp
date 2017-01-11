#include <memory> 

#include <sys/types.h> 
#include <sys/stat.h> 

#include "base_record.h"

#if 0
base_record::base_record()
{
	//g_env.m_record_ssh_path
	m_buf = new unsigned char[MAX_SIZE_PER_FILE];
	memset(m_buf, 0, MAX_SIZE_PER_FILE);
	m_buf_offset = 0;
	m_begin_time = 0;
	m_last_time = 0;
	m_file_current_index = 0;
	m_current_file = 0;
	m_totol_size = 0;
}


base_record::~base_record()
{
	if (NULL != m_buf)
	{
		delete[] m_buf;
		m_buf = NULL;
	}
}

void base_record::begin(int record_id, int record_type)
{
	char szPath[1024] = { 0 };
	ex_astr ssh_path;
	
	m_begin_time = ex_get_tick_count();
	m_last_time = m_begin_time;
	m_file_current_index = 0;
	m_current_file = 0;
	if (record_type == 2)
	{
		//ex_mkdirs()

#ifdef EX_OS_WIN32
		ts_str2astr(g_env.m_record_ssh_path, ssh_path);
		sprintf_s(szPath, "%s\\%d\\", ssh_path.c_str(), record_id);
		int ret = _mkdir(szPath);
#else
		ssh_path = g_env.m_record_ssh_path;
		snprintf(szPath, 1024, "%s/%d", ssh_path.c_str(), record_id);
		EXLOGV("try to create folder for record: [%s]\n", szPath);
		int status = mkdir(szPath, S_IRWXU | S_IRWXG | S_IROTH | S_IXOTH);
		EXLOGV("create folder for record return %d, errno=%d.\n", status, errno);
#endif
		m_current_path = szPath;
		open_next_file();
	}
}
void base_record::end()
{
	ex_u64 current_time = ex_get_tick_count();
	ex_u64 internal_time = m_last_time - m_begin_time;

	save_buffer_to_file(int(internal_time));

	if (m_buf)
	{
		delete[] m_buf;
		m_buf = NULL;
	}
	if (m_current_file)
	{
		fclose(m_current_file);
	}

	ts_replay_header header = {0};
	ex_strcpy(header.ID, 16, "teleport");
	ex_strcpy(header.version, 16, "1.0.0.1");
	header.total_time = (ex_u32)internal_time;
	header.total_file_count = (ex_u8)m_file_current_index;
	header.total_size = (ex_u8)m_totol_size;
	int ts_replay_header_len = sizeof(ts_replay_header);
	char szPath[1024] = { 0 };
#ifdef EX_OS_WIN32
	sprintf_s(szPath, "%s\\head.init", m_current_path.c_str());
#else
	snprintf(szPath, 1024, "%s/head.init", m_current_path.c_str());
#endif
	FILE* f = NULL;
	if ((f = fopen(szPath, "wb")) == NULL) /* open file TEST.$$$ */
	{
		return;
	}

	int ret = fwrite(&header, sizeof(ts_replay_header), 1, f);
	ret = fwrite(&m_timelist[0], m_timelist.size() * sizeof(int), 1, f);
	fclose(f);

	char szTermPath[1024] = { 0 };
#ifdef EX_OS_WIN32
	sprintf_s(szTermPath, "%s\\term.init", m_current_path.c_str());
#else
	snprintf(szTermPath, 1024, "%s/term.init", m_current_path.c_str());
#endif

	if ((f = fopen(szTermPath, "wb")) == NULL) 
	{
		return;
	}
	ssh_terms_data_header terms_header = { 0 };
	ex_strcpy(terms_header.ID, 16,"teleport");
	ex_strcpy(terms_header.version, 16,"1.0.0.1");
	terms_header.term_count = (ex_u32)m_windows_size_list.size();
	ret = fwrite(&terms_header,sizeof(ssh_terms_data_header), 1, f);
	if (m_windows_size_list.size() > 0)
	{
		ret = fwrite(&m_windows_size_list[0], m_windows_size_list.size() * sizeof(ssh_terms_data), 1, f);
	}
	
	fclose(f);
}

void base_record::windows_size(ssh_terms_data size_info)
{
	ex_u64 internal_time = ex_get_tick_count() - m_begin_time;
	size_info.time = (ex_u32)internal_time;
	m_windows_size_list.push_back(size_info);
}

void base_record::record(unsigned char* buf, int len, int cmd)
{
	ex_u64 current_time = ex_get_tick_count();
	ex_u64 internal_time = current_time - m_begin_time;
	m_last_time = current_time;

	//bool bSwitchFile = false;
	//bool bWriteFile = false;

	ts_replay_data_header replay_header = {0};
	replay_header.action = (ex_u8)cmd;
	replay_header.time = (ex_u32)internal_time;
	replay_header.size = (ex_u32)len;
	//int header_len = sizeof(ts_replay_data_header);

	bool bRet = cached_buffer(&replay_header, buf, len);
	if (!bRet)
	{
		//�����������ѻ�����ļ���������ջ���
		save_buffer_to_file(int(internal_time));

		//���¸��ļ�
		open_next_file();

		bRet = cached_buffer(&replay_header, buf, len);

		if (!bRet)
		{
			//�������̫�󣬲��ܻ��棬ֱ�Ӵ��ļ�
			save_to_file(ex_u32(internal_time), &replay_header, buf, len);
			open_next_file();
		}
	}
}

bool base_record::cached_buffer(ts_replay_data_header* header, unsigned char* buf, int len) 
{
	size_t header_len = sizeof(ts_replay_data_header);
	if ((m_buf_offset + len + header_len) > MAX_SIZE_PER_FILE)
	{
		return false;
	}

	//���ȹ���ֱ�Ӵ滺��
	memcpy(m_buf + m_buf_offset, header, header_len);
	m_buf_offset += header_len;

	memcpy(m_buf + m_buf_offset, buf, len);
	m_buf_offset += len;

	return true;
}

bool base_record::open_next_file()
{
	char szPath[1024] = { 0 };
#ifdef EX_OS_WIN32
	sprintf_s(szPath, "%s\\%d.ts", m_current_path.c_str(), m_file_current_index);
#else
	snprintf(szPath, 1024, "%s/%d.ts", m_current_path.c_str(), m_file_current_index);
#endif
	if (NULL != m_current_file) 
	{
		fclose(m_current_file);
	}
	if ((m_current_file = fopen(szPath, "wb")) == NULL) /* open file TEST.$$$ */
	{
		return false;
	}

	m_file_current_index++;

	return true;
}

bool base_record::save_buffer_to_file(int internal_time)
{
	if(NULL == m_current_file)
		return false;

	int ret = fwrite(m_buf, m_buf_offset, 1, m_current_file); /* д��struct�ļ�*/
	m_totol_size += m_buf_offset;

	m_buf_offset = 0;
	m_timelist.push_back(ex_u32(internal_time));
	return true;
}

bool base_record::save_to_file(int internal_time,ts_replay_data_header* header, unsigned char* buf, int len)
{
	if(NULL == m_current_file)
		return false;

	int ret = fwrite(header, sizeof(ts_replay_data_header), 1, m_current_file);
	ret = fwrite(buf, len, 1, m_current_file);

	m_totol_size += sizeof(ts_replay_data_header);
	m_totol_size += len;
	m_timelist.push_back(ex_u32(internal_time));
	return true;
}
#endif

//====================================================
// NEW INTERFACE
//====================================================



TppRecBase::TppRecBase()
{
	m_cache.reserve(MAX_SIZE_PER_FILE);
	m_start_time = 0;
	m_last_time = 0;
}

TppRecBase::~TppRecBase()
{
}

void TppRecBase::begin(const wchar_t* base_path, const wchar_t* base_fname, int record_id, const TS_SESSION_INFO& info)
{
	m_start_time = ex_get_tick_count();

	m_base_fname = base_fname;
	m_base_path = base_path;

	wchar_t _str_rec_id[24] = { 0 };
	ex_wcsformat(_str_rec_id, 24, L"%06d", record_id);
	ex_path_join(m_base_path, false, _str_rec_id, NULL);
	ex_mkdirs(m_base_path);

	_on_begin(info);
}

void TppRecBase::end()
{
	_on_end();

#ifdef EX_DEBUG
	if (m_cache.size() > 0)
	{
		EXLOGE("[ssh] not all record data saved.\n");
	}
#endif
}
