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
	replay_path = args->replay_path;

	get_connect_info = args->func_get_connect_info;
	free_connect_info = args->func_free_connect_info;
	session_begin = args->func_session_begin;
	session_update = args->func_session_update;
	session_end = args->func_session_end;

	if (NULL == get_connect_info || NULL == free_connect_info || NULL == session_begin || NULL == session_update || NULL == session_end)
	{
		EXLOGE("invalid init args(2).\n");
		return false;
	}

	if (NULL == args->cfg)
	{
		EXLOGE("invalid init args(3).\n");
		return false;
	}

	if (!_on_init(args))
	{
		EXLOGE("invalid init args(4).\n");
		return false;
	}

	return true;
}
