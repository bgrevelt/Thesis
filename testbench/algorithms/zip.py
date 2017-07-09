import zipfile
import json
from gwf import File as gwf

deflate = False

def init(parameters):
    decoded = json.loads(parameters)
    global deflate
    if 'compress' in decoded and decoded['compress'] == True:
        deflate = True

def compress(input_path, output_path):
    with open(input_path, 'rb') as input_file:
        mode = zipfile.ZIP_DEFLATED if deflate else zipfile.ZIP_STORED
        with zipfile.ZipFile(output_path, 'w', mode) as myzip:
            myzip.write(input_path)
        return 0

def decompress(input_path, output_path, record_id = None):
    if(record_id != None):
        return decompress_record(input_path, output_path, record_id)

    with open(output_path, 'wb') as output_file:
        mode = zipfile.ZIP_DEFLATED if deflate else zipfile.ZIP_STORED
        with zipfile.ZipFile(input_path, 'r', mode) as myzip:
            objects = myzip.infolist()
            assert len(objects) == 1
            output_file.write( myzip.read(objects[0]))
        return 0

def decompress_record(input_path, output_path, record_id):
    # decompress the file to a temporary location
    temp_file = output_path + '_TEMP'
    decompress(input_path, temp_file)
    #use GWF to read the entire file
    gwf_file = gwf(temp_file)
    for wc in gwf_file.read():
        if wc.ping_number == record_id:
            with open(output_path, 'wb') as f:
                f.write(wc.serialize())
            break


