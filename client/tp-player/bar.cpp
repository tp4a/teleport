#include "bar.h"
#include <QPainter>
#include <QDebug>


#define FONT_SIZE_DEFAULT           12
#define TIME_STR_PIXEL_SIZE         16
#define TEXT_COLOR                  QColor(255,255,255,153)

typedef struct RES_MAP {
    RES_ID id;
    const char* name;
}RES_MAP;

static RES_MAP img_res[res__max] = {
    {res_bg_left, "bg-left"},
    {res_bg_mid, "bg-mid"},
    {res_bg_right, "bg-right"},
    {res_bs_left, "btn-left"},
    {res_bs_mid, "btn-mid"},
    {res_bs_right, "btn-right"},
    {res_bsh_left, "btnsel-left"},
    {res_bsh_mid, "btnsel-mid"},
    {res_bsh_right, "btnsel-right"},
    {res_pbh_left, "prgbarh-left"},
    {res_pbh_mid, "prgbarh-mid"},
    {res_pb_mid, "prgbar-mid"},
    {res_pb_right, "prgbar-right"},
//    {res_pp, "prgpt"},
//    {res_pph, "prgpt-hover"},
    {res_cb, "select"},
    {res_cbh, "selected"},
//    {res_play, "play"},
//    {res_play_hover, "play-hover"},
//    {res_pause, "pause"},
//    {res_pause_hover, "pause-hover"}
};

typedef struct SPEED_MAP {
    int id;
    const char* title;
}SPEED_MAP;

static SPEED_MAP speed[speed_count] = {
    {speed_1x, "1x"},
    {speed_2x, "2x"},
    {speed_4x, "4x"},
    {speed_8x, "8x"},
    {speed_16x, "16x"}
};

static inline int min(int a, int b){
    return a < b ? a : b;
}

static inline int max(int a, int b){
    return a > b ? a : b;
}

Bar::Bar() {
    m_img_ready = false;
    m_width = 0;
    m_height = 0;
    m_str_total_time = "00:00";
    m_str_passed_time = "00:00";
    m_str_passed_time_last_draw = "--:--";

    m_percent = 0;
    m_percent_last_draw = -1;

    m_play_hover = false;
    m_playing = true; // 0=play, 2=pause
    m_speed_selected = speed_1x;
    m_speed_hover = speed_count;    // speed_count=no-hover
    m_skip_selected = true;
}

Bar::~Bar() {

}

bool Bar::init(QWidget* owner) {
    m_owner = owner;

    // 加载所需的图像资源
    int i = 0;
    for(i = 0; i < res__max; ++i) {
        QString name;
        name.sprintf(":/tp-player/res/bar/%s.png", img_res[i].name);
        if(!m_res[i].load(name))
            return false;
    }

    // 无需合成的图像
    if(!m_img_btn_play[play_running][widget_normal].load(":/tp-player/res/bar/play.png")
            || !m_img_btn_play[play_running][widget_hover].load(":/tp-player/res/bar/play-hover.png")
            || !m_img_btn_play[play_paused][widget_normal].load(":/tp-player/res/bar/pause.png")
            || !m_img_btn_play[play_paused][widget_hover].load(":/tp-player/res/bar/pause-hover.png")
            || !m_img_progress_pointer[widget_normal].load(":/tp-player/res/bar/prgpt.png")
            || !m_img_progress_pointer[widget_hover].load(":/tp-player/res/bar/prgpt-hover.png")
            ) {
        return false;
    }

    m_height = m_res[res_bg_left].height();

    return true;
}

void Bar::start(uint32_t total_ms, int width) {
    bool is_first_start = (m_width == 0);
    m_width = width;

    m_total_ms = total_ms;
    _ms_to_str(total_ms, m_str_total_time);


    // 首次播放时，调整位置左右居中，距窗口顶部10点处。
    if(is_first_start) {
        _init_imgages();
        QRect rc = m_owner->rect();
        m_rc = QRect(0, 0, m_width, m_height);
        m_rc.moveTo((rc.width() - m_width)/2, 10);
        //m_rc.moveTo(10, 600);
        qDebug("m_rc (%d,%d)-(%d,%d)", m_rc.left(), m_rc.top(), m_rc.right(), m_rc.bottom());
    }
}

