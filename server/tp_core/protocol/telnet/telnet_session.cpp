#include "telnet_session.h"
#include "telnet_proxy.h"
#include "tpp_env.h"
#include <teleport_const.h>

#define TELNET_IAC        0xFF
#define TELNET_DONT        0xFE
#define TELNET_DO        0xFD
#define TELNET_WONT        0xFC
#define TELNET_WILL        0xFB
#define TELNET_SB        0xFA
#define TELNET_SE        0xF0


TelnetSession::TelnetSession(TelnetProxy *proxy) :
        m_proxy(proxy),
        m_conn_info(NULL) {
    m_state = TP_SESS_STAT_RUNNING;
    m_startup_win_size_recorded = false;
    m_db_id = 0;
    m_is_relay = false;
    m_is_closed = false;
    m_first_client_pkg = true;
    m_last_access_timestamp = (ex_u32) time(NULL);

    m_win_width = 0;
    m_win_height = 0;

    m_is_putty_mode = false;

    m_username_sent = false;
    m_password_sent = false;

    m_conn_server = new TelnetConn(this, false);
    m_conn_client = new TelnetConn(this, true);

    m_status = s_client_connect;

    m_client_addr = "unknown-ip";
}

TelnetSession::~TelnetSession() {
    delete m_conn_client;
    delete m_conn_server;

    if (NULL != m_conn_info) {
        g_telnet_env.free_connect_info(m_conn_info);
    }

    EXLOGD("[telnet] session destroy.\n");
}

void TelnetSession::save_record() {
    m_rec.save_record();
}

void TelnetSession::check_noop_timeout(ex_u32 t_now, ex_u32 timeout) {
    if (t_now == 0)
        EXLOGW("[telnet] try close session by kill.\n");
    else if (t_now - m_last_access_timestamp > timeout)
        EXLOGW("[telnet] try close session by timeout.\n");
    if (t_now == 0 || t_now - m_last_access_timestamp > timeout)
        _do_close(TP_SESS_STAT_END);
}

void TelnetSession::_session_error(int err_code) {
    int db_id = 0;
    if (!g_telnet_env.session_begin(m_conn_info, &db_id) || db_id == 0) {
        EXLOGE("[telnet] can not write session error to database.\n");
        return;
    }

    g_telnet_env.session_end(m_sid.c_str(), db_id, err_code);
}

bool TelnetSession::_on_session_begin() {
    if (!g_telnet_env.session_begin(m_conn_info, &m_db_id)) {
        EXLOGE("[telnet] can not save to database, session begin failed.\n");
        return false;
    }

    if (!g_telnet_env.session_update(m_db_id, m_conn_info->protocol_sub_type, TP_SESS_STAT_STARTED)) {
        EXLOGE("[telnet] can not update state, session begin failed.\n");
        return false;
    }

    m_rec.begin(g_telnet_env.replay_path.c_str(), L"tp-telnet", m_db_id, m_conn_info);

    return true;
}

bool TelnetSession::_on_session_end() {
    if (m_db_id > 0) {
        // 如果会话过程中没有发生错误，则将其状态改为结束，否则记录下错误值
        if (m_state == TP_SESS_STAT_RUNNING || m_state == TP_SESS_STAT_STARTED)
            m_state = TP_SESS_STAT_END;

        EXLOGD("[telnet] session end with code: %d\n", m_state);
        g_telnet_env.session_end(m_sid.c_str(), m_db_id, m_state);
    }

    return true;
}

uv_loop_t *TelnetSession::get_loop(void) {
    return m_proxy->get_loop();
}

void TelnetSession::close(int err_code) {
    _do_close(err_code);
}

void TelnetSession::do_next(TelnetConn *conn, sess_state status) {
    if (m_status < s_close)
        m_status = status;

    do_next(conn);
}

void TelnetSession::do_next(TelnetConn *conn) {
    sess_state new_status;
    ASSERT(m_status != s_dead);

    switch (m_status) {
        case s_noop:
            return;

        case s_client_connect:
            new_status = _do_client_connect(conn);
            break;

        case s_negotiation_with_client:
            new_status = _do_negotiation_with_client(conn);
            break;
        case s_server_connected:
            new_status = _do_server_connected();
            break;
        case s_relay:
            new_status = _do_relay(conn);
            break;

        case s_close:
            new_status = _do_close(m_state);
            break;
        case s_closing:
            new_status = _do_check_closing();
            break;
        case s_all_conn_closed:
            new_status = s_dead;
            break;
        default:
            //UNREACHABLE();
            return;
    }

    m_status = new_status;

    if (m_status == s_dead) {
        EXLOGW("[telnet] try to remove session.\n");
        _on_session_end();
        m_is_closed = true;
        m_proxy->clean_session();
    }
}

