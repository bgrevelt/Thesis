#pragma once
#include <assert.h>

template<typename T>
	const char * ParseField(const char* src, T& dst)
	{
		auto p = reinterpret_cast<const T*>(src);
		dst = *p;
		return reinterpret_cast<const char*>(++p);
	}

template<typename T>
	char * SerializeField(char* dst, T src)
	{
		auto p = reinterpret_cast<T*>(dst);
		*p = src;
		return reinterpret_cast<char*>(++p);
	}

// TODO: We should template the data type as well
template<typename size_type>
char* SerializeRange(char* dst, const std::vector<std::uint8_t>& src)
{
	size_type size = src.size();
	assert(src.size() == size);

	memcpy(dst, (char*)&size, sizeof(size));
	dst += sizeof(size);
	memcpy(dst, src.data(), size);
	dst += size;
	return dst;
}

// TODO: We should template the data type as well
template<typename size_type>
const char* ParseRange(std::vector<std::uint8_t>& dst, const char* src)
{
	size_type size;
	src = ParseField(src, size);
	dst.resize(size);
	memcpy(dst.data(), src, size);
	src += size;
	return src;
}