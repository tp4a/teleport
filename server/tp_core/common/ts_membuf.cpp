#include "ts_membuf.h"
#include <memory.h>

MemBuffer::MemBuffer()// : m_buffer(NULL), m_data_size(0), m_buffer_size(0)
{
	m_buffer = NULL;
	m_data_size = 0;
	m_buffer_size = 0;
	//EXLOGI("[mbuf:%p] create new instance.\n", this);
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
	//EXLOGI("[mbuf:%p] destroy instance\n", this);
}

void MemBuffer::append(const ex_u8* data, size_t size)
{
	//EXLOGD("[mbuf:%p] call reserve() in append()\n", this);
	reserve(m_data_size + size);

	// TODO: should return boolean.
	if(NULL == m_buffer)
		return;

	//EXLOGD("[mbuf:%p] append(): buffer: %p, m_buf_size: %d, m_data_size: %d, data: %p, size: %d\n", this, m_buffer, m_buffer_size, m_data_size, data, size);
	memcpy(m_buffer+m_data_size, data, size);
	m_data_size += size;
}

void MemBuffer::reserve(size_t size)
{
	if (size <= m_buffer_size)
	{
		//EXLOGD("[mbuf:%p] reserve(1): m_buf: %p, m_buf_size: %d, need size: %d, skip.\n", this, m_buffer, m_buffer_size, size);
		return;
	}

	// 将新的缓冲区大小取整到 MEMBUF_BLOCK_SIZE 的整数倍
	size_t new_size = (size + MEMBUF_BLOCK_SIZE - 1) & ~(MEMBUF_BLOCK_SIZE - 1);
	//EXLOGD("[mbuf:%p] reserve(2): m_buf: %p, m_buf_size: %d, size: %d, new size: %d.\n", this, m_buffer, m_buffer_size, size, new_size);

	if (NULL == m_buffer)
	{
		//EXLOGD("[mbuf:%p] calloc(%d).\n", this, new_size);
		m_buffer = (ex_u8*)calloc(1, new_size);
	}
	else
	{
		//EXLOGD("[mbuf:%p] realloc(%d).\n", this, new_size);
		m_buffer = (ex_u8*)realloc(m_buffer, new_size);
	}

	m_buffer_size = new_size;

	// TODO: reserve() should return boolean.
	if(NULL == m_buffer)
	{
		//EXLOGD("[mbuf:%p] ----- m_buffer == NULL.\n", this);
		m_buffer_size = 0;
		m_data_size = 0;
	}
	//else
	//{
		//EXLOGD("[mbuf:%p] m_buffer == %p.\n", this, m_buffer);
	//}

	//TSLOGD("[mbuf] reserve(): #%d, buffer-size: %d, data-size: %d\n", m_index, m_buffer_size, m_data_size);
	//EXLOGD("[mbuf:%p] reserve(3): m_buf: %p, buffer-size: %d, data-size: %d\n", this, m_buffer, m_buffer_size, m_data_size);
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