void Bar::end() {
    if(m_passed_ms != m_total_ms)
        update_passed_time(m_total_ms);
}

void Bar::_init_imgages() {
    m_img_bg = QPixmap(m_width, m_height);
    m_img_bg.fill(Qt::transparent);//用透明色填充
    QPainter pp(&m_img_bg);
    QFont font = pp.font();

    // 合成背景图像
    {

        pp.drawPixmap(0, 0, m_res[res_bg_left].width(), m_res[res_bg_left].height(), m_res[res_bg_left]);
        pp.drawPixmap(m_res[res_bg_left].width(), 0, m_width - m_res[res_bg_left].width() - m_res[res_bg_right].width(), m_height, m_res[res_bg_mid]);
        pp.drawPixmap(m_width-m_res[res_bg_right].width(), 0, m_res[res_bg_right].width(), m_height, m_res[res_bg_right]);
    }

    {
        m_rc_btn_play = QRect(15, (m_height - m_img_btn_play[play_running][widget_normal].height())/2 , m_img_btn_play[play_running][widget_normal].width(), m_img_btn_play[play_running][widget_normal].height());
    }

    // 合成速度按钮
    {
        int w = 42, h = m_res[res_bs_left].height();
        QRect rc(0, 0, w, h);
        QPixmap btn[widget__max];

        // 未选中状态
        btn[widget_normal] = QPixmap(w, h);
        btn[widget_normal].fill(Qt::transparent);//用透明色填充
        QPainter pn(&btn[widget_normal]);
        pn.drawPixmap(0, 0, m_res[res_bs_left].width(), m_res[res_bs_left].height(), m_res[res_bs_left]);
        pn.drawPixmap(m_res[res_bs_left].width(), 0, w - m_res[res_bs_left].width() - m_res[res_bs_right].width(), h, m_res[res_bs_mid]);
        pn.drawPixmap(w-m_res[res_bs_right].width(), 0, m_res[res_bs_right].width(), h, m_res[res_bs_right]);
        // 选中状态
        btn[widget_hover] = QPixmap(w, h);
        btn[widget_hover].fill(Qt::transparent);//用透明色填充
        QPainter ph(&btn[widget_hover]);
        ph.drawPixmap(0, 0, m_res[res_bsh_left].width(), m_res[res_bsh_left].height(), m_res[res_bsh_left]);
        ph.drawPixmap(m_res[res_bsh_left].width(), 0, w - m_res[res_bsh_left].width() - m_res[res_bsh_right].width(), h, m_res[res_bsh_mid]);
        ph.drawPixmap(w-m_res[res_bsh_right].width(), 0, m_res[res_bsh_right].width(), h, m_res[res_bsh_right]);

        for(int i = 0; i < widget__max; ++i) {
            for(int j = 0; j < speed_count; ++j) {
                m_img_btn_speed[j][i] = QPixmap(w, h);
                m_img_btn_speed[j][i].fill(Qt::transparent);
                QPainter ps(&m_img_btn_speed[j][i]);
                ps.setPen(TEXT_COLOR);
                QFont font = ps.font();
                font.setFamily("consolas");
                font.setPixelSize(FONT_SIZE_DEFAULT);
                ps.setFont(font);
                ps.drawPixmap(0, 0, w, h, btn[i]);
                ps.drawText(rc, Qt::AlignCenter, speed[j].title);
            }
        }
    }

    // 合成跳过无操作选项
    {
        // 计算显示跳过无操作选项字符串的宽高
        font.setFamily("微软雅黑");
        font.setBold(false);
        font.setPixelSize(FONT_SIZE_DEFAULT);
        pp.setFont(font);
        QFontMetrics fm = pp.fontMetrics();

        {
            int h = fm.height();
            if(h < m_res[res_cb].height())
                h = m_res[res_cb].height();
            m_rc_skip = QRect(0, 0, fm.width("无操作则跳过")+8+m_res[res_cb].width(), h);
        }

        int w = m_rc_skip.width();
        int h = m_rc_skip.height();
        int chkbox_top = (m_rc_skip.height() - m_res[res_cb].height()) / 2;
        int text_left = m_res[res_cb].width() + 8;
        int text_top = (m_rc_skip.height() - fm.height()) / 2;

        {
            m_img_skip[widget_normal] = QPixmap(w,h);
            m_img_skip[widget_normal].fill(Qt::transparent);
            QPainter ps(&m_img_skip[widget_normal]);
            ps.setPen(TEXT_COLOR);
            QFont font = ps.font();
            font.setFamily("微软雅黑");
            font.setPixelSize(FONT_SIZE_DEFAULT);
            ps.setFont(font);
            ps.drawPixmap(0, chkbox_top, m_res[res_cb].width(), m_res[res_cb].height(), m_res[res_cb]);
            ps.drawText(QRect(text_left, text_top, w-text_left, h-text_top), Qt::AlignCenter, "无操作则跳过");
        }

        {
            m_img_skip[widget_hover] = QPixmap(w,h);
            m_img_skip[widget_hover].fill(Qt::transparent);
            QPainter ps(&m_img_skip[widget_hover]);
            ps.setPen(TEXT_COLOR);
            QFont font = ps.font();
            font.setFamily("微软雅黑");
            font.setPixelSize(FONT_SIZE_DEFAULT);
            ps.setFont(font);
            ps.drawPixmap(0, chkbox_top, m_res[res_cbh].width(), m_res[res_cbh].height(), m_res[res_cbh]);
            ps.drawText(QRect(text_left, text_top, w-text_left, h-text_top), Qt::AlignCenter, "无操作则跳过");
        }
    }

    {
        // 计算显示时间所需的宽高
        font.setFamily("consolas");
        font.setBold(true);
        font.setPixelSize(TIME_STR_PIXEL_SIZE);
        pp.setFont(font);
        {
            QFontMetrics fm = pp.fontMetrics();
            m_rc_time_passed = QRect(0, 0, fm.width("00:00:00"), fm.height());
            m_rc_time_total = m_rc_time_passed;
        }

        m_img_time_total = QPixmap(m_rc_time_total.width(), m_rc_time_total.height());
        m_img_time_total.fill(Qt::transparent);
        QPainter pp(&m_img_time_total);
        pp.setPen(TEXT_COLOR);
        QFont font = pp.font();
        font.setFamily("consolas");
        font.setBold(true);
        font.setPixelSize(TIME_STR_PIXEL_SIZE);
        pp.setFont(font);
        pp.drawText(m_rc_time_total, Qt::AlignLeft, m_str_total_time);

        // 定位时间字符串的位置
        m_rc_time_passed.moveTo(15+m_img_btn_play[play_running][widget_normal].width()+10, 18);
        m_rc_time_total.moveTo(m_width - 15 - m_rc_time_total.width(), 18);

        int prog_width = m_rc_time_total.left() - 10 - 10 - m_rc_time_passed.right();// - m_img_progress_pointer[widget_normal].width();
        int prog_height = max(m_res[res_pbh_left].height(), m_img_progress_pointer->height());
        m_rc_progress = QRect(0, 0, prog_width, prog_height);
        m_rc_progress.moveTo(m_rc_time_passed.right() + 10, m_rc_time_passed.height() + (m_rc_time_passed.height() - prog_height)/2);

        qDebug("prog: %d,%d  w:%d,h:%d", m_rc_progress.left(), m_rc_progress.top(), prog_width, prog_height);
    }


    // 定位速度按钮
    {
        int left = m_rc_time_passed.right() + 10;
        int top = m_rc_time_passed.bottom() + 8;
        for(int i = 0; i < speed_count; i++) {
            m_rc_btn_speed[i] = QRect(left, top, m_img_btn_speed[i][widget_normal].width(), m_img_btn_speed[i][widget_normal].height());
            left += m_img_btn_speed[i][widget_normal].width() + 8;
        }
    }

    // 定位跳过选项
    {
        int left = m_rc_time_total.left() - m_rc_skip.width() - 10;
        int top = m_rc_time_passed.bottom() + 10;
        m_rc_skip.moveTo(left, top);
    }

    m_img_ready = true;
}