/*
关闭一个session的策略：
1. 两个TelnetConn实例各自关闭自身，当自己关闭完成时，调用session的 on_conn_closed();
2. session->on_conn_closed()被调用时，检查两个conn是否都关闭完成了，如果都关闭了，标记本session为已关闭.
*/

sess_state TelnetSession::_do_close(int state) {
    EXLOGD("[telnet]   _do_close(). m_status=%d\n", m_status);
    if (m_status >= s_close)
        return m_status;

    if (state == TP_SESS_STAT_END) {
        if (!m_is_relay)
            m_state = TP_SESS_STAT_ERR_INTERNAL;
        else
            m_state = state;
    } else {
        if (!m_is_relay)
            _session_error(state);
        m_state = state;
    }
    EXLOGV("[telnet] close session.\n");
    EXLOGD("[telnet]   _do_close(), conn_client::state=%d, conn_server:state=%d\n", m_conn_client->state(),
           m_conn_server->state());

    m_conn_client->close();
    m_conn_server->close();
    m_status = s_closing;
    return m_status;
}

sess_state TelnetSession::_do_check_closing() {
    if (m_conn_client->state() == TELNET_CONN_STATE_FREE && m_conn_server->state() == TELNET_CONN_STATE_FREE)
        return s_all_conn_closed;
    else
        return s_closing;
}

void TelnetSession::on_conn_close() {
    EXLOGD("[telnet]   on_conn_close(), conn_client::state=%d, conn_server:state=%d\n", m_conn_client->state(),
           m_conn_server->state());
    if (m_conn_client->state() == TELNET_CONN_STATE_FREE && m_conn_server->state() == TELNET_CONN_STATE_FREE) {
        m_status = s_all_conn_closed;
        do_next(m_conn_client);
    }
}

sess_state TelnetSession::_do_client_connect(TelnetConn *conn) {
    // putty会率先发第一个包，SecureCRT会通过脚本发第一个包
    return _do_negotiation_with_client(conn);
}

