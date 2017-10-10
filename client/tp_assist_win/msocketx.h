#ifndef MSOCKETX_H_
#define MSOCKETX_H_

#ifdef _WIN32
#pragma comment(lib,"ws2_32.lib")
#include "winsock2.h"
typedef int socklen_t;
#else
#include <unistd.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <arpa/inet.h>  //for ntohs
#include <sys/time.h> //for timeval
#include <errno.h>
#include <fcntl.h>
#include <netinet/tcp.h>
typedef int SOCKET;
#define SOCKET_ERROR  (-1)
#define INVALID_SOCKET (-1)
#endif

#define CAN_READX           1
#define CAN_WRITEX          2
#define CAN_CONNECTX        4
#define CAN_ACCEPTX         8

class msocketx
{
public:
    msocketx();
    virtual ~msocketx();
public:
    // startup 最先调用,linux可以不用调用
    static bool startup();

    // clearup 程序结束时调用,linux可以不用调用
    static bool clearup();

    // getlasterror 获取上一次错误代码
    static int getlasterror();

public:
    // attch 挂载一个socket
    void attach(SOCKET sock);

    // isvalid 是否有效
    inline bool isvalid();

    // close 会先判断isvalid,然后shutdown,然后closesocket,最后赋值INVALIDSOCKET
    void close();
    
    // setsock 会调用setsockbuff,setsocktime.
    bool setsock();

    // create 建立socket
    bool create(int itype,int iprotocol);

    // bind 绑定指定ip和端口,如果pstrip为空则绑定所有ip
    bool bind(unsigned short usport,const char* pstrip = NULL);

    // sendto 发送收据
    int sendto(const void* pbuf, unsigned int ilen, unsigned int uiip, unsigned short usport, int iflags);

    // sendto 发送收据
    int sendto(const void* pbuf, unsigned int ilen, const char* pszip, unsigned short usport, int iflags);

    // recvfrom 接收数据
    int recvfrom(void* pbuf, unsigned int ilen, unsigned int& uiip, unsigned short& usport, int iflags);

    // send 发送数据
    int send(const void* pbuf, unsigned int ilen,int iflags);

    // recv 接收数据
    int recv(void* pbuf,unsigned int ilen,int iflags);

    // listen 监听
    bool listen(int ibacklog);

    // accept 接收
    bool accept(SOCKET& sock,sockaddr* peeraddr,socklen_t* addrlen);

    bool accept(msocketx& sock,sockaddr* peeraddr,socklen_t* addrlen);

    // connect 连接,usport为主机字节序.
    int connect(const char* pszip,unsigned short usport,bool bblock);

    // wait 等待iflagx事件,事件如上面的CAN_READX...出错返回-1,0表示超时,
    //      正常返回可操作类型,用&取出判断
    int wait(unsigned int uimilli,int iflagx);
public:
    // setblock 设置是否阻塞
    bool setblock(bool bblock = false);

    // setsockbuff 设置socket系统缓冲区大小
    bool setsockbuff(unsigned int uirecvlen = 4 * 1024 * 1024,
        unsigned int uisendlen = 4 * 1024 * 1024);

    // setsocktime 设置send\recv操作超时时间.
    bool setsocktime(unsigned int uimillisecond = 500);

    // setsocknagle 是否启用nagle算法.
    bool setsocknagle(bool benable = true);

    // shutdown     0 read,1 write,2 both
    int shutdown(int ihow);

    // closesocket  最基本的关掉socket
    int closesocket();

    // getsockname 获取该socket当前绑定地址,ulip 为网络序,usport为主机序
    int getsockname(unsigned int& uiip,unsigned short& usport);
    
private:
    SOCKET m_sock;
};

#endif  //MSOCKETX_H_
