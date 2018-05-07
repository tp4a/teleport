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
	
	Json::Value& get_root() {return m_root;}
	
	ex_astr term_name;
	ex_astr term_display;
	ex_astr term_app;
	ex_astr term_profile;
	
	ex_astr rdp_name;
	ex_astr rdp_display;
	ex_astr rdp_app;
	//ex_astr rdp_cmdline;
	
protected:
	bool _load(const ex_astr& str_json);

protected:
	Json::Value m_root;
};

extern TsCfg g_cfg;

#endif // __TS_CFG_H__
