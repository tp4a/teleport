#include <memory>

#include "base_record.h"

TppRecBase::TppRecBase() {
    m_cache.reserve(MAX_SIZE_PER_FILE);
    m_start_time = 0;
}

TppRecBase::~TppRecBase() {
}

bool TppRecBase::begin(const wchar_t *base_path, const wchar_t *base_fname, int record_id, const TPP_CONNECT_INFO *info) {
    m_start_time = ex_get_tick_count();

    m_base_fname = base_fname;
    m_base_path = base_path;

    wchar_t _str_rec_id[24] = {0};
    ex_wcsformat(_str_rec_id, 24, L"%09d", record_id);
    if (!ex_path_join(m_base_path, false, _str_rec_id, NULL))
        return false;
    if (!ex_mkdirs(m_base_path))
        return false;

    return _on_begin(info);
}

bool TppRecBase::end() {
    _on_end();

    if (m_cache.size() > 0) {
        EXLOGE("not all record data saved.\n");
        return false;
    }

    return true;
}
