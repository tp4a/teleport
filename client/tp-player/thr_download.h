#ifndef THREADDOWNLOAD_H
#define THREADDOWNLOAD_H

#include <QThread>

/*
为支持“边下载，边播放”、“可拖动进度条”等功能，录像数据会分为多个文件存放，目前每个文件约4MB。
例如：
  tp-rdp.tpr
  tp-rdp.tpk  (关键帧信息文件，v3.5.0开始引入)
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


class ThreadDownload : public QThread
{
public:
    ThreadDownload(const QString& url);

    virtual void run();
    void stop();

    // 下载 .tpr 和 .tpf 文件，出错返回false，正在下载或已经下载完成则返回true.
    bool prepare(QString& path_base, QString& msg);

private:
    bool m_need_stop;
    QString m_url;

    QString m_path_base;
};

#endif // THREADDOWNLOAD_H
