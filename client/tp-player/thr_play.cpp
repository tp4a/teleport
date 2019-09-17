#include <QCoreApplication>
#include <QDateTime>
#include <QDebug>
#include <QDir>
#include <QFile>
#include <QStandardPaths>

#include "thr_play.h"
#include "record_format.h"

ThreadPlay::ThreadPlay(const QString& res)
{
    m_need_stop = false;
    m_need_pause = false;
    m_speed = 2;
    m_res = res;
    m_thr_download = nullptr;
}

ThreadPlay::~ThreadPlay() {
    stop();
}

void ThreadPlay::stop() {
    if(!isRunning())
        return;

    // warning: never call stop() inside thread::run() loop.

    m_need_stop = true;
    wait();
    qDebug() << "play-thread end.";

    if(m_thr_download) {
        m_thr_download->stop();
        //m_thr_download->wait();
        delete m_thr_download;
        m_thr_download = nullptr;
    }
}

void ThreadPlay::_notify_message(const QString& msg) {
    update_data* _msg = new update_data(TYPE_MESSAGE);
    _msg->message(msg);
    emit signal_update_data(_msg);
}

void ThreadPlay::_notify_error(const QString& err_msg) {
    update_data* _err = new update_data(TYPE_ERROR);
    _err->message(err_msg);
    emit signal_update_data(_err);
}


