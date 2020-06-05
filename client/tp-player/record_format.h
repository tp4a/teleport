#ifndef RECORD_FORMAT_H
#define RECORD_FORMAT_H

#include <Qt>

#define TS_TPPR_TYPE_UNKNOWN    0x0000
#define TS_TPPR_TYPE_SSH        0x0001
#define TS_TPPR_TYPE_RDP        0x0101


#define TS_RECORD_TYPE_RDP_POINTER          0x12    // 鼠标坐标位置改变，用于绘制虚拟鼠标
#define TS_RECORD_TYPE_RDP_IMAGE            0x13    // 服务端返回的图像，用于展示
#define TS_RECORD_TYPE_RDP_KEYFRAME         0x14    //

#define TS_RDP_BTN_FREE                     0
#define TS_RDP_BTN_PRESSED                  1
#define TS_RDP_IMG_RAW                      0       // 未压缩，原始数据（根据bitsPerPixel，多个字节对应一个点的颜色）
#define TS_RDP_IMG_BMP                      1       // 压缩的BMP数据
#define TS_RDP_IMG_ALT                      2

#pragma pack(push,1)

// 录像文件头(随着录像数据写入，会改变的部分)
typedef struct TS_RECORD_HEADER_INFO {
   uint32_t magic;      // "TPPR" 标志 TelePort Protocol Record
   uint16_t ver;        // 录像文件版本，从3.5.0开始，为4
   uint16_t type;       //
   // uint32_t packages;   // 总包数
   uint32_t time_ms;    // 总耗时（毫秒）
   uint32_t dat_file_count; // 数据文件数量
}TS_RECORD_HEADER_INFO;
#define ts_record_header_info_size sizeof(TS_RECORD_HEADER_INFO)

// 录像文件头(固定不变部分)
typedef struct TS_RECORD_HEADER_BASIC {
   uint16_t protocol_type;		// 协议：1=RDP, 2=SSH, 3=Telnet
   uint16_t protocol_sub_type;	// 子协议：100=RDP-DESKTOP, 200=SSH-SHELL, 201=SSH-SFTP, 300=Telnet
   uint64_t timestamp;	// 本次录像的起始时间（UTC时间戳）
   uint16_t width;		// 初始屏幕尺寸：宽
   uint16_t height;		// 初始屏幕尺寸：高
   char user_username[64];	// teleport账号
   char acc_username[64];	// 远程主机用户名

   char host_ip[40];	// 远程主机IP
   char conn_ip[40];	// 远程主机IP
   uint16_t conn_port;	// 远程主机端口

   char client_ip[40];		// 客户端IP

// 	// RDP专有
// 	uint8_t rdp_security;	// 0 = RDP, 1 = TLS
}TS_RECORD_HEADER_BASIC;
#define ts_record_header_basic_size sizeof(TS_RECORD_HEADER_BASIC)

typedef struct TS_RECORD_HEADER {
    TS_RECORD_HEADER_INFO info;
    uint8_t _reserve1[64 - ts_record_header_info_size];
    TS_RECORD_HEADER_BASIC basic;
    uint8_t _reserve2[512 - 64 - ts_record_header_basic_size];
}TS_RECORD_HEADER;

// header部分（header-info + header-basic） = 512B
#define ts_record_header_size sizeof(TS_RECORD_HEADER)

// 一个数据包的头
typedef struct TS_RECORD_PKG {
    uint8_t type;           // 包的数据类型
    uint32_t size;          // 这个包的总大小（不含包头）
    uint32_t time_ms;       // 这个包距起始时间的时间差（毫秒，意味着一个连接不能持续超过49天）
    uint8_t _reserve[3];    // 保留
}TS_RECORD_PKG;


typedef struct TS_RECORD_RDP_POINTER {
    uint16_t x;
    uint16_t y;
    uint8_t button;
    uint8_t pressed;
}TS_RECORD_RDP_POINTER;

// RDP图像更新
typedef struct TS_RECORD_RDP_IMAGE_INFO {
    uint16_t destLeft;
    uint16_t destTop;
    uint16_t destRight;
    uint16_t destBottom;
    uint16_t width;
    uint16_t height;
    uint16_t bitsPerPixel;
    uint8_t format;
    uint8_t _reserved;
    uint32_t dat_len;
    uint32_t zip_len;
}TS_RECORD_RDP_IMAGE_INFO;

// 关键帧索引
typedef struct TS_RECORD_RDP_KEYFRAME_INFO {
    uint32_t time_ms;       // 此关键帧的时间点
    uint32_t file_index;    // 此关键帧图像数据位于哪一个数据文件中
    uint32_t offset;        // 此关键帧图像数据在数据文件中的偏移
}TS_RECORD_RDP_KEYFRAME_INFO;

#pragma pack(pop)


#endif // RECORD_FORMAT_H
