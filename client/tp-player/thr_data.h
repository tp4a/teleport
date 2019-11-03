#ifndef THR_DATA_H
#define THR_DATA_H

#include <QThread>
#include <QQueue>
#include <QMutex>
#include <QNetworkReply>
#include <QFile>
#include <QEventLoop>
#include "update_data.h"
#include "record_format.h"
#include "thr_download.h"

/*
为支持“边下载，边播放”、“可拖动进度条”等功能，录像数据会分为多个文件存放，目前每个文件约4MB。
例如：
  tp-rdp.tpr
  tp-rdp.tpk  (关键帧信息文件，v3.5.1开始引入)
  tp-rdp-1.tpd, tp-rdp-2.tpd, tp-rdp-3.tpd, ...
这样，下载完一个数据文件，即可播放此数据文件中的内容，同时下载线程可以下载后续数据文件。

为支持“拖动进度条”，可以在数据文件中插入关键帧的方式，这就要求记录录像数据的同时对图像数据进行解码，
并同步合成全屏数据（关键帧），每经过一段时间（或者一定数量的图像数据包）之后，就在录像数据文件中增加一个关键帧。
正常播放时，跳过此关键帧。
当进度条拖放发生时，找到目标时间点之前的最后一个关键帧，从此处开始无延时播放到目标时间点，然后正常播放。
因此，需要能够快速定位到各个关键帧，因为有可能此时尚未下载这个关键帧所在的数据文件。定位到此关键帧
所在的数据文件后，下载线程要放弃当前下载任务（如果不是当前正在下载的数据文件），并开始下载新的数据文件。
因此，需要引入新的关键帧信息文件（.tpk），记录各个关键帧数据所在的数据文件序号、偏移、时间点等信息。

另外，为保证数据文件、关键帧信息文件等下载正确，下载时保存到对应的临时文件中，并记录已下载字节数，下载完成后再改名，如：
  tp-rdp.tpk.tmp, tp-rdp.tpk.len
  tp-rdp-1.tpd.tmp, tp-rdp-1.tpd.len, ...
这样，下次需要下载指定文件时，如果发现对应的临时文件存在，可以根据已下载字节数，继续下载。
*/

typedef struct KEYFRAME_INFO {
    uint32_t time_ms;       // 此关键帧的时间点
    uint32_t file_index;    // 此关键帧图像数据位于哪一个数据文件中
    uint32_t offset;        // 此关键帧图像数据在数据文件中的偏移
}KEYFRAME_INFO;

typedef std::vector<KEYFRAME_INFO> KeyFrames;

class MainWindow;

// 下载必要的文件，解析文件数据，生成图像数据（QImage*），将数据包放入待显示队列中，等待 ThrPlay 线程使用
// 注意，无需将所有数据解析并放入待显示队列，此队列有数量限制（例如1000个），避免过多占用内存
class ThrData : public QThread {
    Q_OBJECT
public:
    ThrData(MainWindow* mainwin, const QString& url);
    ~ThrData();

    virtual void run();
    void stop();


    bool have_more_data();

    UpdateData* get_data();

private:
    void _run();

    bool _load_header();
    bool _load_keyframe();

    void _clear_data();
    void _prepare();

    void _notify_message(const QString& msg);
    void _notify_error(const QString& err_msg);

signals:
    void signal_update_data(UpdateData*);

private:
    MainWindow* m_mainwin;
    QQueue<UpdateData*> m_data;
    QMutex m_locker;

    ThrDownload m_thr_download;

    bool m_need_stop;

    bool m_need_download;
    QString m_res;
    QString m_data_path_base;

    QString m_url_base;
    QString m_sid;
    QString m_rid;
    QString m_data_path;

    TS_RECORD_HEADER m_hdr;
    KeyFrames m_kf;
};

#endif // THR_DATA_H