sess_state TelnetSession::_do_negotiation_with_client(TelnetConn *conn) {
    if (NULL == conn)
        return s_negotiation_with_client;

    if (0 == conn->data().size())
        return s_negotiation_with_client;

    if (m_first_client_pkg) {
        m_first_client_pkg = false;

        MemBuffer &mbuf = conn->data();

        if (mbuf.size() > 14 && 0 == memcmp(mbuf.data(), "session:", 8)) {
            m_is_putty_mode = false;

            mbuf.pop(8);
            for (; mbuf.size() > 0;) {
                if (mbuf.data()[mbuf.size() - 1] == 0x0a || mbuf.data()[mbuf.size() - 1] == 0x0d)
                    mbuf.size(mbuf.size() - 1);
                else
                    break;
            }

            mbuf.append((ex_u8 *) "\x00", 1);
            m_sid = (char *) mbuf.data();

            return _do_connect_server();
        } else {
            m_is_putty_mode = true;
        }
    }

    MemBuffer mbuf_msg;
    mbuf_msg.reserve(128);
    MemStream ms_msg(mbuf_msg);

    MemBuffer mbuf_resp;
    mbuf_resp.reserve(conn->data().size());
    MemStream ms_resp(mbuf_resp);

    MemBuffer mbuf_sub;
    mbuf_sub.reserve(128);
    MemStream ms_sub(mbuf_sub);


    MemStream s(conn->data());
    ex_u8 ch = 0;
    ex_u8 ch_cmd = 0;
    for (; s.left() > 0;) {
        ch = s.get_u8();
        if (ch == TELNET_IAC) {
            if (s.left() < 2)
                return _do_close(TP_SESS_STAT_ERR_BAD_PKG);

            if (mbuf_sub.size() > 0) {
                // 已经得到一个sub negotiation，在处理新的数据前，先处理掉旧的
                EXLOG_BIN(mbuf_sub.data(), mbuf_sub.size(), "-=-=-=-=-=");
                ms_sub.reset();
            }

            ch_cmd = s.get_u8();
            if (ch_cmd == TELNET_SB) {
                // SUB NEGOTIATION，变长数据，以 FF F0 结束
                bool have_SE = false;
                ex_u8 ch_sub = 0;
                for (; s.left() > 0;) {
                    ch_sub = s.get_u8();
                    if (ch_sub == TELNET_IAC) {
                        if (s.left() > 0) {
                            if (s.get_u8() == TELNET_SE) {
                                have_SE = true;
                                break;
                            } else
                                return _do_close(TP_SESS_STAT_ERR_BAD_PKG);
                        }
                    } else {
                        ms_sub.put_u8(ch_sub);
                    }
                }

                if (!have_SE)
                    return _do_close(TP_SESS_STAT_ERR_BAD_PKG);
            } else if (ch_cmd == TELNET_DONT) {
                ms_resp.put_u8(TELNET_IAC);
                ms_resp.put_u8(TELNET_WONT);
                ms_resp.put_u8(s.get_u8());
            } else if (ch_cmd == TELNET_DO) {
                ms_resp.put_u8(TELNET_IAC);
                ms_resp.put_u8(TELNET_WILL);
                ms_resp.put_u8(s.get_u8());
            } else if (ch_cmd == TELNET_WONT) {
                ms_resp.put_u8(TELNET_IAC);
                ms_resp.put_u8(TELNET_DONT);
                ms_resp.put_u8(s.get_u8());
            } else if (ch_cmd == TELNET_WILL) {
                ms_resp.put_u8(TELNET_IAC);
                ms_resp.put_u8(TELNET_DO);
                ms_resp.put_u8(s.get_u8());
            } else {
                s.skip(1);
            }
        } else {
            ms_msg.put_u8(ch);
        }
    }

    conn->data().empty();

    if (mbuf_resp.size() > 0) {
        conn->send(mbuf_resp.data(), mbuf_resp.size());
    }

    if (mbuf_sub.size() == 5) {
        // 客户端窗口大小
        if (0x1f == mbuf_sub.data()[0]) {
            ms_sub.rewind();
            ms_sub.skip(1);
            m_win_width = ms_sub.get_u16_be();
            m_win_height = ms_sub.get_u16_be();

            ms_resp.reset();
            ms_resp.put_u8(TELNET_IAC);
            ms_resp.put_u8(TELNET_SB);
            ms_resp.put_bin(mbuf_sub.data(), 5);
            ms_resp.put_u8(TELNET_IAC);
            ms_resp.put_u8(TELNET_SE);
            conn->send(mbuf_resp.data(), mbuf_resp.size());
        }

        // 发送下列指令，putty才会将登陆用户名发过来（也就是SID）
        ex_u8 _d[] = {
                0xff, 0xfa, 0x27, 0x01,
                0x03, 0x53, 0x46, 0x55, 0x54, 0x4c, 0x4e, 0x54, 0x56, 0x45, 0x52, 0x03, 0x53, 0x46, 0x55, 0x54,
                0x4c, 0x4e, 0x54, 0x4d, 0x4f, 0x44, 0x45, 0xff, 0xf0
        };
        m_conn_client->send((ex_u8 *) _d, sizeof(_d));
        return s_negotiation_with_client;
    }

    if (mbuf_sub.size() > 8) {
        // 可能含有putty的登录用户名信息（就是SID啦）
        if (0 == memcmp(mbuf_sub.data(), "\x27\x00\x00\x55\x53\x45\x52\x01", 8))    // '...USER.
        {
            mbuf_sub.pop(8);
            for (; mbuf_sub.size() > 0;) {
                if (mbuf_sub.data()[mbuf_sub.size() - 1] == 0x0a || mbuf_sub.data()[mbuf_sub.size() - 1] == 0x0d)
                    mbuf_sub.size(mbuf_sub.size() - 1);
                else
                    break;
            }

            mbuf_sub.append((ex_u8 *) "\x00", 1);
            m_sid = (char *) mbuf_sub.data();
        }
    }

    if (m_sid.length() > 0) {
        return _do_connect_server();
    }

    return s_negotiation_with_client;
}

