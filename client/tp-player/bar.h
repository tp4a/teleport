#ifndef BAR_H
#define BAR_H

#include <QPainter>
#include <QPixmap>
#include <QWidget>

typedef enum {
    res_bg_left = 0,        // 背景
    res_bg_mid,
    res_bg_right,
    res_btn_normal_left,    // 按钮（速度选择），普通状态
    res_btn_normal_mid,
    res_btn_normal_right,
    res_btn_sel_left,       // 按钮（速度选择），已选中
    res_btn_sel_mid,
    res_btn_sel_right,
    res_btn_hover_left,     // 按钮（速度选择），鼠标滑过
    res_btn_hover_mid,
    res_btn_hover_right,

    res_prgbarh_left,       // 进度条（已经过）左侧
    res_prgbarh_mid,        // 进度条（已经过）中间，拉伸填充
    res_prgbar_mid,         // 进度条（未到达）中间，拉伸填充
    res_prgbar_right,       // 进度条（未到达）右侧
    res_chkbox_normal,      // 复选框
    res_chkbox_hover,
    res_chkbox_sel_normal,
    res_chkbox_sel_hover,

    res__max
}RES_ID;

//typedef enum {
//    widget_normal = 0,
//    widget_hover,
//    widget__max
//}WIDGET_STAT;

#define widget_normal           0
#define widget_hover            1
#define widget_state_count      2

//typedef enum {
//    play_running = 0,
//    play_paused,
//    play__max
//}PLAY_STAT;

#define play_running            0
#define play_paused             1
#define play_state_count        2

#define speed_1x        0
#define speed_2x        1
#define speed_4x        2
#define speed_8x        3
#define speed_count     4

#define btnspd_normal       0
#define btnspd_sel          1
#define btnspd_hover        2
#define btnspd_state_count  3

#define chkbox_normal           0
#define chkbox_selected         1
#define chkbox_state_count      2

class MainWindow;

class Bar {
public:
    Bar();
    ~Bar();

    bool init(MainWindow* owner);
    void start(uint32_t total_ms, int width);
    void end();
    void draw(QPainter& painter, const QRect& rc);
    void update_passed_time(uint32_t ms);

    int get_speed();

    QRect rc(){return m_rc;}

    void onMouseMove(int x, int y);
    void onMousePress(int x, int y, Qt::MouseButton button);
    void onMouseRelease(int x, int y, Qt::MouseButton button);

private:
    void _init_imgages();
    void _ms_to_str(uint32_t ms, QString& str);

private:
    MainWindow* m_owner;

    uint32_t m_total_ms;    // 录像的总时长
    uint32_t m_played_ms;   // 已经播放了的时长
    int m_percent;       // 已经播放了的百分比（0~100）
    int m_percent_last_draw;
    QString m_str_total_time;
    QString m_str_passed_time;
    QString m_str_passed_time_last_draw;

    bool m_img_ready;

    //  从资源中加载的原始图像
    QPixmap m_res[res__max];
    QPixmap m_img_progress_pointer[widget_state_count];

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
    QPixmap m_img_btn_play[play_state_count][widget_state_count];
    QPixmap m_img_btn_speed[speed_count][btnspd_state_count];
    QPixmap m_img_progress;
    QPixmap m_img_skip[chkbox_state_count][widget_state_count];
    QPixmap m_img_time_passed;
    QPixmap m_img_time_total;

    // 各种状态
    bool m_playing; // 0=play, 2=pause
    bool m_play_hover;
    int m_speed_selected;
    int m_speed_hover;    // speed__max=no-hover
    bool m_skip_selected;
    bool m_skip_hover;
    bool m_progress_hover;
    bool m_progress_pressed;

    uint32_t m_resume_ms;   // after drag progress-pointer, resume play from here.
};

#endif // BAR_H
