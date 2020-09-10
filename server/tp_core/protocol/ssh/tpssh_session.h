#ifndef __TPSSH_SESSION_H__
#define __TPSSH_SESSION_H__

#include <ex.h>
#include <libssh/libssh.h>
#include <libssh/server.h>

#include "tpssh_srv.h"
#include "tpssh_cli.h"
#include "tpssh_channel.h"

#define TEST_SSH_SESSION_000000


class SshProxy;

class SshSession {
public:
    SshSession(SshProxy *owner, const char *client_ip, uint16_t client_port);

    virtual ~SshSession();

    bool start(ssh_session sess_tp2cli);

    // 返回会话是否还在运行中，当会话中与客户端和服务端的连接都断开了，则视作会话结束了。
    // SshProxy实例每一秒钟会检查一次会话，如果已经结束了，则删除本会话实例。
    bool is_running() { return m_running; }

    void on_error(int error_code);

    SshClientSide *connect_to_host(
            const std::string &host_ip,
            uint16_t host_port,
            const std::string &acc_name,
            uint32_t &rv
    );

    SshClientSide *tp2srv() { return m_tp2srv; }

    SshServerSide *tp2cli() { return m_tp2cli; }

//    void tp2cli_end(SshServerSide *tp2cli);
//
//    void tp2srv_end(SshClientSide *tp2srv);

    void check_noop_timeout(ex_u32 t_now, ex_u32 timeout);

    void check_channels();

    // save record cache into file. be called per 5 seconds.
    void save_record();

    void keep_alive();

    void update_last_access_time() { m_last_access_timestamp = static_cast<uint32_t>(time(nullptr)); }
    // void update_last_access_time(uint32_t last_time) { m_last_access_timestamp = last_time; }

    const std::string &sid() { return m_sid; };

    const std::string &dbg_name() { return m_dbg_name; }

    // --------------------------
    // 通道管理
    // --------------------------
    bool make_channel_pair(ssh_channel ch_tp2cli, ssh_channel ch_tp2srv);

    SshChannelPair *get_channel_pair(ssh_channel ch);

//    void remove_channel(ssh_channel ch);


private:
    SshProxy *m_owner;
    std::string m_dbg_name;
    std::string m_sid;

    std::string m_client_ip;
    uint16_t m_client_port;

    ExThreadLock m_lock;

    bool m_running;
    SshServerSide *m_tp2cli;
    SshClientSide *m_tp2srv;

    // 此会话的最后数据通过时间
    uint32_t m_last_access_timestamp;

    TPChannelPairs m_pairs;
    // 用于快速查找
    channel_map m_channel_map;
};


#endif // __TPSSH_SESSION_H__