sess_state TelnetSession::_do_connect_server() {

    EXLOGW("[telnet] session-id: [%s]\n", m_sid.c_str());

    m_conn_info = g_telnet_env.get_connect_info(m_sid.c_str());

    if (NULL == m_conn_info) {
        EXLOGE("[telnet] no such session: %s\n", m_sid.c_str());
        return _do_close(TP_SESS_STAT_ERR_SESSION);
    } else {
        m_conn_ip = m_conn_info->conn_ip;
        m_conn_port = m_conn_info->conn_port;
        m_acc_name = m_conn_info->acc_username;
        m_acc_secret = m_conn_info->acc_secret;
        m_username_prompt = m_conn_info->username_prompt;
        m_password_prompt = m_conn_info->password_prompt;

        if (m_conn_info->protocol_type != TP_PROTOCOL_TYPE_TELNET) {
            EXLOGE("[telnet] session '%s' is not for TELNET.\n", m_sid.c_str());
            return _do_close(TP_SESS_STAT_ERR_SESSION);
        }

        if (m_conn_info->auth_type != TP_AUTH_TYPE_NONE) {
            if (m_acc_name.length() == 0 || m_username_prompt.length() == 0 || m_acc_secret.length() == 0 ||
                m_password_prompt.length() == 0) {
                EXLOGE("[telnet] invalid connection param.\n");
                return _do_close(TP_SESS_STAT_ERR_SESSION);
            }
        }

    }

    // try to connect to real server.
    m_conn_server->connect(m_conn_ip.c_str(), m_conn_port);

// 	ex_astr szmsg = "Connect to ";
// 	szmsg += m_conn_ip;
// 	szmsg += "\r\n";
// 	m_conn_client->send((ex_u8*)szmsg.c_str(), szmsg.length());


    return s_noop;
}

sess_state TelnetSession::_do_server_connected() {
    m_conn_client->data().empty();
    m_conn_server->data().empty();

    m_status = s_relay;

    // 如果没有设置用户名/密码，则无需登录
    if (m_conn_info->auth_type == TP_AUTH_TYPE_NONE) {
        m_username_sent = true;
        m_password_sent = true;
    }

    m_is_relay = true;
    EXLOGW("[telnet] enter relay mode.\n");

    if (!_on_session_begin()) {
        return _do_close(TP_SESS_STAT_ERR_INTERNAL);
    }

    int w = 50;
    if (m_win_width != 0) {
#ifdef EX_OS_WIN32
        int w = min(m_win_width, 128);
#else
        int w = std::min(m_win_width, 128);
#endif
        m_startup_win_size_recorded = true;
        m_rec.record_win_size_startup(m_win_width, m_win_height);
    }

    char buf[512] = {0};

    const char *auth_mode = NULL;
    if (m_conn_info->auth_type == TP_AUTH_TYPE_PASSWORD)
        auth_mode = "password";
    else if (m_conn_info->auth_type == TP_AUTH_TYPE_NONE)
        auth_mode = "nothing";
    else
        auth_mode = "unknown";

    ex_astr line(w, '=');

    snprintf(buf, sizeof(buf),
             "\r\n"\
        "%s\r\n"\
        "Teleport TELNET Bastion Server...\r\n"\
        "  - teleport to %s:%d\r\n"\
        "  - authroized by %s\r\n"\
        "%s\r\n"\
        "\r\n\r\n",
             line.c_str(),
             m_conn_ip.c_str(),
             m_conn_port, auth_mode,
             line.c_str()
    );

    m_conn_client->send((ex_u8 *) buf, strlen(buf));

    if (m_is_putty_mode) {
        if (m_conn_info->auth_type != TP_AUTH_TYPE_NONE) {
            ex_astr login_info = "login: ";
            login_info += m_conn_info->acc_username;
            login_info += "\r\n";
            m_conn_client->send((ex_u8 *) login_info.c_str(), login_info.length());
            m_rec.record(TS_RECORD_TYPE_TELNET_DATA, (ex_u8 *) login_info.c_str(), login_info.length());
        }

        ex_u8 _d[] = "\xff\xfb\x1f\xff\xfb\x20\xff\xfb\x18\xff\xfb\x27\xff\xfd\x01\xff\xfb\x03\xff\xfd\x03";
        m_conn_server->send(_d, sizeof(_d) - 1);
    }

    return s_relay;
}

