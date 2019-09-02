#include "mainwindow.h"
#include "ui_mainwindow.h"
#include "rle.h"

#include <QMatrix>
#include <QDebug>
#include <QPainter>

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
            out = QImage(_dat, w, h, QImage::Format_RGB16);
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

    setWindowFlags(windowFlags()&~Qt::WindowMaximizeButtonHint);    // 禁止最大化按钮
    //setFixedSize(this->width(),this->height());                     // 禁止拖动窗口大小

    resize(m_bg.width(), m_bg.height());

    connect(&m_thr_play, SIGNAL(signal_update_data(update_data*)), this, SLOT(on_update_data(update_data*)));
}

MainWindow::~MainWindow()
{
    m_thr_play.stop();
    m_thr_play.wait();
    delete ui;
}

void MainWindow::paintEvent(QPaintEvent *)
{
    QPainter painter(this);

    if(m_show_bg) {
        //qDebug() << "draw bg.";
        painter.setBrush(Qt::black);
        painter.drawRect(this->rect());

        int x = (rect().width() - m_bg.width()) / 2;
        int y = (rect().height() - m_bg.height()) / 2;
        painter.drawImage(x, y, m_bg);
        //painter.drawPixmap(rect(), m_bg1);
    }

    else {
        painter.drawImage(m_img_update_x, m_img_update_y, m_img_update, 0, 0, m_img_update_w, m_img_update_h, Qt::AutoColor);
        //qDebug() << "draw pt (" << m_pt.x << "," << m_pt.y << ")";
        painter.drawImage(m_pt.x, m_pt.y, m_pt_normal);
    }


    if(!m_shown) {
        m_shown = true;
        m_thr_play.start();
    }
}

void MainWindow::on_update_data(update_data* dat) {
    if(!dat)
        return;
//    qDebug() << "slot-event: " << dat->data_type();

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

            memcpy(&m_pt, dat->data_buf() + sizeof(TS_RECORD_PKG), sizeof(TS_RECORD_RDP_POINTER));
            update();
            //update(m_pt.x - 8, m_pt.y - 8, 32, 32);
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

            qDebug() << "img " << ((info->format == TS_RDP_IMG_BMP) ? "+" : " ") << " (" << m_img_update_x << "," << m_img_update_y << "), [" << m_img_update.width() << "x" << m_img_update.height() << "]";


            update(m_img_update_x, m_img_update_y, m_img_update_w, m_img_update_h);
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
            resize(m_rec_hdr.basic.width, m_rec_hdr.basic.height);
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
