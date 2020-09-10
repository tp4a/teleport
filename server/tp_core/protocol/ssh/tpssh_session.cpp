#include "tpssh_session.h"
#include "tpssh_proxy.h"
#include <teleport_const.h>

SshSession::SshSession(SshProxy *owner, const char *client_ip, uint16_t client_port) :
        m_owner(owner),
        m_client_ip(client_ip),
        m_client_port(client_port),
        m_running(true),
        m_tp2cli(nullptr),
        m_tp2srv(nullptr) {
    ex_strformat(m_dbg_name, 128, "C%s:%d", client_ip, client_port);
    m_last_access_timestamp = 0;
}

SshSession::~SshSession() {
    if (m_tp2cli) {
        EXLOGE("[ssh-%s] when destroy, tp<->client not finished yet.\n", m_dbg_name.c_str());
    }
    if (m_tp2srv) {
        EXLOGE("[ssh-%s] when destroy, tp<->server not finished yet.\n", m_dbg_name.c_str());
    }
}

bool SshSession::start(ssh_session sess_tp2cli) {
    if (m_dbg_name.empty())
        return false;

    std::string thread_name;
    ex_strformat(thread_name, 128, "ssh-thread-tp2cli-%s", m_dbg_name.c_str());
    m_tp2cli = new SshServerSide(this, sess_tp2cli, thread_name);
    if (!m_tp2cli) {
        m_running = false;
        return false;
    }

    return m_tp2cli->start();
}

SshClientSide *SshSession::connect_to_host(
        const std::string &host_ip,
        uint16_t host_port,
        const std::string &acc_name,
        uint32_t &rv
) {
    if (m_tp2srv) {
        delete m_tp2srv;
    }

    std::string thread_name;
    ex_strformat(thread_name, 128, "ssh-thread-tp2srv-S%s:%d", host_ip.c_str(), host_port);
    m_tp2srv = new SshClientSide(this, host_ip, host_port, acc_name, thread_name);
    if (!m_tp2srv) {
        EXLOGE("[ssh-%s] create tp2srv instance failed.\n", m_dbg_name.c_str());
        // TODO: set last error.
        on_error(TP_SESS_STAT_ERR_INTERNAL);
        return nullptr;
    }

    rv = m_tp2srv->connect();
    if (rv != TP_SESS_STAT_RUNNING) {
        delete m_tp2srv;
        m_tp2srv = nullptr;
    }

    return m_tp2srv;
}

void SshSession::on_error(int error_code) {
#ifndef TEST_SSH_SESSION_000000
    int db_id = 0;
    if (!g_ssh_env.session_begin(m_conn_info, &db_id) || db_id == 0) {
        EXLOGE("[ssh-%s] can not write session error to database.\n", m_dbg_name.c_str());
        return;
    }

    g_ssh_env.session_end(m_sid.c_str(), db_id, err_code);
#endif
}

void SshSession::save_record() {
    ExThreadSmartLock locker(m_lock);

    auto it = m_pairs.begin();
    for (; it != m_pairs.end(); ++it) {
        (*it)->rec.save_record();
    }
}

void SshSession::keep_alive() {
//    m_need_send_keepalive = true;
//     EXLOGD("[ssh] keep-alive.\n");
//     if(m_srv_session)
//         ssh_send_keepalive(m_srv_session);
//     if (m_session)
//         ssh_send_keepalive(m_session);
}

void SshSession::check_noop_timeout(ex_u32 t_now, ex_u32 timeout) {
    ExThreadSmartLock locker(m_lock);

    bool need_stop = false;

    if (t_now == 0) {
        EXLOGW("[ssh-%s] try close channel by kill.\n", m_dbg_name.c_str());
        need_stop = true;
    }
    else if (m_last_access_timestamp != 0 && t_now - m_last_access_timestamp > timeout) {
        if (!m_channel_map.empty()) {
            EXLOGW("[ssh-%s] try close channel by timeout.\n", m_dbg_name.c_str());
            need_stop = true;
        }
    }

    if (need_stop) {
        if (m_tp2cli)
            m_tp2cli->stop();
        if (m_tp2srv)
            m_tp2srv->stop();
    }
}

