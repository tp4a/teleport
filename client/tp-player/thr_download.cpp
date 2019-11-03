#include <QDebug>
#include <QDir>
#include <QFile>
#include <QNetworkCookie>

#include "thr_download.h"
#include "util.h"
#include "downloader.h"
#include "record_format.h"

//=================================================================
// ThrDownload
//=================================================================

ThrDownload::ThrDownload() {
    m_need_stop = false;
    m_have_tpr = false;
    m_have_tpk = false;
    m_have_tpd = nullptr;
    m_need_tpk = false;
    m_running = true;
}

ThrDownload::~ThrDownload() {
    if(m_have_tpd)
        delete[] m_have_tpd;
}

//	tp-player.exe http://teleport.domain.com:7190/{sub/path/}tp_1491560510_ca67fceb75a78c9d/1234 (注意，并不直接访问此URI，实际上其并不存在)
//                TP服务器地址(可能包含子路径哦，例如上例中的{sub/path/}部分)/session-id(用于判断当前授权用户)/录像会话编号

bool ThrDownload::init(const QString& local_data_path_base, const QString &res) {
    m_data_path_base = local_data_path_base;

    QString _tmp_res = res.toLower();
    if(!_tmp_res.startsWith("http")) {
        return false;
    }

    QStringList _uris = res.split('/');
    if(_uris.size() < 3) {
        return false;
    }

    m_sid = _uris[_uris.size()-2];
    m_rid = _uris[_uris.size()-1];
    m_url_base = res.left(res.length() - m_sid.length() - m_rid.length() - 2);

    if(m_sid.length() == 0 || m_rid.length() == 0 || m_url_base.length() == 0)
        return false;

    return true;
}

void ThrDownload::stop() {
    if(!m_running)
        return;
//    if(!isRunning())
//        return;
    m_need_stop = true;
    wait();
    qDebug("data thread stop() end.");
}

//	tp-player.exe http://teleport.domain.com:7190/{sub/path/}tp_1491560510_ca67fceb75a78c9d/1234 (注意，并不直接访问此URI，实际上其并不存在)
//                TP服务器地址(可能包含子路径哦，例如上例中的{sub/path/}部分)/session-id(用于判断当前授权用户)/录像会话编号

void ThrDownload::run() {
    _run();
    m_running = false;
    qDebug("ThrDownload thread run() end.");
}

void ThrDownload::_run() {
//    m_state = statDownloading;

    if(!_download_tpr()) {
//        m_state = statFailDone;
        return;
    }
    m_have_tpr = true;

    m_have_tpd = new bool[m_tpd_count];
    for(uint32_t i = 0; i < m_tpd_count; ++i) {
        m_have_tpd[i] = false;
    }

    if(m_need_tpk) {
        if(!_download_tpk()) {
//            m_state = statFailDone;
            return;
        }
        m_have_tpk = true;
    }

    uint32_t file_idx = 0;
    for(;;) {
        if(m_need_stop)
            break;
        QString str_fidx;
        str_fidx.sprintf("%d", file_idx+1);

        QString tpd_fname = QString("%1/tp-rdp-%2.tpd").arg(m_data_path, str_fidx);
        tpd_fname = QDir::toNativeSeparators(tpd_fname);

        QString tmp_fname = QString("%1/tp-rdp-%2.tpd.downloading").arg(m_data_path, str_fidx);
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
            if(!_download_file(url, tmp_fname)) {
//                m_state = statFailDone;
                return;
            }

            if(!QFile::rename(tmp_fname, tpd_fname)) {
//                m_state = statFailDone;
                return;
            }
        }

        m_have_tpd[file_idx] = true;

        file_idx += 1;
        if(file_idx >= m_tpd_count)
            break;
    }

//    m_state = statSuccessDone;
}

