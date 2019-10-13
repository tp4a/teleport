#include "mainwindow.h"
#include "ui_mainwindow.h"
#include "rle.h"

#include <QMatrix>
#include <QDebug>
#include <QPainter>
#include <QDesktopWidget>
#include <QPaintEvent>
#include <QMessageBox>
#include <QDialogButtonBox>

bool rdpimg2QImage(QImage& out, int w, int h, int bitsPerPixel, bool isCompressed, uint8_t* dat, uint32_t len) {
    switch(bitsPerPixel) {
    case 15:
        if(isCompressed) {
            uint8_t* _dat = (uint8_t*)calloc(1, w*h*2);
            if(!bitmap_decompress1(_dat, w, h, dat, len)) {
                free(_dat);
                return false;
            }
            out = QImage(_dat, w, h, QImage::Format_RGB555);
            free(_dat);
        }
        else {
            out = QImage(dat, w, h, QImage::Format_RGB555).transformed(QMatrix(1.0, 0.0, 0.0, -1.0, 0.0, 0.0)) ;
        }
        break;
    case 16:
        if(isCompressed) {

            uint8_t* _dat = (uint8_t*)calloc(1, w*h*2);
            if(!bitmap_decompress2(_dat, w, h, dat, len)) {
                free(_dat);
                return false;
            }

            // TODO: 这里需要进一步优化，直接操作QImage的buffer。
//            QTime t1;
//            t1.start();

            out = QImage(w, h, QImage::Format_RGB16);
            for(int y = 0; y < h; y++) {
                for(int x = 0; x < w; x++) {
                    uint16 a = ((uint16*)_dat)[y * w + x];
                    uint8 r = ((a & 0xf800) >> 11) * 255 / 31;
                    uint8 g = ((a & 0x07e0) >> 5) * 255 / 63;
                    uint8 b = (a & 0x001f) * 255 / 31;
                    out.setPixelColor(x, y, QColor(r,g,b));
                }
            }
//            qDebug("parse: %dB, %dms", len, t1.elapsed());

            free(_dat);
        }
        else {
            out = QImage(dat, w, h, QImage::Format_RGB16).transformed(QMatrix(1.0, 0.0, 0.0, -1.0, 0.0, 0.0)) ;
        }
        break;
    case 24:
        qDebug() << "--------NOT support 24";
        break;
    case 32:
        qDebug() << "--------NOT support 32";
        break;
    }

    return true;
}

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
    //m_shown = false;
    m_show_default = true;
    m_bar_shown = false;
    m_bar_fade_in = false;
    m_bar_fading = false;
    m_bar_opacity = 1.0;
    memset(&m_pt, 0, sizeof(TS_RECORD_RDP_POINTER));

    m_thr_play = nullptr;
    m_play_state = PLAY_STATE_UNKNOWN;

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

    setWindowFlags(windowFlags()&~Qt::WindowMaximizeButtonHint);    // 禁止最大化按钮
    setFixedSize(m_default_bg.width(), m_default_bg.height());                     // 禁止拖动窗口大小

    if(!m_bar.init(this)) {
        qDebug("bar init failed.");
        return;
    }

//    connect(&m_thr_play, SIGNAL(signal_update_data(update_data*)), this, SLOT(_do_update_data(update_data*)));
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
        //m_thr_play->wait();
        //qDebug() << "play thread stoped.";

        disconnect(m_thr_play, SIGNAL(signal_update_data(update_data*)), this, SLOT(_do_update_data(update_data*)));

        delete m_thr_play;
        m_thr_play = nullptr;
    }

    delete ui;
}

void MainWindow::set_resource(const QString &res) {
    m_res = res;
}

void MainWindow::_do_first_run() {
    _start_play_thread();
}

void MainWindow::_start_play_thread() {
    if(m_thr_play) {
        m_thr_play->stop();
        //m_thr_play->wait();

        disconnect(m_thr_play, SIGNAL(signal_update_data(update_data*)), this, SLOT(_do_update_data(update_data*)));

        delete m_thr_play;
        m_thr_play = nullptr;
    }

    m_thr_play = new ThreadPlay(m_res);
    connect(m_thr_play, SIGNAL(signal_update_data(update_data*)), this, SLOT(_do_update_data(update_data*)));
    m_thr_play->speed(m_bar.get_speed());
    m_thr_play->start();
}

void MainWindow::speed(int s) {
    if(m_thr_play)
        m_thr_play->speed(s);
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

        {
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

        // 绘制浮动控制窗
        if(m_bar_fading) {
            painter.setOpacity(m_bar_opacity);
            m_bar.draw(painter, e->rect());
        }
        else if(m_bar_shown) {
            m_bar.draw(painter, e->rect());
        }
    }

//    if(!m_shown) {
//        m_shown = true;
//        //m_thr_play.start();
//        _start_play_thread();
//    }
}

void MainWindow::pause() {
    if(m_play_state != PLAY_STATE_RUNNING)
        return;
    m_thr_play->pause();
    m_play_state = PLAY_STATE_PAUSE;
}

void MainWindow::resume() {
    if(m_play_state == PLAY_STATE_PAUSE)
        m_thr_play->resume();
    else if(m_play_state == PLAY_STATE_STOP)
        //m_thr_play->start();
        _start_play_thread();

    m_play_state = PLAY_STATE_RUNNING;
}

