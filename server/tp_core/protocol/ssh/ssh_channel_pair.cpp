#include "ssh_channel_pair.h"
#include "ssh_session.h"
#include "tpp_env.h"

#include <teleport_const.h>

SshChannelPair::SshChannelPair(SshSession* _owner, uint32_t dbg_id, ssh_channel _rsc_tp2cli, ssh_channel _rsc_tp2srv) :
        m_owner(_owner),
        m_dbg_id(dbg_id),
        type(TS_SSH_CHANNEL_TYPE_UNKNOWN),
        win_width(0),
        rsc_tp2cli(_rsc_tp2cli),
        rsc_tp2srv(_rsc_tp2srv)
{
    last_access_timestamp = (ex_u32)time(nullptr);
    ex_strformat(m_dbg_name, 128, "%s-%d", m_owner->dbg_name().c_str(), dbg_id);

    state = TP_SESS_STAT_RUNNING;
    db_id = 0;

    is_first_server_data = true;
    need_close = false;

    m_pty_stat = PTY_STAT_NORMAL_WAIT_PROMPT;
}

SshChannelPair::~SshChannelPair() = default;

void SshChannelPair::process_pty_data_from_client(const uint8_t* data, uint32_t len)
{
    if (data == nullptr || len == 0)
        return;

    if (len == 1)
    {
        if (data[0] == 0x0d)
        {
            // 0x0d 回车键
            if (!m_cmd.empty())
            {
                // EXLOGD("[%s] CMD=[%s]\n", m_owner->dbg_name().c_str(), m_cmd.str().c_str());
                rec.record_command(0, m_cmd.str());
            }
            m_cmd.reset();
            m_pty_stat = PTY_STAT_NORMAL_WAIT_PROMPT;
            // EXLOGD("------ turn to PTY_STAT_NORMAL_WAIT_PROMPT, input single RETURN.\n");
            return;
        }
        else if (data[0] == 0x03)
        {
            // 0x03 Ctrl-C
            m_pty_stat = PTY_STAT_NORMAL_WAIT_PROMPT;
            // EXLOGD("------ turn to PTY_STAT_NORMAL_WAIT_PROMPT, input Ctrl-C.\n");
            return;
        }
        else if (data[0] == 0x09)
        {
            // 0x09 TAB键
            if (m_pty_stat == PTY_STAT_WAIT_CLIENT_INPUT || m_pty_stat == PTY_STAT_TAB_WAIT_PROMPT || m_pty_stat == PTY_STAT_TAB_PRESSED)
            {
                m_pty_stat = PTY_STAT_TAB_PRESSED;
                // EXLOGD("------ turn to PTY_STAT_TAB_PRESSED, input TAB.\n");
                return;
            }
        }
        else if (data[0] == 0x7f)
        {
            // 7f backspace 回删键
            m_pty_stat = PTY_STAT_WAIT_SERVER_ECHO;
            // EXLOGD("------ turn to PTY_STAT_WAIT_SERVER_ECHO, input BACKSPACE.\n");
            return;
        }
    }
    else if (len == 3)
    {
        if (data[0] == 0x1b && data[1] == 0x5b && (data[2] == 0x41 || data[2] == 0x42 || data[2] == 0x43 || data[2] == 0x44))
        {
            // 1b 5b 41 (上箭头)
            // 1b 5b 42 (下箭头)
            // 1b 5b 43 (右箭头)
            // 1b 5b 44 (左箭头)
            m_pty_stat = PTY_STAT_WAIT_SERVER_ECHO;
            // EXLOGD("------ turn to PTY_STAT_WAIT_SERVER_ECHO, input ARROW.\n");
            return;
        }
    }
    else if (len == 4)
    {
        if (data[0] == 0x1b && data[1] == 0x5b && data[2] == 0x33 && data[3] == 0x7e)
        {
            // 1b 5b 33 7e (删除一个字符)
            m_pty_stat = PTY_STAT_WAIT_SERVER_ECHO;
            // EXLOGD("------ turn to PTY_STAT_WAIT_SERVER_ECHO, input DEL.\n");
            return;
        }
    }

    if (len >= 512)
    {
        if (m_pty_stat != PTY_STAT_EXEC_MULTI_LINE_CMD)
        {
            m_pty_stat = PTY_STAT_NORMAL_WAIT_PROMPT;
            // EXLOGD("------ turn to PTY_STAT_NORMAL_WAIT_PROMPT, input too large.\n");
        }
        return;
    }

    int return_count = 0;
    bool valid_input = true;

    int offset = 0;
    int last_return_pos = 0;
    for (; offset < len;)
    {
        uint8_t ch = data[offset];

        switch (ch)
        {
        case 0x1b:
            if (offset + 1 < len)
            {
                if (data[offset + 1] == 0x5b)
                {
                    valid_input = false;
                    break;
                }
            }

            break;
        case 0x0d:return_count++;
            last_return_pos = offset;
            break;
        default:break;
        }

        if (!valid_input)
            break;

        offset++;
    }

    if (!valid_input)
    {
        if (m_pty_stat != PTY_STAT_EXEC_MULTI_LINE_CMD)
        {
            m_pty_stat = PTY_STAT_NORMAL_WAIT_PROMPT;
            // EXLOGD("------ turn to PTY_STAT_NORMAL_WAIT_PROMPT, input invalid.\n");
        }
        return;
    }

    if (return_count > 0)
    {
        std::string tmp_cmd((const char*)data, last_return_pos + 1);
        EXLOGD("[%s] Paste CMD=[%s]\n", m_owner->dbg_name().c_str(), tmp_cmd.c_str());
        rec.record_command(1, tmp_cmd);

        m_pty_stat = PTY_STAT_EXEC_MULTI_LINE_CMD;
        // EXLOGD("------ turn to PTY_STAT_EXEC_MULTI_LINE_CMD, maybe paste.\n");
    }
    else
    {
        m_pty_stat = PTY_STAT_WAIT_SERVER_ECHO;
        // EXLOGD("------ turn to PTY_STAT_WAIT_SERVER_ECHO, input something.\n");
    }
}

