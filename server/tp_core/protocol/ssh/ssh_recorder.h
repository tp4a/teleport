#ifndef __TPP_SSH_RECORDER_H__
#define __TPP_SSH_RECORDER_H__

#include "../../common/base_record.h"

#define TS_RECORD_TYPE_SSH_TERM_SIZE		0x01		// 终端大小（行数与列数）
#define TS_RECORD_TYPE_SSH_DATA				0x02		// 用于展示的数据内容

#pragma pack(push,1)

// 录像文件头
// typedef struct TS_RECORD_HEADER
// {
// 	ex_u32 magic;		// "TPPR" 标志 TelePort Protocol Record
// 	ex_u64 timestamp;	// 本次录像的起始时间（UTC时间戳）
// 	ex_u32 packages;	// 总包数
// 	ex_u32 time_ms;		// 总耗时（毫秒）
// 	ex_u16 width;		// 初始屏幕尺寸：宽
// 	ex_u16 height;		// 初始屏幕尺寸：高
// 	ex_u16 file_count;	// 数据文件总数
// 	ex_u32 file_size;	// 所有数据文件的总大小（不包括每个数据文件的头，即4字节的每文件大小）
// 	char account[16];	// teleport账号
// 	char username[16];	// 远程主机用户名
// 	char ip[18];
// 	ex_u16 port;
// 
// 	ex_u8 reserve[128 - 4 - 8 - 4 - 4 - 2 - 2 - 2 - 4 - 16 - 16 - 18 - 2];	// 保留
// }TS_RECORD_HEADER;
// 
// // 一个数据包的头
// typedef struct TS_RECORD_PKG
// {
// 	ex_u8 type;			// 包的数据类型
// 	ex_u32 size;		// 这个包的总大小（不含包头）
// 	ex_u32 time_ms;		// 这个包距起始时间的时间差（毫秒，意味着一个连接不能持续超过49天）
// 	ex_u8 reserve[3];	// 保留
// }TS_RECORD_PKG;

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
	void record_command(const ex_astr& cmd);

    void flush_record();

protected:
	bool _on_begin(const TPP_CONNECT_INFO* info);
	bool _on_end();

	bool _save_to_data_file();
	bool _save_to_cmd_file();

protected:
	TS_RECORD_HEADER m_head;

	MemBuffer m_cmd_cache;

    bool m_save_full_header;

    FILE* m_file_info;
    FILE* m_file_data;
    FILE* m_file_cmd;
};

#endif // __TPP_SSH_RECORDER_H__
