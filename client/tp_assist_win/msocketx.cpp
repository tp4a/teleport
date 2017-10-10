#include "stdafx.h"
#include "msocketx.h"

#ifdef _WIN32
#pragma warning(disable:4244)
#endif

msocketx::msocketx()
{
	m_sock = INVALID_SOCKET;
}

msocketx::~msocketx()
{
	close();
}
int msocketx::getsockname(unsigned int& uiip, unsigned short& usport)
{
	sockaddr_in addr;
	socklen_t ilen = sizeof(addr);

	int nret = ::getsockname(m_sock, (sockaddr*)&addr, &ilen);
	if (nret != SOCKET_ERROR)
	{
		uiip = addr.sin_addr.s_addr;
		usport = ntohs(addr.sin_port);
	}

	return nret;
}

int msocketx::shutdown(int ihow)
{
	return ::shutdown(m_sock, ihow);
}

int msocketx::closesocket()
{
#ifdef _WIN32
	return ::closesocket(m_sock);
#else
	return ::close(m_sock);
#endif
}

void msocketx::close()
{
	if (isvalid())
	{
		shutdown(0);
		closesocket();
		m_sock = INVALID_SOCKET;
	}
}

bool msocketx::startup()
{
#ifdef _WIN32
	WSADATA wsaData;
	if (WSAStartup(MAKEWORD(2, 2), &wsaData) != 0)
		return false;
#endif
	return true;
}

bool msocketx::clearup()
{
#ifdef _WIN32
	return WSACleanup() == 0;
#endif
	return true;
}

int msocketx::getlasterror()
{
#ifdef _WIN32
	return WSAGetLastError();
#else
	return errno;
#endif
}

void msocketx::attach(SOCKET sock)
{
	if (sock == INVALID_SOCKET)
		return;
	m_sock = sock;
}

bool msocketx::isvalid()
{
	return m_sock != INVALID_SOCKET;
}

bool msocketx::setsockbuff(unsigned int uirecvlen /* = 4 * 1024 * 1024 */,
	unsigned int uisendlen /* = 4 * 1024 * 1024 */)
{
	return (setsockopt(m_sock, SOL_SOCKET, SO_SNDBUF, (char*)&uisendlen, sizeof(uisendlen)) == 0) &&
		(setsockopt(m_sock, SOL_SOCKET, SO_RCVBUF, (char*)&uirecvlen, sizeof(uirecvlen)) == 0);
}

bool msocketx::setsocknagle(bool benable /* = true */)
{
	socklen_t iflag = (benable ? 0 : 1);
	return setsockopt(m_sock, IPPROTO_TCP, TCP_NODELAY, (char*)&iflag, sizeof(iflag)) == 0;
}

bool msocketx::setsocktime(unsigned int uimillisecond /* = 500 */)
{
#ifdef _WIN32
	return (setsockopt(m_sock, SOL_SOCKET, SO_SNDTIMEO, (char*)&uimillisecond, sizeof(uimillisecond)) == 0) &&
		(setsockopt(m_sock, SOL_SOCKET, SO_RCVTIMEO, (char*)&uimillisecond, sizeof(uimillisecond)) == 0);
#else
	struct timeval timeout;
	timeout.tv_sec = uimillisecond / 1000;
	timeout.tv_usec = (uimillisecond % 1000) * 1000;
	return (setsockopt(m_sock, SOL_SOCKET, SO_SNDTIMEO, (char*)&timeout, sizeof(timeout)) == 0) &&
		(setsockopt(m_sock, SOL_SOCKET, SO_RCVTIMEO, (char*)&timeout, sizeof(timeout)) == 0);
#endif
}

bool msocketx::setsock()
{
	return setsockbuff() && setsocktime();
}

bool msocketx::setblock(bool bblock /* = false */)
{
#ifdef _WIN32
	u_long b = bblock ? 0 : 1;
	return ioctlsocket(m_sock, FIONBIO, &b) == 0;
#else
	int flags = fcntl(m_sock, F_GETFL, 0);
	if (bblock)
		flags |= O_NONBLOCK;
	else
		flags &= (~O_NONBLOCK);
	return fcntl(m_sock, F_SETFL, flags) != -1;
#endif
}

bool msocketx::create(int itype, int iprotocol)
{
	if (isvalid())
		return true;
	m_sock = socket(AF_INET, itype, iprotocol);

	return isvalid();
}

bool msocketx::bind(unsigned short usport, const char* pstrip /* = NULL */)
{
	sockaddr_in addr = { 0 };
	unsigned long nResult = 0;

	addr.sin_family = AF_INET;

	if (pstrip == NULL)
		addr.sin_addr.s_addr = htonl(INADDR_ANY);
	else
	{
		nResult = inet_addr(pstrip);
		if (nResult == INADDR_NONE)
			return false;

		addr.sin_addr.s_addr = nResult;
	}
	addr.sin_port = htons(usport);

	return ::bind(m_sock, (sockaddr*)&addr, sizeof(addr)) == 0;
}

int msocketx::sendto(const void* pbuf, unsigned int ilen, unsigned int uiip, unsigned short usport, int iflags)
{
	if (pbuf == NULL)
		return -1;

	sockaddr_in addr = { 0 };

	addr.sin_family = AF_INET;
	addr.sin_addr.s_addr = uiip;
	addr.sin_port = htons(usport);

	return ::sendto(m_sock, (char*)pbuf, ilen, iflags, (sockaddr*)&addr, sizeof(addr));
}

