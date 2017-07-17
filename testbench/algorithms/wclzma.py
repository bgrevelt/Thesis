import os
import pylzma
import gwf
import struct

_record_header_format = '<II' # block size including header, record ID
header_length = struct.calcsize(_record_header_format)

def init(parameters):
    pass

def compress(input_path, output_path):
    gwf_file = gwf.File(input_path)
    with open(output_path, 'wb') as output_file:
        for record in gwf_file.read():
            compressed = pylzma.compress(record.serialize())
            write_block(compressed, record.ping_number, output_file)

def decompress(input_path, output_path, record_id = None):
    file_size = os.path.getsize(input_path)
    with open(input_path, 'rb') as input_file, open(output_path, 'wb') as output_file:
        while input_file.tell() < file_size:
            block_size, current_record_id = read_block_header(input_file)
            if record_id == None or record_id == current_record_id:
                compressed_data = read_compressed_data(input_file, block_size)
                decompressed_data = pylzma.decompress(compressed_data)
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

# def _compress(data):
#     compressed_data_length = ctypes.c_uint()
#     compressed = _compress_function(ctypes.c_char_p(data), ctypes.c_uint(len(data)), ctypes.byref(compressed_data_length))
#     data = compressed[:compressed_data_length.value]
#
#     # We now have the data in python space, so the library can deallocate the data
#     _destroy_function(compressed)
#
#     return data
#
# def _decompress(data):
#     decompressed_data_length = ctypes.c_uint()
#     decompressed = _decompress_function(ctypes.c_char_p(data), ctypes.c_uint(len(data)), ctypes.byref(decompressed_data_length))
#     data = decompressed[:decompressed_data_length.value]
#
#     # We now have the data in python space, so the library can deallocate the data
#     _destroy_function(decompressed)
#
#     return data
#
#
# def decompress(input_path, output_path, record_id = None):
#     if record_id == None:
#         return full_decompress(input_path, output_path)
#     else:
#         return partial_decompress(input_path, output_path, record_id)
#
# def full_decompress(input_path, output_path):
#     with open(input_path, 'rb') as in_file, open(output_path, 'wb') as out_file:
#        obj = pylzma.decompressobj()
#        while True:
#            tmp = in_file.read(1)
#            if not tmp:
#                break
#            decompressed = obj.decompress(tmp)
#            if decompressed:
#                out_file.write(decompressed)
#
#        decompressed = obj.flush()
#        out_file.write(decompressed)
#
# def partial_decompress(input_path, output_path, record_id):
#     # decompress the file to a temporary location
#     temp_file = output_path + '_TEMP'
#     full_decompress(input_path, temp_file)
#
#     #use GWF to read the entire file
#     gwf_file = gwf.File(temp_file)
#     for wc in gwf_file.read():
#         if wc.ping_number == record_id:
#             with open(output_path, 'wb') as f:
#                 f.write(wc.serialize())
#             break
#
#     gwf_file = None
#     os.remove(temp_file)
