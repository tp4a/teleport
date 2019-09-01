#ifndef __TS_BASE_RECORD_H__
#define __TS_BASE_RECORD_H__

#include "base_env.h"
#include "ts_membuf.h"
#include "protocol_interface.h"

#include <ex.h>

#define MAX_SIZE_PER_FILE 4194304  // 4M = 1024*1024*4

#pragma pack(push,1)

/*
 * 录像
 *
 * 一个录像分为两个文件，一个信息文件，一个数据文件。
 * 服务内部缓存最大4M，或者5秒，就将数据写入数据文件中，并同时更新信息文件。
 *
 */


 // 录像文件头(随着录像数据写入，会改变的部分)
typedef struct TS_RECORD_HEADER_INFO {
    ex_u32 magic;		// "TPPR" 标志 TelePort Protocol Record
    ex_u16 ver;			// 录像文件版本，目前为3
    ex_u32 packages;	// 总包数
    ex_u32 time_ms;		// 总耗时（毫秒）
    //ex_u32 file_size;	// 数据文件大小
}TS_RECORD_HEADER_INFO;
#define ts_record_header_info_size sizeof(TS_RECORD_HEADER_INFO)

// 录像文件头(固定不变部分)
typedef struct TS_RECORD_HEADER_BASIC {
    ex_u16 protocol_type;		// 协议：1=RDP, 2=SSH, 3=Telnet
    ex_u16 protocol_sub_type;	// 子协议：100=RDP-DESKTOP, 200=SSH-SHELL, 201=SSH-SFTP, 300=Telnet
    ex_u64 timestamp;	// 本次录像的起始时间（UTC时间戳）
    ex_u16 width;		// 初始屏幕尺寸：宽
    ex_u16 height;		// 初始屏幕尺寸：高
    char user_username[64];	// teleport账号
    char acc_username[64];	// 远程主机用户名

    char host_ip[40];	// 远程主机IP
    char conn_ip[40];	// 远程主机IP
    ex_u16 conn_port;	// 远程主机端口

    char client_ip[40];		// 客户端IP

// 	// RDP专有
// 	ex_u8 rdp_security;	// 0 = RDP, 1 = TLS

//    ex_u8 _reserve[512 - 2 - 2 - 8 - 2 - 2 - 64 - 64 - 40 - 40 - 2 - 40 - 1 - ts_record_header_info_size];
    ex_u8 _reserve[512 - 2 - 2 - 8 - 2 - 2 - 64 - 64 - 40 - 40 - 2 - 40 - ts_record_header_info_size];
}TS_RECORD_HEADER_BASIC;
#define ts_record_header_basic_size sizeof(TS_RECORD_HEADER_BASIC)

typedef struct TS_RECORD_HEADER {
    TS_RECORD_HEADER_INFO info;
    TS_RECORD_HEADER_BASIC basic;
}TS_RECORD_HEADER;

// header部分（header-info + header-basic） = 512B
#define ts_record_header_size sizeof(TS_RECORD_HEADER)


// 一个数据包的头
typedef struct TS_RECORD_PKG {
    ex_u8 type;			// 包的数据类型
    ex_u32 size;		// 这个包的总大小（不含包头）
    ex_u32 time_ms;		// 这个包距起始时间的时间差（毫秒，意味着一个连接不能持续超过49天）
    ex_u8 _reserve[3];	// 保留
}TS_RECORD_PKG;

#pragma pack(pop)

class TppRecBase {
public:
    TppRecBase();
    virtual ~TppRecBase();

    bool begin(const wchar_t* base_path, const wchar_t* base_fname, int record_id, const TPP_CONNECT_INFO* info);
    bool end();

protected:
    virtual bool _on_begin(const TPP_CONNECT_INFO* info) = 0;
    virtual bool _on_end() = 0;

protected:
    ex_wstr m_base_path;		// 录像文件基础路径，例如 /usr/local/teleport/data/replay/ssh/123，数字编号是内部附加的，作为本次会话录像文件的目录名称
    ex_wstr m_base_fname;		// 录像文件的文件名，不含扩展名部分，内部会以此为基础合成文件全名，并将录像文件存放在 m_base_path 指向的目录中

    ex_u64 m_start_time;

    MemBuffer m_cache;
};

#endif // __TS_BASE_RECORD_H__
