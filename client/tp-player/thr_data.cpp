#include <QDebug>
#include <QDir>
#include <QFile>
#include <QNetworkCookie>
#include <QStandardPaths>
#include <qcoreapplication.h>

#include "thr_play.h"
#include "thr_data.h"
#include "util.h"
#include "downloader.h"
#include "record_format.h"
#include "mainwindow.h"


//=================================================================
// ThrData
//=================================================================

ThrData::ThrData(MainWindow* mainwin, const QString& res) {
    m_mainwin = mainwin;
    m_res = res;
    m_need_download = false;
    m_need_stop = false;
//    m_dl = nullptr;

#ifdef __APPLE__
    QString data_path_base = QStandardPaths::writableLocation(QStandardPaths::DesktopLocation);
    data_path_base += "/tp-testdata/";
#else
    m_local_data_path_base = QCoreApplication::applicationDirPath() + "/record";
#endif
    qDebug("data-path-base: %s", m_local_data_path_base.toStdString().c_str());

    //    qDebug() << "AppConfigLocation:" << QStandardPaths::writableLocation(QStandardPaths::AppConfigLocation);
    //    qDebug() << "AppDataLocation:" << QStandardPaths::writableLocation(QStandardPaths::AppDataLocation);
    //    qDebug() << "AppLocalDataLocation:" << QStandardPaths::writableLocation(QStandardPaths::AppLocalDataLocation);
    //    qDebug() << "ConfigLocation:" << QStandardPaths::writableLocation(QStandardPaths::ConfigLocation);
    //    qDebug() << "CacheLocation:" << QStandardPaths::writableLocation(QStandardPaths::CacheLocation);
    //    qDebug() << "GenericCacheLocation:" << QStandardPaths::writableLocation(QStandardPaths::GenericCacheLocation);

    /*
AppConfigLocation: "C:/Users/apex/AppData/Local/tp-player"
AppDataLocation: "C:/Users/apex/AppData/Roaming/tp-player"
AppLocalDataLocation: "C:/Users/apex/AppData/Local/tp-player"
ConfigLocation: "C:/Users/apex/AppData/Local/tp-player"
CacheLocation: "C:/Users/apex/AppData/Local/tp-player/cache"
GenericCacheLocation: "C:/Users/apex/AppData/Local/cache"
     */
}

ThrData::~ThrData() {
}

void ThrData::stop() {
    if(!isRunning())
        return;
    m_need_stop = true;
    wait();
    qDebug("data thread stop() end.");
}

void ThrData::_notify_message(const QString& msg) {
    UpdateData* _msg = new UpdateData(TYPE_MESSAGE);
    _msg->message(msg);
    emit signal_update_data(_msg);
}

void ThrData::_notify_error(const QString& msg) {
    UpdateData* _msg = new UpdateData(TYPE_ERROR);
    _msg->message(msg);
    emit signal_update_data(_msg);
}

//	tp-player.exe http://teleport.domain.com:7190/{sub/path/}tp_1491560510_ca67fceb75a78c9d/1234 (注意，并不直接访问此URI，实际上其并不存在)
//                TP服务器地址(可能包含子路径哦，例如上例中的{sub/path/}部分)/session-id(用于判断当前授权用户)/录像会话编号

void ThrData::run() {
    _run();
    qDebug("ThrData thread run() end.");
}

