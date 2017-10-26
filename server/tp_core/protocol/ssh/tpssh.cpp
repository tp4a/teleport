#include "ssh_proxy.h"
#include "tpp_env.h"

#include <teleport_const.h>

TPP_API ex_rv tpp_init(TPP_INIT_ARGS* init_args)
{
#ifdef EX_OS_UNIX
	ssh_threads_set_callbacks(ssh_threads_get_pthread());
	ssh_init();
#else
	ssh_init();
#endif

	if (!g_ssh_env.init(init_args))
		return TPE_FAILED;

	return 0;
}

TPP_API ex_rv tpp_start(void)
{
	if (!g_ssh_proxy.init())
		return TPE_FAILED;
	if (!g_ssh_proxy.start())
		return TPE_FAILED;

	return 0;
}

TPP_API ex_rv tpp_stop(void)
{
	g_ssh_proxy.stop();
	return 0;
}

TPP_API void tpp_timer(void) {
	// be called per one second.
	g_ssh_proxy.timer();
}
