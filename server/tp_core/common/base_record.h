#ifndef __TS_BASE_RECORD_H__
#define __TS_BASE_RECORD_H__

#include "base_env.h"
#include "ts_membuf.h"
#include "protocol_interface.h"

#include <ex.h>

#define MAX_SIZE_PER_FILE 4194304  // 4M = 1024*1024*4

#pragma pack(push,1)

// 录像文件头
typedef struct TS_RECORD_HEADER
{
	ex_u32 magic;		// "TPPR" 标志 TelePort Protocol Record
	ex_u16 ver;			// 录像文件版本，目前为2
	ex_u16 protocol;	// 协议：1=RDP, 2=SSH, 3=Telnet
	ex_u64 timestamp;	// 本次录像的起始时间（UTC时间戳）
	ex_u32 packages;	// 总包数
	ex_u32 time_ms;		// 总耗时（毫秒）
	ex_u16 width;		// 初始屏幕尺寸：宽
	ex_u16 height;		// 初始屏幕尺寸：高
	ex_u16 file_count;	// 数据文件总数
	ex_u32 file_size;	// 所有数据文件的总大小（不包括每个数据文件的头，即4字节的每文件大小）
	char account[16];	// teleport账号
	char username[16];	// 远程主机用户名
	char ip[18];
	ex_u16 port;

	// RDP专有
	ex_u8 rdp_security;	// 0 = RDP, 1 = TLS

	ex_u8 reserve[128 - 4 - 2 - 2 - 8 - 4 - 4 - 2 - 2 - 2 - 4 - 16 - 16 - 18 - 2 - 1];	// 保留
}TS_RECORD_HEADER;

// 一个数据包的头
typedef struct TS_RECORD_PKG
{
	ex_u8 type;			// 包的数据类型
	ex_u32 size;		// 这个包的总大小（不含包头）
	ex_u32 time_ms;		// 这个包距起始时间的时间差（毫秒，意味着一个连接不能持续超过49天）
	ex_u8 reserve[3];	// 保留
}TS_RECORD_PKG;

#pragma pack(pop)

class TppRecBase
{
public:
	TppRecBase();
	virtual ~TppRecBase();

	void begin(const wchar_t* base_path, const wchar_t* base_fname, int record_id, const TPP_SESSION_INFO* info);
	void end(void);

	virtual void record(ex_u8 type, const ex_u8* data, size_t size) = 0;

protected:
	virtual void _on_begin(const TPP_SESSION_INFO* info) = 0;
	virtual void _on_end(void) = 0;

protected:
	int m_protocol;

	ex_wstr m_base_path;		// 录像文件基础路径，例如 /usr/local/eom/teleport/data/replay/ssh/123，数字编号是内部附加的，作为本次会话录像文件的目录名称
	ex_wstr m_base_fname;		// 录像文件的文件名，不含扩展名部分，内部会以此为基础合成文件全名，并将录像文件存放在 m_base_path 指向的目录中

	ex_u64 m_start_time;
	ex_u64 m_last_time;

	MemBuffer m_cache;
};

#endif // __TS_BASE_RECORD_H__
