#ifndef __TS_MEMSTREAM_H__
#define __TS_MEMSTREAM_H__

#include "ts_membuf.h"

class MemStream
{
public:
	MemStream(MemBuffer& mbuf);
	~MemStream();

	void reset(void); // 清空缓冲区数据（但不释放内存），指针移动到头部

	bool seek(size_t offset);	// 移动指针到指定偏移，如果越界，则返回错误
	bool rewind(size_t n = 0);	// 回退n字节，如果越界，返回错误，如果n为0，则回退到最开始处
	bool skip(size_t n);	// 跳过n字节，如果越界，则返回错误

	ex_u8* ptr(void) { return m_mbuf.data() + m_offset; } // 返回当前数据指针
	size_t offset(void) { return m_offset; } // 返回当前指针相对数据起始的偏移

	size_t left(void) { return m_mbuf.size() - m_offset; }	// 返回剩余数据的大小（从当前数据指针到缓冲区结尾）

	ex_u8 get_u8(void);
	ex_u16 get_u16_le(void);
	ex_u16 get_u16_be(void);
	ex_u32 get_u32_le(void);
	ex_u32 get_u32_be(void);
	ex_u8* get_bin(size_t n); // 返回当前指向的数据的指针，内部偏移会向后移动n字节

	void put_zero(size_t n);  // 填充n字节的0
	void put_u8(ex_u8 v);
	void put_u16_le(ex_u16 v);
	void put_u16_be(ex_u16 v);
	void put_u32_le(ex_u32 v);
	void put_u32_be(ex_u32 v);
	void put_bin(const ex_u8* p, size_t n); // 填充p指向的n字节数据

	size_t size(void) { return m_mbuf.size(); }

private:
	MemBuffer& m_mbuf;
	size_t m_offset;
};

#endif // __TS_MEMSTREAM_H__
