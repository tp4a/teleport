#include "mainwindow.h"
#include "ui_mainwindow.h"

#include <QMatrix>
#include <QDebug>
#include <QPainter>
#include <QDesktopWidget>
#include <QPaintEvent>
#include <QMessageBox>
#include <QDialogButtonBox>

static inline int min(int a, int b){
    return a < b ? a : b;
}

static inline int max(int a, int b){
    return a > b ? a : b;
}

MainWindow::MainWindow(QWidget *parent) :
    QMainWindow(parent),
    ui(new Ui::MainWindow)
{
    m_show_default = true;
    m_bar_shown = false;
    m_bar_fade_in = false;
    m_bar_fading = false;
    m_bar_opacity = 1.0;
    m_show_message = false;
    memset(&m_pt, 0, sizeof(TS_RECORD_RDP_POINTER));

    m_thr_play = nullptr;
    m_play_state = PLAY_STATE_UNKNOWN;
    m_thr_data = nullptr;

    ui->setupUi(this);

    ui->centralWidget->setMouseTracking(true);
    setMouseTracking(true);

    // frame-less window.
//#ifdef __APPLE__
//    setWindowFlags(Qt::FramelessWindowHint | Qt::MSWindowsFixedSizeDialogHint | Qt::Window);
//    OSXCode::fixWin(winId());
//#else
//    setWindowFlags(Qt::FramelessWindowHint | Qt::MSWindowsFixedSizeDialogHint | windowFlags());
//#endif //__APPLE__

    m_pt_normal.load(":/tp-player/res/cursor.png");
    m_default_bg.load(":/tp-player/res/bg.png");

    m_canvas = QPixmap(m_default_bg.width(), m_default_bg.height());
    QPainter pp(&m_canvas);
    pp.drawPixmap(0, 0, m_default_bg, 0, 0, m_default_bg.width(), m_default_bg.height());


    setWindowFlags(windowFlags()&~Qt::WindowMaximizeButtonHint);    // 禁止最大化按钮
    setFixedSize(m_default_bg.width(), m_default_bg.height());      // 禁止拖动窗口大小

    if(!m_bar.init(this)) {
        qDebug("bar init failed.");
        return;
    }


    connect(&m_timer_first_run, SIGNAL(timeout()), this, SLOT(_do_first_run()));
    connect(&m_timer_bar_fade, SIGNAL(timeout()), this, SLOT(_do_bar_fade()));
    connect(&m_timer_bar_delay_hide, SIGNAL(timeout()), this, SLOT(_do_bar_delay_hide()));

    m_timer_first_run.setSingleShot(true);
    m_timer_first_run.start(500);
}

MainWindow::~MainWindow()
{
    if(m_thr_play) {
        m_thr_play->stop();

        disconnect(m_thr_play, SIGNAL(signal_update_data(UpdateData*)), this, SLOT(_do_update_data(UpdateData*)));

        delete m_thr_play;
        m_thr_play = nullptr;
    }

    if(m_thr_data) {
        m_thr_data->stop();
        disconnect(m_thr_data, SIGNAL(signal_update_data(UpdateData*)), this, SLOT(_do_update_data(UpdateData*)));
        delete m_thr_data;
        m_thr_data = nullptr;
    }

    delete ui;
}

void MainWindow::set_resource(const QString &res) {
    m_res = res;
}

void MainWindow::_do_first_run() {
    m_thr_data = new ThrData(this, m_res);
    connect(m_thr_data, SIGNAL(signal_update_data(UpdateData*)), this, SLOT(_do_update_data(UpdateData*)));
    m_thr_data->start();

    m_thr_play = new ThrPlay(this);
    connect(m_thr_play, SIGNAL(signal_update_data(UpdateData*)), this, SLOT(_do_update_data(UpdateData*)));

    m_thr_play->speed(m_bar.get_speed());
    m_thr_play->start();
}

void MainWindow::set_speed(int s) {
    if(m_thr_play)
        m_thr_play->speed(s);
}

void MainWindow::set_skip(bool s) {
    if(m_thr_play)
        m_thr_play->skip(s);
}

