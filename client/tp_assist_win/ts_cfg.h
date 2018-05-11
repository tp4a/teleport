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

	ex_wstr ssh_app;
	ex_wstr ssh_cmdline;
	ex_wstr scp_app;
	ex_wstr scp_cmdline;
	ex_wstr telnet_app;
	ex_wstr telnet_cmdline;

	ex_wstr rdp_name;
	ex_wstr rdp_app;
	ex_wstr rdp_cmdline;

protected:
	bool _load(const ex_astr& str_json);

protected:
	Json::Value m_root;
};

extern TsCfg g_cfg;

#endif // __TS_CFG_H__
