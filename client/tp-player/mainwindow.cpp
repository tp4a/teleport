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
//                    r = r * 255 / 31;
//                    g = g * 255 / 63;
//                    b = b * 255 / 31;

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
    m_show_bg = true;
    m_bg = QImage(":/tp-player/res/bg");
    m_pt_normal = QImage(":/tp-player/res/cursor.png");
    memset(&m_pt, 0, sizeof(TS_RECORD_RDP_POINTER));

    qDebug() << m_pt_normal.width() << "x" << m_pt_normal.height();

    ui->setupUi(this);

    //qRegisterMetaType<update_data*>("update_data");

    // frame-less window.
//#ifdef __APPLE__
//    setWindowFlags(Qt::FramelessWindowHint | Qt::MSWindowsFixedSizeDialogHint | Qt::Window);
//    OSXCode::fixWin(winId());
//#else
//    setWindowFlags(Qt::FramelessWindowHint | Qt::MSWindowsFixedSizeDialogHint | windowFlags());
//#endif //__APPLE__

    //m_canvas = QPixmap(m_bg.width(), m_bg.height());
    m_canvas.load(":/tp-player/res/bg");

    resize(m_bg.width(), m_bg.height());

    setWindowFlags(windowFlags()&~Qt::WindowMaximizeButtonHint);    // 禁止最大化按钮
    setFixedSize(m_bg.width(), m_bg.height());                     // 禁止拖动窗口大小

    if(!m_bar.init(this, 480))
        return;

    connect(&m_thr_play, SIGNAL(signal_update_data(update_data*)), this, SLOT(on_update_data(update_data*)));
}

MainWindow::~MainWindow()
{
    m_thr_play.stop();
    m_thr_play.wait();
    delete ui;
}

void MainWindow::paintEvent(QPaintEvent *pe)
{
    QPainter painter(this);

    painter.drawPixmap(pe->rect(), m_canvas, pe->rect());

    if(!m_pt_history.empty()) {
        for(int i = 0; i < m_pt_history.count(); i++) {
            //qDebug("pt clean %d,%d", m_pt_history[i].x, m_pt_history[i].y);
            QRect rcpt(m_pt_normal.rect());
            rcpt.moveTo(m_pt_history[i].x - m_pt_normal.width()/2, m_pt_history[i].y-m_pt_normal.height()/2);
            //painter.drawPixmap(rcpt, m_canvas, rcpt);
            qDebug("pt ---- (%d,%d), (%d,%d)", rcpt.x(), rcpt.y(), rcpt.width(), rcpt.height());
            painter.fillRect(rcpt, QColor(255, 255, 0, 128));
        }
        m_pt_history.clear();
    }

    QRect rcpt(m_pt_normal.rect());
    rcpt.moveTo(m_pt.x - m_pt_normal.width()/2, m_pt.y-m_pt_normal.height()/2);
    if(pe->rect().intersects(rcpt)) {
        qDebug("pt draw (%d,%d), (%d,%d)", m_pt.x-m_pt_normal.width()/2, m_pt.y-m_pt_normal.height()/2, m_pt_normal.width(), m_pt_normal.height());
        painter.drawImage(m_pt.x-m_pt_normal.width()/2, m_pt.y-m_pt_normal.height()/2, m_pt_normal);
    }

    m_bar.draw(painter, pe->rect());

//    if(!m_shown) {
//        m_shown = true;
//        m_thr_play.start();
//    }
}

