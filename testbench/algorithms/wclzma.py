import os
import pylzma
import gwf
import struct
import json
import logging

_record_header_format = '<II' # block size including header, record ID
header_length = struct.calcsize(_record_header_format)

compression_mode = 2

def init(parameters):
    decoded = json.loads(parameters)
    global compression_mode
    if 'compression mode' in decoded:
        compression_mode =  decoded['compression mode']
    else:
        logging.warning('Parameters did not contain expected field "compression mode". using default compression mode {}'.format(compression_mode))

def compress(input_path, output_path):
    gwf_file = gwf.File(input_path)
    with open(output_path, 'wb') as output_file:
        for record in gwf_file.read():
            compressed = pylzma.compress(record.serialize(), algorithm=compression_mode)
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

                if record_id != None:
                    return

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
