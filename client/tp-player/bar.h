#ifndef BAR_H
#define BAR_H

#include <QPainter>
#include <QPixmap>
#include <QWidget>

typedef enum {
    res_bg_left = 0,    // 背景左侧
    res_bg_mid,         // 背景中间，拉伸填充
    res_bg_right,       // 背景右侧
    res_bs_left,        // 速度按钮（未选中）左侧
    res_bs_mid,         // 速度按钮（未选中）中间，拉伸填充
    res_bs_right,       // 速度按钮（未选中）右侧
    res_bsh_left,       // 速度按钮（选中）左侧
    res_bsh_mid,        // 速度按钮（选中）中间，拉伸填充
    res_bsh_right,      // 速度按钮（选中）右侧
    res_pbh_left,       // 进度条（已经过）左侧
    res_pbh_mid,        // 进度条（已经过）中间，拉伸填充
    res_pb_mid,         // 进度条（未到达）中间，拉伸填充
    res_pb_right,       // 进度条（未到达）右侧
//    res_pp,             // 进度条上的指示点，未选中
//    res_pph,            // 进度条上的指示点，选中高亮
    res_cb,             // 复选框，未选中
    res_cbh,            // 复选框，已勾选
//    res_play,
//    res_play_hover,
//    res_pause,
//    res_pause_hover,

    res__max
}RES_ID;

typedef enum {
    widget_normal = 0,
    widget_hover,
    widget__max
}WIDGET_STAT;

typedef enum {
    play_running = 0,
    play_paused,
    play__max
}PLAY_STAT;

//typedef enum {
//    speed_1x = 0,
//    speed_2x,
//    speed_4x,
//    speed_8x,
//    speed_16x,
//    speed__max,
//}SPEED;

#define speed_1x        0
#define speed_2x        1
#define speed_4x        2
#define speed_8x        3
#define speed_16x       4
#define speed_count     5

class Bar {
public:
    Bar();
    ~Bar();

    bool init(QWidget* owner);
    void start(uint32_t total_ms, int width);
    void end();
    void draw(QPainter& painter, const QRect& rc);
    void update_passed_time(uint32_t ms);

    QRect rc(){return m_rc;}

    void onMouseMove(int x, int y);

private:
    void _init_imgages();
    void _ms_to_str(uint32_t ms, QString& str);

private:
    QWidget* m_owner;

    uint32_t m_total_ms;    // 录像的总时长
    uint32_t m_passed_ms;   // 已经播放了的时长
    int m_percent;       // 已经播放了的百分比（0~100）
    int m_percent_last_draw;
    QString m_str_total_time;
    QString m_str_passed_time;
    QString m_str_passed_time_last_draw;

    bool m_img_ready;

    //  从资源中加载的原始图像
    QPixmap m_res[res__max];
    QPixmap m_img_progress_pointer[widget__max];

    int m_width;
    int m_height;
    // 此浮动窗相对于父窗口的坐标和大小
    QRect m_rc;

    // 尺寸和定位（此浮动窗内部的相对坐标）
    QRect m_rc_btn_play;
    QRect m_rc_btn_speed[speed_count];
    QRect m_rc_time_passed;
    QRect m_rc_time_total;
    QRect m_rc_progress;
    QRect m_rc_skip;

    // 画布，最终输出的图像
    //QPixmap m_canvas;

    // 合成的图像
    QPixmap m_img_bg;
    QPixmap m_img_btn_play[play__max][widget__max];
    QPixmap m_img_btn_speed[speed_count][widget__max];
    QPixmap m_img_progress;
    QPixmap m_img_skip[widget__max];
    QPixmap m_img_time_passed;
    QPixmap m_img_time_total;

    // 各种状态
    bool m_play_hover;
    bool m_playing; // 0=play, 2=pause
    int m_speed_selected;
    int m_speed_hover;    // speed__max=no-hover
    bool m_skip_selected;
    //bool m_skip_hover;
};

#endif // BAR_H
