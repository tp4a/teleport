#ifndef __TPP_SSH_RECORDER_H__
#define __TPP_SSH_RECORDER_H__

#include "../../common/base_record.h"

#define TS_RECORD_TYPE_SSH_TERM_SIZE		0x01		// 终端大小（行数与列数）
#define TS_RECORD_TYPE_SSH_DATA				0x02		// 用于展示的数据内容

#pragma pack(push,1)

// 记录窗口大小改变的数据包
typedef struct TS_RECORD_WIN_SIZE
{
	ex_u16 width;
	ex_u16 height;
}TS_RECORD_WIN_SIZE;

#pragma pack(pop)

class TppSshRec : public TppRecBase
{
public:
	TppSshRec();
	virtual ~TppSshRec();

	void record(ex_u8 type, const ex_u8* data, size_t size);
	void record_win_size_startup(int width, int height);
	void record_win_size_change(int width, int height);
	void record_command(int flag, const ex_astr& cmd);

    void save_record();

protected:
	bool _on_begin(const TPP_CONNECT_INFO* info);
	bool _on_end();

	bool _save_to_info_file();
	bool _save_to_data_file();
	bool _save_to_cmd_file();

protected:
	TS_RECORD_HEADER m_head;
	bool m_header_changed;

	MemBuffer m_cmd_cache;

    bool m_save_full_header;

    FILE* m_file_info;
    FILE* m_file_data;
    FILE* m_file_cmd;
};

#endif // __TPP_SSH_RECORDER_H__