void SshChannelPair::process_pty_data_from_server(const uint8_t* data, uint32_t len)
{
    if (data == nullptr || len == 0)
        return;

    bool contains_prompt = false;
    if (m_pty_stat == PTY_STAT_NORMAL_WAIT_PROMPT
        || m_pty_stat == PTY_STAT_TAB_WAIT_PROMPT
        || m_pty_stat == PTY_STAT_MULTI_CMD_WAIT_PROMPT
        || m_pty_stat == PTY_STAT_WAIT_SERVER_ECHO)
    {
        if (_contains_cmd_prompt(data, len))
        {
            contains_prompt = true;

            if (m_pty_stat == PTY_STAT_NORMAL_WAIT_PROMPT)
            {
                // EXLOGD("------ turn to PTY_STAT_WAIT_CLIENT_INPUT, recv prompt after exec.\n");
                m_pty_stat = PTY_STAT_WAIT_CLIENT_INPUT;
                return;
            }
            else if (m_pty_stat == PTY_STAT_TAB_WAIT_PROMPT)
            {
                // EXLOGD("------ turn to PTY_STAT_WAIT_CLIENT_INPUT, recv prompt after TAB.\n");
                m_pty_stat = PTY_STAT_WAIT_CLIENT_INPUT;
                return;
            }
            else if (m_pty_stat == PTY_STAT_MULTI_CMD_WAIT_PROMPT)
            {
                // EXLOGD("------ turn to PTY_STAT_MULTI_CMD_WAIT_PROMPT, recv prompt while multi-exec.\n");
                m_pty_stat = PTY_STAT_EXEC_MULTI_LINE_CMD;
                return;
            }
            else if (m_pty_stat == PTY_STAT_WAIT_SERVER_ECHO)
            {
                // EXLOGD("------ turn to PTY_STAT_WAIT_CLIENT_INPUT, recv prompt while wait echo.\n");
                m_pty_stat = PTY_STAT_WAIT_CLIENT_INPUT;
                m_cmd.reset();
                return;
            }
        }
    }

    if (!contains_prompt)
    {
        if (m_pty_stat == PTY_STAT_NORMAL_WAIT_PROMPT
            || m_pty_stat == PTY_STAT_TAB_WAIT_PROMPT
            || m_pty_stat == PTY_STAT_MULTI_CMD_WAIT_PROMPT)
        {
            return;
        }
    }

    if (!(
            m_pty_stat == PTY_STAT_WAIT_SERVER_ECHO
            || m_pty_stat == PTY_STAT_EXEC_MULTI_LINE_CMD
            || m_pty_stat == PTY_STAT_MULTI_CMD_WAIT_PROMPT
            || m_pty_stat == PTY_STAT_TAB_WAIT_PROMPT
            || m_pty_stat == PTY_STAT_TAB_PRESSED
    ))
    {
        // EXLOGD("------ keep PTY_STAT, recv but not in ECHO or multi-cmd mode.\n");
        return;
    }

    if (len > 512)
    {
        // EXLOGD("------ keep PTY_STAT, recv too large.\n");
        return;
    }

    // 处理输入回显，合成最终的命令行字符串
    // https://www.systutorials.com/docs/linux/man/4-console_codes/
    int offset = 0;
    bool esc_mode = false;
    int esc_arg = 0;
    for (; offset < len;)
    {
        uint8_t ch = data[offset];

        if (esc_mode)
        {
            switch (ch)
            {
            case '0':
            case '1':
            case '2':
            case '3':
            case '4':
            case '5':
            case '6':
            case '7':
            case '8':
            case '9':esc_arg = esc_arg * 10 + (ch - '0');
                break;

            case 0x3f:
            case ';':
            case '>':m_cmd.reset();
                return;

            case 0x4b:
            {    // 'K'
                if (0 == esc_arg)
                {
                    // 删除光标到行尾的字符串
                    m_cmd.erase_to_end();
                }
                else if (1 == esc_arg)
                {
                    // 删除从开始到光标处的字符串
                    m_cmd.erase_to_begin();
                }
                else if (2 == esc_arg)
                {
                    // 删除整行
                    m_cmd.reset();
                }

                esc_mode = false;
                break;
            }
            case 0x43:
            {// ^[C
                // 光标右移
                if (esc_arg == 0)
                    esc_arg = 1;
                m_cmd.cursor_move_right(esc_arg);
                esc_mode = false;
                break;
            }
            case 0x44:
            { // ^[D
                // 光标左移
                if (esc_arg == 0)
                    esc_arg = 1;
                m_cmd.cursor_move_left(esc_arg);
                esc_mode = false;
                break;
            }

            case 0x50:
            {
                // 'P' 删除指定数量的字符
                if (esc_arg == 0)
                    esc_arg = 1;
                m_cmd.erase_chars(esc_arg);
                esc_mode = false;
                break;
            }

            case 0x40:
            {    // '@' 插入指定数量的空白字符
                if (esc_arg == 0)
                    esc_arg = 1;
                m_cmd.insert_white_space(esc_arg);
                esc_mode = false;
                break;
            }

            default:esc_mode = false;
                break;
            }

            offset++;
            continue;
        }

        switch (ch)
        {
        case 0x07:
            // 响铃
            break;
        case 0x08:
        {
            // 光标左移
            m_cmd.cursor_move_left(1);
            break;
        }
        case 0x1b:
        {
            if (offset + 1 < len)
            {
                if (data[offset + 1] == 0x5b)
                {
                    esc_mode = true;
                    esc_arg = 0;

                    offset += 1;
                }
            }

            break;
        }
        case 0x0d:
        {
            if (offset + 1 < len && data[offset + 1] == 0x0a)
            {
                if (m_pty_stat == PTY_STAT_EXEC_MULTI_LINE_CMD)
                {
                    if (!m_cmd.empty())
                        EXLOGD("[%s] one of multi-cmd, CMD=[%s]\n", m_owner->dbg_name().c_str(), m_cmd.str().c_str());
                    m_cmd.reset();

                    m_pty_stat = PTY_STAT_MULTI_CMD_WAIT_PROMPT;
                    // EXLOGD("------ turn to PTY_STAT_MULTI_CMD_WAIT_PROMPT, recv 0x0d0a after multi-exec.\n");

                    if (_contains_cmd_prompt(data, len))
                    {
                        m_pty_stat = PTY_STAT_EXEC_MULTI_LINE_CMD;
                        // EXLOGD("------ turn to PTY_STAT_EXEC_MULTI_LINE_CMD, recv prompt after multi-exec.\n");
                    }
                }
                else if (m_pty_stat == PTY_STAT_TAB_PRESSED)
                {
                    m_pty_stat = PTY_STAT_TAB_WAIT_PROMPT;
                    // EXLOGD("------ turn to PTY_STAT_TAB_WAIT_PROMPT, recv 0d0a after TAB pressed.\n");
                }
                return;
            }

            break;
        }
        default:m_cmd.replace(ch);
            if (m_pty_stat == PTY_STAT_WAIT_SERVER_ECHO)
            {
                m_pty_stat = PTY_STAT_WAIT_CLIENT_INPUT;
                // EXLOGD("------ turn to PTY_STAT_WAIT_CLIENT_INPUT, recv something.\n");
            }
            break;
        }

        offset++;
    }

    if (m_pty_stat == PTY_STAT_MULTI_CMD_WAIT_PROMPT && contains_prompt)
    {
        m_pty_stat = PTY_STAT_EXEC_MULTI_LINE_CMD;
        // EXLOGD("------ turn to PTY_STAT_EXEC_MULTI_LINE_CMD, recv prompt.\n");
    }
}

