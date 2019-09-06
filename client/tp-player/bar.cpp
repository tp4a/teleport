#include "bar.h"

#include <QPainter>

Bar::Bar() {

}

Bar::~Bar() {

}

bool Bar::init(QWidget* owner, int width) {
    m_owner = owner;

    // 加载所需的图像资源
    if(!m_bg_left.load(":/tp-player/res/bar/bg-left.png")
            || !m_bg_mid.load(":/tp-player/res/bar/bg-mid.png")
            || !m_bg_right.load(":/tp-player/res/bar/bg-right.png")
            || !m_btn_left.load(":/tp-player/res/bar/btn-left.png")
            || !m_btn_mid.load(":/tp-player/res/bar/btn-mid.png")
            || !m_btn_right.load(":/tp-player/res/bar/btn-right.png")
            || !m_btnsel_left.load(":/tp-player/res/bar/btnsel-left.png")
            || !m_btnsel_mid.load(":/tp-player/res/bar/btnsel-mid.png")
            || !m_btnsel_right.load(":/tp-player/res/bar/btnsel-right.png")
            || !m_prgbarh_left.load(":/tp-player/res/bar/prgbarh-left.png")
            || !m_prgbarh_mid.load(":/tp-player/res/bar/prgbarh-mid.png")
            || !m_prgbar_left.load(":/tp-player/res/bar/prgbar-left.png")
            || !m_prgbar_mid.load(":/tp-player/res/bar/prgbar-mid.png")
            || !m_prgbar_right.load(":/tp-player/res/bar/prgbar-right.png")
            || !m_prgpt.load(":/tp-player/res/bar/prgpt.png")
            || !m_prgpt_hover.load(":/tp-player/res/bar/prgpt-hover.png")
            || !m_select.load(":/tp-player/res/bar/select.png")
            || !m_selected.load(":/tp-player/res/bar/selected.png")
            || !m_play.load(":/tp-player/res/bar/play.png")
            || !m_play_hover.load(":/tp-player/res/bar/play-hover.png")
    )
        return false;

    // 创建背景图像
    m_bg = QPixmap(width, m_bg_left.height());
    m_bg.fill(Qt::transparent);//用透明色填充
    QPainter pp(&m_bg);
    pp.drawPixmap(0, 0, m_bg_left, 0, 0, m_bg_left.width(), m_bg_left.height());
    pp.drawPixmap(m_bg_left.width(), 0, m_bg.width() - m_bg_left.width() - m_bg_right.width(), m_bg_left.height(), m_bg_mid);
    pp.drawPixmap(m_bg.width()-m_bg_right.width(), 0, m_bg_right, 0, 0, m_bg_right.width(), m_bg_right.height());

    //pp.drawPixmap(10, 10, m_prgpt, 0, 0, m_prgpt.width(), m_prgpt.height());
    pp.drawPixmap(10, 10, m_play.width(), m_play.height(), m_play);


    return true;
}

void Bar::draw(QPainter& painter, const QRect& rc){
    painter.drawPixmap(10, 150, m_bg, 0, 0, m_bg.width(), m_bg.height());
}
