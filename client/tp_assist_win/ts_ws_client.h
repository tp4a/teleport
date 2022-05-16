#ifndef __TS_WS_CLIENT_H__
#define __TS_WS_CLIENT_H__

#include "ts_const.h"

#include <vector>
#include <string>
#include <map>

#include <ex.h>
#include <json/json.h>
#include <teleport_const.h>

#include "../../external/mongoose/mongoose.h"

#define MESSAGE_TYPE_REQUEST    0
#define MESSAGE_TYPE_RESPONSE   1

typedef struct AssistMessage
{
    int command_id;
    std::string method;

    AssistMessage() :
            command_id(0),
            method("UNKNOWN") {}
} AssistMessage;

class TsWsClient : public ExThreadBase
{
public:
    TsWsClient();

    ~TsWsClient();

    static void init_app(void* app);
    static void stop_all_client();

    static void url_scheme_handler(const std::string& url);

protected:
    void _thread_loop(void);

    // bool _on_init();

private:
    void _register(const std::string& ws_url, uint32_t assist_id, const std::string& session_id);

    void _on_message(const std::string& message, std::string& buf);

    void _rpc_func_run_client(ex_astr& buf, AssistMessage& msg_req, Json::Value& js_root);

    void _rpc_func_get_config(ex_astr& buf, AssistMessage& msg_req, Json::Value& js_root);

    void _rpc_func_set_config(ex_astr& buf, AssistMessage& msg_req, Json::Value& js_root);

    void _rpc_func_select_file(ex_astr& buf, AssistMessage& msg_req, Json::Value& js_root);

    void _create_response(ex_astr& buf, const AssistMessage& msg_ret, int err_code);

    void _create_response(ex_astr& buf, const AssistMessage& msg_ret, int err_code, const ex_wstr& message);

    void _create_response(ex_astr& buf, const AssistMessage& msg_ret, int err_code, const ex_wstr& message, Json::Value& data);

    //    void _rpc_func_check(const ex_astr& func_args, ex_astr& buf);
    //    void _rpc_func_rdp_play(const ex_astr& func_args, ex_astr& buf);
    //    void _rpc_func_file_action(const ex_astr& func_args, ex_astr& buf);
    //    void _rpc_func_get_version(const ex_astr& func_args, ex_astr& buf);



    static void _mg_event_handler(struct mg_connection* nc, int ev, void* ev_data);

    static void _process_register(const std::string& param, Json::Value& js_root);

private:
    struct mg_mgr m_mg_mgr;
    struct mg_connection* m_nc;
    uint32_t m_assist_id;
};

#endif // __TS_WS_CLIENT_H__