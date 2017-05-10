#include "ssh_proxy.h"
#include "tpp_env.h"

TPP_API ex_rv tpp_init(TPP_INIT_ARGS* init_args)
{
#ifdef EX_OS_UNIX
	ssh_threads_set_callbacks(ssh_threads_get_pthread());
	ssh_init();
#endif

	if (!g_ssh_env.init(init_args))
		return TSR_FAILED;

	return 0;
}

TPP_API ex_rv tpp_start(void)
{
	if (!g_ssh_proxy.init())
		return TSR_FAILED;
	if (!g_ssh_proxy.start())
		return TSR_FAILED;

	return 0;
}

TPP_API ex_rv tpp_stop(void)
{
	g_ssh_proxy.stop();
	return 0;
}
