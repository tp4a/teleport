#ifndef __SSH_CHANNEL_PAIR_H__
#define __SSH_CHANNEL_PAIR_H__

#include <ex.h>
#include <libssh/libssh.h>

#include "ssh_recorder.h"

class SshSession;

class SshCommand {
public:
    SshCommand();

    virtual ~SshCommand();

    void reset() {
        m_cmd.clear();
        m_pos = m_cmd.end();
        _dump("reset");
    }

    std::string str() {
        if (empty())
            return "";
        else
            return std::string(m_cmd.begin(), m_cmd.end());
    }

    bool empty() const {
        return m_cmd.empty();
    }

    void erase_to_end() {
        // 删除光标到行尾的字符串
        m_cmd.erase(m_pos, m_cmd.end());
        m_pos = m_cmd.end();
        _dump("erase to end");
    }

    void erase_to_begin() {
        // 删除从开始到光标处的字符串
        m_cmd.erase(m_cmd.begin(), m_pos);
        m_pos = m_cmd.begin();
        _dump("erase to begin");
    }

    void cursor_move_right(int count) {
        // 光标右移
        for (int i = 0; i < count; ++i) {
            if (m_pos != m_cmd.end())
                m_pos++;
            else
                break;
        }
        _dump("cursor move right");
    }

    void cursor_move_left(int count) {
        // 光标左移
        for (int i = 0; i < count; ++i) {
            if (m_pos != m_cmd.begin())
                m_pos--;
            else
                break;
        }
        _dump("cursor move left");
    }

    void erase_chars(int count) {
        // 删除指定数量的字符
        for (int i = 0; i < count; ++i) {
            if (m_pos != m_cmd.end())
                m_pos = m_cmd.erase(m_pos);
            else
                break;
        }
        _dump("erase char");
    }

    void insert_white_space(int count) {
        // 插入指定数量的空白字符
        for (int i = 0; i < count; ++i) {
            m_pos = m_cmd.insert(m_pos, ' ');
        }
        _dump("insert white space");
    }

    void replace(uint8_t ch) {
        if (m_pos != m_cmd.end()) {
            m_pos = m_cmd.erase(m_pos);
            m_pos = m_cmd.insert(m_pos, ch);
            m_pos++;
        }
        else {
            m_cmd.push_back(ch);
            //cmd_char_pos = cmd_char_list.end();
            m_pos = m_cmd.end();
        }
        _dump("replace char");
    }

    void insert(const uint8_t* data, int len) {
        for (int i = 0; i < len; ++i) {
            if (m_pos == m_cmd.end()) {
                m_cmd.push_back(data[i]);
                m_pos = m_cmd.end();
            }
            else {
                m_pos = m_cmd.insert(m_pos, data[i]);
                m_pos++;
            }
        }
        _dump("insert chars");
    }

    void insert(uint8_t ch) {
        if (m_pos == m_cmd.end()) {
            m_cmd.push_back(ch);
            m_pos = m_cmd.end();
        }
        else {
            m_pos = m_cmd.insert(m_pos, ch);
            m_pos++;
        }
        _dump("insert char");
    }

protected:
    void _dump(const char* msg);

private:
    std::list<char> m_cmd;
    std::list<char>::iterator m_pos;
};

// SSH命令解析，有限状态机状态值
enum PTY_STAT {
    PTY_STAT_NORMAL_WAIT_PROMPT = 0,
    PTY_STAT_MULTI_CMD_WAIT_PROMPT,
    PTY_STAT_TAB_PRESSED,
    PTY_STAT_TAB_WAIT_PROMPT,
    PTY_STAT_WAIT_CLIENT_INPUT,
    PTY_STAT_EXEC_MULTI_LINE_CMD,
    PTY_STAT_WAIT_SERVER_ECHO,
};


class SshChannelPair {
    friend class SshSession;

public:
    SshChannelPair(SshSession* owner, uint32_t dbg_id, ssh_channel rsc_tp2cli, ssh_channel rsc_tp2srv);

    virtual ~SshChannelPair();

    void process_pty_data_from_client(const uint8_t* data, uint32_t len);

    void process_pty_data_from_server(const uint8_t* data, uint32_t len);


    void process_sftp_command(ssh_channel ch, const uint8_t* data, uint32_t len);

    // when client<->server channel created, start to record.
    bool record_begin(const TPP_CONNECT_INFO* conn_info);

    // stop record because channel closed.
    void record_end();

protected:
    bool _contains_cmd_prompt(const uint8_t* data, uint32_t len);

protected:
    SshSession* m_owner;
    uint32_t m_dbg_id;
    std::string m_dbg_name;

    int type;       // TS_SSH_CHANNEL_TYPE_SHELL or TS_SSH_CHANNEL_TYPE_SFTP
    int win_width;  // window width, in char count.

    ssh_channel rsc_tp2cli;
    ssh_channel rsc_tp2srv;

    uint32_t last_access_timestamp;

    TppSshRec rec;
    int db_id;
    int state;

    bool is_first_server_data;
    bool need_close;

    SshCommand m_cmd;

    PTY_STAT m_pty_stat;
};

typedef std::list<SshChannelPair*> TPChannelPairs;
typedef std::map<ssh_channel, SshChannelPair*> channel_map;

#endif //__SSH_CHANNEL_PAIR_H__
