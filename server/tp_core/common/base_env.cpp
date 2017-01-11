#include "base_env.h"

TppEnvBase::TppEnvBase()
{}

TppEnvBase::~TppEnvBase()
{}

bool TppEnvBase::init(TPP_INIT_ARGS* args)
{
	if (NULL == args)
	{
		EXLOGE("invalid init args(1).\n");
		return false;
	}

	EXLOG_USE_LOGGER(args->logger);

	exec_path = args->exec_path;
	etc_path = args->etc_path;

	take_session = args->func_take_session;
	session_begin = args->func_session_begin;
	session_end = args->func_session_end;

	if (NULL == take_session || NULL == session_begin || NULL == session_end)
	{
		EXLOGE("invalid init args(2).\n");
		return false;
	}

	if (NULL == args->cfg)
	{
		EXLOGE("invalid init args(3).\n");
		return false;
	}

	ExIniSection* ps = args->cfg->GetSection(L"common");
	if (NULL == ps)
	{
		EXLOGE("invalid config(1).\n");
		return false;
	}

	if (!ps->GetStr(L"replay-path", replay_path))
	{
		replay_path = exec_path;
		ex_path_join(replay_path, true, L"..", L"data", L"replay", NULL);
	}

	if (!_on_init(args))
	{
		EXLOGE("invalid init args(4).\n");
		return false;
	}

	return true;
}