void ThrData::_run() {
    if(!_load_header())
        return;

    if(!_load_keyframe())
        return;

    uint32_t file_idx = 0;
    for(;;) {
        if(m_need_stop)
            break;
        QString str_fidx;
        str_fidx.sprintf("%d", file_idx+1);

        QString tpd_fname = QString("%1/tp-rdp-%2.tpd").arg(m_path_base, str_fidx);
        tpd_fname = QDir::toNativeSeparators(tpd_fname);

        if(m_need_download) {
            QString tmp_fname = QString("%1/tp-rdp-%2.tpd.downloading").arg(m_path_base, str_fidx);
            tmp_fname = QDir::toNativeSeparators(tmp_fname);

            QFileInfo fi_tmp(tmp_fname);
            if(fi_tmp.isFile()) {
                QFile::remove(tmp_fname);
            }

            QFileInfo fi_tpd(tpd_fname);
            if(!fi_tpd.exists()) {
                QString url = QString("%1/audit/get-file?act=read&type=rdp&rid=%2&f=tp-rdp-%3.tpd").arg(m_url_base, m_rid, str_fidx);

                qDebug() << "URL : " << url;
                qDebug() << "TPD : " << tmp_fname;
                if(!_download_file(url, tmp_fname))
                    return;

                if(!QFile::rename(tmp_fname, tpd_fname))
                    return;
            }
        }

        qDebug() << "TPD: " << tpd_fname;

        QFile f_tpd(tpd_fname);
        if(!f_tpd.open(QFile::ReadOnly)) {
            qDebug() << "Can not open " << tpd_fname << " for read.";
            _notify_error(QString("%1\n\n%3").arg(LOCAL8BIT("无法打开录像数据文件！"), tpd_fname));
            return;
        }

        qint64 filesize = f_tpd.size();
        qint64 processed = 0;

        // 加载并解析到待播放队列
        qint64 read_len = 0;
        for(;;) {
            {
//                if(m_need_stop)
//                    break;

//                m_locker.lock();

//                if(m_data.size() > 500) {
//                    msleep(1000);
//                    continue;
//                }

//                m_locker.unlock();
            }

            if(filesize - processed < sizeof(TS_RECORD_PKG)) {
                qDebug("invaid tp-rdp-%d.tpd file, filesize=%d, processed=%d, need=%d.", file_idx+1, filesize, processed, sizeof(TS_RECORD_PKG));
                _notify_error(QString("%1\n\n%3").arg(LOCAL8BIT("错误的录像数据文件！"), tpd_fname));
                return;
            }

            TS_RECORD_PKG pkg;
            read_len = f_tpd.read(reinterpret_cast<char*>(&pkg), sizeof(pkg));
            if(read_len == 0)
                break;
            if(read_len != sizeof(TS_RECORD_PKG)) {
                qDebug("invaid tp-rdp-%d.tpd file, read_len=%d (1).", file_idx+1, read_len);
                _notify_error(QString("%1\n\n%3").arg(LOCAL8BIT("错误的录像数据文件！"), tpd_fname));
                return;
            }
            processed += sizeof(TS_RECORD_PKG);

            if(filesize - processed < pkg.size) {
                qDebug("invaid tp-rdp-%d.tpd file (2).", file_idx+1);
                _notify_error(QString("%1\n\n%3").arg(LOCAL8BIT("错误的录像数据文件！"), tpd_fname));
                return;
            }

            if(pkg.type == TS_RECORD_TYPE_RDP_KEYFRAME) {
                qDebug("----key frame: %d, pkg.size=%d", pkg.time_ms, pkg.size);
                if(pkg.size > 0) {
                    f_tpd.read(pkg.size);
                }
                continue;
            }

            UpdateData* dat = new UpdateData(TYPE_DATA);
            dat->alloc_data(sizeof(TS_RECORD_PKG) + pkg.size);
            memcpy(dat->data_buf(), &pkg, sizeof(TS_RECORD_PKG));
            read_len = f_tpd.read(reinterpret_cast<char*>(dat->data_buf()+sizeof(TS_RECORD_PKG)), pkg.size);
            if(read_len != pkg.size) {
                delete dat;
                qDebug("invaid tp-rdp-%d.tpd file (3).", file_idx+1);
                _notify_error(QString("%1\n\n%3").arg(LOCAL8BIT("错误的录像数据文件！"), tpd_fname));
                return;
            }


            {
                m_locker.lock();
                m_data.enqueue(dat);
//                qDebug("data count: %d", m_data.size());
                m_locker.unlock();
            }
        }




        file_idx += 1;
        if(file_idx >= m_hdr.info.dat_file_count)
            break;
    }
}