void MainWindow::_do_update_data(update_data* dat) {
    if(!dat)
        return;

    UpdateDataHelper data_helper(dat);

    if(dat->data_type() == TYPE_DATA) {

        if(dat->data_len() <= sizeof(TS_RECORD_PKG)) {
            qDebug() << "invalid record package(1).";
            return;
        }

        TS_RECORD_PKG* pkg = (TS_RECORD_PKG*)dat->data_buf();

        if(pkg->type == TS_RECORD_TYPE_RDP_POINTER) {
            if(dat->data_len() != sizeof(TS_RECORD_PKG) + sizeof(TS_RECORD_RDP_POINTER)) {
                qDebug() << "invalid record package(2).";
                return;
            }

            TS_RECORD_RDP_POINTER pt;
            memcpy(&pt, &m_pt, sizeof(TS_RECORD_RDP_POINTER));

            // 更新虚拟鼠标信息，这样下一次绘制界面时就会在新的位置绘制出虚拟鼠标
            memcpy(&m_pt, dat->data_buf() + sizeof(TS_RECORD_PKG), sizeof(TS_RECORD_RDP_POINTER));
            update(m_pt.x - m_pt_normal.width()/2, m_pt.y - m_pt_normal.width()/2, m_pt_normal.width(), m_pt_normal.height());

            update(pt.x - m_pt_normal.width()/2, pt.y - m_pt_normal.width()/2, m_pt_normal.width(), m_pt_normal.height());
        }
        else if(pkg->type == TS_RECORD_TYPE_RDP_IMAGE) {
            if(dat->data_len() <= sizeof(TS_RECORD_PKG) + sizeof(TS_RECORD_RDP_IMAGE_INFO)) {
                qDebug() << "invalid record package(3).";
                return;
            }

            TS_RECORD_RDP_IMAGE_INFO* info = (TS_RECORD_RDP_IMAGE_INFO*)(dat->data_buf() + sizeof(TS_RECORD_PKG));
            uint8_t* img_dat = dat->data_buf() + sizeof(TS_RECORD_PKG) + sizeof(TS_RECORD_RDP_IMAGE_INFO);
            uint32_t img_len = dat->data_len() - sizeof(TS_RECORD_PKG) - sizeof(TS_RECORD_RDP_IMAGE_INFO);

            QImage img_update;
            rdpimg2QImage(img_update, info->width, info->height, info->bitsPerPixel, (info->format == TS_RDP_IMG_BMP) ? true : false, img_dat, img_len);

            int x = info->destLeft;
            int y = info->destTop;
            int w = info->destRight - info->destLeft + 1;
            int h = info->destBottom - info->destTop + 1;

            QPainter pp(&m_canvas);
            pp.drawImage(x, y, img_update, 0, 0, w, h, Qt::AutoColor);

            update(x, y, w, h);
        }

        return;
    }

    else if(dat->data_type() == TYPE_PLAYED_MS) {
        m_bar.update_passed_time(dat->played_ms());
        return;
    }

    else if(dat->data_type() == TYPE_MESSAGE) {
        QPainter pp(&m_canvas);
        QRect rcWin(0, 0, m_canvas.width(), m_canvas.height());
        pp.drawText(rcWin, Qt::AlignLeft|Qt::TextDontPrint, dat->message(), &m_rc_message);

        qDebug("message, w=%d, h=%d", m_rc_message.width(), m_rc_message.height());
        m_rc_message.setWidth(m_rc_message.width()+60);
        m_rc_message.setHeight(m_rc_message.height()+60);

        m_img_message = QPixmap(m_rc_message.width(), m_rc_message.height());
        m_img_message.fill(Qt::transparent);
        QPainter pm(&m_img_message);
        pm.setPen(QColor(255,255,255,153));
        pm.fillRect(m_rc_message, QColor(0,0,0,190));

        QRect rcText(m_rc_message);
        rcText.setLeft(30);
        rcText.setTop(30);
        pm.drawText(rcText, Qt::AlignLeft, dat->message());
        m_rc_message.moveTo(
                    (m_canvas.width() - m_rc_message.width())/2,
                    (m_canvas.height() - m_rc_message.height())/3
                    );
        return;
    }

    else if(dat->data_type() == TYPE_ERROR) {
        QMessageBox::warning(nullptr, QGuiApplication::applicationDisplayName(), dat->message());
        QApplication::instance()->exit(0);
        return;
    }

    // 这是播放开始时收到的第一个数据包
    else if(dat->data_type() == TYPE_HEADER_INFO) {
        if(dat->data_len() != sizeof(TS_RECORD_HEADER)) {
            qDebug() << "invalid record header.";
            return;
        }
        memcpy(&m_rec_hdr, dat->data_buf(), sizeof(TS_RECORD_HEADER));

        qDebug() << "resize (" << m_rec_hdr.basic.width << "," << m_rec_hdr.basic.height << ")";

        if(m_canvas.width() != m_rec_hdr.basic.width && m_canvas.height() != m_rec_hdr.basic.height) {
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
        }

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
        if (m_rec_hdr.basic.conn_port == 3389)
            title.sprintf("[%s] %s@%s [Teleport-RDP录像回放]", m_rec_hdr.basic.acc_username, m_rec_hdr.basic.user_username, m_rec_hdr.basic.conn_ip);
        else
            title.sprintf("[%s] %s@%s:%d [Teleport-RDP录像回放]", m_rec_hdr.basic.acc_username, m_rec_hdr.basic.user_username, m_rec_hdr.basic.conn_ip, m_rec_hdr.basic.conn_port);

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
//    QApplication::instance()->exit(0);
//    return;
    if(!m_show_default) {
        QRect rc = m_bar.rc();
        if(rc.contains(e->pos())) {
            m_bar.onMousePress(e->x(), e->y());
        }
    }
}
