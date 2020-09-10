#ifndef __TPSSH__CHANNEL_H__
#define __TPSSH__CHANNEL_H__

#include <map>
#include <list>

#include <ex.h>
#include <libssh/libssh.h>

#include "tpssh_rec.h"

class SshServerSide;

class SshClientSide;

class SshSession;

class SshChannelPair {
    friend class SshServerSide;

    friend class SshClientSide;

    friend class SshSession;

public:
    SshChannelPair(
            SshSession *owner,
            //ssh_session session_tp2cli,
            ssh_channel channel_tp2cli,
            //ssh_session session_tp2srv,
            ssh_channel channel_tp2srv
    );

    virtual ~SshChannelPair();

    // when client<->server channel created, start to record.
    bool record_begin();

    // stop record because channel closed.
    void record_end();

    void update_session_state(int protocol_sub_type, int state);

    void close();

    void process_ssh_command(ssh_channel ch, const ex_u8 *data, uint32_t len);

    void process_sftp_command(ssh_channel ch, const ex_u8 *data, uint32_t len);

protected:
    SshSession *m_owner;
    int type;    // TS_SSH_CHANNEL_TYPE_SHELL or TS_SSH_CHANNEL_TYPE_SFTP

    //ssh_session session_tp2cli;
    ssh_channel channel_tp2cli;
    //ssh_session session_tp2srv;
    ssh_channel channel_tp2srv;

    TppSshRec rec;
    ex_u32 last_access_timestamp;

    int state;
    int db_id;
    int channel_id;     // for debug only.

    int win_width;      // window width, in char count.

    bool is_first_server_data;
    bool need_close;

    // for ssh command record cache.
    bool server_ready;
    bool maybe_cmd;
    bool process_srv;
    bool client_single_char;
    std::list<char> cmd_char_list;
    std::list<char>::iterator cmd_char_pos;
};

typedef std::list<SshChannelPair *> TPChannelPairs;
typedef std::map<ssh_channel, SshChannelPair *> channel_map;

#endif // __TPSSH__CHANNEL_H__
