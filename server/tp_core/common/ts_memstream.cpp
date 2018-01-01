#include "ts_memstream.h"

MemStream::MemStream(MemBuffer& mbuf) : m_mbuf(mbuf)
{
	m_offset = 0;
}

MemStream::~MemStream()
{}

void MemStream::reset(void)
{
	m_mbuf.empty();
	rewind();
}


bool MemStream::seek(size_t offset)
{
	if (offset > m_mbuf.size())
		return false;

	m_offset = offset;
	return true;
}

bool MemStream::skip(size_t n)
{
	if (0 == n)
		return true;

	if (m_offset + n > m_mbuf.size())
		return false;
	m_offset += n;
	return true;
}

bool MemStream::rewind(size_t n)
{
	if (m_offset < n)
		return false;

	if (0 == n)
		m_offset = 0;
	else
		m_offset -= n;
	return true;
}

ex_u8 MemStream::get_u8(void)
{
	ASSERT(m_offset + 1 <= m_mbuf.size());

	ex_u8 v = (m_mbuf.data() + m_offset)[0];
	m_offset++;
	return v;
}

ex_u16 MemStream::get_u16_le(void)
{
	ASSERT(m_offset + 2 <= m_mbuf.size());

	ex_u8* p = m_mbuf.data() + m_offset;
#if defined(B_ENDIAN) 
	ex_u16 v = (ex_u16)(p[0] | (p[1] << 8));
#else
	ex_u16 v = ((ex_u16*)p)[0];
#endif
	m_offset += 2;
	return v;
}

ex_u16 MemStream::get_u16_be(void)
{
	ASSERT(m_offset + 2 <= m_mbuf.size());

	ex_u8* p = m_mbuf.data() + m_offset;
#if defined(B_ENDIAN) 
	ex_u16 v = ((ex_u16*)p)[0];
#else
	ex_u16 v = (ex_u16)((p[0] << 8) | p[1]);
#endif
	m_offset += 2;
	return v;
}


ex_u32 MemStream::get_u32_le(void)
{
	ASSERT(m_offset + 4 <= m_mbuf.size());

	ex_u8* p = m_mbuf.data() + m_offset;
#if defined(B_ENDIAN) 
	ex_u32 v = (ex_u32)(p[0] | (p[1] << 8) | (p[2] << 16) | (p[3] << 24));
#else
	ex_u32 v = ((ex_u32*)p)[0];
#endif
	m_offset += 4;
	return v;
}

ex_u32 MemStream::get_u32_be(void)
{
	ASSERT(m_offset + 4 <= m_mbuf.size());

	ex_u8* p = m_mbuf.data() + m_offset;
#if defined(B_ENDIAN) 
	ex_u32 v = ((ex_u32*)p)[0];
#else
	ex_u32 v = (ex_u32)((p[0] << 24) | (p[1] << 16) | (p[2] << 8) | p[3]);
#endif
	m_offset += 4;
	return v;
}

ex_u8* MemStream::get_bin(size_t n)
{
	ASSERT(m_offset + 4 <= m_mbuf.size());
	ex_u8* p = m_mbuf.data() + m_offset;
	m_offset += n;
	return p;
}


void MemStream::put_zero(size_t n)
{
	m_mbuf.reserve(m_mbuf.size() + n);
	memset(m_mbuf.data() + m_offset, 0, n);
	m_offset += n;
	if (m_mbuf.size() < m_offset)
		m_mbuf.size(m_offset);
}

void MemStream::put_u8(ex_u8 v)
{
	m_mbuf.reserve(m_mbuf.size() + 1);

	(m_mbuf.data() + m_offset)[0] = v;
	m_offset++;
	if (m_mbuf.size() < m_offset)
		m_mbuf.size(m_offset);
}

void MemStream::put_u16_le(ex_u16 v)
{
	m_mbuf.reserve(m_mbuf.size() + 2);

	ex_u8* p = m_mbuf.data() + m_offset;
#if defined(B_ENDIAN) 
	p[0] = (ex_u8)v;
	p[1] = (ex_u8)(v >> 8);
#else
	((ex_u16*)p)[0] = v;
#endif
	m_offset += 2;
	if (m_mbuf.size() < m_offset)
		m_mbuf.size(m_offset);
}

void MemStream::put_u16_be(ex_u16 v)
{
	m_mbuf.reserve(m_mbuf.size() + 2);

	ex_u8* p = m_mbuf.data() + m_offset;
#if defined(B_ENDIAN) 
	((ex_u16*)p)[0] = v;
#else
	ex_u8* _v = (ex_u8*)&v;
	p[0] = _v[1];
	p[1] = _v[0];
#endif
	m_offset += 2;
	if (m_mbuf.size() < m_offset)
		m_mbuf.size(m_offset);
}

void MemStream::put_u32_le(ex_u32 v)
{
	m_mbuf.reserve(m_mbuf.size() + 4);

	ex_u8* p = m_mbuf.data() + m_offset;
#if defined(B_ENDIAN) 
	p[0] = (ex_u8)v;
	p[1] = (ex_u8)(v >> 8);
	p[2] = (ex_u8)(v >> 16);
	p[3] = (ex_u8)(v >> 24);
#else
	((ex_u32*)p)[0] = v;
#endif
	m_offset += 4;
	if (m_mbuf.size() < m_offset)
		m_mbuf.size(m_offset);
}

void MemStream::put_u32_be(ex_u32 v)
{
	m_mbuf.reserve(m_mbuf.size() + 4);

	ex_u8* p = m_mbuf.data() + m_offset;
#if defined(B_ENDIAN) 
	((ex_u32*)p)[0] = v;
#else
	ex_u8* _v = (ex_u8*)&v;
	p[0] = _v[3];
	p[1] = _v[2];
	p[2] = _v[1];
	p[3] = _v[0];
#endif
	m_offset += 4;
	if (m_mbuf.size() < m_offset)
		m_mbuf.size(m_offset);
}

void MemStream::put_bin(const ex_u8* p, size_t n)
{
	m_mbuf.reserve(m_mbuf.size() + n);
	memcpy(m_mbuf.data() + m_offset, p, n);
	m_offset += n;
	if (m_mbuf.size() < m_offset)
		m_mbuf.size(m_offset);
}

