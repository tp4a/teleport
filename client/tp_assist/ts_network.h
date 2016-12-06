#pragma once

#include <map>

struct ICMPheaderRet
{
	unsigned int		ulSrcServerIP;				//IP地址
	unsigned int		ulDesServerIP;				//IP地址
	int					nPacketsSent;				//发送的包
	int					nPacketsReceived;			//收到的包
	int					nMinRoundTripTime;			//最大时间
	int					nMaxRoundTripTime;			//最短时间
	int					nAverageRoundTripTime;		//平均时间
	int					nSesssionID;				//sessionId
};
typedef std::map<unsigned int, ICMPheaderRet>ICMPheaderRetMap;

struct ICMPheader
{
	unsigned char	byType;
	unsigned char	byCode;
	unsigned short	nChecksum;
	unsigned short	nId;
	unsigned short	nSequence;
	unsigned int	Tick;
};

struct IPheader
{
	unsigned char	byVerLen;
	unsigned char	byTos;
	unsigned short	nTotalLength;
	unsigned short	nId;
	unsigned short	nOffset;
	unsigned char	byTtl;
	unsigned char	byProtocol;
	unsigned short	nChecksum;
	unsigned int	nSrcAddr;
	unsigned int	nDestAddr;
};
bool TestTCPPort(const ex_astr& strServerIP, int port);

int ICMPSendTo(ICMPheaderRet* pICMPheaderRet, char* pszRemoteIP, int nMessageSize, int nCount);
