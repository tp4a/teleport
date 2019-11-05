#include <QDebug>
#include <QDir>
#include <QFile>
#include <QNetworkCookie>
#include <QStandardPaths>
#include <qcoreapplication.h>
#include <inttypes.h>

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
    m_need_restart = false;
    m_wait_restart = false;
    m_need_show_kf = false;

    m_file_idx = 0;
    m_offset = 0;

#ifdef __APPLE__
    m_data_path_base = QStandardPaths::writableLocation(QStandardPaths::DesktopLocation);
    m_data_path_base += "/tp-testdata/";
#else
    m_data_path_base = QCoreApplication::applicationDirPath() + "/record";
#endif
    qDebug("data-path-base: %s", m_data_path_base.toStdString().c_str());

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
    _clear_data();
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

void ThrData::run() {
    _run();
    qDebug("ThrData thread run() end.");
}

void ThrData::_run() {

    QString _tmp_res = m_res.toLower();
    if(_tmp_res.startsWith("http")) {
        m_need_download = true;
        _notify_message(LOCAL8BIT("正在准备录像数据，请稍候..."));

        if(!m_thr_download.init(m_data_path_base, m_res)) {
            _notify_error(QString("%1\n\n%2").arg(LOCAL8BIT("无法下载录像文件！\n\n"), m_res));
            return;
        }

        m_thr_download.start();
        msleep(100);

        for(;;) {
            if(m_need_stop)
                return;
            if(!m_thr_download.is_running() || m_thr_download.is_tpk_downloaded())
                break;
            msleep(100);
        }

        if(!m_thr_download.is_tpk_downloaded())
            return;

        m_thr_download.get_data_path(m_data_path);
    }
    else {
        QFileInfo fi_chk_link(m_res);
        if(fi_chk_link.isSymLink())
            m_res = fi_chk_link.symLinkTarget();

        QFileInfo fi(m_res);
        if(!fi.exists()) {
            _notify_error(QString("%1\n\n%2").arg(LOCAL8BIT("指定的文件或目录不存在！"), m_res));
            return;
        }

        if(fi.isFile()) {
            m_data_path = fi.path();
        }
        else if(fi.isDir()) {
            m_data_path = m_res;
        }

        m_data_path = QDir::toNativeSeparators(m_data_path);
    }

    // 到这里，.tpr和.tpk文件均已经下载完成了。

    if(!_load_header())
        return;

    if(!_load_keyframe())
        return;


    UpdateData* dat = new UpdateData(m_hdr);
    emit signal_update_data(dat);


    QFile* fdata = nullptr;
    //uint32_t file_idx = 0;
    //uint32_t start_offset = 0;
    qint64 file_size = 0;
    qint64 file_processed = 0;
    qint64 read_len = 0;
    QString str_fidx;

    for(;;) {
        // 任何时候确保第一时间响应退出操作
        if(m_need_stop)
            return;

        if(m_need_restart) {
            if(fdata) {
                fdata->close();
                delete fdata;
                fdata = nullptr;
            }

            m_wait_restart = true;
            msleep(50);
            continue;
        }

        // 如果所有文件都已经处理完了，则等待（可能用户会拖动滚动条，或者重新播放）
        if(m_file_idx >= m_hdr.info.dat_file_count) {
            msleep(500);
            continue;
        }

        // 看看待播放队列中还有多少个数据包
        int pkg_count_in_queue = 0;
        int pkg_need_add = 0;

        m_locker.lock();
        pkg_count_in_queue = m_data.size();
        m_locker.unlock();

        // 少于500个的话，补足到1000个
        if(m_data.size() < 500)
            pkg_need_add = 1000 - pkg_count_in_queue;

        if(pkg_need_add == 0) {
            msleep(100);
            continue;
        }

        for(int i = 0; i < pkg_need_add; ++i) {
            if(m_need_stop)
                return;
            if(m_need_restart)
                break;

            // 如果数据文件尚未打开，则打开它
            if(fdata == nullptr) {
                str_fidx.sprintf("%d", m_file_idx+1);
                QString tpd_fname = QString("%1/tp-rdp-%2.tpd").arg(m_data_path, str_fidx);
                tpd_fname = QDir::toNativeSeparators(tpd_fname);

                QFileInfo fi_tpd(tpd_fname);
                if(!fi_tpd.exists()) {
                    if(m_need_download) {
                        // 此文件尚未下载完成，等待
                        for(;;) {
                            if(m_need_stop)
                                return;
                            if(!m_thr_download.is_running() || m_thr_download.is_tpd_downloaded(m_file_idx))
                                break;
                            msleep(100);
                        }

                        // 下载失败了
                        if(!m_thr_download.is_tpd_downloaded(m_file_idx))
                            return;
                    }
                }

                fdata = new QFile(tpd_fname);
                if(!fdata->open(QFile::ReadOnly)) {
                    qDebug() << "Can not open " << tpd_fname << " for read.";
                    _notify_error(QString("%1\n\n%2").arg(LOCAL8BIT("无法打开录像数据文件！"), tpd_fname));
                    return;
                }

                file_size = fdata->size();
                file_processed = 0;
                qDebug("Open file tp-rdp-%d.tpd, processed: %" PRId64 ", size: %" PRId64, m_file_idx+1, file_processed, file_size);
            }
//            qDebug("B processed: %" PRId64 ", size: %" PRId64, file_processed, file_size);

            // 如果指定了起始偏移，则跳过这部分数据
            if(m_offset > 0) {
                fdata->seek(m_offset);
                file_processed = m_offset;
                m_offset = 0;
            }

            //----------------------------------
            // 读取一个数据包
            //----------------------------------
            if(file_size - file_processed < sizeof(TS_RECORD_PKG)) {
                qDebug("invaid tp-rdp-%d.tpd file, filesize=%" PRId64 ", processed=%" PRId64 ", need=%d.", m_file_idx+1, file_size, file_processed, sizeof(TS_RECORD_PKG));
                _notify_error(QString("%1\ntp-rdp-%2.tpd").arg(LOCAL8BIT("错误的录像数据文件！"), str_fidx));
                return;
            }

            TS_RECORD_PKG pkg;
            read_len = fdata->read(reinterpret_cast<char*>(&pkg), sizeof(TS_RECORD_PKG));
    //        if(read_len == 0)
    //            break;
            if(read_len != sizeof(TS_RECORD_PKG)) {
                qDebug("invaid tp-rdp-%d.tpd file, read_len=%" PRId64 " (1).", m_file_idx+1, read_len);
                _notify_error(QString("%1\ntp-rdp-%2.tpd").arg(LOCAL8BIT("错误的录像数据文件！"), str_fidx));
                return;
            }
            file_processed += sizeof(TS_RECORD_PKG);

            if(file_size - file_processed < pkg.size) {
                qDebug("invaid tp-rdp-%d.tpd file (2).", m_file_idx+1);
                _notify_error(QString("%1\ntp-rdp-%2.tpd").arg(LOCAL8BIT("错误的录像数据文件！"), str_fidx));
                return;
            }

            if(pkg.size == 0) {
                qDebug("################## too bad.");
            }

            QByteArray pkg_data = fdata->read(pkg.size);
            if(pkg_data.size() != pkg.size) {
                qDebug("invaid tp-rdp-%d.tpd file, read_len=%" PRId64 " (3).", m_file_idx+1, read_len);
                _notify_error(QString("%1\ntp-rdp-%2.tpd").arg(LOCAL8BIT("错误的录像数据文件！"), str_fidx));
                return;
            }
            file_processed += pkg.size;

            UpdateData* dat = new UpdateData();
            if(!dat->parse(pkg, pkg_data)) {
                qDebug("invaid tp-rdp-%d.tpd file (4).", m_file_idx+1);
                _notify_error(QString("%1\ntp-rdp-%2.tpd").arg(LOCAL8BIT("错误的录像数据文件！"), str_fidx));
                return;
            }

            // 拖动滚动条后，需要显示一次关键帧数据，然后跳过后续关键帧。
            if(pkg.type == TS_RECORD_TYPE_RDP_KEYFRAME) {
                qDebug("----key frame: %ld, processed=%" PRId64 ", pkg.size=%d", pkg.time_ms, file_processed, pkg.size);
                if(m_need_show_kf) {
                    m_need_show_kf = false;
                    qDebug("++ show keyframe.");
                }
                else {
                    qDebug("-- skip keyframe.");
                    delete dat;
                    dat = nullptr;
                }
            }


            // 数据放到待播放列表中
            if(dat) {
                m_locker.lock();
                m_data.enqueue(dat);
                m_locker.unlock();
            }

            // 让线程调度器让播放线程有机会执行
            msleep(1);

            // 如果此文件已经处理完毕，则关闭文件，这样下次处理一个新的文件
            if(file_processed >= file_size) {
                fdata->close();
                delete fdata;
                fdata = nullptr;
                m_file_idx++;
            }

            if(m_file_idx >= m_hdr.info.dat_file_count) {
                UpdateData* dat = new UpdateData(TYPE_END);
                m_locker.lock();
                m_data.enqueue(dat);
                m_locker.unlock();
                break;
            }
        }
    }
}

