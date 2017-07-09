import struct
import numpy as np
import matplotlib.pyplot as plt
import datetime
import os

class File:
    def __init__(self, path):
        self.path = path
        self.fin = None

    def write(self, ping_generator):
        with open(self.path, 'wb') as f:
            for ping in ping_generator:
                p = GenericWaterColumnPing.from_ping(ping)
                bytes_written = f.write(p.serialize())

    def read(self):
        with open(self.path, 'rb') as f:
            file_size = os.path.getsize(self.path)
            while f.tell() < file_size:
                yield GenericWaterColumnPing.from_file(f)

class GenericWaterColumnBeam:
    beam_header_struct = '<IIH'

    def __init__(self, amplitude_samples, phase_samples, generic_data):
        self.amplitude_samples = amplitude_samples
        self.phase_samples = phase_samples
        self.generic_data = generic_data

    @classmethod
    def from_beam(cls, water_column_beam):
        amplitude_samples = water_column_beam.get_amplitude_samples()
        phase_samples = water_column_beam.get_phase_samples()
        generic_data = water_column_beam.get_generic_data()
        return cls(amplitude_samples, phase_samples, generic_data)

    @classmethod
    def from_file(cls, f):
        header = struct.unpack(cls.beam_header_struct, f.read(struct.calcsize(cls.beam_header_struct)))
        amplitude_sample_size = header[0]
        phase_sample_size = header[1]
        generic_data_size = header[2]
        amplitude_samples = f.read(amplitude_sample_size)
        phase_samples = f.read(phase_sample_size)
        generic_data = f.read(generic_data_size)
        return cls(amplitude_samples, phase_samples, generic_data)

    def serialize(self):
        header = struct.pack(self.beam_header_struct, len(self.amplitude_samples), len(self.phase_samples), len(self.generic_data))
        return header + self.amplitude_samples + self.phase_samples + self.generic_data

class GenericWaterColumnPing:
    header_struct = '<IIIHBBH'

    def __init__(self, ping_number, ping_time_seconds, ping_time_micro_seconds, amplitude_sample_format, phase_sample_format, generic_data, beams, file_offset=None, size=None):
        self.ping_number = ping_number
        self.ping_time_seconds = ping_time_seconds
        self.ping_time_micro_seconds = ping_time_micro_seconds
        self.amplitude_sample_format = amplitude_sample_format
        self.phase_sample_format = phase_sample_format
        self.generic_data = generic_data
        self.beams = beams
        self.file_offset = file_offset
        self.size = size

    @classmethod
    def from_ping(cls, water_column_ping):
        ping_number = water_column_ping.get_ping_number()
        seconds_since_epoch = (water_column_ping.get_ping_time() - datetime.datetime.utcfromtimestamp(0)).total_seconds()
        ping_time_seconds = int(seconds_since_epoch // 1)
        ping_time_micro_seconds = int(((seconds_since_epoch % 1) * 1E6) // 1)
        amplitude_sample_format = water_column_ping.get_amplitude_sample_format()
        phase_sample_format = water_column_ping.get_phase_sample_format()
        generic_data = water_column_ping.get_generic_data()
        beams = []
        for beam in water_column_ping.get_beams():
            beams.append(GenericWaterColumnBeam.from_beam(beam))

        return cls(ping_number, ping_time_seconds, ping_time_micro_seconds, amplitude_sample_format, phase_sample_format, generic_data, beams)

    @classmethod
    def from_file(cls, f):
        file_offset = f.tell()
        header = struct.unpack(cls.header_struct, f.read(struct.calcsize(cls.header_struct)))
        ping_number = header[0]
        ping_time_seconds = header[1]
        ping_time_micro_seconds = header[2]
        number_of_beams = header[3]
        amplitude_sample_format = header[4]
        phase_sample_format = header[5]
        generic_data_size = header[6]
        generic_data = f.read(generic_data_size)
        beams = []
        for beam in range(number_of_beams):
            beams.append(GenericWaterColumnBeam.from_file(f))

        size = f.tell() - file_offset
        return cls(ping_number, ping_time_seconds, ping_time_micro_seconds, amplitude_sample_format, phase_sample_format, generic_data, beams, file_offset, size)

    def serialize(self):
        header = struct.pack(self.header_struct, self.ping_number, self.ping_time_seconds, self.ping_time_micro_seconds, len(self.beams), self.amplitude_sample_format, self.phase_sample_format, len(self.generic_data))
        serialized = header + self.generic_data
        for beam in self.beams:
            serialized += beam.serialize()
        return serialized

    def get_sample_format_as_struct_format_specifier(self):
        if self.amplitude_sample_format == 0:
            return 'b'
        elif self.amplitude_sample_format == 1:
            return 'B'
        if self.amplitude_sample_format == 2:
            return 'h'
        elif self.amplitude_sample_format == 3:
            return 'H'
        elif self.amplitude_sample_format == 4:
            return 'i'
        elif self.amplitude_sample_format == 5:
            return 'I'
        else:
            raise ValueError("We don't support all formats yet")

    def ampltidue_array(self, decimate_factor = 1):
        number_of_samples =  lambda beam: int(len(beam.amplitude_samples) / struct.calcsize(self.get_sample_format_as_struct_format_specifier()))
        beam_samples = [struct.unpack('<{count}{format}'.format(count=number_of_samples(beam),format=self.get_sample_format_as_struct_format_specifier()), beam.amplitude_samples) for beam in self.beams]

        height = max([len(b) for b in beam_samples]) // decimate_factor + 1
        width = len(beam_samples)
        array = np.zeros((height, width))
        for i, samples in enumerate(beam_samples):
            for j, sample in enumerate(samples):
                if(j % decimate_factor != 0):
                    continue

                if self.amplitude_sample_format == 0:
                    sample += 2**8 / 2
                elif self.amplitude_sample_format == 2:
                    sample += 2**16 /2
                elif self.amplitude_sample_format == 4:
                    sample += 2**32 /2

                array[j//decimate_factor][i] = sample

        return array

    def show(self, decimate_factor = 1):
        a = self.ampltidue_array(decimate_factor)
        plt.imshow(a, cmap='gray', vmax=np.mean(a) + 2 * np.std(a), aspect='equal')
        plt.show()

def test():
    print('Test is geupdate!')
