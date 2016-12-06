#include "stdafx.h"
#include "msocketx.h"
#include "ts_network.h"

#include <iostream>
using namespace std;

unsigned short CalcChecksum(char *pBuffer, int nLen)
{
	//Checksum for ICMP is calculated in the same way as for
	//IP header

	//This code was taken from: http://www.netfor2.com/ipsum.htm

	unsigned short nWord;
	unsigned int nSum = 0;
	int i;

	//Make 16 bit words out of every two adjacent 8 bit words in the packet
	//and add them up
	for (i = 0; i < nLen; i = i + 2)
	{
		nWord = ((pBuffer[i] << 8) & 0xFF00) + (pBuffer[i + 1] & 0xFF);
		nSum = nSum + (unsigned int)nWord;
	}

	//Take only 16 bits out of the 32 bit sum and add up the carries
	while (nSum >> 16)
	{
		nSum = (nSum & 0xFFFF) + (nSum >> 16);
	}

	//One's complement the result
	nSum = ~nSum;

	return ((unsigned short)nSum);
}

bool ValidateChecksum(char *pBuffer, int nLen)
{
	unsigned short nWord;
	unsigned int nSum = 0;
	int i;

	//Make 16 bit words out of every two adjacent 8 bit words in the packet
	//and add them up
	for (i = 0; i < nLen; i = i + 2)
	{
		nWord = ((pBuffer[i] << 8) & 0xFF00) + (pBuffer[i + 1] & 0xFF);
		nSum = nSum + (unsigned int)nWord;
	}

	//Take only 16 bits out of the 32 bit sum and add up the carries
	while (nSum >> 16)
	{
		nSum = (nSum & 0xFFFF) + (nSum >> 16);
	}

	//To validate the checksum on the received message we don't complement the sum
	//of one's complement
	//One's complement the result
	//nSum = ~nSum;

	//The sum of one's complement should be 0xFFFF
	return ((unsigned short)nSum == 0xFFFF);
}

