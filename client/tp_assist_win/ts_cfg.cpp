#include "stdafx.h"
#include "ts_cfg.h"
#include "ts_env.h"


TsCfg g_cfg;

TsCfg::TsCfg()
{}

TsCfg::~TsCfg()
{}

bool TsCfg::init(void) {
	ex_astr file_content;
	if (!ex_read_text_file(g_env.m_cfg_file, file_content)) {
		EXLOGE("can not load config file.\n");
		return false;
	}

	if (!_load(file_content))
		return false;

	return true;
}

bool TsCfg::save(const ex_astr& new_value)
{
	if (!_load(new_value))
		return false;

	Json::StyledWriter jwriter;
	ex_astr val = jwriter.write(m_root);

	if (!ex_write_text_file(g_env.m_cfg_file, val)) {
		EXLOGE("can not save config file.\n");
		return false;
	}

	return true;
}

bool TsCfg::_load(const ex_astr& str_json) {
	Json::Reader jreader;

	if (!jreader.parse(str_json.c_str(), m_root)) {
		EXLOGE("can not parse new config data, not in json format?\n");
		return false;
	}

	ex_astr sel_name;
	int i = 0;
	ex_astr tmp;

	//===================================
	// check ssh config
	//===================================

	if (!m_root["ssh"].isObject()) {
		EXLOGE("invalid config, error 1.\n");
		return false;
	}

	if (!m_root["ssh"]["selected"].isString()) {
		EXLOGE("invalid config, error 2.\n");
		return false;
	}

	sel_name = m_root["ssh"]["selected"].asCString();

	if (!m_root["ssh"]["available"].isArray() || m_root["ssh"]["available"].size() == 0) {
		EXLOGE("invalid config, error 3.\n");
		return false;
	}

	for (i = 0; i < m_root["ssh"]["available"].size(); ++i) {

		if (
			!m_root["ssh"]["available"][i]["name"].isString()
			|| !m_root["ssh"]["available"][i]["app"].isString()
			|| !m_root["ssh"]["available"][i]["cmdline"].isString()
			) {
			EXLOGE("invalid config, error 4.\n");
			return false;
		}

		if (m_root["ssh"]["available"][i]["display"].isNull()) {
			m_root["ssh"]["available"][i]["display"] = m_root["ssh"]["available"][i]["name"];
		}

		if (m_root["ssh"]["available"][i]["name"].asCString() != sel_name)
			continue;

// 		if (m_root["ssh"]["available"][i]["disp"].isString()) {
// 			ssh_display = m_root["ssh"]["available"][i]["display"].asCString();
// 		}
// 		else if (m_root["ssh"]["available"][i]["disp"].isNull()) {
// 			m_root["ssh"]["available"][i]["disp"] = ssh_name;
// 			ssh_display = ssh_name;
// 		}
// 		else {
// 			EXLOGE("invalid config, error 5.\n");
// 			return false;
// 		}

		tmp = m_root["ssh"]["available"][i]["app"].asCString();
		ex_astr2wstr(tmp, ssh_app);
		tmp = m_root["ssh"]["available"][i]["cmdline"].asCString();
		ex_astr2wstr(tmp, ssh_cmdline);

// 		ssh_app = m_root["ssh"]["available"][i]["app"].asCString();
// 		ssh_cmdline = m_root["ssh"]["available"][i]["cmdline"].asCString();

		break;
	}

	if (ssh_app.length() == 0 || ssh_cmdline.length() == 0) {
		EXLOGE("invalid config, error 6.\n");
		return false;
	}

	//===================================
	// check scp config
	//===================================

	if (!m_root["scp"].isObject()) {
		EXLOGE("invalid config, error 1.\n");
		return false;
	}

	if (!m_root["scp"]["selected"].isString()) {
		EXLOGE("invalid config, error 2.\n");
		return false;
	}

	sel_name = m_root["scp"]["selected"].asCString();

	if (!m_root["scp"]["available"].isArray() || m_root["scp"]["available"].size() == 0) {
		EXLOGE("invalid config, error 3.\n");
		return false;
	}

	for (i = 0; i < m_root["scp"]["available"].size(); ++i) {

		if (
			!m_root["scp"]["available"][i]["name"].isString()
			|| !m_root["scp"]["available"][i]["app"].isString()
			|| !m_root["scp"]["available"][i]["cmdline"].isString()
			) {
			EXLOGE("invalid config, error 4.\n");
			return false;
		}

		if (m_root["scp"]["available"][i]["display"].isNull()) {
			m_root["scp"]["available"][i]["display"] = m_root["scp"]["available"][i]["name"];
		}

		if (m_root["scp"]["available"][i]["name"].asCString() != sel_name)
			continue;

		tmp = m_root["scp"]["available"][i]["app"].asCString();
		ex_astr2wstr(tmp, scp_app);
		tmp = m_root["scp"]["available"][i]["cmdline"].asCString();
		ex_astr2wstr(tmp, scp_cmdline);

		break;
	}

	if (scp_app.length() == 0 || scp_cmdline.length() == 0) {
		EXLOGE("invalid config, error 6.\n");
		return false;
	}

	//===================================
	// check telnet config
	//===================================

	if (!m_root["telnet"].isObject()) {
		EXLOGE("invalid config, error 1.\n");
		return false;
	}

	if (!m_root["telnet"]["selected"].isString()) {
		EXLOGE("invalid config, error 2.\n");
		return false;
	}

	sel_name = m_root["telnet"]["selected"].asCString();

	if (!m_root["telnet"]["available"].isArray() || m_root["telnet"]["available"].size() == 0) {
		EXLOGE("invalid config, error 3.\n");
		return false;
	}

	for (i = 0; i < m_root["telnet"]["available"].size(); ++i) {

		if (
			!m_root["telnet"]["available"][i]["name"].isString()
			|| !m_root["telnet"]["available"][i]["app"].isString()
			|| !m_root["telnet"]["available"][i]["cmdline"].isString()
			) {
			EXLOGE("invalid config, error 4.\n");
			return false;
		}

		if (m_root["telnet"]["available"][i]["display"].isNull()) {
			m_root["telnet"]["available"][i]["display"] = m_root["telnet"]["available"][i]["name"];
		}

		if (m_root["telnet"]["available"][i]["name"].asCString() != sel_name)
			continue;

		tmp = m_root["telnet"]["available"][i]["app"].asCString();
		ex_astr2wstr(tmp, telnet_app);
		tmp = m_root["telnet"]["available"][i]["cmdline"].asCString();
		ex_astr2wstr(tmp, telnet_cmdline);

		break;
	}

	if (telnet_app.length() == 0 || telnet_cmdline.length() == 0) {
		EXLOGE("invalid config, error 6.\n");
		return false;
	}

	return true;
}