void Bar::_ms_to_str(uint32_t ms, QString& str) {
    int h = 0, m = 0, s = 0;
    s = ms / 1000;
    if(ms % 1000 > 500)
        s += 1;

    h = s / 3600;
    s = s % 3600;
    m = s / 60;
    s = s % 60;

    if(h > 0)
        str.sprintf("%02d:%02d:%02d", h, m, s);
    else
        str.sprintf("%02d:%02d", m, s);
}

void Bar::update_passed_time(uint32_t ms) {
    QString str_passed;
    _ms_to_str(ms, str_passed);

    if(m_str_passed_time != str_passed)
    {
        m_str_passed_time = str_passed;
        m_owner->update(m_rc.left()+m_rc_time_passed.left(), m_rc.top()+m_rc_time_passed.top(), m_rc_time_passed.width(), m_rc_time_passed.height());
    }

    int percent = 0;
    if(ms > m_total_ms) {
        percent = 100;
        m_passed_ms = m_total_ms;
    }
    else {
        m_passed_ms = ms;
        percent = (int)(((double)m_passed_ms / (double)m_total_ms) * 100);
    }

    if(percent != m_percent) {
        m_percent = percent;
        m_owner->update(m_rc.left()+m_rc_progress.left(), m_rc.top()+m_rc_progress.top(), m_rc_progress.width(), m_rc_progress.height());
    }
}

