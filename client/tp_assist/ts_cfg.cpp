#include "stdafx.h"
#include "ts_ini.h"
#include "ts_cfg.h"
#include "ts_env.h"

TsCfgSSH g_cfgSSH;
TsCfgScp g_cfgScp;
TsCfgTelnet g_cfgTelnet;

void split_by_char(ex_wstr s, char ch, std::vector<ex_wstr>& ret)
{
	int pos;

	while (s.length() != 0)
	{
		pos = s.find_first_of(ch, 0);
		if (-1 == pos)
		{
			ret.push_back(s);
			s = s.erase(0, s.length());
		}
		else if (0 == pos)
		{
			s = s.erase(0, pos + 1);
		}
		else
		{
			ex_wstr temp;
			temp.append(s, 0, pos);
			ret.push_back(temp);
			s = s.erase(0, pos + 1);
		}
	}
}

//=====================================================================
// Base Configuration Class
//=====================================================================

TsClientCfgBase::TsClientCfgBase()
{
	m_clientsetmap.clear();
	m_client_list.clear();
}

TsClientCfgBase::~TsClientCfgBase()
{}

bool TsClientCfgBase::_init(void)
{
	client_set temp;

	TsIniSection* cfg = NULL;
	cfg = m_ini.GetSection(_T("common"));
	if (NULL == cfg)
	{
		TSLOGE("[ERROR] Invalid configuration, [common] section not found.\n");
		return false;
	}

	ex_wstr _wstr;
	if (!cfg->GetStr(_T("current_client"), _wstr)) {
		return false;
	}

	m_current_client = _wstr;

	if (!cfg->GetStr(_T("client_list"), _wstr)) {
		return false;
	}

	std::vector<ex_wstr> c_list;
	split_by_char(_wstr, ',', c_list);

	std::vector<ex_wstr>::iterator it;
	for (it = c_list.begin(); it != c_list.end(); it++)
	{
		ex_wstr sec_name = it->c_str();
		cfg = m_ini.GetSection(sec_name);
		if (NULL == cfg)
		{
			TSLOGE("[ERROR] Invalid configuration, [common] section not found.\n");
			return false;
		}

		if (!cfg->GetStr(_T("name"), _wstr)) {
			continue;
		}
		temp.name = _wstr;

		if (!cfg->GetStr(_T("path"), _wstr)) {
			continue;
		}
		temp.path = _wstr;

		if (!cfg->GetStr(_T("alias_name"), _wstr)) {
			continue;
		}
		temp.alias_name = _wstr;

		if (!cfg->GetStr(_T("command_line"), _wstr)) {
			continue;
		}
		temp.commandline = _wstr;

		if (!cfg->GetStr(_T("desc"), _wstr)) {
			continue;
		}
		temp.desc = _wstr;

		temp.default = 0;

		m_clientsetmap[temp.name] = temp;
		m_client_list.push_back(temp.name);
	}

	return true;
}

void TsClientCfgBase::set(ex_wstr sec_name, ex_wstr key, ex_wstr value)
{
	if (sec_name != _T("common"))
	{
		clientsetmap::iterator it = m_clientsetmap.find(sec_name);
		if (it == m_clientsetmap.end())
			return;
	}

	TsIniSection* cfg = NULL;
	cfg = m_ini.GetSection(sec_name);
	if (NULL == cfg)
	{
		TSLOGE("[ERROR] Invalid configuration, [common] section not found.\n");
		return;
	}
	cfg->SetValue(key, value);

	return;
}

void TsClientCfgBase::save()
{
	m_ini.Save(EX_CODEPAGE_UTF8);
}

//=====================================================

TsCfgSSH::TsCfgSSH()
{}

TsCfgSSH::~TsCfgSSH()
{}

bool TsCfgSSH::init(void)
{
	m_current_client = _T("putty");

	client_set temp;
	temp.name = _T("putty");
	temp.alias_name = _T("PuTTY (内置)");
	temp.path = g_env.m_tools_path;
	temp.path += _T("\\putty\\putty.exe");
	temp.commandline = _T("-ssh -pw **** -P {host_port} -l {user_name} {host_ip}");
	temp.desc = _T("PuTTY为开放源代码软件，主要由Simon Tatham维护，使用MIT licence授权。");
	temp.default = 1;

	m_clientsetmap[temp.name] = temp;
	m_client_list.push_back(temp.name);

	if (!m_ini.LoadFromFile(g_env.m_ssh_client_conf_file))
	{
		TSLOGE("can not load ssh config file.\n");
		return false;
	}

	return _init();
}

//=====================================================

TsCfgScp::TsCfgScp()
{}

TsCfgScp::~TsCfgScp()
{}

bool TsCfgScp::init(void)
{
	m_current_client = _T("winscp");
	client_set temp;


	temp.name = _T("winscp");
	temp.alias_name = _T("WinSCP (内置)");
	temp.path = g_env.m_tools_path;
	temp.path += _T("\\winscp\\winscp.exe");
	temp.commandline = _T("/sessionname=\"TP#{real_ip}\" {user_name}:****@{host_ip}:{host_port}");
	temp.desc = _T("WinSCP是一个Windows环境下使用SSH的开源图形化SFTP客户端。同时支持SCP协议。它的主要功能就是在本地与远程计算机间安全的复制文件。");
	temp.default = 1;
	m_clientsetmap[temp.name] = temp;
	m_client_list.push_back(temp.name);

	if (!m_ini.LoadFromFile(g_env.m_scp_client_conf_file))
	{
		TSLOGE("can not load scp config file.\n");
		return false;
	}

	return _init();
}

//=====================================================

TsCfgTelnet::TsCfgTelnet()
{}

TsCfgTelnet::~TsCfgTelnet()
{}

bool TsCfgTelnet::init(void)
{
	m_current_client = _T("putty");
	client_set temp;

	temp.name = _T("putty");
	temp.alias_name = _T("PuTTY (内置)");
	temp.path = g_env.m_tools_path;
	temp.path += _T("\\putty\\putty.exe");
	//temp.commandline = _T("-telnet -P {host_port} -l {user_name} {host_ip}");
	temp.commandline = _T("telnet://{user_name}@{host_ip}:{host_port}");
	temp.desc = _T("PuTTY为开放源代码软件，主要由Simon Tatham维护，使用MIT licence授权。");

	temp.default = 1;
	m_clientsetmap[temp.name] = temp;
	m_client_list.push_back(temp.name);

	if (!m_ini.LoadFromFile(g_env.m_telnet_client_conf_file))
	{
		TSLOGE("can not load telnet config file.\n");
		return false;
	}

	return _init();
}