bool SshChannelPair::_contains_cmd_prompt(const uint8_t* data, uint32_t len)
{
    // 正常情况下，收到的服务端数据（一包数据不会太大，可以考虑限定在512字节范围内），从后向前查找 0x07，它的位置
    // 应该位于倒数256字节范围内（这之后的数据可能是命令行提示符的内容了，不会太长的）。继续向前找，应该能够找到正
    // 序为 1b 5d 30/31/32/33 3b ... 直到刚才的 07。满足这样格式的，99%可能处于命令行模式了，还有1%可能是Mac
    // 下，每次执行命令后会立刻返回两个提示符用于用户界面改变标题，然后才是命令执行的输出，最后再输出一次提示符。
    // 格式：   1b 5d Ps 3b Pt 07
    //      Ps = 0    ====>  '0'=0x30,    Change Icon Name and Window Title to Pt.
    //      Ps = 1    ====>  '1'=0x31,    Change Icon Name to Pt.
    //      Ps = 2    ====>  '2'=0x32,    Change Window Title to Pt.
    //      Ps = 3    ====>  '3'=0x33,    Set X property on top-level window.
    //      Ps = 其他的值，我们就不care了。
    // https://invisible-island.net/xterm/ctlseqs/ctlseqs.html#h2-Operating-System-Controls

    // 服务端返回大量数据时，一一解析会导致操作变慢，需要有方法避免
    // 暂时的做法是数据长度超过一定阈值时，跳过解析判断，这种情况下不会是回显数据
    // 例如 cat 一个大文件，数据包一次可能会超过16KB。
    if (len >= 2048)
        return false;

    bool found_0x07 = false;
    bool found_0x3b = false;
    bool found_Ps = false;
    bool found_0x5d = false;

    int offset = static_cast<int>(len) - 1;

    for (int i = 0; offset >= 0; i++)
    {
        if (i > 256)
            return false;

        if (found_0x5d)
            return (data[offset] == 0x1b);

        if (found_Ps)
        {
            found_0x5d = (data[offset] == 0x5d);
            if (!found_0x5d)
                return false;
            offset--;
            continue;
        }

        if (found_0x3b)
        {
            found_Ps = (data[offset] == 0x30 || data[offset] == 0x31 || data[offset] == 0x32);
            if (!found_Ps)
                return false;
            offset--;
            continue;
        }

        if (!found_0x07)
        {
            found_0x07 = (data[offset] == 0x07);
            offset--;
            continue;
        }

        found_0x3b = (data[offset] == 0x3b);
        offset--;
    }

    return false;
}

