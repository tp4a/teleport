#ifndef BAR_H
#define BAR_H

#include <QPainter>
#include <QPixmap>
#include <QWidget>


class Bar {
public:
    Bar();
    ~Bar();

    bool init(QWidget* owner, int width);
    void draw(QPainter& painter, const QRect& rc);

private:
    QWidget* m_owner;
    int m_width;


    QPixmap m_bg;

    QPixmap m_bg_left;
    QPixmap m_bg_mid;
    QPixmap m_bg_right;

    QPixmap m_btn_left;
    QPixmap m_btn_mid;
    QPixmap m_btn_right;

    QPixmap m_btnsel_left;
    QPixmap m_btnsel_mid;
    QPixmap m_btnsel_right;

    QPixmap m_prgbarh_left;
    QPixmap m_prgbarh_mid;

    QPixmap m_prgbar_left;
    QPixmap m_prgbar_mid;
    QPixmap m_prgbar_right;

    QPixmap m_prgpt;
    QPixmap m_prgpt_hover;

    QPixmap m_select;
    QPixmap m_selected;

    QPixmap m_play;
    QPixmap m_play_hover;
};

#endif // BAR_H
