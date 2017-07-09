#pragma once
#include <jasper/jasper.h>
#include <boost/algorithm/string.hpp>
#include <boost/format.hpp>
#undef max

namespace FormatConversion
{

size_t formatToNumberOfBytes(GWF::sampleFormat format)
{
	switch (format)
	{
		case GWF::sampleFormat::i8:
		case GWF::sampleFormat::u8:
			return 1;
		case GWF::sampleFormat::i16:
		case GWF::sampleFormat::u16:
			return 2;
		case GWF::sampleFormat::i32:
		case GWF::sampleFormat::u32:
		case GWF::sampleFormat::i64:
		case GWF::sampleFormat::u64:
		case GWF::sampleFormat::ieee_f32:
		case GWF::sampleFormat::ibm_f32:
		case GWF::sampleFormat::ieee_f64:
		case GWF::sampleFormat::ibm_f64:
			// Not supported			
			break;
		default:
			break;
	}
	assert(false);
	return 0;
}

bool sampleFormatIsSigned(GWF::sampleFormat format)
{
	return (
		format == GWF::sampleFormat::i8 ||
		format == GWF::sampleFormat::i16 ||		
		format == GWF::sampleFormat::i32 ||
		format == GWF::sampleFormat::i64 ||		
		format == GWF::sampleFormat::ieee_f32 ||
		format == GWF::sampleFormat::ibm_f32 ||
		format == GWF::sampleFormat::ieee_f64 ||
		format == GWF::sampleFormat::ibm_f64
		);
}

template<typename T>
char* CopySamples(char* dst, const char* src, size_t length, int offset=0)
{
	// Copy the raw sample data
	memcpy(dst, src, length);

	if(offset != 0)
	{
		// If we need to apply an offset to the samples, we need to interpret them as the right sample format
		auto sample = dst;
		while(sample < dst + length)
		{
			T value;
			ParseField(sample, value);
			sample = SerializeField(sample, static_cast<T>(value + offset));
		}
	}
	return dst + length;
}

char* CopySamples(char* dst, const GWF::Beam& beam)
{
	auto src = beam.m_AmplitudeData.data();
	auto length = beam.m_AmplitudeData.size();
	int offset = 0;
	if(sampleFormatIsSigned(beam.m_amplitudeFormat))
		offset = static_cast<int>(std::powf(2, formatToNumberOfBytes(beam.m_amplitudeFormat) * 8)) / 2;

	switch (beam.m_amplitudeFormat)
	{
		case GWF::sampleFormat::i8:
			return CopySamples<std::int8_t>(dst, (const char*)src, length, offset);
		case GWF::sampleFormat::u8:
			return CopySamples<std::uint8_t>(dst, (const char*)src, length, offset);
		case GWF::sampleFormat::i16:
			return CopySamples<std::int16_t>(dst, (const char*)src, length, offset);
		case GWF::sampleFormat::u16:
			return CopySamples<std::uint16_t>(dst, (const char*)src, length, offset);
		default:
			break;
	}
	assert(false);
	return nullptr;	
}

char* CopySamples(GWF::Beam& beam, const char* src)
{
	auto dst = beam.m_AmplitudeData.data();
	auto length = beam.m_AmplitudeData.size();
	int offset = 0;
	if(sampleFormatIsSigned(beam.m_amplitudeFormat))
	{
		offset = static_cast<int>(std::powf(2, formatToNumberOfBytes(beam.m_amplitudeFormat) * 8)) / 2;
		offset *= -1;
	}

	switch (beam.m_amplitudeFormat)
	{
		case GWF::sampleFormat::i8:
			return CopySamples<std::int8_t>((char*)dst, src, length, offset);
		case GWF::sampleFormat::u8:
			return CopySamples<std::uint8_t>((char*)dst, src, length, offset);
		case GWF::sampleFormat::i16:
			return CopySamples<std::int16_t>((char*)dst, src, length, offset);
		case GWF::sampleFormat::u16:
			return CopySamples<std::uint16_t>((char*)dst, src, length, offset);
		default:
			break;
	}
	assert(false);
	return nullptr;	
}



std::pair<std::shared_ptr<char>, size_t> WcdSamplesToPgm(const GWF::WaterColumn& wcd)
{
	assert(
		wcd.m_amplitudeFormat == GWF::sampleFormat::i8 || 
		wcd.m_amplitudeFormat == GWF::sampleFormat::u8 ||
		wcd.m_amplitudeFormat == GWF::sampleFormat::i16 ||
		wcd.m_amplitudeFormat == GWF::sampleFormat::u16
	);

	size_t max_number_of_sample_bytes = 0;
	for(auto i=0u ; i < wcd.m_Beams.size() ; ++i)
		max_number_of_sample_bytes = std::max(max_number_of_sample_bytes, wcd.m_Beams[i].m_AmplitudeData.size());

	auto bytes_per_sample = formatToNumberOfBytes(wcd.m_amplitudeFormat);
	auto max_sample_value = static_cast<int>(std::powf(2, bytes_per_sample * 8) ) -1;

	auto width = max_number_of_sample_bytes / bytes_per_sample;
	auto height = wcd.m_Beams.size();	

	auto header = str(boost::format("P5\n%d %d\n%d\n") % width % height % max_sample_value);
	size_t size = header.size() + (width * height * bytes_per_sample);

	auto image = static_cast<char*>(malloc(size));
	memset(image, 0, size);
	memcpy(image, header.data(), header.size());
	auto beam_image = image + header.size();

	for(auto i=0u ; i < wcd.m_Beams.size() ; ++i)
	{
		auto& beam = wcd.m_Beams[i];
		CopySamples(beam_image, beam);
		beam_image += max_number_of_sample_bytes;
	}

	return std::make_pair(std::shared_ptr<char>(image), size);
}

void PgmToWcdSamples(std::pair<std::shared_ptr<char>, size_t> pgm, GWF::WaterColumn& wcd)
{	
	// determine header length
	auto whitespaces = 0;
	auto read = 0;
	while(whitespaces < 4 && read < pgm.second)
	{
		if(isspace(*(pgm.first.get() + read)))
			whitespaces++;
		read++;
	}

	assert(whitespaces == 4);	

	std::string header(pgm.first.get(), read);	
	std::vector<std::string> headerItems;
	boost::split(headerItems, header, boost::is_any_of("\t \n"));
	assert(headerItems.size() >= 4);

	auto bytes_per_sample = formatToNumberOfBytes(wcd.m_amplitudeFormat);
	auto max_sample_value_according_to_gwc = static_cast<int>(std::powf(2, bytes_per_sample * 8) ) -1;

	size_t number_of_beams = std::stoi(headerItems[2]);
	assert(number_of_beams == wcd.m_Beams.size());
	size_t samples_per_beam = std::stoi(headerItems[1]);
	size_t sample_bytes_per_beam = samples_per_beam * bytes_per_sample;
	size_t max_sample_value_according_to_header = std::stoi(headerItems[3]);

	
	assert(max_sample_value_according_to_header == max_sample_value_according_to_gwc);

	auto serializedBeam = pgm.first.get() + header.size();
	for(auto beamIndex = 0 ; beamIndex < number_of_beams ; beamIndex++ )
	{
		assert(wcd.m_Beams[beamIndex].m_AmplitudeData.size() <= sample_bytes_per_beam);
		CopySamples(wcd.m_Beams[beamIndex], serializedBeam);
		serializedBeam += sample_bytes_per_beam;
	}
}

std::pair<std::shared_ptr<char>, size_t> ConvertPgmToJpeg2k(std::pair<std::shared_ptr<char>, size_t> pgm)
{
	jas_init();

	auto input_stream = jas_stream_memopen(pgm.first.get(), pgm.second);
	auto pnm_image = jas_image_decode(input_stream, jas_image_strtofmt ("pnm"), nullptr);

	// Let's assume that we are actually compressing. So the compressed image should be
	// no larger than the original 
	auto jpeg2k_memory = static_cast<char*>(malloc(pgm.second));
	auto jpeg2k_stream = jas_stream_memopen(jpeg2k_memory, pgm.second);

	jas_image_encode(pnm_image, jpeg2k_stream, jas_image_strtofmt ("jp2"), nullptr); 
	jas_stream_flush(jpeg2k_stream);
	auto compressed_size = jas_stream_tell(jpeg2k_stream);

	jas_stream_close(input_stream);
	jas_stream_close(jpeg2k_stream);
	jas_image_destroy(pnm_image);

	return std::make_pair(std::shared_ptr<char>(jpeg2k_memory), compressed_size);
}

std::pair<std::shared_ptr<char>, size_t> ConvertJpeg2kToPGM(std::pair<char*, size_t> jp2, size_t uncompressed_size)
{
	jas_init();

	auto input_stream = jas_stream_memopen(jp2.first, jp2.second);
	auto jp2_image = jas_image_decode(input_stream, jas_image_strtofmt ("jp2"), nullptr);

	auto pgm_memory = static_cast<char*>(malloc(uncompressed_size));
	auto pgm_stream = jas_stream_memopen(pgm_memory, uncompressed_size);

	jas_image_encode(jp2_image, pgm_stream, jas_image_strtofmt ("pnm"), nullptr); 
	jas_stream_flush(pgm_stream);
	auto decompressed_size = jas_stream_tell(pgm_stream);

	jas_stream_close(input_stream);
	jas_stream_close(pgm_stream);
	jas_image_destroy(jp2_image);
	
	return std::make_pair(std::shared_ptr<char>(pgm_memory), decompressed_size);
}
}