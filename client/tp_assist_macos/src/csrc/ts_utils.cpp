#include <unistd.h>
#include "ts_utils.h"

#define HEXTOI(x) (isdigit(x) ? x - '0' : x - 'W')

int ts_url_decode(const char *src, int src_len, char *dst, int dst_len, int is_form_url_encoded)
{
    int i, j, a, b;

    for (i = j = 0; i < src_len && j < dst_len - 1; i++, j++)
    {
        if (src[i] == '%')
        {
            if (i < src_len - 2 && isxdigit(*(const unsigned char *)(src + i + 1)) &&
                isxdigit(*(const unsigned char *)(src + i + 2))) {
                a = tolower(*(const unsigned char *)(src + i + 1));
                b = tolower(*(const unsigned char *)(src + i + 2));
                dst[j] = (char)((HEXTOI(a) << 4) | HEXTOI(b));
                i += 2;
            }
            else
            {
                return -1;
            }
        }
        else if (is_form_url_encoded && src[i] == '+')
        {
            dst[j] = ' ';
        }
        else
        {
            dst[j] = src[i];
        }
    }

    dst[j] = '\0'; /* Null-terminate the destination */

    return i >= src_len ? j : -1;
}
