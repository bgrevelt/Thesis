#pragma once
#include <utility>
#include <functional>
#include "WaterColumn.h"

#ifdef JPEG2KLIBRARY_EXPORTS  
#define JPEG2KLIBRARY_API __declspec(dllexport)   
#else  
#define JPEG2KLIBRARY_API __declspec(dllimport)   
#endif  

JPEG2KLIBRARY_API char* Compress(char* uncompressedData, unsigned int uncompressedDataSize, unsigned int* compressedSize);
JPEG2KLIBRARY_API char* Decompress(char* compressedData, unsigned int compressedDataSize, unsigned int* decompressedSize);
JPEG2KLIBRARY_API void Destroy(char* data);