int ICMPSendTo(ICMPheaderRet* pICMPheaderRet, char* pszRemoteIP, int nMessageSize, int nCount)
{
	int nTimeOut = 500;	//Request time out for echo request (in milliseconds)
	ICMPheader sendHdr;
	//char *pSendBuffer = NULL;
	SOCKET sock;
	sock = socket(AF_INET, SOCK_RAW, IPPROTO_ICMP);	//Create a raw socket which will use ICMP
	if (sock == INVALID_SOCKET)
	{
		return -1;
	}
	SOCKADDR_IN dest;	//Dest address to send the ICMP request
	memset(&dest, 0, sizeof(0));
	dest.sin_addr.S_un.S_addr = inet_addr(pszRemoteIP);
	dest.sin_family = AF_INET;
	//dest.sin_port = rand ();	//Pick a random port


	int nResult = 0;
	int nTry = 0;
	int nSequence = 0;
	fd_set fdRead;
	//SYSTEMTIME timeSend, timeRecv;
	unsigned long timeTick = 0;
	int nTotalRoundTripTime = 0, nMaxRoundTripTime = 0, nMinRoundTripTime = -1, nRoundTripTime = 0;
	int nPacketsSent = 0, nPacketsReceived = 0;

	timeval timeInterval = { 0, 0 };
	timeInterval.tv_usec = nTimeOut * 1000;

	sendHdr.nId = htons(rand());	//Set the transaction Id


	while (nPacketsSent < nCount)
	{
		//Create the message buffer, which is big enough to store the header and the message data
		///pSendBuffer = new char [sizeof (ICMPheader) + nMessageSize];
		char Sendbuf[1024] = { 0 };
		int len = (sizeof(ICMPheader) + nMessageSize);
		sendHdr.byCode = 0;	//Zero for ICMP echo and reply messages
		sendHdr.nSequence = htons(nSequence++);
		sendHdr.byType = 8;	//Eight for ICMP echo message
		sendHdr.nChecksum = 0;	//Checksum is calculated later on

		memcpy_s(Sendbuf, sizeof(ICMPheader), &sendHdr, sizeof(ICMPheader));	//Copy the message header in the buffer
		memset(Sendbuf + sizeof(ICMPheader), 'x', nMessageSize);	//Fill the message with some arbitary value

																	//Calculate checksum over ICMP header and message data
		sendHdr.nChecksum = htons(CalcChecksum(Sendbuf, sizeof(ICMPheader) + nMessageSize));

		//Copy the message header back into the buffer
		memcpy_s(Sendbuf, sizeof(ICMPheader), &sendHdr, sizeof(ICMPheader));

		//::GetSystemTime (&timeSend);
		timeTick = GetTickCount();
		nResult = sendto(sock, Sendbuf, sizeof(ICMPheader) + nMessageSize, 0, (SOCKADDR *)&dest, sizeof(SOCKADDR_IN));

		//Save the time at which the ICMP echo message was sent


		++nPacketsSent;

		if (nResult == SOCKET_ERROR)
		{
			cerr << endl << "An error occured in sendto operation: " << "WSAGetLastError () = " << WSAGetLastError() << endl;
			//UnInitialize ();
			closesocket(sock);
			return -1;
		}
	next:
		FD_ZERO(&fdRead);
		FD_SET(sock, &fdRead);

		if ((nResult = select(0, &fdRead, NULL, NULL, &timeInterval))
			== SOCKET_ERROR)
		{
			cerr << endl << "An error occured in select operation: " << "WSAGetLastError () = " <<
				WSAGetLastError() << endl;
			closesocket(sock);
			//delete []pSendBuffer;
			return -2;
		}
		//printf("FD_ISSET Enter --- 0\n");
		if (nResult > 0 && FD_ISSET(sock, &fdRead))
		{
			//printf("FD_ISSET Enter --- 1\n");
			//Allocate a large buffer to store the response
			char buf[1500] = { 0 };
			struct sockaddr_in addr;
			int addr_len = sizeof(struct sockaddr_in);
			memset(&addr, 0, sizeof(sockaddr_in));
			if ((nResult = recvfrom(sock, buf, 1500, 0, (struct sockaddr *)&addr, &addr_len))
				== SOCKET_ERROR)
			{
				cerr << endl << "An error occured in recvfrom operation: " << "WSAGetLastError () = " <<
					WSAGetLastError() << endl;
				//UnInitialize ();
				//delete []pSendBuffer;
				closesocket(sock);
				return -3;
			}

			//printf("FD_ISSET Enter --- 2 IP%s\n",inet_ntoa(addr.sin_addr));
			string strIP = inet_ntoa(addr.sin_addr);
			if (strIP.compare(pszRemoteIP) == 0)
			{
				//Get the time at which response is received
				//::GetSystemTime (&timeRecv);
				//We got a response so we construct the ICMP header and message out of it
				ICMPheader recvHdr;
				char *pICMPbuffer = NULL;

				//The response includes the IP header as well, so we move 20 bytes ahead to read the ICMP header
				pICMPbuffer = buf + sizeof(IPheader);

				//ICMP message length is calculated by subtracting the IP header size from the 
				//total bytes received
				int nICMPMsgLen = nResult - sizeof(IPheader);

				//Construct the ICMP header
				memcpy_s(&recvHdr, sizeof(recvHdr), pICMPbuffer, sizeof(recvHdr));

				//Construct the IP header from the response
				IPheader ipHdr;
				memcpy_s(&ipHdr, sizeof(ipHdr), buf, sizeof(ipHdr));

				recvHdr.nId = recvHdr.nId;
				recvHdr.nSequence = recvHdr.nSequence;
				recvHdr.nChecksum = ntohs(recvHdr.nChecksum);

				if (recvHdr.byType == 0 &&
					recvHdr.nId == sendHdr.nId &&
					recvHdr.nSequence == sendHdr.nSequence &&
					ValidateChecksum(pICMPbuffer, nICMPMsgLen) &&
					memcmp(Sendbuf + sizeof(ICMPheader), buf + sizeof(ICMPheader) + sizeof(IPheader),
						nResult - sizeof(ICMPheader) - sizeof(IPheader)) == 0)
				{
					printf("FD_ISSET Enter --- 3\n");
					int nRoundTripTime = 0;

					nRoundTripTime = (GetTickCount() - timeTick);

					nTotalRoundTripTime = nTotalRoundTripTime + nRoundTripTime;

					if (nMinRoundTripTime == -1)
					{
						nMinRoundTripTime = nRoundTripTime;
						nMaxRoundTripTime = nRoundTripTime;
					}
					else if (nRoundTripTime < nMinRoundTripTime)
					{
						nMinRoundTripTime = nRoundTripTime;
					}
					else if (nRoundTripTime > nMaxRoundTripTime)
					{
						nMaxRoundTripTime = nRoundTripTime;
					}

					++nPacketsReceived;
				}
				else
				{
					cout << "The echo reply is not correct! Type : " << recvHdr.byType << endl;
				}
			}
			else
			{
				goto next;
			}

			//Check if the response is an echo reply, transaction ID and sequence number are same
			//as for the request, and that the checksum is correct
			//if (recvHdr.byType == 0 &&
			//	recvHdr.nId == sendHdr.nId &&
			//	recvHdr.nSequence == sendHdr.nSequence &&
			//	ValidateChecksum (pICMPbuffer, nICMPMsgLen)  && 
			//	memcmp (pSendBuffer + sizeof(ICMPheader), pRecvBuffer + sizeof (ICMPheader) + sizeof(IPheader), 
			//	nResult - sizeof (ICMPheader) - sizeof(IPheader)) == 0)
			//{
			//	printf("FD_ISSET Enter --- 3\n");

			//	int nRoundTripTime = 0;

			//	nRoundTripTime = (GetTickCount() - timeTick);

			//	nTotalRoundTripTime = nTotalRoundTripTime + nRoundTripTime;

			//	if (nMinRoundTripTime == -1)
			//	{
			//		nMinRoundTripTime = nRoundTripTime;
			//		nMaxRoundTripTime = nRoundTripTime;
			//	}
			//	else if (nRoundTripTime < nMinRoundTripTime)
			//	{
			//		nMinRoundTripTime = nRoundTripTime;
			//	}
			//	else if (nRoundTripTime > nMaxRoundTripTime)
			//	{
			//		nMaxRoundTripTime = nRoundTripTime;
			//	}

			//	++nPacketsReceived;
			//}
			//else
			//{
			//	cout << "The echo reply is not correct!" << endl;
			//}

			//delete []pRecvBuffer;
		}
		else
		{
			cout << "Request timed out. Tick : " << GetTickCount() << endl;
		}
	}
	cout << endl << "Ping statistics for " << pszRemoteIP << ":" << endl << '\t' << "Packets: Sent = " << nPacketsSent << ", Received = " <<
		nPacketsReceived << ", Lost = " << (nPacketsSent - nPacketsReceived) << " (" <<
		((nPacketsSent - nPacketsReceived) / (float)nPacketsSent) * 100 << "% loss)" << endl << '\t';

	pICMPheaderRet->nPacketsSent = nPacketsSent;
	pICMPheaderRet->nPacketsReceived = nPacketsReceived;
	if (nPacketsReceived > 0)
	{
		//	cout << "\rApproximate round trip times in milli-seconds:" << endl << '\t' << "Minimum = " << nMinRoundTripTime << 
		//		"ms, Maximum = " << nMaxRoundTripTime << "ms, Average = " << nTotalRoundTripTime / (float)nPacketsReceived << "ms" << endl;

		pICMPheaderRet->nMinRoundTripTime = nMinRoundTripTime;
		pICMPheaderRet->nMaxRoundTripTime = nMaxRoundTripTime;
		pICMPheaderRet->nAverageRoundTripTime = (int)(nTotalRoundTripTime / (float)nPacketsReceived);
	}
	else
	{

		pICMPheaderRet->nMinRoundTripTime = -1;
		pICMPheaderRet->nMaxRoundTripTime = -1;
		pICMPheaderRet->nAverageRoundTripTime = -1;
		//getchar();
	}
	closesocket(sock);
	//cout << '\r' << endl;
	return 0;

}

bool TestTCPPort(const ex_astr& strServerIP, int port)
{
	int icount = 0;

	unsigned int uibegconn = GetTickCount();
	unsigned int uicostconn = 0;

	msocketx sock;
	sock.create(SOCK_STREAM, IPPROTO_TCP);
	sock.setsocktime(1000);
	int iconn = sock.connect(strServerIP.c_str(), port, false);


	bool bFailed = true;

	while (++icount <= 2)
	{
		int nRet = sock.wait(1000, CAN_CONNECTX);
		if (nRet < 0)
		{
			continue;
		}

		if ((nRet & CAN_CONNECTX) == CAN_CONNECTX)
		{
			return true;
		}
		else
		{
			continue;
		}
	}

	return false;
}
