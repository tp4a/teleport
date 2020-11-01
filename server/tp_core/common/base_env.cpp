#include "base_env.h"

TppEnvBase::TppEnvBase() :
        get_connect_info(nullptr),
        free_connect_info(nullptr),
        session_begin(nullptr),
        session_update(nullptr),
        session_end(nullptr) {}

TppEnvBase::~TppEnvBase() = default;

bool TppEnvBase::init(TPP_INIT_ARGS* args) {
    if (nullptr == args) {
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

    if (!get_connect_info || !free_connect_info || !session_begin || !session_update || !session_end) {
        EXLOGE("invalid init args(2).\n");
        return false;
    }

    if (nullptr == args->cfg) {
        EXLOGE("invalid init args(3).\n");
        return false;
    }

    if (!_on_init(args)) {
        EXLOGE("invalid init args(4).\n");
        return false;
    }

    return true;
}