void MainWindow::paintEvent(QPaintEvent *e)
{
    QPainter painter(this);

    if(m_show_default) {
        painter.drawPixmap(e->rect(), m_default_bg, e->rect());
    }
    else {
        painter.drawPixmap(e->rect(), m_canvas, e->rect());

        QRect rcpt(m_pt_normal.rect());
        rcpt.moveTo(m_pt.x - m_pt_normal.width()/2, m_pt.y-m_pt_normal.height()/2);
        if(e->rect().intersects(rcpt)) {
            painter.drawPixmap(m_pt.x-m_pt_normal.width()/2, m_pt.y-m_pt_normal.height()/2, m_pt_normal);
        }

//        {
//            QRect rc_draw = e->rect();
//            QRect rc(m_rc_message);
//            //rc.moveTo(m_rc.left()+rc.left(), m_rc.top() + rc.top());

//            int from_x = max(rc_draw.left(), rc.left()) - rc.left();
//            int from_y = max(rc_draw.top(), rc.top()) - rc.top();
//            int w = min(rc.right(), rc_draw.right()) - rc.left() - from_x + 1;
//            int h = min(rc.bottom(), rc_draw.bottom()) - rc.top() - from_y + 1;
//            int to_x = rc.left() + from_x;
//            int to_y = rc.top() + from_y;
//            painter.drawPixmap(to_x, to_y, m_img_message, from_x, from_y, w, h);
//        }

        // 绘制浮动控制窗
        if(m_bar_fading) {
            painter.setOpacity(m_bar_opacity);
            m_bar.draw(painter, e->rect());
        }
        else if(m_bar_shown) {
            m_bar.draw(painter, e->rect());
        }
    }

    if(m_show_message) {
        QRect rc_draw = e->rect();
        QRect rc(m_rc_message);
        //rc.moveTo(m_rc.left()+rc.left(), m_rc.top() + rc.top());

        int from_x = max(rc_draw.left(), rc.left()) - rc.left();
        int from_y = max(rc_draw.top(), rc.top()) - rc.top();
        int w = min(rc.right(), rc_draw.right()) - rc.left() - from_x + 1;
        int h = min(rc.bottom(), rc_draw.bottom()) - rc.top() - from_y + 1;
        int to_x = rc.left() + from_x;
        int to_y = rc.top() + from_y;
        painter.drawPixmap(to_x, to_y, m_img_message, from_x, from_y, w, h);
    }
}

void MainWindow::pause() {
    if(m_play_state != PLAY_STATE_RUNNING)
        return;
    m_thr_play->pause();
    m_play_state = PLAY_STATE_PAUSE;
}

void MainWindow::resume(bool relocate, uint32_t ms) {
    if(m_play_state == PLAY_STATE_PAUSE) {
        if(relocate)
            m_thr_data->restart(ms);
        m_thr_play->resume(relocate, ms);
    }
    else if(m_play_state == PLAY_STATE_STOP) {
//        _start_play_thread();
        m_thr_data->restart(ms);
        m_thr_play->resume(true, ms);
    }

    m_play_state = PLAY_STATE_RUNNING;
}

