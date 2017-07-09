#pragma once
#include "jpeg_2k_compression.h"
#include "Parsing.hpp"
#include "WaterColumn.h"
#include "FormatConversion.h"
#include <set>
#include <assert.h>


/* TODO: There is the possibility to create a reader for the Jasper library that directly read the wcd format. This would save the conversion to PGM. */

/* The compressed file format looks as follows:

	-------------------------------------------
	| BYTE   |        Amplitude format        |
	-------------------------------------------
	| BYTE   |           phase format         |
	-------------------------------------------
	| UINT16 |         Number of beams        |
	-------------------------------------------
	| UINT16 |     Ping generic data size     |
	-------------------------------------------
	| BYTE[] |       Ping generic data        |
	-------------------------------------------
	| UINT16 |   Generic data size beam 1     |
	-------------------------------------------
	| BYTE[] |     Generic data beam 1        |
	-------------------------------------------
	| UINT32 | Number of phase samples beam 1 |
	-------------------------------------------
	| BYTE[] |        Phase samples beam 1    |
	-------------------------------------------
	| UINT32 | Amplitude sample count beam 1  |
	-------------------------------------------
	| UINT16 |   Generic data size beam 2     |
	-------------------------------------------
	| BYTE[] |     Generic data beam 2        |
	-------------------------------------------
	| UINT32 | Number of phase samples beam 2 |
	-------------------------------------------
	| BYTE[] |        Phase samples beam 2    |
	-------------------------------------------
	| UINT32 | Amplitude sample count beam 2  |
	-------------------------------------------
	|                  .....                  |
	|                  .....                  |
	|                  .....                  |
	-------------------------------------------
	| UINT16 |   Generic data size beam N     |
	-------------------------------------------
	| BYTE[] |     Generic data beam N        |
	-------------------------------------------
	| UINT32 | Number of phase samples beam N |
	-------------------------------------------
	| BYTE[] |        Phase samples beam N    |
	-------------------------------------------
	| UINT32 | Amplitude sample count beam N  |	
	-------------------------------------------
	| UINT32 |  size of uncompressed samples  |	
	-------------------------------------------
	|       Amplitude samples as jpeg2k       |
	-------------------------------------------
*/

static char* WriteAmplitudeFormat(char* dst, const GWF::WaterColumn& wcd);
static char* WritePhaseFormat(char* dst, const GWF::WaterColumn& wcd);
static char* WriteNumberOfBeams(char* dst, const GWF::WaterColumn& wcd);
static char* WriteGenericPingData(char* dst, const GWF::WaterColumn& wcd);
static char* WriteGenericBeamData(char* dst, const GWF::Beam& beam);
static char* WriteBeamPhaseData(char* dst, const GWF::Beam& beam);
static char* WriteBeamAmplitudeSampleCount(char* dst, const GWF::Beam& beam);
static char* WriteAmplitudeSamples(char* dst, const GWF::WaterColumn& wcd);
static char* WritePingNumber(char* dst, const GWF::WaterColumn& wcd);
static char* WritePingTime(char* dst, const GWF::WaterColumn& wcd);

static const char* ReadAmplitudeFormat(const char* src, GWF::sampleFormat& format);
static const char* ReadPhaseFormat(const char* src, GWF::sampleFormat& format);
static const char* ReadNumberOfBeams(const char* src, GWF::WaterColumn& wcd);
static const char* ReadGenericPingData(const char* src, GWF::WaterColumn& wcd);
static const char* ReadGenericBeamData(const char* src, GWF::Beam& beam);
static const char* ReadBeamPhaseData(const char* src, GWF::Beam& beam);
static const char* ReadBeamAmplitudeSampleCount(const char* src, GWF::Beam& beam);
static const char* ReadAmplitudeSamples(const char* src, size_t length, GWF::WaterColumn& wcd);
const char * ReadPingNumber(const char * src, std::uint32_t & pingNumber);
const char * ReadPingTime(const char * src, std::pair<PING_TIME_S_TYPE, PING_TIME_US_TYPE>& pingTime);

