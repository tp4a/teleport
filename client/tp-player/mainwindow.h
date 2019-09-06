#ifndef MAINWINDOW_H
#define MAINWINDOW_H

#include <QMainWindow>
#include <QVector>
#include "bar.h"
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
    bool m_shown;

    ThreadPlay m_thr_play;

    QPixmap m_canvas;

    Bar m_bar;

    bool m_show_bg;
    TS_RECORD_HEADER m_rec_hdr;

    QImage m_pt_normal;
    TS_RECORD_RDP_POINTER m_pt;
    QVector<TS_RECORD_RDP_POINTER> m_pt_history;


    QImage m_img_update;
    int m_win_board_w;
    int m_win_board_h;
    int m_img_update_x;
    int m_img_update_y;
    int m_img_update_w;
    int m_img_update_h;
};

#endif // MAINWINDOW_H