void Bar::onMouseMove(int x, int y) {
    // 映射鼠标坐标点到本浮动窗内部的相对位置
    QPoint pt(x-m_rc.left(), y-m_rc.top());

    bool play_hover = m_rc_btn_play.contains(pt);
    if(play_hover != m_play_hover) {
        m_play_hover = play_hover;
        m_owner->update(m_rc.left()+m_rc_btn_play.left(), m_rc.top()+m_rc_btn_play.top(), m_rc_btn_play.width(), m_rc_btn_play.height());
    }
    if(play_hover)
        return;

    int speed_hover = speed_count;
    for(int i = 0; i < speed_count; ++i) {
        if(m_rc_btn_speed[i].contains(pt)) {
            speed_hover = i;
            break;
        }
    }
    if(m_speed_hover != speed_hover) {
        if(m_speed_hover != speed_count) {
            m_owner->update(m_rc.left()+m_rc_btn_speed[m_speed_hover].left(), m_rc.top()+m_rc_btn_speed[m_speed_hover].top(), m_rc_btn_speed[m_speed_hover].width(), m_rc_btn_speed[m_speed_hover].height());
        }
        m_speed_hover = speed_hover;
        if(m_speed_hover != speed_count) {
            m_owner->update(m_rc.left()+m_rc_btn_speed[m_speed_hover].left(), m_rc.top()+m_rc_btn_speed[m_speed_hover].top(), m_rc_btn_speed[m_speed_hover].width(), m_rc_btn_speed[m_speed_hover].height());
        }
    }

    // TODO: more hover detect.
}

