import os
import struct
import logging
import datetime
from collections import OrderedDict
from copy import deepcopy
from .wcd_congregator import *

class KongsbergPingTime:
    def __init__(self, date, time):
        print(date)
        print(time)
        self.year = date / 1E4
        date -= self.year * 1E4
        self.month = date / 1E2
        date -= self.month * 1E2
        self.day = date
        self.hours
        self.minutes
        self.sec

class KongsbergPacket:
    def __init__(self, fin):

        temp = fin.read(8)
        if not temp or len(temp) != 8:
            raise ValueError("This should really be a different exception type. Reading packet failed")

        unpacked = struct.unpack('<IBBH', temp);
        self.size = unpacked[0] + 4
        self.packet_type = unpacked[2]
        self.model_number = unpacked[3]
        fin.seek(-8, 1)
        self.data = fin.read(self.size)

    def raw_data(self):
        return self.data

class KongsbergWaterColumnTxSector:
    def __init__(self, data):
        self.fmt = '<hHBB'
        unpacked = struct.unpack(self.fmt, data[:struct.calcsize(self.fmt)])
        self.tilt_angle = unpacked[0] * 0.01
        self.center_frequency = unpacked[1] * 10
        self.sector_number = unpacked[2]

    def calcsize(self):
        return struct.calcsize(self.fmt)

    def __str__(self):
        variables = deepcopy(vars(self))
        del variables['fmt']
        del variables['sector_number']
        return "Sector {}:\n".format(self.sector_number) + "\n".join([ "\t{}: {}".format(key, value) for key, value in variables.items()]) + "\n"

class KongsbergWaterColumnbeam:
    def __init__(self, data):
        self.header_fmt = '<hHHHBB'
        unpacked = struct.unpack(self.header_fmt, data[:struct.calcsize(self.header_fmt)])
        self.beam_angle = unpacked[0] * 0.01
        self.start_range_sample_number = unpacked[1]
        self.number_of_samples = unpacked[2]
        self.detection_range = unpacked[3]
        self.transmit_sector = unpacked[4]
        self.beam_number = unpacked[5]
        self.binary_header = data[:struct.calcsize(self.header_fmt)]
        self.samples = data[struct.calcsize(self.header_fmt) : struct.calcsize(self.header_fmt) + self.number_of_samples ]

        #index = struct.calcsize(self.header_fmt)
        # for i in range(self.number_of_samples):
        #     fmt = '<b'
        #     self.samples.append(struct.unpack(fmt, data[index:index+struct.calcsize(fmt)])[0])
        #     index += struct.calcsize(fmt)

    def calcsize(self):
        return struct.calcsize(self.header_fmt) + len(self.samples)

    def __str__(self):
        variables = deepcopy(vars(self))
        del variables['header_fmt']
        del variables['samples']
        return "\n".join([ "\t{}: {}".format(key, value) for key, value in variables.items()]) + "\n"

    def get_amplitude_samples(self):
        return self.samples;

    def get_phase_samples(self):
        return bytes()

    def get_generic_data(self):
        return self.binary_header

    def get_number_of_amplitude_samples(self):
        return len(self.samples)

class KongsbergWaterColumnPacket:
    def __init__(self, packet):
        self.header = OrderedDict()
        self.header_fmt = '<IBBHIIHHHHHHHHIhBbBBBB'
        unpacked = struct.unpack(self.header_fmt, packet.data[:struct.calcsize(self.header_fmt)])
        self.header['number of bytes in datagram'] = unpacked[0]
        self.header['STX'] = unpacked[1]
        self.header['type_of_datagram'] = unpacked[2]
        self.header['model'] = unpacked[3]
        date = unpacked[4]
        time = unpacked[5]
        self.header['ping_time'] = self._get_pingtime(date, time)
        self.header['ping_number'] = unpacked[6]
        self.header['serial_number'] = unpacked[7]
        self.header['number_of_datagrams'] = unpacked[8]
        self.header['datagram_number'] = unpacked[9]
        self.header['number of transmit sectors'] = unpacked[10]
        self.header['total number of receive beams'] = unpacked[11]
        self.header['number of beams in packet'] = unpacked[12]
        self.header['sound speed'] = unpacked[13]
        self.header['sampling frequency'] = unpacked[14]
        self.header['Tx time heave'] = unpacked[15]
        self.header['TVG X'] = unpacked[16]
        self.header['TVG C'] = unpacked[17]
        self.header['scanning info'] = unpacked[18]

        self.tx_sectors = []
        self.beams = []

        index = struct.calcsize(self.header_fmt)
        for i in range(self.header['number of transmit sectors']):
            sector = KongsbergWaterColumnTxSector(packet.data[index:])
            self.tx_sectors.append(sector)
            index += sector.calcsize()

        self.binary_header = packet.data[:index]

        for i in range(self.header['number of beams in packet']):
            beam = KongsbergWaterColumnbeam(packet.data[index:])
            self.beams.append(beam)
            index += beam.calcsize()

        self.binary_header += packet.data[index:]

    def __str__(self):
        r = ""
        for k,v in self.header.items():
            r += '{}: {}\n'.format(k, v)

        for sector in self.tx_sectors:
            r += str(sector)

        for index, beam in enumerate(self.beams):
            r += 'Beam {}:\n'.format(index + 1) + str(beam)

        return r

    def _get_pingtime(self, date, time):
        year = date // 10000
        date -= year * 10000
        month = date // 100
        date -= month * 100
        day = date
        return datetime.datetime(year, month, day) + datetime.timedelta(milliseconds=time)

    def get_amplitude_sample_format(self):
        return 0

    def get_phase_sample_format(self):
        return 0

    def get_generic_data(self):
        return self.binary_header

    def get_beams(self):
        return self.beams

    def get_ping_number(self):
        return self.header['ping_number']

    def get_ping_time(self):
        return self.header['ping_time']

class reader_kongsberg:
    def __init__(self, path : str):
        self.path = path
        self.bytesRead = 0
        self.size = os.path.getsize(path)

    def packets(self):
        try:
            while self.bytesRead < self.size:
                packet = KongsbergPacket(self.fin)
                self.bytesRead += packet.size
                yield packet
        except ValueError as e:
            logging.error(e)
            pass

    def open(self):
        self.fin = open(self.path, 'rb')

    def close(self):
        self.fin.close()


class KongsbergAllParser:
    def __init__(self):
        self.path = None
        self.parser = None
        self.wc_generator = None
        self.first_wc_packet = None

    def GetSupportedExtensions(self):
        return ['.all', '.wcd']

    def Open(self, path):
        self.path = path
        self.parser = reader_kongsberg(path)
        self.parser.open()
        self.wc_generator = (packet for packet in self.parser.packets() if packet.packet_type == 107)

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

        return ("Kongsberg", "{}".format(self.first_wc_packet.model_number))


    def _FindWcPacket(self):
        if self.wc_generator == None:
            raise ValueError

        if self.first_wc_packet == None:
            try:
                self.first_wc_packet = next(self.wc_generator)
            except StopIteration:
                logging.debug("No water column data in {}".format(self.path))
                pass

    def water_column_packets(self):
        return congregate(KongsbergWaterColumnPacket(packet) for packet in self.parser.packets() if packet.packet_type == 107)