void SshChannelPair::process_sftp_command(ssh_channel ch, const uint8_t* data, uint32_t len)
{
    // SFTP protocol: https://tools.ietf.org/html/draft-ietf-secsh-filexfer-13
    // EXLOG_BIN(data, len, "[sftp] client channel data");

    // TODO: 根据客户端的请求和服务端的返回，可以进一步判断用户是如何操作文件的，比如读、写等等，以及操作的结果是成功还是失败。
    // 记录格式：  time-offset,flag,action,result,file-path,[file-path]
    //   其中，flag目前总是为0，可以忽略（为保证与ssh-cmd格式一致），time-offset/action/result 都是数字
    //        file-path是被操作的对象，规格为 长度:实际内容，例如，  13:/root/abc.txt

    // 暂时仅处理客户端的请求
    if (ch != rsc_tp2cli)
        return;

    if (len < 9)
        return;

    int pkg_len = (int)((data[0] << 24) | (data[1] << 16) | (data[2] << 8) | data[3]);
    if (pkg_len + 4 != len)
        return;

    ex_u8 sftp_cmd = data[4];

    if (sftp_cmd == 0x01)
    {
        // 0x01 = 1 = SSH_FXP_INIT
        rec.record_command(0, "SFTP INITIALIZE\r\n");
        EXLOGD("[sftp-%s] SFTP INITIALIZE\n", m_owner->dbg_name().c_str());
        return;
    }

    // 需要的数据至少14字节
    // uint32 + byte + uint32 + (uint32 + char + ...)
    // pkg_len + cmd + req_id + string( length + content...)
    if (len < 14)
        return;

    ex_u8* str1_ptr = (ex_u8*)data + 9;
    int str1_len = (int)((str1_ptr[0] << 24) | (str1_ptr[1] << 16) | (str1_ptr[2] << 8) | str1_ptr[3]);
    // 	if (str1_len + 9 != pkg_len)
    // 		return;
    ex_u8* str2_ptr = nullptr;// (ex_u8*)data + 13;
    int str2_len = 0;// (int)((data[9] << 24) | (data[10] << 16) | (data[11] << 8) | data[12]);


    switch (sftp_cmd)
    {
    case 0x03:
        // 0x03 = 3 = SSH_FXP_OPEN
        EXLOGD("[sftp-%s] SSH_FXP_OPEN\n", m_owner->dbg_name().c_str());
        break;
    case 0x0b:
        // 0x0b = 11 = SSH_FXP_OPENDIR
        EXLOGD("[sftp-%s] SSH_FXP_OPENDIR\n", m_owner->dbg_name().c_str());
        break;
    case 0x0d:
        // 0x0d = 13 = SSH_FXP_REMOVE
        EXLOGD("[sftp-%s] SSH_FXP_REMOVE\n", m_owner->dbg_name().c_str());
        break;
    case 0x0e:
        // 0x0e = 14 = SSH_FXP_MKDIR
        EXLOGD("[sftp-%s] SSH_FXP_MKDIR\n", m_owner->dbg_name().c_str());
        break;
    case 0x0f:
        // 0x0f = 15 = SSH_FXP_RMDIR
        EXLOGD("[sftp-%s] SSH_FXP_RMDIR\n", m_owner->dbg_name().c_str());
        break;
    case 0x12:
        // 0x12 = 18 = SSH_FXP_RENAME
        // rename操作数据中包含两个字符串
        str2_ptr = str1_ptr + str1_len + 4;
        str2_len = (int)((str2_ptr[0] << 24) | (str2_ptr[1] << 16) | (str2_ptr[2] << 8) | str2_ptr[3]);
        EXLOGD("[sftp-%s] SSH_FXP_RENAME\n", m_owner->dbg_name().c_str());
        break;
    case 0x15:
        // 0x15 = 21 = SSH_FXP_LINK
        // link操作数据中包含两个字符串，前者是新的链接文件名，后者是现有被链接的文件名
        str2_ptr = str1_ptr + str1_len + 4;
        str2_len = (int)((str2_ptr[0] << 24) | (str2_ptr[1] << 16) | (str2_ptr[2] << 8) | str2_ptr[3]);
        EXLOGD("[sftp-%s] SSH_FXP_LINK\n", m_owner->dbg_name().c_str());
        break;
    default:return;
    }

    int total_len = 5 + str1_len + 4;
    if (str2_len > 0)
        total_len += str2_len + 4;
    if (total_len > pkg_len)
        return;

    char msg[2048] = {0};
    if (str2_len == 0)
    {
        ex_astr str1((char*)((ex_u8*)data + 13), str1_len);
        ex_strformat(msg, 2048, "%d,%d,%s", sftp_cmd, 0, str1.c_str());
    }
    else
    {
        ex_astr str1((char*)(str1_ptr + 4), str1_len);
        ex_astr str2((char*)(str2_ptr + 4), str2_len);
        ex_strformat(msg, 2048, "%d,%d,%s:%s", sftp_cmd, 0, str1.c_str(), str2.c_str());
    }

    EXLOGD("[sftp-%s] %s\n", m_owner->dbg_name().c_str(), msg);
    rec.record_command(0, msg);
}