void MainWindow::_do_update_data(UpdateData* dat) {
    if(!dat)
        return;

    UpdateDataHelper data_helper(dat);

    if(dat->data_type() == TYPE_POINTER) {
        TS_RECORD_RDP_POINTER pt;
        memcpy(&pt, &m_pt, sizeof(TS_RECORD_RDP_POINTER));

        // 更新虚拟鼠标信息，这样下一次绘制界面时就会在新的位置绘制出虚拟鼠标
        memcpy(&m_pt, dat->get_pointer(), sizeof(TS_RECORD_RDP_POINTER));
        update(m_pt.x - m_pt_normal.width()/2, m_pt.y - m_pt_normal.width()/2, m_pt_normal.width(), m_pt_normal.height());

        update(pt.x - m_pt_normal.width()/2, pt.y - m_pt_normal.width()/2, m_pt_normal.width(), m_pt_normal.height());

        return;
    }
    else if(dat->data_type() == TYPE_IMAGE) {
        UpdateImages uimgs;
        if(!dat->get_images(uimgs))
            return;

        if(uimgs.size() > 1) {
            // 禁止界面更新
            setUpdatesEnabled(false);
        }


        QPainter pp(&m_canvas);
        for(int i = 0; i < uimgs.size(); ++i) {
            pp.drawImage(uimgs[i].x, uimgs[i].y, *(uimgs[i].img), 0, 0, uimgs[i].w, uimgs[i].h, Qt::AutoColor);
            update(uimgs[i].x, uimgs[i].y, uimgs[i].w, uimgs[i].h);
        }


        if(uimgs.size() > 1) {
            // 允许界面更新
            setUpdatesEnabled(true);
        }

        return;
    }

    else if(dat->data_type() == TYPE_PLAYED_MS) {
        m_bar.update_passed_time(dat->played_ms());
        return;
    }

    else if(dat->data_type() == TYPE_DISABLE_DRAW) {
        // 禁止界面更新
        setUpdatesEnabled(false);
        return;
    }

    else if(dat->data_type() == TYPE_ENABLE_DRAW) {
        // 允许界面更新
        setUpdatesEnabled(true);
        return;
    }

    else if(dat->data_type() == TYPE_MESSAGE) {
        if(dat->message().isEmpty()) {
            m_show_message = false;
            return;
        }

        m_show_message = true;

        qDebug("1message, w=%d, h=%d", m_canvas.width(), m_canvas.height());
//        if(0 == m_canvas.width()) {
//            QMessageBox::warning(nullptr, QGuiApplication::applicationDisplayName(), dat->message());
//            return;
//        }

        QPainter pp(&m_canvas);
        QRect rcWin(0, 0, m_canvas.width(), m_canvas.height());
        pp.drawText(rcWin, Qt::AlignLeft|Qt::TextDontPrint, dat->message(), &m_rc_message);

        qDebug("2message, w=%d, h=%d", m_rc_message.width(), m_rc_message.height());
        m_rc_message.setWidth(m_rc_message.width()+60);
        m_rc_message.setHeight(m_rc_message.height()+60);

        m_img_message = QPixmap(m_rc_message.width(), m_rc_message.height());
        m_img_message.fill(Qt::transparent);
        QPainter pm(&m_img_message);
        pm.setPen(QColor(255,255,255,153));
        pm.fillRect(m_rc_message, QColor(0,0,0,190));

        QRect rcRect(m_rc_message);
        rcRect.setWidth(rcRect.width()-1);
        rcRect.setHeight(rcRect.height()-1);
        pm.drawRect(rcRect);

        QRect rcText(m_rc_message);
        rcText.setLeft(30);
        rcText.setTop(30);
        pm.drawText(rcText, Qt::AlignLeft, dat->message());
        m_rc_message.moveTo(
                    (m_canvas.width() - m_rc_message.width())/2,
                    (m_canvas.height() - m_rc_message.height())/3
                    );

        update(m_rc_message.x(), m_rc_message.y(), m_rc_message.width(), m_rc_message.height());

        return;
    }

    else if(dat->data_type() == TYPE_ERROR) {
        QMessageBox::critical(this, QGuiApplication::applicationDisplayName(), dat->message());
        QApplication::instance()->exit(0);
        return;
    }

    // 这是播放开始时收到的第一个数据包
    else if(dat->data_type() == TYPE_HEADER_INFO) {
        TS_RECORD_HEADER* hdr = dat->get_header();
        if(hdr == nullptr)
            return;
        memcpy(&m_rec_hdr, hdr, sizeof(TS_RECORD_HEADER));

        qDebug() << "resize (" << m_rec_hdr.basic.width << "," << m_rec_hdr.basic.height << ")";

        //if(m_canvas.width() != m_rec_hdr.basic.width && m_canvas.height() != m_rec_hdr.basic.height) {
            m_canvas = QPixmap(m_rec_hdr.basic.width, m_rec_hdr.basic.height);

            //m_win_board_w = frameGeometry().width() - geometry().width();
            //m_win_board_h = frameGeometry().height() - geometry().height();

            QDesktopWidget *desktop = QApplication::desktop(); // =qApp->desktop();也可以
            qDebug("desktop w:%d,h:%d, this w:%d,h:%d", desktop->width(), desktop->height(), width(), height());
            //move((desktop->width() - this->width())/2, (desktop->height() - this->height())/2);
            move(10, (desktop->height() - m_rec_hdr.basic.height)/2);

            //setFixedSize(m_rec_hdr.basic.width + m_win_board_w, m_rec_hdr.basic.height + m_win_board_h);
            //resize(m_rec_hdr.basic.width + m_win_board_w, m_rec_hdr.basic.height + m_win_board_h);
            //resize(m_rec_hdr.basic.width, m_rec_hdr.basic.height);
            setFixedSize(m_rec_hdr.basic.width, m_rec_hdr.basic.height);
        //}

        m_canvas.fill(QColor(38, 73, 111));

        m_show_default = false;
        repaint();

        m_bar.start(m_rec_hdr.info.time_ms, 640);
        m_bar_shown = true;
        m_play_state = PLAY_STATE_RUNNING;

        update(m_bar.rc());

        m_bar_fade_in = false;
        m_bar_fading = true;
        m_timer_bar_delay_hide.start(2000);

        QString title;
        if (m_rec_hdr.basic.conn_port == 3389) {
//            title = QString(LOCAL8BIT("[%1] %2@%3 [Teleport-RDP录像回放]").arg(m_rec_hdr.basic.acc_username, m_rec_hdr.basic.user_username, m_rec_hdr.basic.conn_ip));
            title = QString(LOCAL8BIT("用户 %1 访问 %2 的 %3 账号").arg(m_rec_hdr.basic.user_username, m_rec_hdr.basic.conn_ip, m_rec_hdr.basic.acc_username));
        }
        else {
            QString _port;
            _port.sprintf("%d", m_rec_hdr.basic.conn_port);
            //title = QString(LOCAL8BIT("[%1] %2@%3:%4 [Teleport-RDP录像回放]").arg(m_rec_hdr.basic.acc_username, m_rec_hdr.basic.user_username, m_rec_hdr.basic.conn_ip, _port));
            title = QString(LOCAL8BIT("用户 %1 访问 %2:%3 的 %4 账号").arg(m_rec_hdr.basic.user_username, m_rec_hdr.basic.conn_ip, _port, m_rec_hdr.basic.acc_username));
        }

        setWindowTitle(title);

        return;
    }


    else if(dat->data_type() == TYPE_END) {
        m_bar.end();
        m_play_state = PLAY_STATE_STOP;

        return;
    }
}

