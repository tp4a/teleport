#ifndef __TS_ERRNO_H__
#define __TS_ERRNO_H__

//#include "ts_types.h"

#define TS_RDP_PROXY_PORT		52089
#define TS_RDP_PROXY_HOST		"0.0.0.0"

#define TS_SSH_PROXY_PORT		52189
#define TS_SSH_PROXY_HOST		"0.0.0.0"

#define TS_TELNET_PROXY_PORT	52389
#define TS_TELNET_PROXY_HOST	"0.0.0.0"

#define TS_HTTP_RPC_PORT		52080
//#define TS_HTTP_RPC_HOST		"127.0.0.1"
#define TS_HTTP_RPC_HOST		"localhost"


#define TS_RDP_PROTOCOL_RDP          0
#define TS_RDP_PROTOCOL_TLS          1
#define TS_RDP_PROTOCOL_HYBRID       2
#define TS_RDP_PROTOCOL_RDSTLS       4
#define TS_RDP_PROTOCOL_HYBRID_EX    8

#endif // __TS_ERRNO_H__