void MainWindow::on_update_data(update_data* dat) {
    if(!dat)
        return;

    if(dat->data_type() == TYPE_DATA) {
        m_show_bg = false;

        if(dat->data_len() <= sizeof(TS_RECORD_PKG)) {
            qDebug() << "invalid record package(1).";
            delete dat;
            return;
        }

        TS_RECORD_PKG* pkg = (TS_RECORD_PKG*)dat->data_buf();

        if(pkg->type == TS_RECORD_TYPE_RDP_POINTER) {
            if(dat->data_len() != sizeof(TS_RECORD_PKG) + sizeof(TS_RECORD_RDP_POINTER)) {
                qDebug() << "invalid record package(2).";
                delete dat;
                return;
            }

            // 将现有虚拟鼠标信息放入历史队列，这样下一次绘制界面时就会将其清除掉
            m_pt_history.push_back(m_pt);

            // 更新虚拟鼠标信息，这样下一次绘制界面时就会在新的位置绘制出虚拟鼠标
            memcpy(&m_pt, dat->data_buf() + sizeof(TS_RECORD_PKG), sizeof(TS_RECORD_RDP_POINTER));
            //qDebug("pt new position %d,%d", m_pt.x, m_pt.y);

            //setUpdatesEnabled(false);
            update(m_pt.x - m_pt_normal.width()/2, m_pt.y - m_pt_normal.width()/2, m_pt_normal.width(), m_pt_normal.height());
            //setUpdatesEnabled(true);
        }
        else if(pkg->type == TS_RECORD_TYPE_RDP_IMAGE) {
            if(dat->data_len() <= sizeof(TS_RECORD_PKG) + sizeof(TS_RECORD_RDP_IMAGE_INFO)) {
                qDebug() << "invalid record package(3).";
                delete dat;
                return;
            }

            TS_RECORD_RDP_IMAGE_INFO* info = (TS_RECORD_RDP_IMAGE_INFO*)(dat->data_buf() + sizeof(TS_RECORD_PKG));
            uint8_t* img_dat = dat->data_buf() + sizeof(TS_RECORD_PKG) + sizeof(TS_RECORD_RDP_IMAGE_INFO);
            uint32_t img_len = dat->data_len() - sizeof(TS_RECORD_PKG) - sizeof(TS_RECORD_RDP_IMAGE_INFO);

            rdpimg2QImage(m_img_update, info->width, info->height, info->bitsPerPixel, (info->format == TS_RDP_IMG_BMP) ? true : false, img_dat, img_len);

            m_img_update_x = info->destLeft;
            m_img_update_y = info->destTop;
            m_img_update_w = info->destRight - info->destLeft + 1;
            m_img_update_h = info->destBottom - info->destTop + 1;

            setUpdatesEnabled(false);
            QPainter pp(&m_canvas);
            pp.drawImage(m_img_update_x, m_img_update_y, m_img_update, 0, 0, m_img_update_w, m_img_update_h, Qt::AutoColor);

            update(m_img_update_x, m_img_update_y, m_img_update_w, m_img_update_h);
            setUpdatesEnabled(true);
        }

        delete dat;
        return;
    }


    if(dat->data_type() == TYPE_HEADER_INFO) {
        if(dat->data_len() != sizeof(TS_RECORD_HEADER)) {
            qDebug() << "invalid record header.";
            delete dat;
            return;
        }
        memcpy(&m_rec_hdr, dat->data_buf(), sizeof(TS_RECORD_HEADER));
        delete dat;

        qDebug() << "resize (" << m_rec_hdr.basic.width << "," << m_rec_hdr.basic.height << ")";
        if(m_rec_hdr.basic.width > 0 && m_rec_hdr.basic.height > 0) {

            m_canvas = QPixmap(m_rec_hdr.basic.width, m_rec_hdr.basic.height);


            m_win_board_w = frameGeometry().width() - geometry().width();
            m_win_board_h = frameGeometry().height() - geometry().height();

            //setFixedSize(m_rec_hdr.basic.width + m_win_board_w, m_rec_hdr.basic.height + m_win_board_h);
            //resize(m_rec_hdr.basic.width + m_win_board_w, m_rec_hdr.basic.height + m_win_board_h);
            setFixedSize(m_rec_hdr.basic.width, m_rec_hdr.basic.height);
            resize(m_rec_hdr.basic.width, m_rec_hdr.basic.height);

            QDesktopWidget *desktop = QApplication::desktop(); // =qApp->desktop();也可以
            qDebug("desktop width: %d", desktop->width());
            //move((desktop->width() - this->width())/2, (desktop->height() - this->height())/2);
            move(10, (desktop->height() - this->height())/2);
        }

        QString title;
        if (m_rec_hdr.basic.conn_port == 3389)
            title.sprintf("[%s] %s@%s [Teleport-RDP录像回放]", m_rec_hdr.basic.acc_username, m_rec_hdr.basic.user_username, m_rec_hdr.basic.conn_ip);
        else
            title.sprintf("[%s] %s@%s:%d [Teleport-RDP录像回放]", m_rec_hdr.basic.acc_username, m_rec_hdr.basic.user_username, m_rec_hdr.basic.conn_ip, m_rec_hdr.basic.conn_port);

        setWindowTitle(title);

        return;
    }


    delete dat;
}
