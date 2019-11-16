#include "update_data.h"

#include <QImage>
#include <QDebug>


UpdateData::UpdateData() : QObject(nullptr)
{
    _init();
}

UpdateData::UpdateData(int data_type) : QObject(nullptr)
{
    _init();
    m_data_type = data_type;
}

UpdateData::UpdateData(int data_type, uint32_t time_ms) : QObject(nullptr)
{
    _init();
    m_data_type = data_type;
    m_time_ms = time_ms;
}

UpdateData::UpdateData(const TS_RECORD_HEADER& hdr) : QObject(nullptr)
{
    _init();
    m_data_type = TYPE_HEADER_INFO;
    m_hdr = new TS_RECORD_HEADER;
    memcpy(m_hdr, &hdr, sizeof(TS_RECORD_HEADER));
}

void UpdateData::_init() {
    m_data_type = TYPE_UNKNOWN;
    m_hdr = nullptr;
    m_pointer = nullptr;

    m_data_buf = nullptr;
    m_data_len = 0;
    m_time_ms = 0;
}

UpdateData::~UpdateData() {
    if(m_hdr)
        delete m_hdr;
    if(m_pointer)
        delete m_pointer;
    for(int i = 0; i < m_images.size(); ++i) {
        delete m_images[i].img;
    }
    m_images.clear();

    if(m_data_buf)
        delete m_data_buf;
}

void UpdateData::set_pointer(uint32_t ts, const TS_RECORD_RDP_POINTER* p) {
    m_data_type = TYPE_POINTER;
    m_time_ms = ts;
    m_pointer = new TS_RECORD_RDP_POINTER;
    memcpy(m_pointer, p, sizeof(TS_RECORD_RDP_POINTER));
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
