#include "update_data.h"

UpdateData::UpdateData(int data_type, QObject *parent) : QObject(parent)
{
    m_data_type = data_type;
    m_data_buf = nullptr;
    m_data_len = 0;
}

UpdateData::~UpdateData() {
    if(m_data_buf)
        delete m_data_buf;
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