bool ThrData::_load_header() {
    QString msg;
    QString _tmp_res = m_res.toLower();

    if(_tmp_res.startsWith("http")) {
        m_need_download = true;
    }

    if(m_need_download) {
        _notify_message(LOCAL8BIT("正在准备录像数据，请稍候..."));

        QStringList _uris = m_res.split('/');
        if(_uris.size() < 3) {
            qDebug() << "invalid param: " << m_res;
            return false;
        }

        m_sid = _uris[_uris.size()-2];
        m_rid = _uris[_uris.size()-1];
        m_url_base = m_res.left(m_res.length() - m_sid.length() - m_rid.length() - 2);

        qDebug() << "url-base:[" << m_url_base << "], sid:[" << m_sid << "], rid:[" << m_rid << "]";

        // download .tpr
        QString url = QString("%1/audit/get-file?act=read&type=rdp&rid=%2&f=tp-rdp.tpr").arg(m_url_base, m_rid);
        QByteArray data;
        if(!_download_file(url, data))
            return false;

        if(data.size() != sizeof(TS_RECORD_HEADER)) {
            qDebug("invalid header file. %d", data.size());
            _notify_error(QString("%1\n\n%2").arg(LOCAL8BIT("指定的文件或目录不存在！"), _tmp_res));
            return false;
        }

        memcpy(&m_hdr, data.data(), sizeof(TS_RECORD_HEADER));
    }
    else {
        QFileInfo fi_chk_link(m_res);
        if(fi_chk_link.isSymLink())
            _tmp_res = fi_chk_link.symLinkTarget();
        else
            _tmp_res = m_res;

        QFileInfo fi(_tmp_res);
        if(!fi.exists()) {
            _notify_error(QString("%1\n\n%2").arg(LOCAL8BIT("指定的文件或目录不存在！"), _tmp_res));
            return false;
        }

        if(fi.isFile()) {
            m_path_base = fi.path();
        }
        else if(fi.isDir()) {
            m_path_base = _tmp_res;
        }

        m_path_base = QDir::toNativeSeparators(m_path_base);

        qDebug() << "PATH_BASE: " << m_path_base;

        QString filename = QString("%1/tp-rdp.tpr").arg(m_path_base);
        filename = QDir::toNativeSeparators(filename);
        qDebug() << "TPR: " << filename;

        QFile f(filename);
        if(!f.open(QFile::ReadOnly)) {
            qDebug() << "Can not open " << filename << " for read.";
            _notify_error(QString("%1\n\n%2").arg(LOCAL8BIT("无法打开录像信息文件！"), filename));
            return false;
        }

        memset(&m_hdr, 0, sizeof(TS_RECORD_HEADER));

        qint64 read_len = 0;
        read_len = f.read(reinterpret_cast<char*>(&m_hdr), sizeof(TS_RECORD_HEADER));
        if(read_len != sizeof(TS_RECORD_HEADER)) {
            qDebug() << "invaid .tpr file.";
            _notify_error(QString("%1\n\n%2").arg(LOCAL8BIT("错误的录像信息文件！"), filename));
            return false;
        }
    }

    if(m_hdr.info.ver != 4) {
        qDebug() << "invaid .tpr file.";
        _notify_error(QString("%1 %2%3").arg(LOCAL8BIT("不支持的录像文件版本 "), QString(m_hdr.info.ver), LOCAL8BIT("！\n\n此播放器支持录像文件版本 4。")));
        return false;
    }

    if(m_hdr.basic.width == 0 || m_hdr.basic.height == 0) {
        _notify_error(LOCAL8BIT("错误的录像信息，未记录窗口尺寸！"));
        return false;
    }

    if(m_hdr.info.dat_file_count == 0) {
        _notify_error(LOCAL8BIT("错误的录像信息，未记录数据文件数量！"));
        return false;
    }


    // 下载得到的数据应该是一个TS_RECORD_HEADER，解析此数据，生成本地文件路径，并保存之。
    if(m_need_download) {
        QDateTime timeUTC;
        //        timeUTC.setTimeSpec(Qt::UTC);
        //        timeUTC.setTime_t(m_hdr.basic.timestamp);
        timeUTC.setSecsSinceEpoch(m_hdr.basic.timestamp);
        QString strUTC = timeUTC.toString("yyyyMMdd-hhmmss");

        QString strAcc(m_hdr.basic.acc_username);
        int idx = strAcc.indexOf('\\');
        if(-1 != idx) {
            QString _domain = strAcc.left(idx);
            QString _user = strAcc.right(strAcc.length() - idx - 1);
            strAcc = _user + "@" + _domain;
        }

        // .../record/RDP-211-admin-user@domain-192.168.0.68-20191015-020243
        m_path_base = QString("%1/RDP-%2-%3-%4-%5-%6").arg(m_local_data_path_base,
                                                           m_rid,
                                                           m_hdr.basic.user_username,
                                                           strAcc,
                                                           m_hdr.basic.host_ip,
                                                           strUTC
                                                           );

        m_path_base = QDir::toNativeSeparators(m_path_base);

        qDebug() << "PATH_BASE: " << m_path_base;

        QDir dir;
        dir.mkpath(m_path_base);
        QFileInfo fi;
        fi.setFile(m_path_base);
        if(!fi.isDir()) {
            qDebug("can not create folder to save downloaded file.");
            return false;
        }

        QString filename = QString("%1/tp-rdp.tpr").arg(m_path_base);
        filename = QDir::toNativeSeparators(filename);
        qDebug() << "TPR: " << filename;

        QFile f;
        f.setFileName(filename);
        if(!f.open(QIODevice::WriteOnly | QFile::Truncate)){
            qDebug("open file for write failed.");
            return false;
        }

        qint64 written = f.write(reinterpret_cast<const char*>(&m_hdr), sizeof(TS_RECORD_HEADER));
        f.flush();
        f.close();

        if(written != sizeof(TS_RECORD_HEADER)) {
            qDebug("save header file failed.");
            return false;
        }
    }

    return true;
}