char* Compress(char* uncompressedData, unsigned int uncompressedDataSize, unsigned int* compressedSize)
{
	// Parse the data as generic water column data
	GWF::WaterColumn wcd(uncompressedData, uncompressedDataSize);

	// Let's assume that we are at least able not to inflate the data. Allocate a buffer equal to the input size
	auto out_data = (char*)malloc(uncompressedDataSize);
	auto buffer_start = out_data;

	out_data = WritePingNumber(out_data, wcd);
	out_data = WritePingTime(out_data, wcd);
	out_data = WriteAmplitudeFormat(out_data, wcd);
	out_data = WritePhaseFormat(out_data, wcd);
	out_data = WriteNumberOfBeams(out_data, wcd);
	out_data = WriteGenericPingData(out_data, wcd);

	for(auto& beam : wcd.m_Beams)
	{
		out_data = WriteGenericBeamData(out_data, beam);
		out_data = WriteBeamPhaseData(out_data, beam);
		out_data = WriteBeamAmplitudeSampleCount(out_data, beam);
	}

	out_data = WriteAmplitudeSamples(out_data, wcd);
	*compressedSize = static_cast<size_t>(out_data-buffer_start);
	return buffer_start;
}

char* Decompress(char* compressedData, unsigned int compressedDataSize, unsigned int* decompressedSize)
{	
	std::uint32_t pingNumber;
	auto src = ReadPingNumber(compressedData, pingNumber);
	std::pair<PING_TIME_S_TYPE, PING_TIME_US_TYPE> pingTime;
	src = ReadPingTime(src, pingTime);
	GWF::sampleFormat amplitudeFormat;
	src = ReadAmplitudeFormat(src, amplitudeFormat);
	GWF::sampleFormat phaseFormat;
	src = ReadPhaseFormat(src, phaseFormat);

	GWF::WaterColumn wcd(amplitudeFormat, phaseFormat);
	wcd.m_pingNumber = pingNumber;
	wcd.m_pingTime = pingTime;

	src = ReadNumberOfBeams(src, wcd);
	src = ReadGenericPingData(src, wcd);
	for(auto& beam : wcd.m_Beams)
	{
		src = ReadGenericBeamData(src, beam);
		src = ReadBeamPhaseData(src, beam);
		src = ReadBeamAmplitudeSampleCount(src, beam);
	}

	src = ReadAmplitudeSamples(src, compressedDataSize- (src-compressedData), wcd);

	auto serialized = wcd.Serialize();
	*decompressedSize = serialized.second;
	return serialized.first;
}

void Destroy(char* data)
{
	delete data;
}

char * WritePingNumber(char * dst, const GWF::WaterColumn & wcd)
{
	auto pingNumber = static_cast<std::uint32_t>(wcd.m_pingNumber);
	return SerializeField(dst, pingNumber);
}

char * WritePingTime(char * dst, const GWF::WaterColumn & wcd)
{
	auto pingTimeSeconds = static_cast<PING_TIME_S_TYPE>(wcd.m_pingTime.first);
	auto pingTimeMicroSeconds = static_cast<PING_TIME_US_TYPE>(wcd.m_pingTime.second);
	dst = SerializeField(dst, pingTimeSeconds);
	return SerializeField(dst, pingTimeMicroSeconds);
}

char * WriteAmplitudeFormat(char * dst, const GWF::WaterColumn & wcd)
{
	auto amplitudeFormat = static_cast<std::uint8_t>(wcd.m_amplitudeFormat);
	return SerializeField(dst, amplitudeFormat);
}

char * WritePhaseFormat(char * dst, const GWF::WaterColumn & wcd)
{
	auto amplitudeFormat = static_cast<std::uint8_t>(wcd.m_phaseFormat);
	return SerializeField(dst, amplitudeFormat);
}

char * WriteNumberOfBeams(char * dst, const GWF::WaterColumn & wcd)
{
	auto numberOfBeams = static_cast<std::uint16_t>(wcd.m_Beams.size());
	assert(numberOfBeams == wcd.m_Beams.size());
	return SerializeField(dst, numberOfBeams);	
}

char * WriteGenericPingData(char * dst, const GWF::WaterColumn & wcd)
{
	return SerializeRange<std::uint16_t>(dst, wcd.m_GenericData);
}

