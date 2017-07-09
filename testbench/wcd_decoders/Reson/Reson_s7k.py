import os
from .reader import S7kFrameReader
import numpy as np
import struct
import datetime

class Reson7018Beam:
    def __init__(self, size):
        self.amplitude_samples = bytes()
        self.phase_samples = bytes()
        self.number_of_samples = size
        pass

    def get_amplitude_samples(self):
        return self.amplitude_samples

    def get_phase_samples(self):
        return self.phase_samples

    def get_number_of_amplitude_samples(self):
        return self.number_of_samples

    def get_generic_data(self):
        return bytes()

class Reson7018Wrapper:
    def __init__(self, packet):
        self.header = packet
        self.wcd = packet.record()
        self.beams = []
        for i in range(self.wcd.beams):
            self.beams.append(Reson7018Beam(self.wcd.samples))
        for sample in range(self.wcd.samples):
            for beam in range(self.wcd.beams):
                # Some oddness going on here because we need to get back from the numpy array (float64's) to the original sample format
                self.beams[beam].amplitude_samples += struct.pack('H', int(self.wcd.amplitude[sample][beam]))
                self.beams[beam].phase_samples += struct.pack('h', int(self.wcd.phase[sample][beam]))

    def get_amplitude_sample_format(self):
        return 3

    def get_phase_sample_format(selfs):
        return 2

    def get_generic_data(self):
        return self.header.binary_data + self.wcd.binary_header

    def get_beams(self):
        return self.beams

    def get_ping_time(self):
        year = self.header.year
        daysofyear = self.header.day
        hour = self.header.hour
        minute = self.header.minute
        seconds = int(self.header.second // 1)
        microseconds = int(((self.header.second % 1) * 1E6) // 1)

        return datetime.datetime(year, 1, 1, hour, minute, seconds, microseconds) + datetime.timedelta(daysofyear -1 )

    def get_ping_number(self):
        return self.wcd.pingNumber

class Reson7008Beam:
    def __init__(self, packet, beam_index):
        self.packet = packet
        self.beam_index = beam_index

    def get_amplitude_samples(self):
        return self.packet.beams[self.beam_index].amplitude

    def get_phase_samples(self):
        return self.packet.beams[self.beam_index].phase

    def get_number_of_amplitude_samples(self):
        return self.packet.numberOfSamplesInPing

    def get_generic_data(self):
        return bytes(self.packet.beams[self.beam_index].data)

class Reson7008Wrapper:
    def __init__(self, packet):
        self.header = packet
        self.wcd = packet.record()
        self.beams = [Reson7008Beam(self.wcd, i) for i in range(self.wcd.numberOfBeams)]

    def get_amplitude_sample_format(self):
        return 3

    def get_phase_sample_format(selfs):
        return 2

    def get_generic_data(self):
        return bytes(self.wcd.header_data)

    def get_beams(self):
        return self.beams

    def get_ping_time(self):
        year = self.header.year
        daysofyear = self.header.day
        hour = self.header.hour
        minute = self.header.minute
        seconds = int(self.header.second // 1)
        microseconds = int(((self.header.second % 1) * 1E6) // 1)

        return datetime.datetime(year, 1, 1, hour, minute, seconds, microseconds) + datetime.timedelta(daysofyear -1 )

    def get_ping_number(self):
        return self.wcd.pingNumber

class Reson7kParser:
    def __init__(self):
        self.path = None
        self.parser = None
        self.wc_generator = None
        self.first_wc_packet = None

        self.device_types = {
            20 	 : 'RESON SeaBat T20-P ',
            50 	 : 'RESON SeaBat T50-P ',
            100  : 'Generic Position Sensor (e.g., GPS) ',
            101  : 'Generic Heading Sensor (e.g., Gyro) ',
            102  : 'Generic Attitude Sensor ',
            103  : 'Generic MBES ',
            104  : 'Generic Side-scan Sonar ',
            105  : 'Generic Sub-bottom Profiler ',
            1000 : 'Odom Odom MB1 ',
            1001 : 'TrueTime PCISG ',
            1002 : 'Odom Odom MB2 ',
            2000 : 'CDC SMCG 2001 CDC SPG ',
            2002 : 'Empire Magnetics YS2000 Rotator ',
            4013 : 'RESON TC4013 ',
            6000 : 'RESON DiverDat ',
            7000 : 'RESON 7kCenter ',
            7001 : 'RESON 7k User Interface ',
            7003 : 'RESON Teledyne PDS ',
            7004 : 'RESON 7k Logger ',
            7005 : 'BlueView BlueView ProScan ',
            7012 : 'RESON SeaBat',
            7012 : '7100 RESON SeaBat 7100 ',
            7101 : 'RESON SeaBat 7101 ',
            7102 : 'RESON SeaBat 7102 ',
            7111 : 'RESON SeaBat 7111 ',
            7112 : 'RESON SeaBat 7112 ',
            7123 : 'RESON SeaBat 7123 ',
            7125 : 'RESON SeaBat 7125 ',
            7128 : 'RESON SeaBat 7128',
            7150 : 'RESON SeaBat 7150 '
        }

    def GetSupportedExtensions(self):
        return ['.s7k']

    def Open(self, path):
        self.path = path
        self.parser = S7kFrameReader(path)
        self.parser.open()
        self.wc_generator = (recordFrame for recordFrame in self.parser if recordFrame.recordTypeIdentifier in {7008, 7018, 7042})

    def Close(self):
        self.parser.close()
        self.path = None
        self.parser = None
        self.wc_generator = None
        self.first_wc_packet = None


    def ContainsWcd(self):
        if self.first_wc_packet == None:
            self._FindWcPacket()

        return self.first_wc_packet != None

    def GetMakeAndModel(self):
        if self.first_wc_packet == None:
            self._FindWcPacket()

        if self.first_wc_packet == None:
            return ("None", "None")

        if self.first_wc_packet.deviceIdentifier not in self.device_types:
            return ("Reson", "Unknown {}".format(self.first_wc_packet.deviceIdentifier))

        return ("Reson", self.device_types[self.first_wc_packet.deviceIdentifier])

    def _FindWcPacket(self):
        if self.wc_generator == None:
            raise ValueError

        if self.first_wc_packet == None:
            try:
                self.first_wc_packet = next(self.wc_generator)
            except StopIteration:
                pass

    def wrap_wcd(self, record):
        if record.recordTypeIdentifier == 7018:
            return Reson7018Wrapper(record)
        elif record.recordTypeIdentifier == 7008:
            return Reson7008Wrapper(record)
        else:
            raise ValueError('Unsupported packet type {}'.format(record.recordTypeIdentifier))
            return record

    def water_column_packets(self):
        self.parser.close()
        self.parser.open()
        return (self.wrap_wcd(recordFrame) for recordFrame in self.parser if recordFrame.recordTypeIdentifier in {7008, 7018, 7042})

# class reader_reson:
#     def __init__(self):
#         self.device_types = {
#             20 	 : 'RESON SeaBat T20-P ',
#             100  : 'Generic Position Sensor (e.g., GPS) ',
#             101  : 'Generic Heading Sensor (e.g., Gyro) ',
#             102  : 'Generic Attitude Sensor ',
#             103  : 'Generic MBES ',
#             104  : 'Generic Side-scan Sonar ',
#             105  : 'Generic Sub-bottom Profiler ',
#             1000 : 'Odom Odom MB1 ',
#             1001 : 'TrueTime PCISG ',
#             1002 : 'Odom Odom MB2 ',
#             2000 : 'CDC SMCG 2001 CDC SPG ',
#             2002 : 'Empire Magnetics YS2000 Rotator ',
#             4013 : 'RESON TC4013 ',
#             6000 : 'RESON DiverDat ',
#             7000 : 'RESON 7kCenter ',
#             7001 : 'RESON 7k User Interface ',
#             7003 : 'RESON Teledyne PDS ',
#             7004 : 'RESON 7k Logger ',
#             7005 : 'BlueView BlueView ProScan ',
#             7012 : 'RESON SeaBat',
#             7012 : '7100 RESON SeaBat 7100 ',
#             7101 : 'RESON SeaBat 7101 ',
#             7102 : 'RESON SeaBat 7102 ',
#             7111 : 'RESON SeaBat 7111 ',
#             7112 : 'RESON SeaBat 7112 ',
#             7123 : 'RESON SeaBat 7123 ',
#             7125 : 'RESON SeaBat 7125 ',
#             7128 : 'RESON SeaBat 7128 7150 RESON SeaBat 7150 ',
#         }
#
#         self.device_type = None
#         self.block_types = set()
#
#     def contains_water_column_data(self, path):
#         file, ext = os.path.splitext(path)
#         if ext.lower() != '.s7k':
#             return False
#
#         return self.search_for_wcd(path)
#         #self.analyze_file(path)
#         #print(self.block_types)
#         #print(self.block_types.intersection({7018, 7042}))
#         #return len(self.block_types.intersection({7018, 7042})) > 0
#
#     def search_for_wcd(self, path):
#         r = WCD_crawler.Decoders.reader.S7kFrameReader(path)
#         r.open()
#         for recordFrame in r:
#             if recordFrame.recordTypeIdentifier in {7008, 7018, 7042}:
#                 self.device_type = recordFrame.deviceIdentifier
#                 return True
#
#         return False
#
#     def analyze_file(self, path):
#         r = WCD_crawler.Decoders.reader.S7kFrameReader(path)
#         r.open()
#         for recordFrame in r:
#             if self.device_type == None:
#                 self.device_type = recordFrame.deviceIdentifier
#
#             self.block_types.add(recordFrame.recordTypeIdentifier)
#
#     def get_manufacturer(self):
#         return 'Reson'
#
#     def get_device(self):
#         if self.device_type in self.device_types:
#             return self.device_types[self.device_type]
#
#         return 'unknown device %d'.format(self.device_type)
