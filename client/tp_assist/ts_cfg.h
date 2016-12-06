#ifndef __TS_CFG_H__
#define __TS_CFG_H__

#include <ex.h>
#include <vector>
#include <map>

typedef std::vector<ex_wstr> client_list;
struct client_set 
{
	ex_wstr name;
	ex_wstr alias_name;
	ex_wstr path;
	ex_wstr commandline;
	ex_wstr desc;
	int default;
};

typedef std::map<ex_wstr, client_set> clientsetmap;

class TsClientCfgBase
{
public:
	TsClientCfgBase();
	virtual ~TsClientCfgBase();

	virtual bool init(void) = 0;
	void set(ex_wstr sec_name, ex_wstr key, ex_wstr value);
	void save();
	client_list m_client_list;
	clientsetmap m_clientsetmap;
	ex_wstr m_current_client;

protected:
	bool _init(void);

protected:
	TsIniFile m_ini;
};

class TsCfgSSH : public TsClientCfgBase
{
public:
    TsCfgSSH();
    ~TsCfgSSH();

    bool init(void);
};
extern TsCfgSSH g_cfgSSH;

class TsCfgScp : public TsClientCfgBase
{
public:
	TsCfgScp();
	~TsCfgScp();

	bool init(void);
};
extern TsCfgScp g_cfgScp;

class TsCfgTelnet : public TsClientCfgBase
{
public:
	TsCfgTelnet();
	~TsCfgTelnet();

	bool init(void);
};
extern TsCfgTelnet g_cfgTelnet;

#endif // __TS_CFG_H__