void MainWindow::_do_bar_delay_hide() {
    m_bar_fading = true;
    m_timer_bar_delay_hide.stop();
    m_timer_bar_fade.stop();
    m_timer_bar_fade.start(50);
}

void MainWindow::_do_bar_fade() {
    if(m_bar_fade_in) {
        if(m_bar_opacity < 1.0)
            m_bar_opacity += 0.3;
        if(m_bar_opacity >= 1.0) {
            m_bar_opacity = 1.0;
            m_bar_shown = true;
            m_bar_fading = false;
            m_timer_bar_fade.stop();
        }
    }
    else {
        if(m_bar_opacity > 0.0)
            m_bar_opacity -= 0.2;
        if(m_bar_opacity <= 0.0) {
            m_bar_opacity = 0.0;
            m_bar_shown = false;
            m_bar_fading = false;
            m_timer_bar_fade.stop();
        }
    }

    update(m_bar.rc());
}

void MainWindow::mouseMoveEvent(QMouseEvent *e) {
    if(!m_show_default) {
        QRect rc = m_bar.rc();
        if(e->y() > rc.top() - 20 && e->y() < rc.bottom() + 20) {
            if((!m_bar_shown && !m_bar_fading) || (m_bar_fading && !m_bar_fade_in)) {
                m_bar_fade_in = true;
                m_bar_fading = true;

                m_timer_bar_delay_hide.stop();
                m_timer_bar_fade.stop();
                m_timer_bar_fade.start(50);
            }

            if(rc.contains(e->pos()))
                m_bar.onMouseMove(e->x(), e->y());
        }
        else {
            if((m_bar_shown && !m_bar_fading) || (m_bar_fading && m_bar_fade_in)) {
                m_bar_fade_in = false;
                m_bar_fading = true;
                m_timer_bar_fade.stop();
                m_timer_bar_delay_hide.stop();

                if(m_bar_opacity != 1.0)
                    m_timer_bar_fade.start(50);
                else
                    m_timer_bar_delay_hide.start(1000);
            }
        }
    }
}

void MainWindow::mousePressEvent(QMouseEvent *e) {
    if(!m_show_default) {
        QRect rc = m_bar.rc();
        if(rc.contains(e->pos())) {
            m_bar.onMousePress(e->x(), e->y(), e->button());
        }
    }
}

void MainWindow::mouseReleaseEvent(QMouseEvent *e) {
    m_bar.onMouseRelease(e->x(), e->y(), e->button());
}

