#include "ssh_proxy.h"
#include "tpp_env.h"

#include <teleport_const.h>
#include <json/json.h>

TPP_API ex_rv tpp_init(TPP_INIT_ARGS* init_args) {
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

TPP_API ex_rv tpp_start(void) {
    if (!g_ssh_proxy.init())
        return TPE_FAILED;
    if (!g_ssh_proxy.start())
        return TPE_FAILED;

    return 0;
}

TPP_API ex_rv tpp_stop(void) {
    g_ssh_proxy.stop();
    ssh_finalize();
    return 0;
}

TPP_API void tpp_timer(void) {
    // be called per one second.
    g_ssh_proxy.timer();
}

static ex_rv tpp_cmd_set_runtime_config(const char* param) {
    Json::Value jp;
    Json::CharReaderBuilder jcrb;
    std::unique_ptr<Json::CharReader> const jreader(jcrb.newCharReader());
    const char* str_json_begin = param;
    ex_astr err;

    if (!jreader->parse(str_json_begin, param + strlen(param), &jp, &err))
        return TPE_JSON_FORMAT;

    if (!jp.isObject())
        return TPE_PARAM;

    if (jp["noop_timeout"].isNull() || !jp["noop_timeout"].isUInt())
        return TPE_PARAM;

    ex_u32 noop_timeout = jp["noop_timeout"].asUInt();
    // if (noop_timeout == 0)
    //     return TPE_PARAM;

    g_ssh_proxy.set_cfg(noop_timeout * 60);

    return TPE_PARAM;
}

static ex_rv tpp_cmd_kill_sessions(const char* param) {
    Json::Value jp;
    Json::CharReaderBuilder reader_builder;
    const char* str_json_begin = param;
    ex_astr err;

    std::unique_ptr<Json::CharReader> const json_reader(reader_builder.newCharReader());
    if (!json_reader->parse(str_json_begin, param + strlen(param), &jp, &err))
        return TPE_JSON_FORMAT;

    if (!jp.isArray())
        return TPE_PARAM;

    ex_astrs ss;

    for (const auto& item : jp) {
        if (!item.isString()) {
            return TPE_PARAM;
        }

        ss.push_back(item.asString());
    }

    g_ssh_proxy.kill_sessions(ss);

    return TPE_PARAM;
}

TPP_API ex_rv tpp_command(ex_u32 cmd, const char* param) {
    if (!param || strlen(param) == 0)
        return TPE_PARAM;

    switch (cmd) {
    case TPP_CMD_SET_RUNTIME_CFG:
        return tpp_cmd_set_runtime_config(param);
    case TPP_CMD_KILL_SESSIONS:
        return tpp_cmd_kill_sessions(param);
    default:
        return TPE_UNKNOWN_CMD;
    }
}
