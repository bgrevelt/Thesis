from . import blocks
import struct, os, sys

class S7kFrameReader:
    """
    Reads all data blocks from an s7k file.

    """

    def __init__(self, filename, skip_data=False):
        self.filename = filename
        self.fin = None
        self.size = None
        self.bytesRead = 0
        self.framesRead = 0
        self.recordFrame = blocks.RecordFrame(skip_data)
        self.skip_data = skip_data

    def open(self):
        try:
            self.fin = open(self.filename, 'rb')
        except IOError as e:
            print >> sys.stderr, "s7kfile.S7kFile.open(): errror: %s\n" % e
            sys.exit(1)
        self.size = os.path.getsize(self.filename)

    def close(self):
        self.fin.close()

    def __iter__(self):
        return self

    def __next__(self):
        if self.bytesRead >= os.path.getsize(self.filename):
            raise StopIteration

        frame = blocks.RecordFrame(self.skip_data)
        try:
            frame.read(self.fin)
        except IOError:
            raise StopIteration

        self.bytesRead += frame.size
        self.framesRead += 1
        return frame

    def progress(self):
        """ Returns the progress as a percentage through file """
        return float(self.bytesRead) / float(self.size) * 100.0

    def reset(self):
        self.fin.seek(0)
        self.bytesRead = 0
        self.framesRead = 0
