#ifndef RLE_H
#define RLE_H

#define	RD_BOOL	int
#define False	0
#define True	1

#define uint8	unsigned char
#define uint16	unsigned short
#define uint32	unsigned int

#ifdef __cplusplus
extern "C" {
#endif

RD_BOOL bitmap_decompress1(uint8 * output, int width, int height, const uint8 * input, int size);
RD_BOOL bitmap_decompress2(uint8 * output, int width, int height, const uint8 * input, int size);
RD_BOOL bitmap_decompress3(uint8 * output, int width, int height, const uint8 * input, int size);
RD_BOOL bitmap_decompress4(uint8 * output, int width, int height, const uint8 * input, int size);

int bitmap_decompress_15(uint8 * output, int output_width, int output_height, int input_width, int input_height, uint8* input, int size);
int bitmap_decompress_16(uint8 * output, int output_width, int output_height, int input_width, int input_height, uint8* input, int size);
int bitmap_decompress_24(uint8 * output, int output_width, int output_height, int input_width, int input_height, uint8* input, int size);
int bitmap_decompress_32(uint8 * output, int output_width, int output_height, int input_width, int input_height, uint8* input, int size);


#ifdef __cplusplus
}
#endif

#endif // RLE_H