#if 0
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

	ExIniSection* cfg = NULL;
	cfg = m_ini.GetSection(_T("common"));
	if (NULL == cfg)
	{
		EXLOGE("[ERROR] Invalid configuration, [common] section not found.\n");
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
			EXLOGE("[ERROR] Invalid configuration, [common] section not found.\n");
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

		temp.is_default = false;

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

	ExIniSection* cfg = NULL;
	cfg = m_ini.GetSection(sec_name);
	if (NULL == cfg)
	{
		EXLOGE("[ERROR] Invalid configuration, [common] section not found.\n");
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
	temp.is_default = true;

	m_clientsetmap[temp.name] = temp;
	m_client_list.push_back(temp.name);

	if (!m_ini.LoadFromFile(g_env.m_ssh_client_conf_file))
	{
		EXLOGE("can not load ssh config file.\n");
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
	temp.is_default = true;
	m_clientsetmap[temp.name] = temp;
	m_client_list.push_back(temp.name);

	if (!m_ini.LoadFromFile(g_env.m_scp_client_conf_file))
	{
		EXLOGE("can not load scp config file.\n");
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

	temp.is_default = true;
	m_clientsetmap[temp.name] = temp;
	m_client_list.push_back(temp.name);

	if (!m_ini.LoadFromFile(g_env.m_telnet_client_conf_file))
	{
		EXLOGE("can not load telnet config file.\n");
		return false;
	}

	return _init();
}
#endif
