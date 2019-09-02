#include <QDebug>
#include <QFile>

#include "thr_play.h"
#include "record_format.h"

static QString REPLAY_PATH = "E:\\work\\tp4a\\teleport\\server\\share\\replay\\rdp\\000000197\\";


ThreadPlay::ThreadPlay()
{
    m_need_stop = false;
}

void ThreadPlay::stop() {
    m_need_stop = true;
}

void ThreadPlay::run() {
    qint64 read_len = 0;
    uint32_t total_pkg = 0;

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

        emit signal_update_data(dat);
    }



    QString dat_filename(REPLAY_PATH);
    dat_filename += "tp-rdp.dat";

    QFile f_dat(dat_filename);
    if(!f_dat.open(QFile::ReadOnly)) {
        qDebug() << "Can not open " << dat_filename << " for read.";
        return;
    }

    for(uint32_t i = 0; i < total_pkg; ++i) {
        if(m_need_stop) {
            qDebug() << "stop, user cancel.";
            break;
        }

        TS_RECORD_PKG pkg;
        read_len = f_dat.read((char*)(&pkg), sizeof(pkg));
        if(read_len != sizeof(TS_RECORD_PKG)) {
            qDebug() << "invaid .dat file.";
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

        emit signal_update_data(dat);
        msleep(5);
    }
}
