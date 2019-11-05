#include <QCoreApplication>
#include <QDateTime>
#include <QDebug>

#include "thr_play.h"
#include "thr_data.h"
#include "mainwindow.h"
#include "record_format.h"
#include "util.h"


/*
 * 录像播放流程：
 *  - 数据处理线程，该线程负责（下载）文件、解析文件，将数据准备成待播放队列；
 *    + 数据处理线程维护待播放队列，少于500个则填充至1000个，每20ms检查一次队列是否少于500个。
 *  - 播放线程从队列中取出一个数据，判断当前时间是否应该播放此数据，如果应该，则将此数据发送给主UI
 *    + if( 播放速率 * (当前时间 - 播放时间) >= (当前数据包偏移时间 - 上个数据包偏移时间))  则 播放
 *    + 如选择“跳过无操作时间”，则数据包偏移时间差超过3秒的，视为3秒。
 */


ThrPlay::ThrPlay(MainWindow* mainwnd) {
    m_mainwnd = mainwnd;
    m_need_stop = false;
    m_need_pause = false;
    m_speed = 1;
    m_skip = false;
    m_start_ms = 0;
}

ThrPlay::~ThrPlay() {
    stop();
}

void ThrPlay::stop() {
    if(!isRunning())
        return;

    // warning: never call stop() inside thread::run() loop.

    m_need_stop = true;
    wait();
    qDebug() << "play-thread end.";

//    if(m_thr_data) {
//        m_thr_data->stop();
//        qDebug("delete thrData.");
//        //m_thr_download->wait();
//        delete m_thr_data;
//        m_thr_data = nullptr;
//    }
}

void ThrPlay::_notify_message(const QString& msg) {
    UpdateData* _msg = new UpdateData(TYPE_MESSAGE);
    _msg->message(msg);
    emit signal_update_data(_msg);
}

void ThrPlay::_notify_error(const QString& msg) {
    UpdateData* _msg = new UpdateData(TYPE_ERROR);
    _msg->message(msg);
    emit signal_update_data(_msg);
}

void ThrPlay::resume(bool relocate, uint32_t start_ms) {
    if(relocate) {
        m_start_ms = start_ms;
        m_first_run = true;
    }
    m_need_pause = false;
}

void ThrPlay::run() {

    ThrData* thr_data = m_mainwnd->get_thr_data();
    m_first_run = true;
    uint32_t last_time_ms = 0;
    uint32_t last_pass_ms = 0;

    UpdateData* dat = nullptr;
    for(;;) {
        if(m_need_stop)
            break;

        // 1. 从ThrData的待播放队列中取出一个数据
        dat = thr_data->get_data();
        if(dat == nullptr) {
            msleep(20);
            continue;
        }

        if(m_first_run) {
            m_first_run = false;
           _notify_message("");
        }

        if(m_start_ms > 0) {
            if(dat->get_time() < m_start_ms) {
                emit signal_update_data(dat);
                continue;
            }
            last_time_ms = m_start_ms;
            m_start_ms = 0;
        }

        // 2. 根据数据包的信息，等待到播放时间点
        uint32_t need_wait_ms = 0;
        uint32_t this_time_ms = dat->get_time();
        uint32_t this_pass_ms = last_time_ms;
        if(this_time_ms > 0) {
            need_wait_ms = this_time_ms - last_time_ms;

            if(need_wait_ms > 0) {
                uint32_t time_wait = 0;

                // 如果设置了跳过无操作区间，将超过1秒的等待时间压缩至1秒。
                if(m_skip) {
                    if(need_wait_ms > 1000)
                        need_wait_ms = 1000;
                }

                for(;;) {
                    time_wait = need_wait_ms > 10 ? 10 : need_wait_ms;
                    msleep(time_wait);

                    if(m_need_pause) {
                        while(m_need_pause) {
                            msleep(50);
                            if(m_need_stop)
                                break;
                        }
                    }

                    if(m_need_stop)
                        break;

                    if(m_start_ms > 0) {
//                        if(dat) {
//                            delete dat;
//                            dat = nullptr;
//                        }
                        break;
                    }

                    time_wait *= m_speed;

                    // 如果已经在等待长时间无操作区间内，用户设置了跳过无操作区间，则将超过0.5秒的等待时间压缩至0.5秒。
                    if(m_skip) {
                        if(need_wait_ms > 500)
                            need_wait_ms = 500;
                    }

                    this_pass_ms += time_wait;
                    if(this_pass_ms - last_pass_ms > 100) {
                        UpdateData* _passed_ms = new UpdateData(TYPE_PLAYED_MS);
                        _passed_ms->played_ms(this_pass_ms);
                        emit signal_update_data(_passed_ms);
                        last_pass_ms = this_pass_ms;
                    }

                    if(need_wait_ms <= time_wait)
                        break;
                    else
                        need_wait_ms -= time_wait;
                }

                if(m_need_stop)
                    break;

//                if(m_start_ms > 0) {
//                    if(dat) {
//                        delete dat;
//                        dat = nullptr;
//                    }
//                    break;
//                }
            }

            last_time_ms = this_time_ms;
        }

        // 3. 将数据包发送给主UI界面进行显示
        if(dat->data_type() == TYPE_END) {
            _notify_message(LOCAL8BIT("播放结束"));
        }

        emit signal_update_data(dat);
    }

    if(dat != nullptr)
        delete dat;
}