void ThreadPlay::run() {

//#ifdef __APPLE__
//    QString currentPath = QStandardPaths::writableLocation(QStandardPaths::DesktopLocation);
//    currentPath += "/tp-testdata/";
//#else
//    QString currentPath = QCoreApplication::applicationDirPath() + "/testdata/";
//#endif

    // /Users/apex/Library/Preferences/tp-player
    //qDebug() << "appdata:" << QStandardPaths::writableLocation(QStandardPaths::AppConfigLocation);

    // /private/var/folders/_3/zggrxjdx1lxcdqnfsbgpcwzh0000gn/T
    //qDebug() << "tmp:" << QStandardPaths::writableLocation(QStandardPaths::TempLocation);

    // base of data path (include the .tpr file)
    QString path_base;

    QString _tmp_res = m_res.toLower();
    if(_tmp_res.startsWith("http")) {
        qDebug() << "DOWNLOAD";
        m_need_download = true;

        _notify_message("正在缓存录像数据，请稍候...");

        m_thr_download = new ThreadDownload(m_res);
        m_thr_download->start();

        QString msg;
        for(;;) {
            msleep(500);

            if(m_need_stop)
                return;

            if(!m_thr_download->prepare(path_base, msg)) {
                msg.sprintf("指定的文件或目录不存在！\n\n%s", _tmp_res.toStdString().c_str());
                _notify_error(msg);
                return;
            }

            if(path_base.length())
                break;
        }
    }
    else {
        {
            QFileInfo fi(m_res);
            if(fi.isSymLink())
                _tmp_res = fi.symLinkTarget();
            else
                _tmp_res = m_res;
        }

        QFileInfo fi(_tmp_res);
        if(!fi.exists()) {
            QString msg;
            msg.sprintf("指定的文件或目录不存在！\n\n%s", _tmp_res.toStdString().c_str());
            _notify_error(msg);
            return;
        }

        if(fi.isFile()) {
            path_base = fi.path();
        }
        else if(fi.isDir()) {
            path_base = m_res;
        }

        path_base += "/";
    }


    qint64 read_len = 0;
    uint32_t total_pkg = 0;
    uint32_t total_ms = 0;
    uint32_t file_count = 0;

    //======================================
    // 加载录像基本信息数据
    //======================================

    QString tpr_filename(path_base);
    tpr_filename += "tp-rdp.tpr";

    QFile f_hdr(tpr_filename);
    if(!f_hdr.open(QFile::ReadOnly)) {
        qDebug() << "Can not open " << tpr_filename << " for read.";
        QString msg;
        msg.sprintf("无法打开录像信息文件！\n\n%s", tpr_filename.toStdString().c_str());
        _notify_error(msg);
        return;
    }
    else {
        update_data* dat = new update_data(TYPE_HEADER_INFO);
        dat->alloc_data(sizeof(TS_RECORD_HEADER));

        read_len = f_hdr.read((char*)(dat->data_buf()), dat->data_len());
        if(read_len != sizeof(TS_RECORD_HEADER)) {
            delete dat;
            qDebug() << "invaid .tpr file.";
            QString msg;
            msg.sprintf("错误的录像信息文件！\n\n%s", tpr_filename.toStdString().c_str());
            _notify_error(msg);
            return;
        }

        TS_RECORD_HEADER* hdr = (TS_RECORD_HEADER*)dat->data_buf();

        if(hdr->info.ver != 4) {
            delete dat;
            qDebug() << "invaid .tpr file.";
            QString msg;
            msg.sprintf("不支持的录像文件版本 %d！\n\n此播放器支持录像文件版本 4。", hdr->info.ver);
            _notify_error(msg);
            return;
        }

        if(hdr->basic.width == 0 || hdr->basic.height == 0) {
            _notify_error("错误的录像信息，未记录窗口尺寸！");
            return;
        }

        if(hdr->info.dat_file_count == 0) {
            _notify_error("错误的录像信息，未记录数据文件数量！");
            return;
        }

        total_pkg = hdr->info.packages;
        total_ms = hdr->info.time_ms;
        file_count = hdr->info.dat_file_count;

        emit signal_update_data(dat);
    }

    //======================================
    // 加载录像文件数据并播放
    //======================================

    uint32_t pkg_count = 0;
    uint32_t time_pass = 0;
    uint32_t time_last_pass = 0;
    qint64 time_begin = QDateTime::currentMSecsSinceEpoch();
    QString msg;

    for(uint32_t fidx = 0; fidx < file_count; ++fidx) {
        if(m_need_stop) {
            qDebug() << "stop, user cancel 1.";
            break;
        }

        QString tpd_filename;
        tpd_filename.sprintf("%stp-rdp-%d.tpd", path_base.toStdString().c_str(), fidx+1);

        // for test.
        msg.sprintf("无法打开录像数据文件！\n\n%s", tpd_filename.toStdString().c_str());
        _notify_message(msg);

        QFile f_dat(tpd_filename);
        if(!f_dat.open(QFile::ReadOnly)) {
            qDebug() << "Can not open " << tpd_filename << " for read.";
            msg.sprintf("无法打开录像数据文件！\n\n%s", tpd_filename.toStdString().c_str());
            _notify_error(msg);
            return;
        }

        for(;;) {
            if(m_need_stop) {
                qDebug() << "stop, user cancel 2.";
                break;
            }

            if(m_need_pause) {
                msleep(50);
                time_begin += 50;
                continue;
            }

            TS_RECORD_PKG pkg;
            read_len = f_dat.read((char*)(&pkg), sizeof(pkg));
            if(read_len == 0)
                break;
            if(read_len != sizeof(TS_RECORD_PKG)) {
                qDebug() << "invaid .tpd file (1).";
                msg.sprintf("错误的录像数据文件！\n\n%s", tpd_filename.toStdString().c_str());
                _notify_error(msg);
                return;
            }

            update_data* dat = new update_data(TYPE_DATA);
            dat->alloc_data(sizeof(TS_RECORD_PKG) + pkg.size);
            memcpy(dat->data_buf(), &pkg, sizeof(TS_RECORD_PKG));
            read_len = f_dat.read((char*)(dat->data_buf()+sizeof(TS_RECORD_PKG)), pkg.size);
            if(read_len != pkg.size) {
                delete dat;
                qDebug() << "invaid .tpd file.";
                msg.sprintf("错误的录像数据文件！\n\n%s", tpd_filename.toStdString().c_str());
                _notify_error(msg);
                return;
            }

            pkg_count++;

            time_pass = (uint32_t)(QDateTime::currentMSecsSinceEpoch() - time_begin) * m_speed;
            if(time_pass > total_ms)
                time_pass = total_ms;
            if(time_pass - time_last_pass > 200) {
                update_data* _passed_ms = new update_data(TYPE_PLAYED_MS);
                _passed_ms->played_ms(time_pass);
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
                    update_data* _passed_ms = new update_data(TYPE_PLAYED_MS);
                    _passed_ms->played_ms(_time_pass);
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
    }

    if(pkg_count < total_pkg) {
        qDebug() << "total-pkg:" << total_pkg << ", played:" << pkg_count;
        msg.sprintf("录像数据文件有误！\n\n部分录像数据缺失！");
        _notify_message(msg);
    }

    update_data* _end = new update_data(TYPE_END);
    emit signal_update_data(_end);
}