int msocketx::sendto(const void* pbuf, unsigned int ilen, const char* pszip, unsigned short usport, int iflags)
{
	if (pbuf == NULL)
		return -1;
	return sendto(pbuf, ilen, inet_addr(pszip), usport, iflags);
}

int msocketx::recvfrom(void* pbuf, unsigned int ilen, unsigned int& uiip, unsigned short& usport, int iflags)
{
	if (pbuf == NULL)
		return -1;

	sockaddr_in srcaddr = { 0 };
	socklen_t iaddrlen = sizeof(srcaddr);

	int nret = ::recvfrom(m_sock, (char*)pbuf, ilen, iflags, (sockaddr*)&srcaddr, &iaddrlen);
	if (nret != SOCKET_ERROR)
	{
		usport = htons(srcaddr.sin_port);
		uiip = srcaddr.sin_addr.s_addr;
	}
	return nret;
}

int msocketx::send(const void* pbuf, unsigned int ilen, int iflags)
{
	if (pbuf == NULL)
		return -1;

	return ::send(m_sock, (char*)pbuf, ilen, iflags);
}

int msocketx::recv(void* pbuf, unsigned int ilen, int iflags)
{
	if (pbuf == NULL)
		return -1;

	return ::recv(m_sock, (char*)pbuf, ilen, iflags);
}

bool msocketx::listen(int ibacklog)
{
	return ::listen(m_sock, ibacklog) == 0;
}

bool msocketx::accept(SOCKET& sock, sockaddr* peeraddr, socklen_t* addrlen)
{
	sock = ::accept(m_sock, peeraddr, addrlen);
	return sock != INVALID_SOCKET;
}

bool msocketx::accept(msocketx& sock, sockaddr* peeraddr, socklen_t* addrlen)
{
	SOCKET socktmp = ::accept(m_sock, peeraddr, addrlen);
	sock.m_sock = socktmp;
	return socktmp != INVALID_SOCKET;
}

int msocketx::connect(const char* pszip, unsigned short usport, bool bblock)
{
	if (pszip == NULL)
		return -1;

	if (!isvalid())
	{
		if (!create(SOCK_STREAM, 0))
			return -1;
	}
	setblock(bblock);

	sockaddr_in addr = { 0 };

	addr.sin_port = htons(usport);
	addr.sin_addr.s_addr = inet_addr(pszip);
	addr.sin_family = AF_INET;

	return ::connect(m_sock, (sockaddr*)&addr, sizeof(addr));
}

int msocketx::wait(unsigned int uimilli, int iflagx)
{
	timeval timeout;
	timeout.tv_sec = uimilli / 1000;
	timeout.tv_usec = (uimilli % 1000) * 1000;

	fd_set *prfds = NULL, *pwfds = NULL, *pefds = NULL;
	int iret = 0;

	if ((iflagx & CAN_CONNECTX) == CAN_CONNECTX)
	{
		pwfds = new(std::nothrow) fd_set;
		if (pwfds == NULL)
			return -1;

		pefds = new(std::nothrow) fd_set;
		if (pefds == NULL)
		{
			if (pwfds)
				delete pwfds;
			return -1;
		}

		FD_ZERO(pwfds);
		FD_ZERO(pefds);

		FD_SET(m_sock, pwfds);
		FD_SET(m_sock, pefds);

		iret = ::select(m_sock + 1, NULL, pwfds, pefds, &timeout);
		if (iret > 0)
		{
			if (FD_ISSET(m_sock, pwfds) || FD_ISSET(m_sock, pefds))
			{
				int iopt = 0;
				socklen_t ioptlen = sizeof(iopt);
				if (getsockopt(m_sock, SOL_SOCKET, SO_ERROR, (char*)&iopt, &ioptlen) == 0)
				{
					if (iopt == 0)
						iret = CAN_CONNECTX;
					else
						iret = SOCKET_ERROR;
				}
				else
					iret = SOCKET_ERROR;
			}
		}
		if (pwfds)
			delete pwfds;
		if (pefds)
			delete pefds;
		return iret;
	}

	if ((iflagx & CAN_READX) == CAN_READX || (iflagx & CAN_ACCEPTX) == CAN_ACCEPTX)
	{
		prfds = new(std::nothrow) fd_set;
		if (prfds == NULL)
			return -1;

		FD_ZERO(prfds);
		FD_SET(m_sock, prfds);
	}
	if ((iflagx & CAN_WRITEX) == CAN_WRITEX)
	{
		pwfds = new(std::nothrow) fd_set;
		if (pwfds == NULL)
		{
			if (prfds)
				delete prfds;
			return -1;
		}

		FD_ZERO(pwfds);
		FD_SET(m_sock, pwfds);
	}

	iret = ::select(m_sock + 1, prfds, pwfds, NULL, &timeout);
	if (iret > 0)
	{
		int itmp = 0;
		if (prfds)
			if (FD_ISSET(m_sock, prfds))
				itmp |= CAN_READX;
		if (pwfds)
			if (FD_ISSET(m_sock, pwfds))
				itmp |= CAN_WRITEX;
		iret = itmp;
	}

	if (pwfds)
		delete pwfds;
	if (prfds)
		delete prfds;

	return iret;
}