bool ThrDownload::_download_tpr() {
    QString url = QString("%1/audit/get-file?act=read&type=rdp&rid=%2&f=tp-rdp.tpr").arg(m_url_base, m_rid);
    QByteArray data;
    if(!_download_file(url, data))
        return false;

    if(data.size() != sizeof(TS_RECORD_HEADER)) {
        qDebug("invalid header data. %d", data.size());
        m_error = QString(LOCAL8BIT("录像信息文件数据错误！"));
        return false;
    }

    TS_RECORD_HEADER* hdr = reinterpret_cast<TS_RECORD_HEADER*>(data.data());
//    if(hdr->info.ver != 4) {
//        qDebug() << "invaid .tpr file.";
//        m_last_error = QString("%1 %2%3").arg(LOCAL8BIT("不支持的录像文件版本 "), QString(hdr->info.ver), LOCAL8BIT("！\n\n此播放器支持录像文件版本 4。"));
//        return false;
//    }

//    if(m_hdr.basic.width == 0 || m_hdr.basic.height == 0) {
//        _notify_error(LOCAL8BIT("错误的录像信息，未记录窗口尺寸！"));
//        return false;
//    }

//    if(m_hdr.info.dat_file_count == 0) {
//        _notify_error(LOCAL8BIT("错误的录像信息，未记录数据文件数量！"));
//        return false;
//    }


    // 下载得到的数据应该是一个TS_RECORD_HEADER，解析此数据，生成本地文件路径，并保存之。
    QDateTime timeUTC;
    //        timeUTC.setTimeSpec(Qt::UTC);
    //        timeUTC.setTime_t(m_hdr.basic.timestamp);
    timeUTC.setSecsSinceEpoch(hdr->basic.timestamp);
    QString strUTC = timeUTC.toString("yyyyMMdd-hhmmss");

    QString strAcc(hdr->basic.acc_username);
    int idx = strAcc.indexOf('\\');
    if(-1 != idx) {
        QString _domain = strAcc.left(idx);
        QString _user = strAcc.right(strAcc.length() - idx - 1);
        strAcc = _user + "@" + _domain;
    }

    QString strType;
    if(hdr->info.type == TS_TPPR_TYPE_SSH) {
        strType = "SSH";
    }
    else if(hdr->info.type == TS_TPPR_TYPE_RDP) {
        strType = "RDP";
        m_need_tpk = true;
    }
    else {
        strType = "UNKNOWN";
    }

    // .../record/RDP-211-admin-user@domain-192.168.0.68-20191015-020243
    m_data_path = QString("%1/%2-%3-%4-%5-%6-%7").arg(m_data_path_base, strType, m_rid, hdr->basic.user_username, strAcc, hdr->basic.host_ip, strUTC);
    m_data_path = QDir::toNativeSeparators(m_data_path);
    qDebug() << "PATH_BASE: " << m_data_path;

    QDir dir;
    dir.mkpath(m_data_path);
    QFileInfo fi;
    fi.setFile(m_data_path);
    if(!fi.isDir()) {
        qDebug("can not create folder to save downloaded file.");
        return false;
    }

    QString filename = QString("%1/tp-rdp.tpr").arg(m_data_path);
    filename = QDir::toNativeSeparators(filename);
    qDebug() << "TPR: " << filename;

    QFile f;
    f.setFileName(filename);
    if(!f.open(QIODevice::WriteOnly | QFile::Truncate)){
        qDebug("open file for write failed.");
        return false;
    }

    qint64 written = f.write(reinterpret_cast<const char*>(hdr), sizeof(TS_RECORD_HEADER));
    f.flush();
    f.close();

    if(written != sizeof(TS_RECORD_HEADER)) {
        qDebug("save header file failed.");
        return false;
    }

    m_tpd_count = hdr->info.dat_file_count;

    return true;
}

bool ThrDownload::_download_tpk() {
    QString tpk_fname = QString("%1/tp-rdp.tpk").arg(m_data_path);
    tpk_fname = QDir::toNativeSeparators(tpk_fname);

    QString tmp_fname = QString("%1/tp-rdp.tpk.downloading").arg(m_data_path);
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

    return true;
}

bool ThrDownload::_download_file(const QString& url, const QString filename) {
    Downloader dl;
    if(!dl.request(url, m_sid, filename)) {
        qDebug() << "download failed.";
        m_error = QString("%1").arg(LOCAL8BIT("下载文件失败！"));
        return false;
    }

    return true;
}

bool ThrDownload::_download_file(const QString& url, QByteArray& data) {
    Downloader dl;
    if(!dl.request(url, m_sid, &data)) {
        qDebug() << "download failed.";
        m_error = QString("%1").arg(LOCAL8BIT("下载文件失败！"));
        return false;
    }

    return true;
}

bool ThrDownload::is_tpd_downloaded(uint32_t file_idx) const {
    if(!m_have_tpd)
        return false;
    if(file_idx >= m_tpd_count)
        return false;
    return m_have_tpd[file_idx];
}

