#include "ts_membuf.h"
#include <memory.h>

MemBuffer::MemBuffer() : m_buffer(NULL), m_data_size(0), m_buffer_size(0)
{
}

MemBuffer::~MemBuffer()
{
	if (NULL != m_buffer)
	{
		free(m_buffer);
		m_buffer = NULL;
	}
	m_data_size = 0;
	m_buffer_size = 0;

	//TSLOGD("[mbuf] #%d destroied with buffer-size: %d, data-size: %d.\n", m_index, m_buffer_size, m_data_size);
}

void MemBuffer::append(const ex_u8* data, size_t size)
{
	reserve(m_data_size + size);

	// TODO: should return boolean.
	if(NULL == m_buffer)
		return;

	memcpy(m_buffer+m_data_size, data, size);
	m_data_size += size;
}

void MemBuffer::reserve(size_t size)
{
	if (size <= m_buffer_size)
		return;

	// 将新的缓冲区大小取整到 MEMBUF_BLOCK_SIZE 的整数倍
	int new_size = (size + MEMBUF_BLOCK_SIZE - 1) & ~(MEMBUF_BLOCK_SIZE - 1);

	if (NULL == m_buffer)
		m_buffer = (ex_u8*)calloc(1, new_size);
	else
		m_buffer = (ex_u8*)realloc(m_buffer, new_size);

	m_buffer_size = new_size;

	// TODO: reserve() should return boolean.
	if(NULL == m_buffer)
	{
		m_buffer_size = 0;
		m_data_size = 0;
	}

	//TSLOGD("[mbuf] reserve(): #%d, buffer-size: %d, data-size: %d\n", m_index, m_buffer_size, m_data_size);
}

void MemBuffer::concat(const MemBuffer& m)
{
	if (0 == m.m_data_size)
		return;

	append(m.m_buffer, m.m_data_size);
}

void MemBuffer::pop(size_t size)
{
#ifdef EX_DEBUG
	if (size > m_data_size)
		EXLOGE("[mbuf] too big to pop, want to pop %d bytes, but have %d bytes.\n", size, m_data_size);
#endif

	if (size >= m_data_size)
	{
		memset(m_buffer, 0, m_data_size);
		m_data_size = 0;
	}
	else
	{
		m_data_size -= size;
		memmove(m_buffer, m_buffer + size, m_data_size);
	}
}