bool ThrData::_load_keyframe() {
    QString tpk_fname = QString("%1/tp-rdp.tpk").arg(m_path_base);
    tpk_fname = QDir::toNativeSeparators(tpk_fname);

    if(m_need_download) {
        QString tmp_fname = QString("%1/tp-rdp.tpk.downloading").arg(m_path_base);
        tmp_fname = QDir::toNativeSeparators(tmp_fname);

        QFileInfo fi_tmp(tmp_fname);
        if(fi_tmp.isFile()) {
            QFile::remove(tmp_fname);
        }

        QFileInfo fi_tpk(tpk_fname);
        if(!fi_tpk.exists()) {
            QString url = QString("%1/audit/get-file?act=read&type=rdp&rid=%2&f=tp-rdp.tpk").arg(m_url_base, m_rid);
            qDebug() << "TPK: " << tmp_fname;
            if(!_download_file(url, tmp_fname))
                return false;

            if(!QFile::rename(tmp_fname, tpk_fname))
                return false;
        }
    }

    qDebug() << "TPK: " << tpk_fname;

    QFile f_kf(tpk_fname);
    if(!f_kf.open(QFile::ReadOnly)) {
        qDebug() << "Can not open " << tpk_fname << " for read.";
        _notify_error(QString("%1\n\n%3").arg(LOCAL8BIT("无法打开关键帧信息文件！"), tpk_fname));
        return false;
    }

    qint64 fsize = f_kf.size();
    if(!fsize || fsize % sizeof(KEYFRAME_INFO) != 0) {
        qDebug() << "Can not open " << tpk_fname << " for read.";
        _notify_error(LOCAL8BIT("关键帧信息文件格式错误！"));
        return false;
    }

    qint64 read_len = 0;
    int kf_count = fsize / sizeof(KEYFRAME_INFO);
    for(int i = 0; i < kf_count; ++i) {
        KEYFRAME_INFO kf;
        memset(&kf, 0, sizeof(KEYFRAME_INFO));
        read_len = f_kf.read(reinterpret_cast<char*>(&kf), sizeof(KEYFRAME_INFO));
        if(read_len != sizeof(KEYFRAME_INFO)) {
            qDebug() << "invaid .tpk file.";
            _notify_error(LOCAL8BIT("关键帧信息文件格式错误！"));
            return false;
        }

        m_kf.push_back(kf);
    }

    return true;
}

bool ThrData::_download_file(const QString& url, const QString filename) {
    if(!m_need_download) {
        qDebug() << "download not necessary.";
        return false;
    }

    Downloader dl;
    if(!dl.request(url, m_sid, filename)) {
        qDebug() << "download failed.";
        _notify_error(QString("%1").arg(LOCAL8BIT("下载文件失败！")));
        return false;
    }

    return true;
}

bool ThrData::_download_file(const QString& url, QByteArray& data) {
    if(!m_need_download) {
        qDebug() << "download not necessary.";
        return false;
    }

    Downloader dl;

    if(!dl.request(url, m_sid, &data)) {
        qDebug() << "download failed.";
        _notify_error(QString("%1").arg(LOCAL8BIT("下载文件失败！")));
        return false;
    }

    return true;
}


void ThrData::_prepare() {
    UpdateData* d = new UpdateData(TYPE_HEADER_INFO);

    m_locker.lock();
    m_data.enqueue(d);
    m_locker.unlock();
}

UpdateData* ThrData::get_data() {

    m_locker.lock();
    UpdateData* d = m_data.dequeue();
    m_locker.unlock();

    return d;
}
