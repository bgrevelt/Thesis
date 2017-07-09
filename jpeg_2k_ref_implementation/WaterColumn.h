#pragma once
#include <cstdint>
#include <vector>
#include "Parsing.hpp"
#include "types.h"
#include "beam.h"

namespace GWF
{
	class WaterColumn
	{
	public:	
		WaterColumn(const char* data, size_t size) // Construct from serialized data
		{
			PING_NUMBER_TYPE pingNumber;
			PING_TIME_S_TYPE pingTimeSeconds;
			PING_TIME_US_TYPE pingTimeMicroSeconds;
			NUMBER_OF_BEAMS_TYPE numberOfBeams;
			GENERIC_DATA_SIZE_TYPE genericDataSize;
			SAMPLE_FORMAT_TYPE amplitudeSampleFormat;
			SAMPLE_FORMAT_TYPE phaseSampleFormat;

			data = ParseField(data, pingNumber);
			data = ParseField(data, pingTimeSeconds);
			data = ParseField(data, pingTimeMicroSeconds);
			data = ParseField(data, numberOfBeams);
			data = ParseField(data, amplitudeSampleFormat);
			data = ParseField(data, phaseSampleFormat);
			data = ParseField(data, genericDataSize);

			m_pingNumber = pingNumber;
			m_pingTime = std::make_pair(pingTimeSeconds, pingTimeMicroSeconds);
			m_amplitudeFormat = static_cast<sampleFormat>(amplitudeSampleFormat);
			m_phaseFormat = static_cast<sampleFormat>(phaseSampleFormat);

			m_GenericData.resize(genericDataSize);
			memcpy(m_GenericData.data(), data, genericDataSize);

			data += genericDataSize;

			m_Beams.reserve(numberOfBeams);
			for(auto i=0u ; i<numberOfBeams ; ++i)
			{
				m_Beams.emplace_back(data, size, static_cast<sampleFormat>(amplitudeSampleFormat), static_cast<sampleFormat>(phaseSampleFormat));			
				data += m_Beams.back().GetSerializedSize();
			}
		}

		WaterColumn(sampleFormat amplitudeFormat, sampleFormat phaseFormat)
		{
			m_amplitudeFormat = amplitudeFormat;
			m_phaseFormat = phaseFormat;
		}

		size_t GetSerializedSize()
		{
			size_t size = 0;
			size += sizeof(PING_NUMBER_TYPE);
			size += sizeof(PING_TIME_S_TYPE);
			size += sizeof(PING_TIME_US_TYPE);
			size += sizeof(NUMBER_OF_BEAMS_TYPE);
			size += sizeof(GENERIC_DATA_SIZE_TYPE);
			size += sizeof(SAMPLE_FORMAT_TYPE);
			size += sizeof(SAMPLE_FORMAT_TYPE);
			size += m_GenericData.size();
			for(auto& beam : m_Beams)
			{
				size += beam.GetSerializedSize();
			}

			return size;
		}

		std::pair<char*, size_t> Serialize()
		{		
			auto total_size = GetSerializedSize();

			auto data = (char*)malloc(total_size);
			auto start = data;

			assert(m_pingNumber <= 0xFFFFFFFF);
			auto pingNumber = static_cast<PING_NUMBER_TYPE>(m_pingNumber);
			assert(m_Beams.size() <= 0xFFFF);
			auto numberOfBeams = static_cast<NUMBER_OF_BEAMS_TYPE>(m_Beams.size());
			assert(m_GenericData.size() <= 0xFFFF);
			auto genericDataSize = static_cast<GENERIC_DATA_SIZE_TYPE>(m_GenericData.size());
			auto amplitudeSampleFormat = static_cast<SAMPLE_FORMAT_TYPE>(m_amplitudeFormat);
			auto phaseSampleFormat = static_cast<SAMPLE_FORMAT_TYPE>(m_phaseFormat);

			data = SerializeField(data, pingNumber);
			data = SerializeField(data, m_pingTime.first);
			data = SerializeField(data, m_pingTime.second);
			data = SerializeField(data, numberOfBeams);
			data = SerializeField(data, amplitudeSampleFormat);
			data = SerializeField(data, phaseSampleFormat);
			data = SerializeField(data, genericDataSize);
			memcpy(data, m_GenericData.data(), m_GenericData.size());
			data += m_GenericData.size();
		
			for(auto& beam : m_Beams)
				data = beam.Serialize(data);

			return std::make_pair(start, data - start);
		}



	public:
		sampleFormat m_amplitudeFormat;
		sampleFormat m_phaseFormat;
		std::vector<std::uint8_t> m_GenericData;
		std::vector<Beam> m_Beams;
		size_t m_pingNumber;
		std::pair<PING_TIME_S_TYPE, PING_TIME_US_TYPE> m_pingTime;
	};
}