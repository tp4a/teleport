#include <QDateTime>
#include <QDebug>
#include <QFile>

#include "thr_play.h"
#include "record_format.h"

static QString REPLAY_PATH = "E:\\work\\tp4a\\teleport\\server\\share\\replay\\rdp\\000000197\\";


ThreadPlay::ThreadPlay()
{
    m_need_stop = false;
    m_need_pause = false;
    m_speed = 2;
}

void ThreadPlay::stop() {
    m_need_stop = true;
}

void ThreadPlay::run() {

    sleep(1);

    qint64 read_len = 0;
    uint32_t total_pkg = 0;
    uint32_t total_ms = 0;

    QString hdr_filename(REPLAY_PATH);
    hdr_filename += "tp-rdp.tpr";

    QFile f_hdr(hdr_filename);
    if(!f_hdr.open(QFile::ReadOnly)) {
        qDebug() << "Can not open " << hdr_filename << " for read.";
        return;
    }
    else {
        update_data* dat = new update_data;
        dat->data_type(TYPE_HEADER_INFO);
        dat->alloc_data(sizeof(TS_RECORD_HEADER));

        read_len = f_hdr.read((char*)(dat->data_buf()), dat->data_len());
        if(read_len != sizeof(TS_RECORD_HEADER)) {
            delete dat;
            qDebug() << "invaid .tpr file.";
            return;
        }

        TS_RECORD_HEADER* hdr = (TS_RECORD_HEADER*)dat->data_buf();
        total_pkg = hdr->info.packages;
        total_ms = hdr->info.time_ms;

        emit signal_update_data(dat);
    }



    QString dat_filename(REPLAY_PATH);
    dat_filename += "tp-rdp.dat";

    QFile f_dat(dat_filename);
    if(!f_dat.open(QFile::ReadOnly)) {
        qDebug() << "Can not open " << dat_filename << " for read.";
        return;
    }

    uint32_t time_pass = 0;
    uint32_t time_last_pass = 0;

    qint64 time_begin = QDateTime::currentMSecsSinceEpoch();

    for(uint32_t i = 0; i < total_pkg; ++i) {
        if(m_need_stop) {
            qDebug() << "stop, user cancel.";
            break;
        }

        if(m_need_pause) {
            msleep(50);
            time_begin += 50;
            continue;
        }

        TS_RECORD_PKG pkg;
        read_len = f_dat.read((char*)(&pkg), sizeof(pkg));
        if(read_len != sizeof(TS_RECORD_PKG)) {
            qDebug() << "invaid .dat file (1).";
            return;
        }

        update_data* dat = new update_data;
        dat->data_type(TYPE_DATA);
        dat->alloc_data(sizeof(TS_RECORD_PKG) + pkg.size);
        memcpy(dat->data_buf(), &pkg, sizeof(TS_RECORD_PKG));
        read_len = f_dat.read((char*)(dat->data_buf()+sizeof(TS_RECORD_PKG)), pkg.size);
        if(read_len != pkg.size) {
            delete dat;
            qDebug() << "invaid .dat file.";
            return;
        }

        time_pass = (uint32_t)(QDateTime::currentMSecsSinceEpoch() - time_begin) * m_speed;
        if(time_pass > total_ms)
            time_pass = total_ms;
        if(time_pass - time_last_pass > 200) {
            update_data* _passed_ms = new update_data;
            _passed_ms->data_type(TYPE_TIMER);
            _passed_ms->passed_ms(time_pass);
            emit signal_update_data(_passed_ms);
            time_last_pass = time_pass;
        }

        if(time_pass >= pkg.time_ms) {
            emit signal_update_data(dat);
            continue;
        }

        // 需要等待
        uint32_t time_wait = pkg.time_ms - time_pass;
        uint32_t wait_this_time = 0;
        for(;;) {
            if(m_need_pause) {
                msleep(50);
                time_begin += 50;
                continue;
            }

            wait_this_time = time_wait;
            if(wait_this_time > 10)
                wait_this_time = 10;

            if(m_need_stop) {
                qDebug() << "stop, user cancel (2).";
                break;
            }

            msleep(wait_this_time);

            uint32_t _time_pass = (uint32_t)(QDateTime::currentMSecsSinceEpoch() - time_begin) * m_speed;
            if(_time_pass > total_ms)
                _time_pass = total_ms;
            if(_time_pass - time_last_pass > 200) {
                update_data* _passed_ms = new update_data;
                _passed_ms->data_type(TYPE_TIMER);
                _passed_ms->passed_ms(_time_pass);
                emit signal_update_data(_passed_ms);
                time_last_pass = _time_pass;
            }

            time_wait -= wait_this_time;
            if(time_wait == 0) {
                emit signal_update_data(dat);
                break;
            }
        }
    }

    update_data* _end = new update_data;
    _end->data_type(TYPE_END);
    emit signal_update_data(_end);
}
