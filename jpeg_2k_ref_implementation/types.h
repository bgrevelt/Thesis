#pragma once
#include <cstdint>
namespace GWF
{
	enum class sampleFormat : std::uint8_t
	{
		i8 = 0,
		u8 = 1,
		i16 = 2,
		u16 = 3,
		i32 = 4,
		u32 = 5,
		i64 = 6 ,
		u64 = 7,
		ieee_f32 = 8,
		ibm_f32 = 9,
		ieee_f64 = 10,
		ibm_f64 = 11
	};

	unsigned int sizes[12] = {1,1,2,2,4,4,8,8,4,4,8,8};

#define PING_NUMBER_TYPE std::uint32_t
#define PING_TIME_S_TYPE std::uint32_t
#define PING_TIME_US_TYPE std::uint32_t
#define NUMBER_OF_BEAMS_TYPE std::uint16_t
#define GENERIC_DATA_SIZE_TYPE std::uint16_t
#define SAMPLE_FORMAT_TYPE std::uint8_t
}