void Bar::draw(QPainter& painter, const QRect& rc_draw){
    if(!m_width)
        return;
    if(!rc_draw.intersects(m_rc))
        return;

    // 绘制背景
    {
        QRect rc(m_rc);
        //rc.moveTo(m_rc.left()+rc.left(), m_rc.top() + rc.top());

        int from_x = max(rc_draw.left(), m_rc.left()) - m_rc.left();
        int from_y = max(rc_draw.top(), m_rc.top()) - m_rc.top();
        int w = min(m_rc.right(), rc_draw.right()) - rc.left() - from_x + 1;
        int h = min(m_rc.bottom(), rc_draw.bottom()) - rc.top() - from_y + 1;
        int to_x = m_rc.left() + from_x;
        int to_y = m_rc.top() + from_y;
        painter.drawPixmap(to_x, to_y, m_img_bg, from_x, from_y, w, h);
    }

    // 绘制播放按钮
    {
        QRect rc(m_rc_btn_play);
        rc.moveTo(m_rc.left()+rc.left(), m_rc.top() + rc.top());
        if(rc_draw.intersects(rc)) {
            int from_x = max(rc_draw.left(), rc.left()) - rc.left();
            int from_y = max(rc_draw.top(), rc.top()) - rc.top();
            int w = min(rc.right(), rc_draw.right()) - rc.left() - from_x + 1;
            int h = min(rc.bottom(), rc_draw.bottom()) - rc.top() - from_y + 1;
            int to_x = rc.left() + from_x;
            int to_y = rc.top() + from_y;
            if(m_playing){
                if(m_play_hover)
                    painter.drawPixmap(to_x, to_y, m_img_btn_play[play_running][widget_hover], from_x, from_y, w, h);
                else
                    painter.drawPixmap(to_x, to_y, m_img_btn_play[play_running][widget_normal], from_x, from_y, w, h);
            } else {
                if(m_play_hover)
                    painter.drawPixmap(to_x, to_y, m_img_btn_play[play_paused][widget_hover], from_x, from_y, w, h);
                else
                    painter.drawPixmap(to_x, to_y, m_img_btn_play[play_paused][widget_normal], from_x, from_y, w, h);
            }
        }
    }

    // 绘制已播放时间
    {
        QRect rc(m_rc_time_passed);
        rc.moveTo(m_rc.left()+rc.left(), m_rc.top() + rc.top());
        if(rc_draw.intersects(rc)) {
            if(m_str_passed_time != m_str_passed_time_last_draw) {
                m_img_time_passed = QPixmap(m_rc_time_passed.width(), m_rc_time_passed.height());
                m_img_time_passed.fill(Qt::transparent);
                QPainter pp(&m_img_time_passed);
                pp.setPen(TEXT_COLOR);
                QFont font = pp.font();
                font.setFamily("consolas");
                font.setBold(true);
                font.setPixelSize(TIME_STR_PIXEL_SIZE);
                pp.setFont(font);
                pp.drawText(QRect(0,0,m_rc_time_passed.width(), m_rc_time_passed.height()), Qt::AlignRight, m_str_passed_time);

                m_str_passed_time_last_draw = m_str_passed_time;
            }

            int from_x = max(rc_draw.left(), rc.left()) - rc.left();
            int from_y = max(rc_draw.top(), rc.top()) - rc.top();
            int w = min(rc.right(), rc_draw.right()) - rc.left() - from_x + 1;
            int h = min(rc.bottom(), rc_draw.bottom()) - rc.top() - from_y + 1;
            int to_x = rc.left() + from_x;
            int to_y = rc.top() + from_y;
            painter.drawPixmap(to_x, to_y, m_img_time_passed, from_x, from_y, w, h);
        }
    }

    // 绘制总时间
    {
        QRect rc(m_rc_time_total);
        rc.moveTo(m_rc.left()+rc.left(), m_rc.top() + rc.top());
        if(rc_draw.intersects(rc)) {
            int from_x = max(rc_draw.left(), rc.left()) - rc.left();
            int from_y = max(rc_draw.top(), rc.top()) - rc.top();
            int w = min(rc.right(), rc_draw.right()) - rc.left() - from_x + 1;
            int h = min(rc.bottom(), rc_draw.bottom()) - rc.top() - from_y + 1;
            int to_x = rc.left() + from_x;
            int to_y = rc.top() + from_y;
            painter.drawPixmap(to_x, to_y, m_img_time_total, from_x, from_y, w, h);
        }
    }

    // 绘制进度条
    {
        QRect rc(m_rc_progress);
        rc.moveTo(m_rc.left()+rc.left(), m_rc.top() + rc.top());

        if(rc_draw.intersects(rc)) {
            if(m_percent_last_draw != m_percent) {
                m_img_progress = QPixmap(m_rc_progress.width(), m_rc_progress.height());
                m_img_progress.fill(Qt::transparent);
                QPainter pp(&m_img_progress);

                // 进度条
                int top = (rc.height() - m_res[res_pbh_left].height())/2;
                int passed_width = rc.width() * m_percent / 100;    // 已经播放的进度条宽度
                int remain_width = rc.width() - passed_width;       // 剩下未播放的进度条宽度

                if(passed_width >= m_res[res_pbh_left].width())
                    pp.drawPixmap(0, top , m_res[res_pbh_left].width(), m_res[res_pbh_left].height(), m_res[res_pbh_left]);
                if(passed_width > 0) {
                    //pp.drawPixmap(m_res[res_pbh_left].width(), top, passed_width - m_res[res_pbh_left].width(), m_res[res_pbh_mid].height(), m_res[res_pbh_mid]);
                    if(remain_width > m_res[res_pb_right].width())
                        pp.drawPixmap(m_res[res_pbh_left].width(), top, passed_width - m_res[res_pbh_left].width(), m_res[res_pbh_mid].height(), m_res[res_pbh_mid]);
                    else
                        pp.drawPixmap(m_res[res_pbh_left].width(), top, passed_width - m_res[res_pbh_left].width() - m_res[res_pb_right].width(), m_res[res_pbh_mid].height(), m_res[res_pbh_mid]);
                }
                if(remain_width > 0)
                    pp.drawPixmap(passed_width, top,  remain_width - m_res[res_pb_right].width(), m_res[res_pb_mid].height(), m_res[res_pb_mid]);
                if(remain_width >= m_res[res_pb_right].width())
                    pp.drawPixmap(rc.width() - m_res[res_pb_right].width(), top , m_res[res_pb_right].width(), m_res[res_pb_right].height(), m_res[res_pb_right]);

                // 进度位置指示
                int left = passed_width - m_img_progress_pointer->width() / 2;
                if(left < 0)
                    left = 0;
                if(left + m_img_progress_pointer->width() > rc.width())
                    left = rc.width() - m_img_progress_pointer->width();
                top = (rc.height() - m_img_progress_pointer[widget_normal].height())/2;
                pp.drawPixmap(left, top , m_img_progress_pointer[widget_normal].width(), m_img_progress_pointer[widget_normal].height(), m_img_progress_pointer[widget_normal]);

                m_percent_last_draw = m_percent;
            }

            int from_x = max(rc_draw.left(), rc.left()) - rc.left();
            int from_y = max(rc_draw.top(), rc.top()) - rc.top();
            int w = min(rc.right(), rc_draw.right()) - rc.left() - from_x + 1;
            int h = min(rc.bottom(), rc_draw.bottom()) - rc.top() - from_y + 1;
            int to_x = rc.left() + from_x;
            int to_y = rc.top() + from_y;
            painter.drawPixmap(to_x, to_y, m_img_progress, from_x, from_y, w, h);
        }
    }

    // 绘制速度按钮
    {
        for(int i = 0; i < speed_count; i++) {
            QRect rc(m_rc_btn_speed[i]);
            rc.moveTo(m_rc.left()+rc.left(), m_rc.top() + rc.top());
            if(rc_draw.intersects(rc)) {
                int from_x = max(rc_draw.left(), rc.left()) - rc.left();
                int from_y = max(rc_draw.top(), rc.top()) - rc.top();
                int w = min(rc.right(), rc_draw.right()) - rc.left() - from_x + 1;
                int h = min(rc.bottom(), rc_draw.bottom()) - rc.top() - from_y + 1;
                int to_x = rc.left() + from_x;
                int to_y = rc.top() + from_y;
                if(m_speed_selected == i || m_speed_hover == i)
                    painter.drawPixmap(to_x, to_y, m_img_btn_speed[i][widget_hover], from_x, from_y, w, h);
                else
                    painter.drawPixmap(to_x, to_y, m_img_btn_speed[i][widget_normal], from_x, from_y, w, h);
            }
        }
    }

    // 绘制跳过选项
    {
        QRect rc(m_rc_skip);
        rc.moveTo(m_rc.left()+rc.left(), m_rc.top() + rc.top());
        if(rc_draw.intersects(rc)) {
            int from_x = max(rc_draw.left(), rc.left()) - rc.left();
            int from_y = max(rc_draw.top(), rc.top()) - rc.top();
            int w = min(rc.right(), rc_draw.right()) - rc.left() - from_x + 1;
            int h = min(rc.bottom(), rc_draw.bottom()) - rc.top() - from_y + 1;
            int to_x = rc.left() + from_x;
            int to_y = rc.top() + from_y;
            //qDebug("skip (%d,%d), (%d,%d)/(%d,%d)", to_x, to_y, from_x, from_y, w, h);
            if(m_skip_selected)
                painter.drawPixmap(to_x, to_y, m_img_skip[widget_hover], from_x, from_y, w, h);
            else
                painter.drawPixmap(to_x, to_y, m_img_skip[widget_normal], from_x, from_y, w, h);
        }
    }
}