void SshSession::check_channels() {
    // 尚未准备好，不用进行检查
    if (m_last_access_timestamp == 0)
        return;

    ExThreadSmartLock locker(m_lock);

    auto it = m_pairs.begin();
    for (; it != m_pairs.end();) {
        ssh_channel ch_tp2cli = (*it)->channel_tp2cli;
        ssh_channel ch_tp2srv = (*it)->channel_tp2srv;

        // 判断是否需要关闭通道：
        // 如果通道一侧打开过，但现在已经关闭了，则需要关闭另外一侧。
        bool need_close = (*it)->need_close;
        if (!need_close) {
            if (ch_tp2cli != nullptr && ssh_channel_is_closed(ch_tp2cli))
                need_close = true;
            if (ch_tp2srv != nullptr && ssh_channel_is_closed(ch_tp2srv))
                need_close = true;
        }

        if (need_close) {
            if (ch_tp2cli != nullptr) {
                if (!ssh_channel_is_closed(ch_tp2cli))
                    ssh_channel_close(ch_tp2cli);
                m_tp2cli->channel_closed(ch_tp2cli);
                ssh_channel_free(ch_tp2cli);
                auto it_map = m_channel_map.find(ch_tp2cli);
                if (it_map != m_channel_map.end())
                    m_channel_map.erase(it_map);
                ch_tp2cli = nullptr;
            }

            if (ch_tp2srv != nullptr) {
                if (!ssh_channel_is_closed(ch_tp2srv))
                    ssh_channel_close(ch_tp2srv);
                m_tp2srv->channel_closed(ch_tp2srv);
                ssh_channel_free(ch_tp2srv);
                auto it_map = m_channel_map.find(ch_tp2srv);
                if (it_map != m_channel_map.end())
                    m_channel_map.erase(it_map);
                ch_tp2srv = nullptr;
            }
        }

        if (ch_tp2cli == nullptr && ch_tp2srv == nullptr) {
            (*it)->record_end();
            delete(*it);
            m_pairs.erase(it++);
        }
        else {
            ++it;
        }
    }

    // 是否要关闭会话（当两端的通道均关闭时，会话也就结束了，由SshProxy中的定时任务来释放此会话实例）
    if (m_pairs.empty()) {
        EXLOGV("[ssh-%s] all channels closed, close this session.\n", m_dbg_name.c_str());

        // todo: 不要直接delete，而是先判断一个线程是否在运行的标记，当线程结束，才删除，否则会导致崩溃。
        delete m_tp2srv;
        delete m_tp2cli;
        m_tp2srv = nullptr;
        m_tp2cli = nullptr;
        m_running = false;
    }
}

// --------------------------
// 通道管理
// --------------------------
bool SshSession::make_channel_pair(ssh_channel ch_tp2cli, ssh_channel ch_tp2srv) {
    ExThreadSmartLock locker(m_lock);

    auto it = m_channel_map.find(ch_tp2cli);
    if (it != m_channel_map.end())
        return false;
    it = m_channel_map.find(ch_tp2srv);
    if (it != m_channel_map.end())
        return false;

    auto _pair = new SshChannelPair(this, ch_tp2cli, ch_tp2srv);
    m_pairs.push_back(_pair);

    m_channel_map.insert(std::make_pair(ch_tp2cli, _pair));
    m_channel_map.insert(std::make_pair(ch_tp2srv, _pair));

    return true;
}

SshChannelPair *SshSession::get_channel_pair(ssh_channel ch) {
    ExThreadSmartLock locker(m_lock);

    auto it = m_channel_map.find(ch);
    if (it == m_channel_map.end())
        return nullptr;

    it->second->last_access_timestamp = static_cast<uint32_t>(time(nullptr));
    return it->second;
}