sess_state TelnetSession::_do_relay(TelnetConn *conn) {
    m_last_access_timestamp = (ex_u32) time(NULL);

    TelnetSession *_this = conn->session();
    bool is_processed = false;

    if (conn->is_server_side()) {
//         EXLOG_BIN(m_conn_client->data().data(), m_conn_client->data().size(), "<-- client:");

        // 收到了客户端发来的数据
        if (_this->m_is_putty_mode && !_this->m_username_sent) {
            if (_this->_putty_replace_username(m_conn_client, m_conn_server)) {
                //_this->m_username_sent = true;
                is_processed = true;
            }
        }

        if (is_processed) {
            m_conn_client->data().empty();
            return s_relay;
        }

        if (_this->_parse_win_size(m_conn_client)) {
            if (!m_startup_win_size_recorded) {
                m_rec.record_win_size_startup(m_win_width, m_win_height);
                m_startup_win_size_recorded = true;
            }
            m_rec.record_win_size_change(m_win_width, m_win_height);
        }

        m_conn_server->send(m_conn_client->data().data(), m_conn_client->data().size());
        m_conn_client->data().empty();
    } else {
//         EXLOG_BIN(m_conn_server->data().data(), m_conn_server->data().size(), "--> server:");

        // 收到了服务端返回的数据
        if (m_conn_server->data().data()[0] != TELNET_IAC)
            m_rec.record(TS_RECORD_TYPE_TELNET_DATA, m_conn_server->data().data(), m_conn_server->data().size());

        if (!_this->m_username_sent && _this->m_acc_name.length() > 0) {
            if (_this->_parse_find_and_send(m_conn_server, m_conn_client, _this->m_username_prompt.c_str(),
                                            _this->m_acc_name.c_str())) {
//				_this->m_username_sent = true;
                is_processed = true;
            }
        }
        if (!_this->m_password_sent && _this->m_password_prompt.length() > 0) {
            if (_this->_parse_find_and_send(m_conn_server, m_conn_client, _this->m_password_prompt.c_str(),
                                            _this->m_acc_secret.c_str())) {
                _this->m_username_sent = true;
                _this->m_password_sent = true;
                _this->m_username_sent = true;
                is_processed = true;
            }
        }

        if (is_processed) {
            m_conn_server->data().empty();
            return s_relay;
        }

        m_conn_client->send(m_conn_server->data().data(), m_conn_server->data().size());
        m_conn_server->data().empty();
    }

    return s_relay;
}

bool TelnetSession::_parse_find_and_send(TelnetConn *conn_recv, TelnetConn *conn_remote, const char *find,
                                         const char *send) {
//     EXLOGV("find prompt and send: [%s] => [%s]\n", find, send);
//     EXLOG_BIN(conn_recv->data().data(), conn_recv->data().size(), "find prompt in data:");

    size_t find_len = strlen(find);
    size_t send_len = strlen(send);
    if (0 == find_len || 0 == send_len || conn_recv->data().size() < find_len) {
        return false;
    }

    int find_range = conn_recv->data().size() - find_len;
    for (int i = 0; i <= find_range; ++i) {
        if (0 == memcmp(conn_recv->data().data() + i, find, find_len)) {
            conn_remote->send(conn_recv->data().data(), conn_recv->data().size());
            conn_recv->data().empty();

            MemBuffer mbuf_msg;
            mbuf_msg.reserve(128);
            mbuf_msg.append((ex_u8 *) send, send_len);
            mbuf_msg.append((ex_u8 *) "\x0d\x0a", 2);
//             EXLOG_BIN(mbuf_msg.data(), mbuf_msg.size(), "find prompt and send:");
            conn_recv->send(mbuf_msg.data(), mbuf_msg.size());
            return true;
        }
    }

#if 0
    MemBuffer mbuf_msg;
    mbuf_msg.reserve(128);
    MemStream ms_msg(mbuf_msg);

    MemStream s(conn_recv->data());
    ex_u8 ch = 0;
    ex_u8 ch_cmd = 0;
    for (; s.left() > 0;)
    {
        ch = s.get_u8();
        if (ch == TELNET_IAC)
        {
            if (s.left() < 2)
                return false;

            ch_cmd = s.get_u8();
            if (ch_cmd == TELNET_SB)
            {
                // SUB NEGOTIATION，变长数据，以 FF F0 结束
                bool have_SE = false;
                ex_u8 ch_sub = 0;
                for (; s.left() > 0;)
                {
                    ch_sub = s.get_u8();
                    if (ch_sub == TELNET_IAC)
                    {
                        if (s.left() > 0)
                        {
                            if (s.get_u8() == TELNET_SE)
                            {
                                have_SE = true;
                                break;
                            }
                            else
                                return false;
                        }
                    }
                }

                if (!have_SE)
                    return false;
            }
            else
            {
                s.skip(1);
            }
        }
        else
        {
            ms_msg.put_u8(ch);
        }
    }

    if (mbuf_msg.size() < find_len)
        return false;

    int find_range = mbuf_msg.size() - find_len;
    for (int i = 0; i < find_range; ++i)
    {
        if (0 == memcmp(mbuf_msg.data() + i, find, find_len))
        {
            conn_remote->send(conn_recv->data().data(), conn_recv->data().size());
            conn_recv->data().empty();

            mbuf_msg.empty();
            mbuf_msg.append((ex_u8*)send, send_len);
            mbuf_msg.append((ex_u8*)"\x0d\x0a", 2);
            conn_recv->send(mbuf_msg.data(), mbuf_msg.size());
            return true;
        }
    }
#endif

    return false;
}

