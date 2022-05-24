#include "ts_main.h"
#include "ts_session.h"
#include "ts_http_rpc.h"
#include "ts_web_rpc.h"
#include "ts_env.h"
#include "ts_ver.h"
#include "tp_tpp_mgr.h"

#include <mbedtls/platform.h>
// #include <mbedtls/debug.h>

bool g_exit_flag = false;

TPP_CONNECT_INFO* tpp_get_connect_info(const char* sid) {
    TS_CONNECT_INFO connect_info;

    bool ret = g_session_mgr.get_connect_info(sid, connect_info);
    if (!ret)
        return nullptr;

    auto info = (TPP_CONNECT_INFO*) calloc(1, sizeof(TPP_CONNECT_INFO));

    info->sid = (char*) calloc(1, connect_info.sid.length() + 1);
    ex_strcpy(info->sid, connect_info.sid.length() + 1, connect_info.sid.c_str());
    info->user_username = (char*) calloc(1, connect_info.user_username.length() + 1);
    ex_strcpy(info->user_username, connect_info.user_username.length() + 1, connect_info.user_username.c_str());
    info->host_ip = (char*) calloc(1, connect_info.host_ip.length() + 1);
    ex_strcpy(info->host_ip, connect_info.host_ip.length() + 1, connect_info.host_ip.c_str());
    info->conn_ip = (char*) calloc(1, connect_info.conn_ip.length() + 1);
    ex_strcpy(info->conn_ip, connect_info.conn_ip.length() + 1, connect_info.conn_ip.c_str());
    info->client_ip = (char*) calloc(1, connect_info.client_ip.length() + 1);
    ex_strcpy(info->client_ip, connect_info.client_ip.length() + 1, connect_info.client_ip.c_str());
    info->acc_username = (char*) calloc(1, connect_info.acc_username.length() + 1);
    ex_strcpy(info->acc_username, connect_info.acc_username.length() + 1, connect_info.acc_username.c_str());
    info->acc_secret = (char*) calloc(1, connect_info.acc_secret.length() + 1);
    ex_strcpy(info->acc_secret, connect_info.acc_secret.length() + 1, connect_info.acc_secret.c_str());
    info->username_prompt = (char*) calloc(1, connect_info.username_prompt.length() + 1);
    ex_strcpy(info->username_prompt, connect_info.username_prompt.length() + 1, connect_info.username_prompt.c_str());
    info->password_prompt = (char*) calloc(1, connect_info.password_prompt.length() + 1);
    ex_strcpy(info->password_prompt, connect_info.password_prompt.length() + 1, connect_info.password_prompt.c_str());

    info->user_id = connect_info.user_id;
    info->host_id = connect_info.host_id;
    info->acc_id = connect_info.acc_id;
    info->conn_port = connect_info.conn_port;
    info->protocol_type = connect_info.protocol_type;
    info->protocol_sub_type = connect_info.protocol_sub_type;
    info->protocol_flag = connect_info.protocol_flag;
    info->record_flag = connect_info.record_flag;
    info->auth_type = connect_info.auth_type;

    return info;
}

void tpp_free_connect_info(TPP_CONNECT_INFO* info) {
    if (nullptr == info)
        return;

    g_session_mgr.free_connect_info(info->sid);

    free(info->sid);
    free(info->user_username);
    free(info->host_ip);
    free(info->conn_ip);
    free(info->client_ip);
    free(info->acc_username);
    free(info->acc_secret);
    free(info->username_prompt);
    free(info->password_prompt);
    free(info);
}

bool tpp_session_begin(const TPP_CONNECT_INFO* info, int* db_id) {
    if (nullptr == info || nullptr == db_id)
        return false;

    TS_CONNECT_INFO connect_info;
    connect_info.sid = info->sid;
    connect_info.user_id = info->user_id;
    connect_info.host_id = info->host_id;
    connect_info.acc_id = info->acc_id;
    connect_info.user_username = info->user_username;
    connect_info.host_ip = info->host_ip;
    connect_info.conn_ip = info->conn_ip;
    connect_info.client_ip = info->client_ip;
    connect_info.acc_username = info->acc_username;

    connect_info.conn_port = info->conn_port;
    connect_info.protocol_type = info->protocol_type;
    connect_info.protocol_sub_type = info->protocol_sub_type;
    connect_info.auth_type = info->auth_type;

    return ts_web_rpc_session_begin(connect_info, *db_id);
}

bool tpp_session_update(int db_id, int protocol_sub_type, int state) {
    return ts_web_rpc_session_update(db_id, protocol_sub_type, state);
}

bool tpp_session_end(const char* sid, int db_id, int ret) {
    return ts_web_rpc_session_end(sid, db_id, ret);
}

int ts_main() {
    ExIniFile& ini = g_env.get_ini();

    EXLOGW("\n");
    EXLOGW("###############################################################\n");
    EXLOGW(L"Teleport Core Server v%ls starting ...\n", TP_SERVER_VER);
    EXLOGW(L"Load config file: %ls.\n", ini.get_filename().c_str());

    ex_ini_sections& secs = ini.GetAllSections();
    TsHttpRpc rpc;

    // 枚举配置文件中的[protocol-xxx]小节，加载对应的协议动态库
    bool all_ok = true;

    do {
        if (!g_session_mgr.start()) {
            EXLOGE("[core] failed to start session-id manager.\n");
            all_ok = false;
            break;
        }

        if (!rpc.init() || !rpc.start()) {
            EXLOGE("[core] rpc init/start failed.\n");
            all_ok = false;
            break;
        }

        for (auto & sec : secs) {
            if (sec.first.length() > 9 && 0 == wcsncmp(sec.first.c_str(), L"protocol-", 9)) {
                ex_wstr libname;
                if (!sec.second->GetStr(L"lib", libname))
                    continue;

                bool enabled = false;
                sec.second->GetBool(L"enabled", enabled, false);
                if (!enabled) {
                    EXLOGW(L"[core] `%ls` not enabled.\n", libname.c_str());
                    continue;
                }

                if (!g_tpp_mgr.load_tpp(libname)) {
                    all_ok = false;
                    break;
                }
            }
        }

    } while (false);

    if (0 == g_tpp_mgr.count()) {
        all_ok = false;
    }

    if (!all_ok) {
        g_exit_flag = true;
    }

    if (!g_exit_flag) {
        ts_web_rpc_register_core();

        EXLOGI("[core] ---- initialized, ready for service ----\n");
        while (!g_exit_flag) {
            ex_sleep_ms(1000);
            g_tpp_mgr.timer();
        }
    }

    EXLOGI("[core] try to stop all thread and exit.\n");
    g_tpp_mgr.stop_all();
    rpc.stop();
    g_session_mgr.stop();

    EXLOGI("[core] done.\n");

    return 0;
}
