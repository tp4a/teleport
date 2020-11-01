#ifndef __TP_TPP_MGR_H__
#define __TP_TPP_MGR_H__

#include "../common/protocol_interface.h"

#include <ex.h>

typedef struct TPP_LIB {
    TPP_LIB() :
            dylib(nullptr),
            init(nullptr),
            start(nullptr),
            stop(nullptr),
            timer(nullptr),
            command(nullptr) {
    }

    ~TPP_LIB() {
        if (nullptr != dylib)
            ex_dlclose(dylib);
        dylib = nullptr;
    }

    EX_DYLIB_HANDLE dylib;
    TPP_INIT_FUNC init;
    TPP_START_FUNC start;
    TPP_STOP_FUNC stop;
    TPP_TIMER_FUNC timer;
    TPP_COMMAND_FUNC command;
} TPP_LIB;

typedef std::list<TPP_LIB*> tpp_libs;

class TppManager {
public:
    TppManager() = default;

    ~TppManager() {
        for (auto lib : m_libs) {
            delete lib;
        }
        m_libs.clear();
    }

    bool load_tpp(const ex_wstr& lib_file);

    void stop_all();

    void timer(); // 大约1秒调用一次

    int count() {
        return m_libs.size();
    }

    void set_runtime_config(const ex_astr& sp);

    void kill_sessions(const ex_astr& sp);

private:
    tpp_libs m_libs;
};

extern TppManager g_tpp_mgr;

#endif // __TP_TPP_MGR_H__