char * WriteGenericBeamData(char * dst, const GWF::Beam& beam)
{
	return SerializeRange<std::uint16_t>(dst, beam.m_GenericData);
}

char * WriteBeamPhaseData(char * dst, const GWF::Beam& beam)
{
	return SerializeRange<std::uint32_t>(dst, beam.m_PhaseData);
}

char * WriteBeamAmplitudeSampleCount(char * dst, const GWF::Beam& beam)
{
	return SerializeField(dst, (std::uint32_t)beam.m_AmplitudeData.size());
}

char * WriteAmplitudeSamples(char * dst, const GWF::WaterColumn& wcd)
{
	std::set<GWF::sampleFormat> supportedSampleFormats = {GWF::sampleFormat::i8, GWF::sampleFormat::u8, GWF::sampleFormat::i16, GWF::sampleFormat::u16};
	if(supportedSampleFormats.find(wcd.m_amplitudeFormat) == supportedSampleFormats.end())
		return nullptr; // TODO: error reporting

	// Create a PGM from the sample data
	auto pgm = FormatConversion::WcdSamplesToPgm(wcd);
	// Then convert the PGM to a JPEG2k
	auto jp2 = FormatConversion::ConvertPgmToJpeg2k(pgm);
	// Write the size of the UNCOMPRESSED image
	std::uint32_t size = pgm.second;
	assert(size == pgm.second); // Make sure we don't have an overflow
	dst = SerializeField(dst, size);
	
	// and write the jpeg2k samples 
	memcpy(dst, jp2.first.get(), jp2.second);

	dst += jp2.second;
	return dst;
}

const char * ReadPingNumber(const char * src, std::uint32_t & pingNumber)
{
	return ParseField(src, pingNumber);
}

const char * ReadPingTime(const char * src, std::pair<PING_TIME_S_TYPE, PING_TIME_US_TYPE>& pingTime)
{
	src = ParseField(src, pingTime.first);
	return ParseField(src, pingTime.second);	
}

const char * ReadAmplitudeFormat(const char * src, GWF::sampleFormat & format)
{
	std::uint8_t f;
	src = ParseField(src, f);
	format = static_cast<GWF::sampleFormat>(f);
	return src;
}

const char * ReadPhaseFormat(const char * src, GWF::sampleFormat & format)
{
	std::uint8_t f;
	src = ParseField(src, f);
	format = static_cast<GWF::sampleFormat>(f);
	return src;
}

const char * ReadNumberOfBeams(const char * src, GWF::WaterColumn & wcd)
{
	std::uint16_t beamCount;
	src = ParseField(src, beamCount);
	
	wcd.m_Beams.resize(beamCount);
	for(auto& beam : wcd.m_Beams)
	{
		beam.m_amplitudeFormat = wcd.m_amplitudeFormat;
		beam.m_phaseFormat = wcd.m_phaseFormat;
	}

	return src;
}

const char * ReadGenericPingData(const char * src, GWF::WaterColumn & wcd)
{
	return ParseRange<std::uint16_t>(wcd.m_GenericData, src);
}

const char * ReadGenericBeamData(const char * src, GWF::Beam & beam)
{
	return ParseRange<std::uint16_t>(beam.m_GenericData, src);
}

const char * ReadBeamPhaseData(const char * src, GWF::Beam & beam)
{
	return ParseRange<std::uint32_t>(beam.m_PhaseData, src);
}

const char * ReadBeamAmplitudeSampleCount(const char * src, GWF::Beam & beam)
{
	std::uint32_t number_of_samples;
	src = ParseField(src, number_of_samples);
	beam.m_AmplitudeData.resize(number_of_samples);
	return src;
}

const char * ReadAmplitudeSamples(const char * src, size_t length, GWF::WaterColumn & wcd)
{
	std::uint32_t uncompressed_size;
	src = ParseField(src, uncompressed_size);
	auto pgm = FormatConversion::ConvertJpeg2kToPGM(std::make_pair(const_cast<char*>(src), length), uncompressed_size);	
	FormatConversion::PgmToWcdSamples(pgm, wcd);
	return src + length;
}
