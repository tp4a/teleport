#ifndef __TS_UTILS_H__
#define __TS_UTILS_H__

#include <ex.h>

extern std::string rdp_content;

bool calc_psw51b(const char* password, std::string& ret);

bool is_digital(std::string str);
std::string strtolower(std::string str);
void SplitString(const std::string& s, std::vector<std::string>& v, const std::string& c);

#endif // __TS_UTILS_H__
