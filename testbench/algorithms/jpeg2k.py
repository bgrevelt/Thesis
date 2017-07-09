import ctypes
import gwf
import struct
import os

jp2kdll = ctypes.WinDLL(r'algorithms/jpeg_2k_compression_lib.dll')
_compress_function = getattr(jp2kdll, "?Compress@@YAPEADPEADIPEAI@Z")
_decompress_function = getattr(jp2kdll, "?Decompress@@YAPEADPEADIPEAI@Z")
_destroy_function = getattr(jp2kdll, "?Destroy@@YAXPEAD@Z")

_decompress_function.restype = ctypes.POINTER(ctypes.c_char)
_compress_function.restype = ctypes.POINTER(ctypes.c_char)

_record_header_format = '<II' # block size including header, record ID
header_length = struct.calcsize(_record_header_format)

def init(parameters):
    pass

def compress(input_path, output_path):
    gwf_file = gwf.File(input_path)
    with open(output_path, 'wb') as out_file:
        for record in gwf_file.read():
            data = record.serialize()
            compressed_data = _compress(data)
            write_block(compressed_data, record.ping_number, out_file)

def decompress(input_path, output_path, record_id = None):
    file_size = os.path.getsize(input_path)
    with open(input_path, 'rb') as input_file, open(output_path, 'wb') as output_file:
        while input_file.tell() < file_size:
            block_size, current_record_id = read_block_header(input_file)
            if record_id == None or record_id == current_record_id:
                compressed_data = read_compressed_data(input_file, block_size)
                decompressed_data = _decompress(compressed_data)
                write_decompressed_data(output_file, decompressed_data)
            else:
                skip_block(input_file, block_size)

def read_compressed_data(file, block_size):
    compressed_data_size = block_size - header_length
    return file.read(compressed_data_size)

def write_decompressed_data(file, data):
    file.write(data)

def write_block(data, record_id, file):
    write_block_header(data, record_id, file)
    file.write(data)

def read_block_header(file):
    header_data = file.read(header_length)
    return struct.unpack(_record_header_format, header_data)

def write_block_header(data, record_id, file):
    block_length = len(data) + header_length
    file.write(struct.pack(_record_header_format, block_length, record_id))

def skip_block(file, block_size):
    compressed_data_size = block_size - header_length
    file.seek(compressed_data_size, 1)

def _compress(data):
    compressed_data_length = ctypes.c_uint()
    compressed = _compress_function(ctypes.c_char_p(data), ctypes.c_uint(len(data)), ctypes.byref(compressed_data_length))
    data = compressed[:compressed_data_length.value]

    # We now have the data in python space, so the library can deallocate the data
    _destroy_function(compressed)

    return data

def _decompress(data):
    decompressed_data_length = ctypes.c_uint()
    decompressed = _decompress_function(ctypes.c_char_p(data), ctypes.c_uint(len(data)), ctypes.byref(decompressed_data_length))
    data = decompressed[:decompressed_data_length.value]

    # We now have the data in python space, so the library can deallocate the data
    _destroy_function(decompressed)

    return data
