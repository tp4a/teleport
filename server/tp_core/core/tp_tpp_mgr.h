#ifndef __TP_TPP_MGR_H__
#define __TP_TPP_MGR_H__

#include "../common/protocol_interface.h"

#include <ex.h>

typedef struct TPP_LIB
{
	TPP_LIB()
	{
		dylib = NULL;
		init = NULL;
	}
	~TPP_LIB()
	{
		if (NULL != dylib)
			ex_dlclose(dylib);
		dylib = NULL;
	}

	EX_DYLIB_HANDLE dylib;
	TPP_INIT_FUNC init;
	TPP_START_FUNC start;
	TPP_STOP_FUNC stop;
	TPP_TIMER_FUNC timer;
// 	TPP_SET_CFG_FUNC set_cfg;

	TPP_COMMAND_FUNC command;
}TPP_LIB;

typedef std::list<TPP_LIB*> tpp_libs;

class TppManager
{
public:
	TppManager()
	{
	}
	~TppManager()
	{
		tpp_libs::iterator it = m_libs.begin();
		for (; it != m_libs.end(); ++it)
		{
			delete (*it);
		}
		m_libs.clear();
	}

	bool load_tpp(const ex_wstr& libfile);
	void stop_all(void);
	void timer(void); // 大约1秒调用一次
	int count(void) { return m_libs.size(); }

	void set_config(int noop_timeout);
	void set_runtime_config(const ex_astr& sp);
	void kill_sessions(const ex_astr& sp);

private:
	tpp_libs m_libs;
};

extern TppManager g_tpp_mgr;

#endif // __TP_TPP_MGR_H__
