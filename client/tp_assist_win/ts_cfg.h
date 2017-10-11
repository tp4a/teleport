#ifndef __TS_CFG_H__
#define __TS_CFG_H__

#include <ex.h>
#include <vector>

#include <json/json.h>

class TsCfg
{
public:
	TsCfg();
	virtual ~TsCfg();

	bool init(void);
	bool save(const ex_astr& new_value);

	Json::Value& get_root() { return m_root; }

// 	ex_astr ssh_name;
// 	ex_astr ssh_display;
// 	ex_astr ssh_app;
// 	ex_astr ssh_cmdline;

	ex_wstr ssh_app;
	ex_wstr ssh_cmdline;
	ex_wstr scp_app;
	ex_wstr scp_cmdline;
	ex_wstr telnet_app;
	ex_wstr telnet_cmdline;

protected:
	bool _load(const ex_astr& str_json);

protected:
	Json::Value m_root;
};

extern TsCfg g_cfg;

//#include <map>
// 
// typedef std::vector<ex_wstr> client_list;
// struct client_set 
// {
// 	ex_wstr name;
// 	ex_wstr alias_name;
// 	ex_wstr path;
// 	ex_wstr commandline;
// 	ex_wstr desc;
// 	bool is_default;
// };
// 
// typedef std::map<ex_wstr, client_set> clientsetmap;
// 
// class TsClientCfgBase
// {
// public:
// 	TsClientCfgBase();
// 	virtual ~TsClientCfgBase();
// 
// 	virtual bool init(void) = 0;
// 	void set(ex_wstr sec_name, ex_wstr key, ex_wstr value);
// 	void save();
// 	client_list m_client_list;
// 	clientsetmap m_clientsetmap;
// 	ex_wstr m_current_client;
// 
// protected:
// 	bool _init(void);
// 
// protected:
// 	ExIniFile m_ini;
// };
// 
// class TsCfgSSH : public TsClientCfgBase
// {
// public:
//     TsCfgSSH();
//     ~TsCfgSSH();
// 
//     bool init(void);
// };
// extern TsCfgSSH g_cfgSSH;
// 
// class TsCfgScp : public TsClientCfgBase
// {
// public:
// 	TsCfgScp();
// 	~TsCfgScp();
// 
// 	bool init(void);
// };
// extern TsCfgScp g_cfgScp;
// 
// class TsCfgTelnet : public TsClientCfgBase
// {
// public:
// 	TsCfgTelnet();
// 	~TsCfgTelnet();
// 
// 	bool init(void);
// };
// extern TsCfgTelnet g_cfgTelnet;

#endif // __TS_CFG_H__
