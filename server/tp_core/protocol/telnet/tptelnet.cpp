#include "telnet_proxy.h"
#include "tpp_env.h"
#include <teleport_const.h>

TPP_API ex_rv tpp_init(TPP_INIT_ARGS* init_args)
{
	if (!g_telnet_env.init(init_args))
		return TPE_FAILED;

	return 0;
}

TPP_API ex_rv tpp_start(void)
{
	if (!g_telnet_proxy.init())
		return TPE_FAILED;
	if (!g_telnet_proxy.start())
		return TPE_FAILED;

	return 0;
}

TPP_API ex_rv tpp_stop(void)
{
	g_telnet_proxy.stop();
	return 0;
}

TPP_API void tpp_timer(void) {
	// be called per one second.
	g_telnet_proxy.timer();
}
