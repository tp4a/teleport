#include "mainwindow.h"
#include "ui_mainwindow.h"
#include "rle.h"

#include <QMatrix>
#include <QDebug>
#include <QPainter>
#include <QDesktopWidget>
#include <QPaintEvent>

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


MainWindow::MainWindow(QWidget *parent) :
    QMainWindow(parent),
    ui(new Ui::MainWindow)
{
    m_shown = false;
    m_show_default = true;
    m_bar_shown = false;
    memset(&m_pt, 0, sizeof(TS_RECORD_RDP_POINTER));

    ui->setupUi(this);

    ui->centralWidget->setMouseTracking(true);
    setMouseTracking(true);

    //qRegisterMetaType<update_data*>("update_data");

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

    connect(&m_thr_play, SIGNAL(signal_update_data(update_data*)), this, SLOT(on_update_data(update_data*)));
}

MainWindow::~MainWindow()
{
    m_thr_play.stop();
    m_thr_play.wait();
    delete ui;
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

        // 绘制浮动控制窗
        if(m_bar_shown)
            m_bar.draw(painter, e->rect());
    }

    if(!m_shown) {
        m_shown = true;
        m_thr_play.start();
    }
}

void MainWindow::on_update_data(update_data* dat) {
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

    if(dat->data_type() == TYPE_TIMER) {
        m_bar.update_passed_time(dat->passed_ms());
        return;
    }

    if(dat->data_type() == TYPE_HEADER_INFO) {
        if(dat->data_len() != sizeof(TS_RECORD_HEADER)) {
            qDebug() << "invalid record header.";
            return;
        }
        memcpy(&m_rec_hdr, dat->data_buf(), sizeof(TS_RECORD_HEADER));

        qDebug() << "resize (" << m_rec_hdr.basic.width << "," << m_rec_hdr.basic.height << ")";
        if(m_rec_hdr.basic.width > 0 && m_rec_hdr.basic.height > 0) {
            m_canvas = QPixmap(m_rec_hdr.basic.width, m_rec_hdr.basic.height);
            m_canvas.fill(QColor(38, 73, 111));

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

            m_show_default = false;
            repaint();

            m_bar.start(m_rec_hdr.info.time_ms, 640);
        }

        QString title;
        if (m_rec_hdr.basic.conn_port == 3389)
            title.sprintf("[%s] %s@%s [Teleport-RDP录像回放]", m_rec_hdr.basic.acc_username, m_rec_hdr.basic.user_username, m_rec_hdr.basic.conn_ip);
        else
            title.sprintf("[%s] %s@%s:%d [Teleport-RDP录像回放]", m_rec_hdr.basic.acc_username, m_rec_hdr.basic.user_username, m_rec_hdr.basic.conn_ip, m_rec_hdr.basic.conn_port);

        setWindowTitle(title);

        return;
    }


    if(dat->data_type() == TYPE_END) {
        m_bar.end();
        return;
    }
}

void MainWindow::mouseMoveEvent(QMouseEvent *e) {
    if(!m_show_default) {
        QRect rc = m_bar.rc();
        if(e->y() > rc.top() - 20 && e->y() < rc.bottom() + 20) {
            if(!m_bar_shown) {
                m_bar_shown = true;
                update(rc);
            }

            if(rc.contains(QPoint(e->x(), e->y())))
                m_bar.onMouseMove(e->x(), e->y());
        }
        else {
            if(m_bar_shown) {
                m_bar_shown = false;
                update(rc);
            }
        }
    }
}