bool TelnetSession::_putty_replace_username(TelnetConn *conn_recv, TelnetConn *conn_remote) {
    bool replaced = false;

    MemBuffer mbuf_msg;
    mbuf_msg.reserve(128);
    MemStream ms_msg(mbuf_msg);

    MemStream s(conn_recv->data());
    ex_u8 ch = 0;
    ex_u8 ch_cmd = 0;
    for (; s.left() > 0;) {
        ch = s.get_u8();
        if (ch == TELNET_IAC) {
            if (s.left() < 2)
                return false;

            ch_cmd = s.get_u8();
            if (ch_cmd == TELNET_SB) {
                size_t _begin = s.offset();
                size_t _end = 0;


                // SUB NEGOTIATION，变长数据，以 FF F0 结束
                bool have_SE = false;
                ex_u8 ch_sub = 0;
                for (; s.left() > 0;) {
                    _end = s.offset();
                    ch_sub = s.get_u8();
                    if (ch_sub == TELNET_IAC) {
                        if (s.left() > 0) {
                            if (s.get_u8() == TELNET_SE) {
                                have_SE = true;
                                break;
                            } else
                                return false;
                        }
                    }
                }

                if (!have_SE)
                    return false;

                size_t len = _end - _begin;
                if (len <= 8 || 0 != memcmp("\x27\x00\x00\x55\x53\x45\x52\x01", conn_recv->data().data() + _begin, 8)) {
                    ms_msg.put_u8(TELNET_IAC);
                    ms_msg.put_u8(TELNET_SB);
                    ms_msg.put_bin(conn_recv->data().data() + _begin, len);
                    ms_msg.put_u8(TELNET_IAC);
                    ms_msg.put_u8(TELNET_SE);
                    continue;
                }

                // 到这里就找到了客户端发来的用户名，我们将其替换为真实的远程账号。

                ms_msg.put_u8(TELNET_IAC);
                ms_msg.put_u8(TELNET_SB);
                ms_msg.put_bin((ex_u8 *) "\x27\x00\x00\x55\x53\x45\x52\x01", 8);

                ms_msg.put_bin((ex_u8 *) m_acc_name.c_str(), m_acc_name.length());

                ms_msg.put_u8(TELNET_IAC);
                ms_msg.put_u8(TELNET_SE);

                replaced = true;
            } else {
                ms_msg.put_u8(ch);
                ms_msg.put_u8(ch_cmd);
                ms_msg.put_u8(s.get_u8());
            }
        } else {
            ms_msg.put_u8(ch);
        }
    }

    if (replaced) {
        conn_remote->send(mbuf_msg.data(), mbuf_msg.size());
        return true;
    }

    return false;
}

bool TelnetSession::_parse_win_size(TelnetConn *conn) {
    if (conn->data().size() < 9)
        return false;
    if (conn->data().data()[0] != TELNET_IAC)
        return false;

    bool is_sub = false;
    MemStream s(conn->data());
    for (; s.left() > 0;) {
        if (s.get_u8() == TELNET_IAC) {
            if (s.left() < 2)
                return false;

            if (s.get_u8() == TELNET_SB) {
                size_t _begin = s.offset();
                size_t _end = 0;

                // SUB NEGOTIATION，变长数据，以 TELNET_IAC+TELNET_SE (FF F0) 结束
                bool have_SE = false;
                ex_u8 ch_sub = 0;
                for (; s.left() > 0;) {
                    _end = s.offset();
                    if (s.get_u8() == TELNET_IAC) {
                        if (s.left() > 0) {
                            if (s.get_u8() == TELNET_SE) {
                                have_SE = true;
                                break;
                            } else
                                return false;
                        }
                    }
                }

                if (!have_SE)
                    return false;

                size_t len = _end - _begin;
                if (len == 5 && 0x1F == conn->data().data()[_begin]) {
                    s.seek(_begin + 1);
                    m_win_width = s.get_u16_be();
                    m_win_height = s.get_u16_be();
                    return true;
                }
            }
        }
    }

    return false;
}
