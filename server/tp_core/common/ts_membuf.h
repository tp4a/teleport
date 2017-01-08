#ifndef __TS_MEMBUF_H__
#define __TS_MEMBUF_H__

#include <ex.h>

#define MEMBUF_BLOCK_SIZE 128

class MemBuffer
{
public:
	MemBuffer();
	virtual ~MemBuffer();

	// 附加size字节的数据到缓冲区末尾（可能会导致缓冲区扩大）
	void append(const ex_u8* data, size_t size);
	// 缓冲区至少为指定字节数（可能会扩大缓冲区，但不会缩小缓冲区，保证有效数据不会被改变）
	void reserve(size_t size);
	// 将m的有效数据附加到自己的有效数据末尾，可能会扩大缓冲区，m内容不变
	void concat(const MemBuffer& m);
	// 从缓冲区头部移除size字节（缓冲区大小可能并不会收缩），剩下的有效数据前移。
	void pop(size_t size);
	// 清空缓冲区（有效数据为0字节，缓冲区不变）
	void empty(void) { m_data_size = 0; }
	bool is_empty(void) { return m_data_size == 0; }

	ex_u8* data(void) { return m_buffer; }
	size_t size(void) { return m_data_size; }
	void size(size_t size) { m_data_size = size; }
	size_t buffer_size(void) { return m_buffer_size; }

private:
	ex_u8* m_buffer;
	size_t m_data_size;
	size_t m_buffer_size;
};

#endif // __TS_MEMBUF_H__
