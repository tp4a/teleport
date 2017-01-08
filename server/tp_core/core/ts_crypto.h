#ifndef __TS_CRYPTO_H__
#define __TS_CRYPTO_H__

#include <ex.h>

// 用于数据库字段的加密/解密，使用内置密钥，加密结果为base64编码的字符串
bool ts_db_field_encrypt(const ex_bin& bin_dec, ex_astr& str_enc);
bool ts_db_field_decrypt(const ex_astr& str_enc, ex_bin& bin_dec);

bool ts_db_field_encrypt(const ex_astr& str_dec, ex_astr& str_enc);
bool ts_db_field_decrypt(const ex_astr& str_enc, ex_astr& str_dec);


#endif // __TS_CRYPTO_H__
