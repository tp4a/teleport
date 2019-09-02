#ifndef MAINWINDOW_H
#define MAINWINDOW_H

#include <QMainWindow>
#include "thr_play.h"
#include "update_data.h"
#include "record_format.h"

namespace Ui {
class MainWindow;
}

class MainWindow : public QMainWindow
{
    Q_OBJECT

public:
    explicit MainWindow(QWidget *parent = nullptr);
    ~MainWindow();

private:
    void paintEvent(QPaintEvent *);


private slots:
    void on_update_data(update_data*);

private:
    Ui::MainWindow *ui;
    QImage m_bg;
    QImage m_pt_normal;
    QImage m_img_update;
    //QPixmap m_bg1;
    bool m_shown;

    ThreadPlay m_thr_play;

    bool m_show_bg;
    TS_RECORD_HEADER m_rec_hdr;
    TS_RECORD_RDP_POINTER m_pt;

    int m_img_update_x;
    int m_img_update_y;
    int m_img_update_w;
    int m_img_update_h;
};

#endif // MAINWINDOW_H