bool SshChannelPair::record_begin(const TPP_CONNECT_INFO* conn_info)
{
#ifndef TEST_SSH_SESSION_000000
    if (!g_ssh_env.session_begin(conn_info, &db_id))
    {
        EXLOGE("[%s] can not save to database, channel begin failed.\n", m_dbg_name.c_str());
        return false;
    }
    // else {
    //     channel_id = db_id;
    //     // EXLOGD("[ssh] [channel:%d] channel begin\n", cp->channel_id);
    // }


    if (!g_ssh_env.session_update(db_id, conn_info->protocol_sub_type, TP_SESS_STAT_STARTED))
    {
        EXLOGE("[%s] can not update state, cannel begin failed.\n", m_dbg_name.c_str());
        return false;
    }


    rec.begin(g_ssh_env.replay_path.c_str(), L"tp-ssh", db_id, conn_info);
#endif
    return true;
}

void SshChannelPair::record_end()
{
#ifndef TEST_SSH_SESSION_000000
    if (db_id > 0)
    {
        EXLOGD("[%s] channel end with code: %d\n", m_dbg_name.c_str(), state);

        // 如果会话过程中没有发生错误，则将其状态改为结束，否则记录下错误值
        if (state == TP_SESS_STAT_RUNNING || state == TP_SESS_STAT_STARTED)
            state = TP_SESS_STAT_END;

        g_ssh_env.session_end(m_owner->sid().c_str(), db_id, state);

        db_id = 0;
    }
    else
    {
        EXLOGD("[%s] when channel end, no db-id.\n", m_dbg_name.c_str());
    }
#endif
}


// ==================================================
// SshCommand
// ==================================================

SshCommand::SshCommand()
{
    m_cmd.clear();
    m_pos = m_cmd.begin();
}

SshCommand::~SshCommand() = default;

void SshCommand::_dump(const char* msg)
{
    // EXLOGD("CMD-BUFFER: %s [%s]\n", msg, str().c_str());
}
