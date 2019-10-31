#ifndef THR_PLAY_H
#define THR_PLAY_H

#include <QThread>
#include "update_data.h"
#include "downloader.h"

// 根据播放规则，将要播放的图像发送给主UI线程进行显示
class ThrPlay : public QThread
{
    Q_OBJECT

friend class ThrData;
public:
    ThrPlay();
    ~ThrPlay();

    virtual void run();
    void stop();
    void pause() {m_need_pause = true;}
    void resume() {m_need_pause = false;}
    void speed(int s) {if(s >= 1 && s <= 16) m_speed = s;}

private:
    void _notify_message(const QString& msg);
    void _notify_error(const QString& err_msg);

signals:
    void signal_update_data(UpdateData*);

private:
    bool m_need_stop;
    bool m_need_pause;
    int m_speed;
};

#endif // THR_PLAY_H
