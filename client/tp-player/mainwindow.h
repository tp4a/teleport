#ifndef MAINWINDOW_H
#define MAINWINDOW_H

#include <QMainWindow>
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
    void paintEvent(QPaintEvent *e);
    void mouseMoveEvent(QMouseEvent *e);

private slots:
    void on_update_data(update_data*);

private:
    Ui::MainWindow *ui;
    //QImage m_bg;
    bool m_shown;
    bool m_show_default;
    bool m_bar_shown;
    QPixmap m_default_bg;

    ThreadPlay m_thr_play;

    QPixmap m_canvas;

    Bar m_bar;

    TS_RECORD_HEADER m_rec_hdr;

    QPixmap m_pt_normal;
    TS_RECORD_RDP_POINTER m_pt;
};

#endif // MAINWINDOW_H
