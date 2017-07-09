#pragma once
#include <cstdint>
#include <vector>
#include "Parsing.hpp"
#include "types.h"

namespace GWF
{
	class Beam
	{
	public:
		Beam() = default;
		
		Beam(sampleFormat amplitudeFormat, sampleFormat phaseFormat, std::pair<char*, size_t> genericData, std::pair<char*, size_t> amplitudeData, std::pair<char*, size_t> phaseData)
		{
			m_amplitudeFormat = amplitudeFormat;
			m_phaseFormat = phaseFormat;
			m_GenericData.resize(genericData.second);
			memcpy(m_GenericData.data(), genericData.first, genericData.second);
			m_AmplitudeData.resize(amplitudeData.second);
			memcpy(m_AmplitudeData.data(), amplitudeData.first, amplitudeData.second);
			m_PhaseData.resize(phaseData.second);
			memcpy(m_PhaseData.data(), phaseData.first, phaseData.second);
		}		

		Beam(const char* data, size_t size, sampleFormat amplitudeSampleFormat, sampleFormat phaseSampleFormat)
		{
			m_amplitudeFormat = amplitudeSampleFormat;
			m_phaseFormat = phaseSampleFormat;

			std::uint32_t numberOfAmplitudeSamples;
			std::uint32_t numberOfPhaseSamples;
			std::uint16_t genericDataSize;

			data = ParseField(data, numberOfAmplitudeSamples);
			data = ParseField(data, numberOfPhaseSamples);
			data = ParseField(data, genericDataSize);

			m_AmplitudeData.resize(numberOfAmplitudeSamples);
			memcpy(m_AmplitudeData.data(), data, numberOfAmplitudeSamples);
			data += numberOfAmplitudeSamples;

			m_PhaseData.resize(numberOfPhaseSamples);
			memcpy(m_PhaseData.data(), data, numberOfPhaseSamples);
			data += numberOfPhaseSamples;

			m_GenericData.resize(genericDataSize);
			memcpy(m_GenericData.data(), data, genericDataSize);			
		}

		// Getter to get all sample data
		template<typename T>
		void GetAmplitudeSamples(T* data, size_t size) const
		{
			if(!checkType(data, m_amplitudeFormat))
				return; //TODO: throw

			if(size < m_AmplitudeData.size() * sizes[static_cast<std::uint8_t>(m_amplitudeFormat)])
				return; // TODO: throw

			memcpy(data, m_AmplitudeData.data(), m_AmplitudeData.size() * sizes[static_cast<std::uint8_t>(m_amplitudeFormat)]);
		}

		// Getter to get a single sample
		template<typename T>
		void GetAmplitudeSample(T* data, size_t index) const
		{
			if(!checkType(data, m_amplitudeFormat))
				return; //TODO: throw

			if(index >= m_AmplitudeData.size() / sizes[static_cast<std::uint8_t>(m_amplitudeFormat)])
				return; // TODO: throw

			*data = *reinterpret_cast<const T*>(m_AmplitudeData.data() + index * sizes[static_cast<std::uint8_t>(m_amplitudeFormat)]);
		}

		size_t GetSerializedSize()
		{
			auto numberOfAmplitudeSamplesSize = sizeof(std::uint32_t);
			auto numberOfPhaseSamples = sizeof(std::uint32_t);
			auto genericDataSize = sizeof(std::uint16_t);
			return numberOfAmplitudeSamplesSize + numberOfPhaseSamples + genericDataSize + 
				m_AmplitudeData.size() + m_PhaseData.size() + m_GenericData.size();
		}

		char* Serialize(char* dst)
		{
			assert(m_AmplitudeData.size() <= 0xFFFFFFFF);
			auto numberOfAmplitudeSamples = static_cast<std::uint32_t>(m_AmplitudeData.size());
			assert(m_PhaseData.size() <= 0xFFFF);
			auto numberOfPhaseSamples = static_cast<std::uint32_t>(m_PhaseData.size());
			assert(m_GenericData.size() <= 0xFFFF);
			auto genericDataSize = static_cast<std::uint16_t>(m_GenericData.size());

			auto data = dst;
			data = SerializeField(data, numberOfAmplitudeSamples);
			data = SerializeField(data, numberOfPhaseSamples);
			data = SerializeField(data, genericDataSize);		
		
			memcpy(data, m_AmplitudeData.data(), m_AmplitudeData.size());
			data += numberOfAmplitudeSamples;
		
			memcpy(data, m_PhaseData.data(), m_PhaseData.size());
			data += numberOfPhaseSamples;

			memcpy(data, m_GenericData.data(), genericDataSize);
			data += genericDataSize;

			return data;
		}

		sampleFormat m_amplitudeFormat;
		sampleFormat m_phaseFormat;
		std::vector<std::uint8_t> m_GenericData;
		std::vector<std::uint8_t> m_AmplitudeData;
		std::vector<std::uint8_t> m_PhaseData;

	private:
		template<typename T>
		bool checkType(T* data, sampleFormat format) const
		{
			return false;
		}

		template<> bool checkType(std::uint8_t* data, sampleFormat format) const { return format == sampleFormat::u8; }
		template<> bool checkType(std::int8_t* data, sampleFormat format) const { return format == sampleFormat::i8; }
		template<> bool checkType(std::uint16_t* data, sampleFormat format) const { return format == sampleFormat::u16; }
		template<> bool checkType(std::int16_t* data, sampleFormat format) const { return format == sampleFormat::i16; }
		template<> bool checkType(std::uint32_t* data, sampleFormat format) const { return format == sampleFormat::u32; }
		template<> bool checkType(std::int32_t* data, sampleFormat format) const { return format == sampleFormat::i32; }
		template<> bool checkType(float* data, sampleFormat format) const { return format == sampleFormat::ieee_f32; }
		template<> bool checkType(double* data, sampleFormat format) const { return format == sampleFormat::ieee_f64; }

	};
}