void ThrData::restart(uint32_t start_ms) {
    // 让处理线程处理完当前循环，然后等待
    m_need_restart = true;

    // 确保处理线程已经处理完当前循环
    for(;;) {
        msleep(50);
        if(m_need_stop)
            return;
        if(m_wait_restart)
            break;
    }

    // 清空待播放队列
    _clear_data();

    if(start_ms == 0) {
        m_offset = 0;
        m_file_idx = 0;
        m_need_show_kf = false;
    }
    else {
        // 找到最接近 start_ms 但小于它的关键帧
        size_t i = 0;
        for(i = 0; i < m_kf.size(); ++i) {
            if(m_kf[i].time_ms > start_ms)
                break;
        }
        if(i > 0)
            i--;

        // 指定要播放的数据的开始位置
        m_offset = m_kf[i].offset;
        m_file_idx = m_kf[i].file_index;
        m_need_show_kf = true;
    }

    qDebug("RESTART: offset=%d, file_idx=%d", m_offset, m_file_idx);

    // 让处理线程继续
    m_wait_restart = false;
    m_need_restart = false;
}

bool ThrData::_load_header() {
    QString msg;
    qDebug() << "PATH_BASE: " << m_data_path;

    QString filename = QString("%1/tp-rdp.tpr").arg(m_data_path);
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

    return true;
}

bool ThrData::_load_keyframe() {
    QString tpk_fname = QString("%1/tp-rdp.tpk").arg(m_data_path);
    tpk_fname = QDir::toNativeSeparators(tpk_fname);

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

void ThrData::_prepare() {
    UpdateData* d = new UpdateData(TYPE_HEADER_INFO);

    m_locker.lock();
    m_data.enqueue(d);
    m_locker.unlock();
}

UpdateData* ThrData::get_data() {
    UpdateData* d = nullptr;

    m_locker.lock();
    if(m_data.size() > 0) {
//        qDebug("get_data(), left: %d", m_data.size());
        d = m_data.dequeue();
    }
    m_locker.unlock();

    return d;
}

void ThrData::_clear_data() {
    m_locker.lock();
    while(m_data.size() > 0) {
        UpdateData* d = m_data.dequeue();
        delete d;
    }
    m_locker.unlock();
}
