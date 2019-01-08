#ifndef __TS_CFG_H__
#define __TS_CFG_H__

#include <ex.h>
#include <vector>

#include <json/json.h>

typedef struct APP_CONFIG {
    ex_astr name;
    ex_astr display;
    ex_astr application;
    ex_astr cmdline;
    ex_astrs description;
}APP_CONFIG;

class TsCfg
{
public:
	TsCfg();
	virtual ~TsCfg();

	bool init(void);
	bool save(const ex_astr& new_value);
	
	Json::Value& get_root() {return m_root;}
	
    APP_CONFIG ssh;
    APP_CONFIG sftp;
    APP_CONFIG telnet;
    APP_CONFIG rdp;

protected:
	bool _load(const ex_astr& str_json);
    bool _parse_app(const Json::Value& m_root, const ex_astr& str_app, APP_CONFIG& cfg);

protected:
	Json::Value m_root;
};

extern TsCfg g_cfg;

#endif // __TS_CFG_H__
