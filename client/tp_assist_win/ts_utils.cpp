// #include <unistd.h>
#include "ts_utils.h"

#include <WinCrypt.h>

#pragma comment(lib, "Crypt32.lib")

//connect to console:i:%d
//compression:i:1
//bitmapcachepersistenable:i:1

// https://www.donkz.nl/overview-rdp-file-settings/
//
// authentication level:i:2\n
//   
//
// negotiate security layer:i:1\n
//   0 = negotiation is not enabled and the session is started by using Secure Sockets Layer (SSL).
//   1 = negotiation is enabled and the session is started by using x.224 encryption.


//redirectdirectx:i:0\n\
//prompt for credentials on client:i:0\n\

std::string rdp_content = "\
administrative session:i:%d\n\
screen mode id:i:%d\n\
use multimon:i:0\n\
desktopwidth:i:%d\n\
desktopheight:i:%d\n\
session bpp:i:16\n\
winposstr:s:0,1,%d,%d,%d,%d\n\
bitmapcachepersistenable:i:1\n\
bitmapcachesize:i:32000\n\
compression:i:1\n\
keyboardhook:i:2\n\
audiocapturemode:i:0\n\
videoplaybackmode:i:1\n\
connection type:i:7\n\
networkautodetect:i:1\n\
bandwidthautodetect:i:1\n\
disableclipboardredirection:i:0\n\
displayconnectionbar:i:1\n\
enableworkspacereconnect:i:0\n\
disable wallpaper:i:1\n\
allow font smoothing:i:0\n\
allow desktop composition:i:0\n\
disable full window drag:i:1\n\
disable menu anims:i:1\n\
disable themes:i:1\n\
disable cursor setting:i:1\n\
full address:s:%s:%d\n\
audiomode:i:0\n\
redirectprinters:i:0\n\
redirectcomports:i:0\n\
redirectsmartcards:i:0\n\
redirectclipboard:i:%d\n\
redirectposdevices:i:0\n\
autoreconnection enabled:i:0\n\
authentication level:i:2\n\
prompt for credentials:i:0\n\
negotiate security layer:i:1\n\
remoteapplicationmode:i:0\n\
alternate shell:s:\n\
shell working directory:s:\n\
gatewayhostname:s:\n\
gatewayusagemethod:i:4\n\
gatewaycredentialssource:i:4\n\
gatewayprofileusagemethod:i:0\n\
promptcredentialonce:i:0\n\
gatewaybrokeringtype:i:0\n\
use redirection server name:i:0\n\
rdgiskdcproxy:i:0\n\
kdcproxyname:s:\n\
drivestoredirect:s:%s\n\
username:s:%s\n\
password 51:b:%s\n\
";

bool calc_psw51b(const char* password, std::string& ret) {
    DATA_BLOB DataIn;
    DATA_BLOB DataOut;

    ex_wstr w_pswd;
    ex_astr2wstr(password, w_pswd, EX_CODEPAGE_ACP);

    DataIn.cbData = w_pswd.length() * sizeof(wchar_t);
    DataIn.pbData = (BYTE*)w_pswd.c_str();


    if (!CryptProtectData(&DataIn, L"psw", nullptr, nullptr, nullptr, 0, &DataOut))
        return false;

    char szRet[5] = { 0 };
    for (DWORD i = 0; i < DataOut.cbData; ++i) {
        sprintf_s(szRet, 5, "%02X", DataOut.pbData[i]);
        ret += szRet;
    }

    LocalFree(DataOut.pbData);
    return true;
}


bool is_digital(std::string str) {
    for (int i = 0; i < str.size(); i++) {
        if (str.at(i) == '-' && str.size() > 1)  // 有可能出现负数
            continue;
        if (str.at(i) > '9' || str.at(i) < '0')
            return false;
    }
    return true;
}

std::string strtolower(std::string str) {
    for (int i = 0; i < str.size(); i++)
    {
        str[i] = tolower(str[i]);
    }
    return str;
}


void SplitString(const std::string& s, std::vector<std::string>& v, const std::string& c)
{
    std::string::size_type pos1, pos2;
    pos2 = s.find(c);
    pos1 = 0;
    while (std::string::npos != pos2)
    {
        v.push_back(s.substr(pos1, pos2 - pos1));

        pos1 = pos2 + c.size();
        pos2 = s.find(c, pos1);
    }
    if (pos1 != s.length())
        v.push_back(s.substr(pos1));
}
