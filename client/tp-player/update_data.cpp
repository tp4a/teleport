#include "update_data.h"
#include "rle.h"

#include <QImage>
#include <QDebug>


static QImage* _rdpimg2QImage(int w, int h, int bitsPerPixel, bool isCompressed, const uint8_t* dat, uint32_t len) {
    QImage* out;
    switch(bitsPerPixel) {
    case 15:
        if(isCompressed) {
            uint8_t* _dat = reinterpret_cast<uint8_t*>(calloc(1, w*h*2));
            if(!bitmap_decompress1(_dat, w, h, dat, len)) {
                free(_dat);
                return nullptr;
            }
            out = new QImage(_dat, w, h, QImage::Format_RGB555);
            free(_dat);
        }
        else {
            out = new QImage(QImage(dat, w, h, QImage::Format_RGB555).transformed(QMatrix(1.0, 0.0, 0.0, -1.0, 0.0, 0.0)));
        }
        return out;

    case 16:
        if(isCompressed) {
            uint8_t* _dat = reinterpret_cast<uint8_t*>(calloc(1, w*h*2));
            if(!bitmap_decompress2(_dat, w, h, dat, len)) {
                free(_dat);
                qDebug() << "22------------------DECOMPRESS2 failed.";
                return nullptr;
            }

            // TODO: 这里需要进一步优化，直接操作QImage的buffer。
            out = new QImage(w, h, QImage::Format_RGB16);
            for(int y = 0; y < h; y++) {
                for(int x = 0; x < w; x++) {
                    uint16 a = ((uint16*)_dat)[y * w + x];
                    uint8 r = ((a & 0xf800) >> 11) * 255 / 31;
                    uint8 g = ((a & 0x07e0) >> 5) * 255 / 63;
                    uint8 b = (a & 0x001f) * 255 / 31;
                    out->setPixelColor(x, y, QColor(r,g,b));
                }
            }
            free(_dat);
            return out;
        }
        else {
            out = new QImage(QImage(dat, w, h, QImage::Format_RGB16).transformed(QMatrix(1.0, 0.0, 0.0, -1.0, 0.0, 0.0)));
        }
        return out;

    case 24:
    case 32:
    default:
        qDebug() << "--------NOT support UNKNOWN bitsPerPix" << bitsPerPixel;
        return nullptr;
    }
}

static QImage* _raw2QImage(int w, int h, const uint8_t* dat, uint32_t len) {
    QImage* out;

    // TODO: 这里需要进一步优化，直接操作QImage的buffer。
    out = new QImage(w, h, QImage::Format_RGB16);
    for(int y = 0; y < h; y++) {
        for(int x = 0; x < w; x++) {
            uint16 a = ((uint16*)dat)[y * w + x];
            uint8 r = ((a & 0xf800) >> 11) * 255 / 31;
            uint8 g = ((a & 0x07e0) >> 5) * 255 / 63;
            uint8 b = (a & 0x001f) * 255 / 31;
            out->setPixelColor(x, y, QColor(r,g,b));
        }
    }
    return out;
}

UpdateData::UpdateData() : QObject(nullptr)
{
    _init();
}

UpdateData::UpdateData(int data_type) : QObject(nullptr)
{
    _init();
    m_data_type = data_type;
}

UpdateData::UpdateData(const TS_RECORD_HEADER& hdr) : QObject(nullptr)
{
    _init();
    m_data_type = TYPE_HEADER_INFO;
    m_hdr = new TS_RECORD_HEADER;
    memcpy(m_hdr, &hdr, sizeof(TS_RECORD_HEADER));
}

UpdateData::UpdateData(uint16_t screen_w, uint16_t screen_h) {
    _init();
    m_screen_w = screen_w;
    m_screen_h = screen_h;
}

void UpdateData::_init() {
    m_data_type = TYPE_UNKNOWN;
    m_hdr = nullptr;
    m_pointer = nullptr;
    m_img = nullptr;
//    m_img_info = nullptr;

    m_data_buf = nullptr;
    m_data_len = 0;
    m_time_ms = 0;

    m_screen_w = 0;
    m_screen_h = 0;
}

UpdateData::~UpdateData() {
    if(m_hdr)
        delete m_hdr;
    if(m_pointer)
        delete m_pointer;
    if(m_img)
        delete m_img;
//    if(m_img_info)
//        delete m_img_info;

    if(m_data_buf)
        delete m_data_buf;
}

bool UpdateData::parse(const TS_RECORD_PKG& pkg, const QByteArray& data) {
    m_time_ms = pkg.time_ms;

    if(pkg.type == TS_RECORD_TYPE_RDP_POINTER) {
        m_data_type = TYPE_POINTER;
        if(data.size() != sizeof(TS_RECORD_RDP_POINTER))
            return false;
        m_pointer = new TS_RECORD_RDP_POINTER;
        memcpy(m_pointer, data.data(), sizeof(TS_RECORD_RDP_POINTER));
        return true;
    }
    else if(pkg.type == TS_RECORD_TYPE_RDP_IMAGE) {
        m_data_type = TYPE_IMAGE;
        if(data.size() <= sizeof(TS_RECORD_RDP_IMAGE_INFO))
            return false;
        const TS_RECORD_RDP_IMAGE_INFO* info = reinterpret_cast<const TS_RECORD_RDP_IMAGE_INFO*>(data.data());
        const uint8_t* img_dat = reinterpret_cast<const uint8_t*>(data.data() + sizeof(TS_RECORD_RDP_IMAGE_INFO));
        uint32_t img_len = data.size() - sizeof(TS_RECORD_RDP_IMAGE_INFO);

        QImage* img = _rdpimg2QImage(info->width, info->height, info->bitsPerPixel, (info->format == TS_RDP_IMG_BMP) ? true : false, img_dat, img_len);
        if(img == nullptr)
            return false;

        m_img = img;
        m_img_x = info->destLeft;
        m_img_y = info->destTop;
        m_img_w = info->destRight - info->destLeft + 1;
        m_img_h = info->destBottom - info->destTop + 1;

        return true;
    }
    else if(pkg.type == TS_RECORD_TYPE_RDP_KEYFRAME) {
        m_data_type = TYPE_IMAGE;
//        const TS_RECORD_RDP_KEYFRAME_INFO* info = reinterpret_cast<const TS_RECORD_RDP_KEYFRAME_INFO*>(data.data());
        const uint8_t* img_dat = reinterpret_cast<const uint8_t*>(data.data() + sizeof(TS_RECORD_RDP_KEYFRAME_INFO));
        uint32_t img_len = data.size() - sizeof(TS_RECORD_RDP_KEYFRAME_INFO);

        QImage* img = _raw2QImage((int)m_screen_w, (int)m_screen_h, img_dat, img_len);
        if(img == nullptr)
            return false;
        m_img = img;
        m_img_x = 0;
        m_img_y = 0;
        m_img_w = m_screen_w;
        m_img_h = m_screen_h;
        return true;
    }

    return false;
}


void UpdateData::alloc_data(uint32_t len) {
    if(m_data_buf)
        delete m_data_buf;

    m_data_buf = new uint8_t[len];
    memset(m_data_buf, 0, len);
    m_data_len = len;
}

void UpdateData::attach_data(const uint8_t* dat, uint32_t len) {
    if(m_data_buf)
        delete m_data_buf;
    m_data_buf = new uint8_t[len];
    memcpy(m_data_buf, dat, len);
    m_data_len = len;
}
