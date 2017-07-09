import struct
import sys
import uuid
import math
import os
import datetime
import calendar
from numpy import *


class RecordFrame:
    """
    The Data Record Frame (DRF) is the wrapper in which all records (sensor
    data or otherwise) shall be embedded. The sync pattern combined with the
    checksum should aid recovery in the event a file becomes corrupted. A
    record frame shall always start with the version and offset fields and can
    be used to dynamically determine the protocol version, if necessary.

    """

    def __init__(self, skip_data=False):
        self.fin = None
        drfHeader = "<HHIIIIHHfBBxxIIxxHxxxxHxxxxxxII"
        self.headerStruct = struct.Struct(drfHeader)
        drfCheckSum = "<I"
        self.checksumStruct = struct.Struct(drfCheckSum)
        self.binary_data = None

        # Data Record Frame Header
        self.protocalVersion = None
        self.offset = None
        self.syncPattern = None
        self.size = None
        self.optionalDataOffset = None
        self.optionalDataIdentifier = None
        self.year = None
        self.day = None
        self.second = None
        self.hour = None
        self.minute = None
        self.recordTypeIdentifier = None
        self.deviceIdentifier = None
        self.systemEnumerator = None
        self.flags = None
        self.totalRecordsInFragmentedData = None
        self.fragmentNumber = None

        # Data Record Frame Data Portion (size varies)
        self.data = None

        # Data Record Frame Checksum
        self.checksum = None

        # Book keepint
        self.skip_data = skip_data
        self.filePosition = None

    def read(self, fin):
        """ Read a Data Record Frame from fin """
        self.fin = fin
        self.filePosition = fin.tell()
        try:
            self.binary_data = fin.read(self.headerStruct.size)
            fields = self.headerStruct.unpack(self.binary_data)
        except IOError as e:
            print >> sys.stderr, "DataRecordFrame.read(): error: %s" % e
            sys.exit(1)

        if len(fields) == 17:
            self.protocalVersion = fields[0]
            self.offset = fields[1]
            self.syncPattern = fields[2]
            self.size = fields[3]
            self.optionalDataOffset = fields[4]
            self.optionalDataIdentifier = fields[5]
            self.year = fields[6]
            self.day = fields[7]
            self.second = fields[8]
            self.hour = fields[9]
            self.minute = fields[10]
            self.recordTypeIdentifier = fields[11]
            self.deviceIdentifier = fields[12]
            self.systemEnumerator = fields[13]
            self.flags = fields[14]
            self.totalRecordsInFragmentedData = fields[15]
            self.fragmentNumber = fields[16]

            # Load data
            bytesToRead = self.size - (self.headerStruct.size + self.checksumStruct.size)
            if (not self.skip_data):
                self.data = fin.read(bytesToRead)
            else:
                curpos = fin.tell()
                fin.seek(curpos + bytesToRead)
                self.data = None

            # Load the checksum
            checksum_data = fin.read(self.checksumStruct.size)
            chkField = self.checksumStruct.unpack(checksum_data)
            self.binary_data += checksum_data
            self.checksum = chkField[0]
        else:
            print >> sys.stderr, "DataRecordFrame.read(): error: read failed"
            sys.exit(1)

    def __str__(self):
        """
        Returns a string representation of a Data Record Frame object.

        """
        s = []
        s.append("%%%% DATA RECORD FRAME (size: %d, position: %d)\n" % (self.size, self.filePosition))
        s.append("ProtocalVersion: %d\n" % self.protocalVersion)
        s.append("Offset: %d\n" % self.offset)
        s.append("Sync Pattern: %d\n" % self.syncPattern)
        s.append("Size: %d\n" % self.size)
        s.append("Optional Data Offset: %d\n" % self.optionalDataOffset)
        s.append("Optional Data Identifier: %d\n" % self.optionalDataIdentifier)
        s.append("Year: %d\n" % self.year)
        s.append("Day: %d\n" % self.day)
        s.append("Second: %f\n" % self.second)
        s.append("Hour: %d\n" % self.hour)
        s.append("Minute: %d\n" % self.minute)
        s.append("Record Type Identifier: %d\n" % self.recordTypeIdentifier)
        s.append("Device Identifier: %d\n" % self.deviceIdentifier)
        s.append("System Enumerator: %d\n" % self.systemEnumerator)
        s.append("Flags: %d\n" % self.flags)
        s.append("Total Records In Fragmented Data Record Set: %d\n" % self.totalRecordsInFragmentedData)
        s.append("Fragment Number: %d\n" % self.fragmentNumber)
        s.append("DATA SECTION: %d (bytes)\n" % (self.size - (self.headerStruct.size + self.checksumStruct.size)))
        s.append("Checksum: %d\n" % self.checksum)
        s.append("--- Data Section --\n")
        s.append(str(self.record()))
        return ''.join(s)

    def record(self):
        """
        Return the record stored in this data frame.

        """
        if (not self.skip_data):
            # Data record was read into memory
            if self.recordTypeIdentifier == SevenKGenericDataRecord.RECORD_TYPE_IDENTIFIER:
                return SevenKGenericDataRecord(self.data)
            elif self.recordTypeIdentifier == VerticalDepthRecord.RECORD_TYPE_IDENTIFIER:
                return VerticalDepthRecord(self.data)
            elif self.recordTypeIdentifier == AttitudeRecord.RECORD_TYPE_IDENTIFIER:
                return AttitudeRecord(self.data)
            elif self.recordTypeIdentifier == NavigationRecord.RECORD_TYPE_IDENTIFIER:
                return NavigationRecord(self.data)
            elif self.recordTypeIdentifier == DepthRecord.RECORD_TYPE_IDENTIFIER:
                return DepthRecord(self.data)
            elif self.recordTypeIdentifier == SnippetsDataRecord.RECORD_TYPE_IDENTIFIER:
                return SnippetsDataRecord(self.data)
            elif self.recordTypeIdentifier == BeamformedDataRecord.RECORD_TYPE_IDENTIFIER:
                return BeamformedDataRecord(self.data)
            elif self.recordTypeIdentifier == SevenKBackscatterImageryRecord.RECORD_TYPE_IDENTIFIER:
                return SevenKBackscatterImageryRecord(self.data)
            elif self.recordTypeIdentifier == RawBathymetryRecord.RECORD_TYPE_IDENTIFIER:
                return RawBathymetryRecord(self.data)
            elif self.recordTypeIdentifier == SevenKBathymetricDataRecord.RECORD_TYPE_IDENTIFIER:
                return SevenKBathymetricDataRecord(self.data)
            elif self.recordTypeIdentifier == SevenKBeamGeometryRecord.RECORD_TYPE_IDENTIFIER:
                return SevenKBeamGeometryRecord(self.data)
            elif self.recordTypeIdentifier == SevenKSonarSettingsRecord.RECORD_TYPE_IDENTIFIER:
                return SevenKSonarSettingsRecord(self.data)
            elif self.recordTypeIdentifier == HeadingRecord.RECORD_TYPE_IDENTIFIER:
                return HeadingRecord(self.data)
            elif self.recordTypeIdentifier == RollPitchHeaveRecord.RECORD_TYPE_IDENTIFIER:
                return RollPitchHeaveRecord(self.data)
            elif self.recordTypeIdentifier == PositionRecord.RECORD_TYPE_IDENTIFIER:
                return PositionRecord(self.data)
            elif self.recordTypeIdentifier == FileHeaderRecord.RECORD_TYPE_IDENTIFIER:
                return FileHeaderRecord(self.data)
            elif self.recordTypeIdentifier == SevenKConfigurationRecord.RECORD_TYPE_IDENTIFIER:
                return SevenKConfigurationRecord(self.data)
            elif self.recordTypeIdentifier == SevenKCenterVersionRecord.RECORD_TYPE_IDENTIFIER:
                return SevenKCenterVersionRecord(self.data)
            elif self.recordTypeIdentifier == CTDRecord.RECORD_TYPE_IDENTIFIER:
                return CTDRecord(self.data)
            elif self.recordTypeIdentifier == SonarInstallationParametersRecord.RECORD_TYPE_IDENTIFIER:
                return SonarInstallationParametersRecord(self.data)
            else:
                return UnknownRecord(self.data)
        else:
            # Data record skipped
            return SkippedDataRecord(self.recordTypeIdentifier, self.size)

    def timeStamp(self):
        """ Returns the Unix timestamp of this frame """
        tstr = "%d-%d %d:%d:%d" % (self.year, self.day, self.hour, self.minute, int(self.second))
        dt = datetime.datetime.strptime(tstr, "%Y-%j %H:%M:%S")
        ts = calendar.timegm(dt.timetuple()) + (self.second - int(self.second))
        return ts

    def raw_data(self):
        self.fin.seek(self.filePosition)
        return self.fin.read(self.size)






class Record:
    """
    A Generic Record Type containing data for a specific sensor

    """
    def __init__(self, data):
        self.recordTypeIdentifier = None
        self.data = data

    def __str__(self):
        return "Generic Record (%d bytes)\n" % len(self.data)

class SkippedDataRecord:
    """
    A empty placeholder for data records that have been skipped over for
    efficient reading.

    """
    def __init__(self, dataTypeIdentifier, bytes):
        self.name = "%s [%d bytes]" % (self.getName(dataTypeIdentifier), bytes)
        self.size = bytes

    def __str__(self):
        return "%s (%d bytes)\n" % (self.name, self.size)

    def getName(self, recordTypeIdentifier):
        if recordTypeIdentifier == SevenKGenericDataRecord.RECORD_TYPE_IDENTIFIER:
            return SevenKGenericDataRecord.NAME
        elif recordTypeIdentifier == VerticalDepthRecord.RECORD_TYPE_IDENTIFIER:
            return VerticalDepthRecord.NAME
        elif recordTypeIdentifier == AttitudeRecord.RECORD_TYPE_IDENTIFIER:
            return AttitudeRecord.NAME
        elif recordTypeIdentifier == NavigationRecord.RECORD_TYPE_IDENTIFIER:
            return NavigationRecord.NAME
        elif recordTypeIdentifier == DepthRecord.RECORD_TYPE_IDENTIFIER:
            return DepthRecord.NAME
        elif recordTypeIdentifier == SnippetsDataRecord.RECORD_TYPE_IDENTIFIER:
            return SnippetsDataRecord.NAME
        elif recordTypeIdentifier == BeamformedDataRecord.RECORD_TYPE_IDENTIFIER:
            return BeamformedDataRecord.NAME
        elif recordTypeIdentifier == SevenKBackscatterImageryRecord.RECORD_TYPE_IDENTIFIER:
            return SevenKBackscatterImageryRecord.NAME
        elif recordTypeIdentifier == RawBathymetryRecord.RECORD_TYPE_IDENTIFIER:
            return RawBathymetryRecord.NAME
        elif recordTypeIdentifier == SevenKBathymetricDataRecord.RECORD_TYPE_IDENTIFIER:
            return SevenKBathymetricDataRecord.NAME
        elif recordTypeIdentifier == SevenKBeamGeometryRecord.RECORD_TYPE_IDENTIFIER:
            return SevenKBeamGeometryRecord.NAME
        elif recordTypeIdentifier == SevenKSonarSettingsRecord.RECORD_TYPE_IDENTIFIER:
            return SevenKSonarSettingsRecord.NAME
        elif recordTypeIdentifier == HeadingRecord.RECORD_TYPE_IDENTIFIER:
            return HeadingRecord.NAME
        elif recordTypeIdentifier == RollPitchHeaveRecord.RECORD_TYPE_IDENTIFIER:
            return RollPitchHeaveRecord.NAME
        elif recordTypeIdentifier == PositionRecord.RECORD_TYPE_IDENTIFIER:
            return PositionRecord.NAME
        elif recordTypeIdentifier == FileHeaderRecord.RECORD_TYPE_IDENTIFIER:
            return FileHeaderRecord.NAME
        elif recordTypeIdentifier == SevenKConfigurationRecord.RECORD_TYPE_IDENTIFIER:
            return SevenKConfigurationRecord.NAME
        elif recordTypeIdentifier == SevenKCenterVersionRecord.RECORD_TYPE_IDENTIFIER:
            return SevenKCenterVersionRecord.NAME
        elif recordTypeIdentifier == CTDRecord.RECORD_TYPE_IDENTIFIER:
            return CTDRecord.NAME
        elif recordTypeIdentifier == SonarInstallationParametersRecord.RECORD_TYPE_IDENTIFIER:
            return SonarInstallationParametersRecord.NAME
        else:
            return UnknownRecord.NAME

class UnknownRecord(Record):
    """
    A unknown or undisclosed record type

    """
    NAME = "Unknown Record Type"

    def __init__(self, data):
        self.recordTypeIdentifier = None
        self.name = "Unknown Record Type [%d bytes]" % len(data)
        self.data = data

    def __str__(self):
        return "(%s)\n" % len(self.data)


class PositionRecord(Record):
    """
    Position Record used in conjuction with Record Type 1011.

    """
    RECORD_TYPE_IDENTIFIER = 1003
    NAME = "Position Record"

    POSITION_TYPE_GEOGRAPHICAL = 0
    POSITION_TYPE_GRID = 1

    def __init__(self, data):
        fmt = "<IfdddBBBB"
        fields = struct.unpack(fmt, data)
        self.name = self.NAME
        self.datumId = fields[0]
        self.latency = fields[1]
        self.northing = fields[2]
        self.easting = fields[3]
        self.height = fields[4]
        self.positionFlag = fields[5]
        self.utmZone = fields[6]
        self.qualityFlag = fields[7]
        self.positioningMethod = fields[8]

    def __str__(self):
        s = []
        s.append("(%s)\n" % self.name)
        s.append("Datum Identifier: %d\n" % self.datumId)
        s.append("Latency: %f\n" % self.latency)
        if self.positionFlag == self.POSITION_TYPE_GEOGRAPHICAL:
            s.append("Latitude (deg): %f\n" % math.degrees(self.northing))
            s.append("Longitude (deg): %f\n" % math.degrees(self.easting))
        else:
            s.append("Northing (m): %f\n" % self.northing)
            s.append("Easting (m): %f\n" % self.easting)
        s.append("Height relative to Datum or Height (m): %f\n" % self.height)
        s.append("Position type flag: %d\n" % self.positionFlag)
        s.append("UTM Zone: %d\n" % self.utmZone)
        s.append("Quality Flag: %d\n" % self.qualityFlag)
        return ''.join(s)


class DepthRecord(Record):
    """
    Depth data record.

    """
    RECORD_TYPE_IDENTIFIER = 1008
    NAME = "Depth Record"

    def __init__(self, data):
        fmt="<BBxxf"
        fields = struct.unpack(fmt, data)
        self.name = self.NAME
        self.depthDescripter = fields[0]
        self.correctionFlag = fields[1]
        self.depth = fields[2]

    def __str__(self):
        s = []
        s.append("(%s)\n" % self.name)
        s.append("Depth Descriptor: %d\n" % self.depthDescripter)
        s.append("Correction Flag: %d\n" % self.correctionFlag)
        s.append("Depth: %f\n" % self.depth)
        return ''.join(s)


class CTDRecord(Record):
    """
    CTD Data Record.

    """
    RECORD_TYPE_IDENTIFIER = 1010
    NAME = "CTD Data Record"

    CONDUCTIVITY_COL = 0
    TEMPERATURE_COL = 1
    PRESSURE_COL = 2
    VELOCITY_COL = 3
    ABSORPTION_COL = 4

    def __init__(self, data):
        headerFormat = "<fBBBBBBxxddfI"
        fields = struct.unpack(headerFormat, data[0:36])
        self.name = self.NAME
        self.frequency = fields[0]
        self.soundVelocitySource = fields[1]
        self.soundVelocityAlgorithm = fields[2]
        self.conductivityFlag = fields[3]
        self.pressureFlag = fields[4]
        self.positionFlag = fields[5]
        self.sampleContentValidity = fields[6]
        self.latitude = fields[7]
        self.longitude = fields[8]
        self.sampleRate = fields[9]
        self.numberOfSamples = fields[10]

        self.data = []
        sampleFormat = "<fffff"
        sampleStruct = struct.Struct(sampleFormat)
        offset = 36
        for i in range(self.numberOfSamples):
            start = offset
            end = start + sampleStruct.size
            self.data.append(sampleStruct.unpack(data[start:end]))
            offset += sampleStruct.size

    def __str__(self):
        s = []
        s.append("(%s)\n" % self.name)
        s.append("Frequency: %f\n" % self.frequency)
        s.append("Sound Velocity Source Flag: %d\n" % self.soundVelocitySource)
        s.append("Sound Velocity Algorithm: %d\n" % self.soundVelocityAlgorithm)
        s.append("Conductivity Flag: %d\n" % self.conductivityFlag)
        s.append("Pressure Flag: %d\n" % self.pressureFlag)
        s.append("Position Flag: %d\n" % self.positionFlag)
        s.append("Sample Content Validity: %d\n" % self.sampleContentValidity)
        s.append("Latitude: %f\n" % self.latitude)
        s.append("Longitude: %f\n" % self.longitude)
        s.append("Sample Rate: %f\n" % self.sampleRate)
        s.append("Number Of Samples: %d\n" % self.numberOfSamples)
        s.append("Salinity\tTemperature\tDepth\tVelocity\tAbsorption\n")

        for sample in self.data:
            s.append("%f\t%f\t%f\t%f\t%f\n" % sample)
        return ''.join(s)

class RollPitchHeaveRecord(Record):
    """
    Motion data record

    """
    RECORD_TYPE_IDENTIFIER = 1012
    NAME = "Roll Pitch Heave Record"

    def __init__(self, data):
        fmt = "<fff"
        self.name = self.NAME
        (self.roll, self.pitch, self.heave) = struct.unpack(fmt, data)

    def __str__(self):
        s = []
        s.append("(%s)\n" % self.name)
        s.append("Roll: %f\n" % self.roll)
        s.append("Pitch: %f\n" % self.pitch)
        s.append("Heave: %f\n" % self.heave)
        return ''.join(s)

class HeadingRecord(Record):
    """
    Vessel heading record.

    """
    RECORD_TYPE_IDENTIFIER = 1013
    NAME = "Heading Record"

    def __init__(self, data):
        self.name = self.NAME
        self.heading = struct.unpack("<f", data)[0]

    def __str__(self):
        s = []
        s.append("(%s)\n" % self.name)
        s.append("Heading (deg): %f\n" % math.degrees(self.heading))
        return ''.join(s)

class NavigationRecord(Record):
    """
    This record is output at the input navigation rate.

    """

    RECORD_TYPE_IDENTIFIER = 1015
    NAME = "Navigation Record"

    def __init__(self, data):
        fmt = "<Bddffffff"
        self.name = self.NAME
        fields = struct.unpack(fmt, data)
        self.verticalReference = fields[0]
        self.latitude = fields[1]
        self.longitude = fields[2]
        self.horizontalPositionAccuracy = fields[3]
        self.vesselHeight = fields[4]
        self.heightAccuracy = fields[5]
        self.speedOverGround = fields[6]
        self.courseOverGround = fields[7]
        self.heading = fields[8]

    def __str__(self):
        s = []
        s.append("(%s)\n" % self.name)
        s.append("Vertical Reference: %d\n" % self.verticalReference)
        s.append("Latitude (deg): %f\n" % math.degrees(self.latitude))
        s.append("Longitude (deg): %f\n" % math.degrees(self.longitude))
        s.append("Horizontal Position Accuracy (m): %f\n" % self.horizontalPositionAccuracy)
        s.append("Vessel Height (m): %f\n" % self.vesselHeight)
        s.append("Height Accuracy (m): %f\n" % self.heightAccuracy)
        s.append("Speed Over Ground (m/s): %f\n" % self.speedOverGround)
        s.append("Course Over Ground (deg): %f\n" % math.degrees(self.courseOverGround))
        s.append("Heading (deg): %f\n" % math.degrees(self.heading))
        return ''.join(s)

class AttitudeRecord(Record):
    """
    This record will be output at the input motion sensor rate.

    """

    RECORD_TYPE_IDENTIFIER = 1016
    NAME = "Attitude Record"

    def __init__(self, data):
        self.name = self.NAME
        self.numberOfAttitudeDataSets = struct.unpack("<B", data[0])[0]
        self.attitudeDataSets = self.getAttitudeDataSets(self.numberOfAttitudeDataSets, data[1:])

    def getAttitudeDataSets(self, numberOfAttitudeDataSets, data):

        dataSetStruct = struct.Struct("<Hffff")
        dataSets = []
        start = 0
        for i in xrange(self.numberOfAttitudeDataSets):
            end = start + dataSetStruct.size
            (delT, roll, pitch, heave, heading) = dataSetStruct.unpack(data[start:end])
            dataSets.append((delT, roll, pitch, heave, heading))
            start = end
        return dataSets

    def __str__(self):
        s = []
        s.append("(%s)\n" % self.name)
        s.append("Number of Attitude Data Sets: %d\n" % self.numberOfAttitudeDataSets)

        for i in xrange(self.numberOfAttitudeDataSets):
            (delt, roll, pitch, heave, heading) = self.attitudeDataSets[i]
            s.append("-" * 20 + "\n")
            s.append("Time Difference From Record Timestamp 0 (s): %d\n" % delt)
            s.append("Roll (deg): %f\n" % math.degrees(roll))
            s.append("Pitch (deg): %f\n" % math.degrees(pitch))
            s.append("Heave (deg): %f\n" % math.degrees(heave))
            s.append("Heading (deg): %f\n" % math.degrees(heading))
        return "".join(s)

class SevenKSonarSettingsRecord(Record):
    """
    This record is produced by the SeaBat 7k sonar 7-P processor series. It
    contains the current sonar settings. The 7-P processor updates this record
    for each ping. This record is available by subscription only.

    """

    RECORD_TYPE_IDENTIFIER = 7000
    NAME = "7K Sonar Settings Record"

    def __init__(self, data):
        fmt = "<QIHffffIIfxxxxfffffIIfffffIfIIIfIffffffffxx"
        fields = struct.unpack(fmt, data)
        self.name = self.NAME
        self.sonarId = fields[0]
        self.pingNumber = fields[1]
        self.multiPingSequence = fields[2]
        self.frequency = fields[3]
        self.sampleRate = fields[4]
        self.receiverBandwidth = fields[5]
        self.txPulseWidth = fields[6]
        self.txPulseTypeId = fields[7]
        self.txPulseEnvelopeId = fields[8]
        self.txPulseEnvelopeParameter = fields[9]
        self.maxPingRate = fields[10]
        self.pingPeriod = fields[11]
        self.rangeSelection = fields[12]
        self.powerSelection = fields[13]
        self.gainSelection = fields[14]
        self.controlFlags = fields[15]
        self.projectorId = fields[16]
        self.projectorBeamSteeringAngleVertical = fields[17]
        self.projectorBeamSteeringAngleHorizontal = fields[18]
        self.projectorBeam3dbBeamWidthVertical = fields[19]
        self.projectorBeam3dbBeamWidthHorizontal = fields[20]
        self.projectorBeamFocalPoint = fields[21]
        self.projectorBeamWeightingWindowType = fields[22]
        self.projectorBeamWeightingWindowParameter = fields[23]
        self.transmitFlags = fields[24]
        self.hydrophoneId = fields[25]
        self.receiveBeamWeightingWindow = fields[26]
        self.receiveBeamWeightingParameter = fields[27]
        self.receiveFlags = fields[28]
        self.receiveBeamWidth = fields[29]
        self.bottomDetectionFilterMinRange = fields[30]
        self.bottomDetectionFilterMaxRange = fields[31]
        self.bottomDetectionFilterMinDepth = fields[32]
        self.bottomDetectionFilterMaxDepth = fields[33]
        self.absorption = fields[34]
        self.soundVelocity = fields[35]
        self.spreading = fields[36]

    def __str__(self):
        s = []
        s.append("(%s)\n" % self.name)
        s.append("Sonar Id: %d\n" % self.sonarId)
        s.append("Ping Number: %d\n" % self.pingNumber)
        s.append("Multi-Ping Sequence: %d\n" % self.multiPingSequence)
        s.append("Frequency: %f (hertz)\n" % self.frequency)
        s.append("Sample Rate: %f (hertz)\n" % self.sampleRate)
        s.append("Receiver Bandwidth: %f (hertz)\n" % self.receiverBandwidth )
        s.append("Tx Pulse Width: %f (seconds)\n" % self.txPulseWidth)
        s.append("Tx Pulse Type Id: %d\n" % self.txPulseTypeId)
        s.append("Tx Pulse Envelope Id: %d\n" % self.txPulseEnvelopeId)
        s.append("Tx Pulse Envelope Parameter: %f\n" % self.txPulseEnvelopeParameter)
        s.append("Max Ping Rate: %f (pings/s)\n" % self.maxPingRate)
        s.append("Ping Period: %f (seconds since last ping)\n" % self.pingPeriod)
        s.append("Range Selection: %f (m)\n" % self.rangeSelection)
        s.append("Power Selection: %f (dB re 1 uPa)\n" % self.powerSelection)
        s.append("Gain Selection: %f (dB)\n" % self.gainSelection)
        s.append("Control Flags: %d\n" % self.controlFlags)
        s.append("Projector Id: %d\n" % self.projectorId)
        s.append("Projector Beam Steering Angle Vertical: %f (rad)\n" % self.projectorBeamSteeringAngleVertical)
        s.append("Projector Beam Steering Angle Horizontal: %f (rad)\n" % self.projectorBeamSteeringAngleHorizontal)
        s.append("Projector -3dB Beam Width Vertical: %f (rad)\n" % self.projectorBeam3dbBeamWidthVertical)
        s.append("Projector -3dB Beam Width Horizontal: %f (rad)\n" % self.projectorBeam3dbBeamWidthHorizontal)
        s.append("Projector Beam Focal Point: %f (m)\n" % self.projectorBeamFocalPoint)
        s.append("Projector Beam Weighting Window Parameter: %f\n" % self.projectorBeamWeightingWindowParameter)
        s.append("Transmit Flags: %d\n" % self.transmitFlags)
        s.append("Hydrophone Id: %d\n" % self.hydrophoneId)
        s.append("Receive Beam Weighting Window: %d\n" % self.receiveBeamWeightingWindow)
        s.append("Receive Beam Weighting Parameter: %d\n" % self.receiveBeamWeightingParameter)
        s.append("Receive Flags: %d\n" % self.receiveFlags)
        s.append("Receive Beam Width: %f (rad)\n" % self.receiveBeamWidth)
        s.append("Bottom Detection Filter Min Range: %f\n" % self.bottomDetectionFilterMinRange)
        s.append("Bottom Detection Filter Max Range: %f\n" % self.bottomDetectionFilterMaxRange)
        s.append("Bottom Detection Filter Min Depth: %f\n" % self.bottomDetectionFilterMinDepth)
        s.append("Bottom Detection Filter Max Depth: %f\n" % self.bottomDetectionFilterMaxDepth)
        s.append("Absorption: %f (dB/km)\n" % self.absorption)
        s.append("Sound Velocity: %f (m/s)\n" % self.soundVelocity)
        s.append("Spreading Loss: %f (dB)\n" % self.spreading)
        return ''.join(s)


class SevenKConfigurationRecord(Record):
    """
    This record is produced by the SeaBat 7k sonar 7-P processor series. It
    contains the configuration information about the sonar capabilities. Each
    sonar's configuration can be found in the record's Module info section
    (see Table 34). The record is created on system startup and does not change
    during operation. The record can be manually requested from the 7-P processor.
    This record is not available for subscription. For details about requesting
    records see record 7500 together with Appendix A of the file format
    description document.

    The dynamic data section for each device is encoded using XML. A sample is
    provided below.

    """

    RECORD_TYPE_IDENTIFIER = 7001
    NAME = "7K Configuration Record"

    def __init__(self, data):
        self.name = self.NAME
        self.sonarId = struct.unpack('<Q', data[0:8])
        self.numberOfDevices = struct.unpack('<I', data[8:12])[0]
        self.deviceInfo = []
        start = 12
        for i in range(self.numberOfDevices):
            (end, deviceInfo) = self.readDeviceInfo(start, data)
            self.deviceInfo.append(deviceInfo)
            start = end

    def readDeviceInfo(self, start, data):
        fmt = "<I64sQI"
        end = start + struct.calcsize(fmt)
        fields = struct.unpack(fmt, data[start:end])

        deviceId = fields[0]
        deviceDescription = fields[1]
        deviceSerialNumber = fields[2]
        deviceInfoLength = fields[3]

        start = end
        end = start + deviceInfoLength
        deviceInfo = struct.unpack('<%ds' % deviceInfoLength, data[start:end])
        return(end, (deviceId, deviceDescription.split('\00')[0], deviceSerialNumber, deviceInfoLength, deviceInfo))

    def __str__(self):
        s = []
        s.append("(%s)\n" % self.name)
        s.append("Sonar ID: %d\n" % self.sonarId)
        s.append("Number of devices/sonars: %d\n" % self.numberOfDevices)

        for device in self.deviceInfo:
            s.append(" :: Device ID: %d\n" % device[0])
            s.append(" :: Device Description: %s\n" % device[1])
            s.append(" :: Device Serial Number: %d\n" % device[2])
            s.append(" :: Device Info Length: %d\n" % device[3])
            s.append(" :: Device Info:\n")
            s.append("%s\n" % device[4])
            s.append("")
        return ''.join(s)

class SevenKBeamGeometryRecord(Record):
    """
    This record is produced by the 7kCenter. It contains the receive beam
    widths and steering. The 7kCenter updates this record when any of the
    values have changed. This record is available by subscription only.

    """

    RECORD_TYPE_IDENTIFIER = 7004
    NAME = "7K Beam Geometry Record"

    def __init__(self, data):
        self.name = self.NAME
        fmt = "<QI"
        fields = struct.unpack(fmt, data[0:12])
        self.sonarId = fields[0]
        self.numberOfReceiverBeams = fields[1]
        start = 12
        end = start + (self.numberOfReceiverBeams * struct.calcsize('f'))
        self.beamVerticalDirectionAngle = array(struct.unpack('<%df' % self.numberOfReceiverBeams, data[start:end]))
        start = end
        end = start + (self.numberOfReceiverBeams * struct.calcsize('f'))
        self.beamHorizontalDirectionAngle = array(struct.unpack('<%df' % self.numberOfReceiverBeams, data[start:end]))
        start = end
        end = start + (self.numberOfReceiverBeams * struct.calcsize('f'))
        self.beamWidthY = array(struct.unpack('<%df' % self.numberOfReceiverBeams, data[start:end]))
        start = end
        end = start + (self.numberOfReceiverBeams * struct.calcsize('f'))
        self.beamWidthX = array(struct.unpack('<%df' % self.numberOfReceiverBeams, data[start:end]))

    def __str__(self):
        s = []
        s.append("(%s)\n" % self.name)
        s.append("Sonar Serial Number: %d\n" % self.sonarId)
        s.append("Number of receiver beams: %d\n" % self.numberOfReceiverBeams)
        s.append("Beam Angles (radians)\n")
        s.append("Vertical\tHorizontal\tWidthY\tWidthX\n")
        for i in range(self.numberOfReceiverBeams):
            s.append("%f\t%f\t%f\t%f\n" % (self.beamVerticalDirectionAngle[i],
                                           self.beamHorizontalDirectionAngle[i],
                                           self.beamWidthY[i], self.beamWidthX[i]))
        return ''.join(s)


class SevenKBathymetricDataRecord(Record):
    """
    This record is produced by the 7kCenter series. It contains the sonar bottom
    detection results. This record is typically not available in a forward looking
    sonar configuration. The 7kCenter updates this data for each ping. This record
    is available by subscription only.

    """

    RECORD_TYPE_IDENTIFIER = 7006
    NAME = "7K Bathymetric Data"

    def __init__(self, data):
        self.name = self.NAME
        fmt = "<QIHIBBf"
        fields = struct.unpack(fmt, data[0:24])
        self.sonarId = fields[0]
        self.pingNumber = fields[1]
        self.multiPingSequence = fields[2]
        self.numberOfReceiveBeams = fields[3]
        self.layerCompensationFlag = fields[4]
        self.soundVelocityFlag = fields[5]
        self.soundVelocity = fields[6]

        start = 24
        end = start + (struct.calcsize('<f') * self.numberOfReceiveBeams)
        self.range = struct.unpack("<%df" % self.numberOfReceiveBeams, data[start:end])

        start = end
        end = start + (struct.calcsize('<B') * self.numberOfReceiveBeams)
        self.quality = struct.unpack("<%dB" % self.numberOfReceiveBeams, data[start:end])

        start = end
        end = start + (struct.calcsize('<f') * self.numberOfReceiveBeams)
        self.intensity = struct.unpack("<%df" % self.numberOfReceiveBeams, data[start:end])

        start = end
        end = start + (struct.calcsize('<f') * self.numberOfReceiveBeams)
        self.minFilterInfo = struct.unpack("<%df" % self.numberOfReceiveBeams, data[start:end])

        start = end
        end = start + (struct.calcsize('<f') * self.numberOfReceiveBeams)
        self.maxFilterInfo = struct.unpack("<%df" % self.numberOfReceiveBeams, data[start:end])

    def __str__(self):
        s = []
        s.append("(%s)\n" % self.name)
        s.append("Sonar Id: %d\n" % self.sonarId)
        s.append("Ping Number: %d\n" % self.pingNumber)
        s.append("Multi-Ping Sequence: %d\n" % self.multiPingSequence)
        s.append("Number of Receiver Beams: %d\n" % self.numberOfReceiveBeams)
        s.append("Layer Compensation Flag: %d\n" % self.layerCompensationFlag)
        s.append("Sound Velocity Flag: %d\n" % self.soundVelocityFlag)
        s.append("Sound Velocity: %f (m/s)\n" % self.soundVelocity)
        s.append("2-Way Time (s)\tQaulity\tIntensity (dB re 1 uPa)\tMin Filter\tMax Filter\n")
        for i in range(self.numberOfReceiveBeams):
            s.append("%f\t%d\t%f\t%f\t%f\n" %
                     (self.range[i], self.quality[i], self.intensity[i], self.minFilterInfo[i], self.maxFilterInfo[i]))
        return ''.join(s)


class SevenKBackscatterImageryRecord(Record):
    """
    This record is produced by the 7kCenter. It contains the side scan sonar data.
    This record is typically not available in a forward looking sonar
    configuration. The 7kCenter updates this data for each ping. This record is
    available by subscription only.

    """
    RECORD_TYPE_IDENTIFIER = 7007
    NAME = "7K Backscatter Record"

    def __init__(self, data):
        self.name = self.NAME
        fmt = "<QIHfIIffffffffHHBB"
        start = 0
        end = start + struct.calcsize(fmt)
        fields = struct.unpack(fmt, data[start:end])
        self.sonarId = fields[0]
        self.pingNumber = fields[1]
        self.multiPingSequence = fields[2]
        self.beamPosition = fields[3]
        self.controlFlags = fields[4]
        self.samplesPerSide = fields[5]
        self.port3dbBeamWidthY = fields[6]
        self.port3dbBeamWidthZ = fields[7]
        self.starboard3dbBeamWidthY = fields[8]
        self.starboard3dbBeamWidthZ = fields[9]
        self.portBeamSteeringAngleY = fields[10]
        self.portBeamSteeringAngleZ = fields[11]
        self.starboardBeamSteeringAngleY = fields[12]
        self.starboardBeamSteeringAngleZ = fields[13]
        self.numberOfBeamsPerSide = fields[14]
        self.currentBeamNumber = fields[15]
        self.numberOfBytesPerSample = fields[16]
        self.dataTypes = fields[17]
        self.portSamples = []
        self.starboardSamples = []

        if self.numberOfBytesPerSample == 2:
            start = 17
            end = start + (2 * self.samplesPerSide)
            self.portSamples = struct.unpack('<%dH' % self.samplesPerSide, data[start:end])
            start = end
            end = start + (2 * self.samplesPerSide)
            self.starboardSamples = struct.unpack('<%dH' % self.samplesPerSide, data[start:end])
        elif self.numberOfBytesPerSample == 4:
            start = 17
            end = start + (4 * self.samplesPerSide)
            self.portSamples = struct.unpack('<%dI' % self.samplesPerSide, data[start:end])
            start = end
            end = start + (4 * self.samplesPerSide)
            self.starboardSamples = struct.unpack('<%dI' % self.samplesPerSide, data[start:end])


    def __str__(self):
        s = []
        s.append("(%s)\n" % self.name)
        s.append("Sonar Id: %d\n" % self.sonarId)
        s.append("Ping Number: %d\n" % self.pingNumber)
        s.append("Beam Position: %f\n" % self.beamPosition)
        s.append("Control Flags: %d\n" % self.controlFlags)
        s.append("Samples Per Side: %d\n" % self.samplesPerSide)
        s.append("Port -3dB Beam Width Y: %f (rad)\n" % self.port3dbBeamWidthY)
        s.append("Port -3dB Beam Width Z: %f (rad)\n" % self.port3dbBeamWidthZ)
        s.append("Starboard -3dB Beam Width Y: %f (rad)\n" % self.starboard3dbBeamWidthY)
        s.append("Starboard -3dB Beam Width Z: %f (rad)\n" % self.starboard3dbBeamWidthZ)
        s.append("Port Beam Steering Angle Y: %f (rad)\n" % self.portBeamSteeringAngleY)
        s.append("Port Beam Steering Angle Z: %f (rad)\n" % self.portBeamSteeringAngleZ)
        s.append("Starboard Beam Steering Angle Y: %f (rad)\n" % self.starboardBeamSteeringAngleY)
        s.append("Starboard Beam Steering Angle Z: %f (rad)\n" % self.starboardBeamSteeringAngleZ)
        s.append("Number of Beams Per Side: %d\n" % self.numberOfBeamsPerSide)
        s.append("Current Beam Number: %d\n" % self.currentBeamNumber)
        s.append("Number of Bytes Per Sample: %d\n" % self.numberOfBytesPerSample)
        s.append("Data Types: %d\n" % self.dataTypes)
        s.append("Port\tStarboard\n")
        for i in range(self.samplesPerSide):
            s.append("%d\t%d\n" % (self.portSamples[i], self.starboardSamples[i]))
        return ''.join(s)

class SevenKGenericWaterColumnDataBeam:
    def __init__(self,data):
        fmt = '<HII'
        self.size = struct.calcsize(fmt)
        self.data = data[:self.size]
        fields = struct.unpack(fmt, self.data)
        self.descriptor = fields[0]
        self.first_sample = fields[1]
        self.last_sample = fields[2]
        self.amplitude = bytes()
        self.phase = bytes()

class SevenKGenericWaterColumnDataBeam2:
    def __init__(self, descriptor, first_sample, last_sample):
        self.descriptor = descriptor
        self.first_sample = first_sample
        self.last_sample = last_sample
        self.amplitude = bytes()
        self.phase = bytes()

class SevenKGenericDataRecord(Record):
    """
    Description: This record is produced by the 7kCenter. It contains the sonar
    beam "I" and "Q" or magnitude and phase data. The 7kCenter transmits
    this data for each ping. This record is available by subscription only. This
    record is used for snippet output as well. Beams and samples are numbered from
    0. First beam to last beam fields are always enumerated from low to high
    numbers.

    The Record Data portion is divided into two distinct parts:

    1. Beam Descriptors
    2. Sample Data

    Beam Descriptors:

    This part of the Record Data section contains each beam descriptor, followed
    by the beginning and ending sample numbers for that beam. For example: b0 s1
    s100 b2 s1 s100 b3 s1 s100

    where b = Beam, s = sample

    Sample Data

    After all of the beams and their corresponding samples have been listed, the
    sample data will be output. Sample data will be output in one of two ways:

    1. All samples for a beam followed by all samples for the next beam (Row
    Column Flag = 0)

    2. First sample for each beam followed by next sample for each beam (Row
    Column Flag = 1).

    """

    RECORD_TYPE_IDENTIFIER = 7008
    NAME = "7k Generic Data Record"

    def __init__(self, data):
        self.name = self.NAME
        fmt = '<QIHHHIBBHI'
        fields = struct.unpack(fmt, data[:struct.calcsize(fmt)])
        self.header_data = data[:struct.calcsize(fmt)]
        self.sonarID = fields[0]
        self.pingNumber = fields[1]
        self.multiPingSequence = fields[2]
        self.numberOfBeams = fields[3]
        self.numberOfSamplesInPing = fields[5]
        self.recordSubsetFlag = fields[6]
        self.rowColumnFlag = fields[7]
        self.dataSampleType = fields[9]
        self.data = data
        self.beams = []
        self.phase_format = 'H' # hard coded for now need to support other formats in the future
        self.amplitude_format = 'H' # hard coded for now need to support other formats in the future

        beams_fmt = '<' + 'HII' * self.numberOfBeams

        beam_offset = struct.calcsize(fmt)
        for i in range(self.numberOfBeams):
            beam = SevenKGenericWaterColumnDataBeam(self.data[beam_offset:])
            self.beams.append(beam)
            beam_offset += beam.size

        # this way is way faster
        # beam_fields = struct.unpack(beams_fmt, data[struct.calcsize(fmt): struct.calcsize(fmt)+struct.calcsize(beams_fmt)] )
        # for i in range(self.numberOfBeams):
        #     field_index = i *3
        #     descriptor = beam_fields[field_index]
        #     first_sample = beam_fields[field_index+1]
        #     last_sample = beam_fields[field_index+2]
        #     beam = SevenKGenericWaterColumnDataBeam2(descriptor, first_sample, last_sample )
        #     self.beams.append(beam)

        #
        sample_data_offset = struct.calcsize(fmt)+struct.calcsize(beams_fmt)
        sample_data_size = (struct.calcsize(self.amplitude_format) + struct.calcsize(self.phase_format)) * self.numberOfBeams * self.numberOfSamplesInPing
        self.sample_data = self.data[ sample_data_offset: sample_data_offset + sample_data_size]
        additional_data = self.data[sample_data_offset + sample_data_size:]
        self.header_data += bytes(additional_data)

        if(len(additional_data) > 0):
            print('Got {} bytes of additional data'.format(len(additional_data)))



        if self.dataSampleType == 0x22:
            self.parse_beams()

    def parse_beams(self):
        magnitude_sample_type = self.dataSampleType & 0xf
        phase_sample_type = (self.dataSampleType & 0xf0) >> 4

        assert magnitude_sample_type == 2, "Sorry, only 16 bit amplitude samples supported for now"
        assert phase_sample_type == 2, "Sorry, only 16 bit phase samples supported for now"
        assert self.dataSampleType & 0xff00 == 0, 'I don\'t know how to process this scientific data'



        for beam_index, beam in enumerate(self.beams):
            number_of_samples = beam.last_sample - beam.first_sample + 1
            assert number_of_samples == self.numberOfSamplesInPing, "If these two are not equal, I'm not sure this will work"
            for sample_index in range(number_of_samples):
                beam.amplitude += self._get_amplitude_sample(beam_index, sample_index)
                beam.phase += self._get_phase_sample(beam_index, sample_index)

    def _get_sample_offset(self, x_index, y_index, x_bound, sample_size):
        return (y_index * x_bound + x_index) * (sample_size * 2)

    def _get_amplitude_sample(self, beam, sample):
        offset = 0
        sample_size = struct.calcsize(self.amplitude_format)

        if self.rowColumnFlag == 0:
            offset = self._get_sample_offset(sample, beam, self.numberOfSamplesInPing, sample_size)
        else:
            offset = self._get_sample_offset(beam, sample, self.numberOfBeams, sample_size)

        return self.sample_data[offset:offset+sample_size]

    def _get_phase_sample(self, beam, sample):
        sample_offset = 0
        sample_size = struct.calcsize(self.phase_format)

        if self.rowColumnFlag == 0:
            offset = self._get_sample_offset(sample, beam, self.numberOfSamplesInPing, sample_size)
        else:
            offset = self._get_sample_offset(beam, sample, self.numberOfBeams, sample_size)

        # offset by the size of the amplitude sample
        offset = offset + struct.calcsize(self.amplitude_format)
        return self.sample_data[offset:offset+sample_size]

    def __str__(self):
        s = []
        s.append('Sonar ID: %d\n' % self.sonarID)
        s.append('Ping number: %d\n' % self.pingNumber)
        s.append('Multi ping sequence: %d\n' % self.multiPingSequence)
        s.append('Number of beams: %d\n' % self.numberOfBeams)
        s.append('Samples in ping: %d\n' % self.numberOfSamplesInPing)
        s.append('Record subset flg: %x\n' % self.recordSubsetFlag)
        s.append('Row column flag: %x\n' % self.rowColumnFlag)
        s.append('Data sample type: %x\n' % self.dataSampleType)
        for beam in self.beams:
            s.append('Beam %d. first sample %d, last sample %d, parsed samples: %d\n' % (beam.descriptor, beam.first_sample, beam.last_sample, len(beam.amplitude)))
        return "".join(s)

class VerticalDepthRecord(Record):
    """
    This record provides vertical depth relative to chart datum or relative to
    the vessel if tidal data is unavailable.

    """

    RECORD_TYPE_IDENTIFIER = 7009
    NAME = "Vertical Depth Record"

    def __init__(self, data):
        self.name = self.NAME
        fmt = "<fIHddffff"
        fields = struct.unpack(fmt, data)
        self.frequency = fields[0]
        self.pingNumber = fields[1]
        self.multiPingSequence = fields[2]
        self.latitude = fields[3]
        self.longitude = fields[4]
        self.heading = fields[5]
        self.alongTrackDistance = fields[6]
        self.acrossTrackDistance = fields[7]
        self.verticalDepth = fields[8]

    def __str__(self):
        s = []
        s.append("(%s)\n" % self.name)
        s.append("Ping Frequency (Hz): %f\n" % self.frequency)
        s.append("Ping Number: %d\n" % self.pingNumber)
        s.append("Multi-Ping Sequence: %d\n" % self.multiPingSequence)
        s.append("Latitude (deg): %f\n" % math.degrees(self.latitude))
        s.append("Longitude (deg): %f\n" % math.degrees(self.longitude))
        s.append("Heading (deg): %f\n" % math.degrees(self.heading))
        s.append("Along Track Distance In Vessel Grid From Reference Point (m): %f\n" % self.alongTrackDistance)
        s.append("Across Track Distance In Vessel Grid From Reference Point (m): %f\n" % self.acrossTrackDistance)
        s.append("Vertical Depth relative to Chart Datum: %f\n" % self.verticalDepth)
        return "".join(s)


class BeamformedDataRecord(Record):
    """
    This record is produced by the 7kCenter series. It contains the sonar beam
    magnitude and phase data. The 7kCenter updates this record on every ping.
    This record is available by subscription only.

    """
    RECORD_TYPE_IDENTIFIER = 7018
    NAME = "Beam Formed Data Record"

    def __init__(self, data):
        self.name = self.NAME
        fmt = "<QIHHI32x"
        fields = struct.unpack(fmt, data[0:struct.calcsize(fmt)])
        self.sonarId = fields[0]
        self.pingNumber = fields[1]
        self.multiPingSequence = fields[2]
        self.beams = fields[3]
        self.samples = fields[4]
        self.binary_header = data[0:struct.calcsize(fmt)]
        self.amplitude = {}
        self.phase = {}
        start = struct.calcsize(fmt)
        self.s = struct.Struct('<Hh')
        self.readBeamformedData(start, data)

    def readBeamformedData(self, start, data):

        self.amplitude = zeros((self.samples, self.beams))
        self.phase = zeros((self.samples, self.beams))
        for sample in range(self.samples):
            for beam in range(self.beams):
                end = start + self.s.size
                (amp, phase) = self.s.unpack(data[start:end])
                self.amplitude[sample][beam] = amp
                self.phase[sample][beam] = phase
                start = end

    def __str__(self):
        s = []
        s.append("(%s)\n" % self.name)
        s.append("Sonar Id: %d\n" % self.sonarId)
        s.append("Ping Number: %d\n" % self.pingNumber)
        s.append("Multi-Ping Sequence: %d\n" % self.multiPingSequence)
        s.append("Beams: %d\n" % self.beams)
        s.append("Samples: %d\n" % self.samples)
        s.append("Sample\tBeam\tAmplitude\tPhase\n")
        for sample in range(self.samples):
            for beam in range(self.beams):
                s.append("%d\t%d\t%d\t%d\n" %
                         (sample, beam, self.amplitude[sample][beam], self.phase[sample][beam]))
        return ''.join(s)


class SevenKCenterVersionRecord(Record):
    """
    This record provides the 7kCenter version as a Null terminated string.

    """
    RECORD_TYPE_IDENTIFIER = 7022
    NAME = "7K Center Version Record"

    def __init__(self, data):
        self.name = self.NAME
        self.versionString = struct.unpack('<32s', data)[0].split('\x00')[0]

    def __str__(self):
        s = []
        s.append("(%s)\n" % self.name)
        s.append("Version String: %s\n" % self.versionString)
        return ''.join(s)

class RawBathymetryRecord(Record):
    """
    Copied this class from MATLAB scripts provided by Reson, no comments.

    """

    RECORD_TYPE_IDENTIFIER = 7027
    NAME = "Raw Bathymetry Record (3D)"

    def __init__(self, data):
        self.name = self.NAME
        fmt = "<QIHIIxxxxxff"
        fields = struct.unpack(fmt, data[0:struct.calcsize(fmt)])
        self.sonarId = fields[0]
        self.pingNumber = fields[1]
        self.multiPingSequence = fields[2]
        self.points = fields[3]
        self.size = fields[4]
        self.sampleRate = fields[5]
        self.transducerAngle = fields[6]
        start = struct.calcsize(fmt)
        self.samples = []
        for i in range(self.points):
            sampFmt = "<HffIIf"
            end = start + struct.calcsize(sampFmt)
            self.samples.append(struct.unpack(sampFmt, data[start:end]))
            start = end


    def __str__(self):
        s = []
        s.append("(%s)\n" % self.name)
        s.append("Sonar Id: %d\n" % self.sonarId)
        s.append("Ping Number: %d\n" % self.sonarId)
        s.append("Multi-Ping Sequence: %d\n" % self.multiPingSequence)
        s.append("Points(?): %d\n" % self.points)
        s.append("Size(?): %d\n" % self.size)
        s.append("Sample Rate: %f\n" % self.sampleRate)
        s.append("Transducer Angle: %f\n" % self.transducerAngle)
        s.append("Beam\tRange\tAngle\tQflag\tQuality\tTPU\n")
        for i in range(self.points):
            s.append("%d\t%f\t%f\t%d\t%d\t%f\n" % self.samples[i])
        return ''.join(s)

class SnippetsDataRecord:

    RECORD_TYPE_IDENTIFIER = 7028
    NAME = "Snippets Data Record"

    def __init__(self, data):
        self.name = self.NAME

    def __str__(self):
        s = []
        s.append("(%s)\n" % self.name)
        return ''.join(s)


class SonarInstallationParametersRecord(Record):
    """
    This record is sent once when a client subscribes for the record and again when a parameter is changed.

    """

    RECORD_TYPE_IDENTIFIER = 7030
    NAME = "Sonar Installation Parameters Record"

    def __init__(self, data):
        self.name = self.NAME
        start = 0
        end = start + 4
        self.frequency = struct.unpack('<f', data[start:end])
        start = end
        end = start + 2
        self.firmwareVersionLength = struct.unpack('<H', data[start:end])[0]
        start = end
        end = start + self.firmwareVersionLength
        self.firmwareVersionInfo = struct.unpack('<%ds' % self.firmwareVersionLength, data[start:end])[0]
        start = end
        end = start + 2
        self.softwareVersionLength = struct.unpack('<H', data[start:end])[0]
        start = end
        end = start + self.softwareVersionLength
        self.softwareVersionInfo = struct.unpack('<%ds' % self.softwareVersionLength, data[start:end])[0]
        start = end
        end = start + 2
        self.recordProtocalLength = struct.unpack('<H', data[start:end])[0]
        start = end
        end = start + self.recordProtocalLength
        self.recordProtocalInfo = struct.unpack('<%ds' % self.recordProtocalLength, data[start:end])[0]

        start = end
        fmt = "<ffffffffffffffffffHfffHf"
        end = start + struct.calcsize(fmt)
        fields = struct.unpack(fmt, data[start:end])
        self.transmitArrayX = fields[0]
        self.transmitArrayY = fields[1]
        self.transmitArrayZ = fields[2]
        self.transmitArrayRoll = fields[3]
        self.transmitArrayPitch = fields[4]
        self.transmitArrayHeading = fields[5]
        self.receiveArrayX = fields[6]
        self.receiveArrayY = fields[7]
        self.receiveArrayZ = fields[8]
        self.receiveArrayRoll = fields[9]
        self.receiveArrayPitch = fields[10]
        self.receiveArrayHeading = fields[11]
        self.motionSensorX = fields[12]
        self.motionSensorY = fields[13]
        self.motionSensorZ = fields[14]
        self.motionSensorRollCalibration = fields[15]
        self.motionSensorPitchCalibration = fields[16]
        self.motionSensorHeadingCalibration = fields[17]
        self.motionSensorTimeDelay = fields[18]
        self.positionSensorX = fields[19]
        self.positionSensorY = fields[20]
        self.positionSensorZ = fields[21]
        self.positionSensorTimeDelay = fields[22]
        self.waterLineVerticalOffset = fields[23]


    def __str__(self):
        s = []
        s.append("(%s)\n" % self.name)
        s.append("Frequency: %f\n" % self.frequency)
        s.append("Length of software version info: %d\n" % self.firmwareVersionLength)
        s.append("Firmware Version Info: %s\n" % self.firmwareVersionInfo)
        s.append("Length of 7k software version info: %d\n" % self.softwareVersionLength)
        s.append("7k software version Info: %s\n" % self.softwareVersionInfo)
        s.append("Length of Record Protocal Info: %d\n" % self.recordProtocalLength)
        s.append("Record Protocal Info: %s\n" % self.recordProtocalInfo)
        s.append("Transmit Array X: %f\n" % self.transmitArrayX)
        s.append("Transmit Array Y: %f\n" % self.transmitArrayY)
        s.append("Transmit Array Z: %f\n" % self.transmitArrayZ)
        s.append("Transmit Array Roll: %f\n" % self.transmitArrayRoll)
        s.append("Transmit Array Pitch: %f\n" % self.transmitArrayPitch)
        s.append("Transmit Array Heading: %f\n" % self.transmitArrayHeading)
        s.append("Receive Array X: %f\n" % self.receiveArrayX)
        s.append("Receive Array Y: %f\n" % self.receiveArrayY)
        s.append("Receive Array Z: %f\n" % self.receiveArrayZ)
        s.append("Receive Array Roll: %f\n" % self.receiveArrayRoll)
        s.append("Receive Array Pitch: %f\n" % self.receiveArrayPitch)
        s.append("Receive Array Heading: %f\n" % self.receiveArrayHeading)
        s.append("Motion Sensor X: %f\n" % self.motionSensorX)
        s.append("Motion Sensor Y: %f\n" % self.motionSensorY)
        s.append("Motion Sensor Z: %f\n" % self.motionSensorZ)
        s.append("Motion Sensor Roll Calibration: %f\n" % self.motionSensorRollCalibration)
        s.append("Motion Sensor Pitch Calibration: %f\n" % self.motionSensorPitchCalibration)
        s.append("Motion Sensor Heading Calibration: %f\n" % self.motionSensorHeadingCalibration)
        s.append("Position Sensor X: %f\n" % self.positionSensorX)
        s.append("Position Sensor Y: %f\n" % self.positionSensorY)
        s.append("Position Sensor Z: %f\n" % self.positionSensorZ)
        s.append("Position Sensor Time Delay: %d\n" % self.positionSensorTimeDelay)
        s.append("Water Line Vertical Offset: %f\n" % self.waterLineVerticalOffset)
        return ''.join(s)

# class SampleType:
#     MAG16_PHASE16 = 0
#     MAG16 = 0
#     MAG8_PHASE8 = 0
#     MAG8 = 0
#     MAG32_PHASE8 = 0
#     MAG32 = 0
#
# class CompressedWaterColumnBeam:
#     def __init__(self, data):
#
#
# class CompressedWaterColumnDataRecord(Record):
#     """
#     This record is produced by the 7kCenter series. It contains the sonar beam
#     magnitude and phase data. The 7kCenter updates this record on every ping.
#     This record is available by subscription only.
#
#     """
#     RECORD_TYPE_IDENTIFIER = 7042
#     NAME = "Compressed Water Column Data Record"
#
#     def __init__(self, data):
#         self.name = self.NAME
#         fmt = "<QIHHIIIffI"
#         self.binary_header = data[0:struct.calcsize(fmt)]
#         fields = struct.unpack(fmt, self.binary_header)
#         self.sonarId = fields[0]
#         self.pingNumber = fields[1]
#         self.multiPingSequence = fields[2]
#         self.beams = fields[3]
#         self.samples = fields[4]
#         self.compressedSamples = fields[5]
#         self.flags = fields[6]
#         self.useMaxBottomDetectionPoint = self.flags & 1
#         self.includeMangitudateDataOnly = (self.flags >> 1) & 1
#         self.compressTo8Bits = (self.flags >> 2) & 1
#         self.Data32Bits = (self.flags >> 32) & 1
#         self.firstSample = fields[7]
#         self.sampleRate = fields[8]
#         self.binary_header = data[0:struct.calcsize(fmt)]
#         self.amplitude = {}
#         self.phase = {}
#         start = struct.calcsize(fmt)
#         self.s = struct.Struct('<Hh')
#         self.readBeamformedData(start, data)
#
#     def readBeamformedData(self, start, data):
#
#         self.amplitude = zeros((self.samples, self.beams))
#         self.phase = zeros((self.samples, self.beams))
#         for sample in range(self.samples):
#             for beam in range(self.beams):
#                 end = start + self.s.size
#                 (amp, phase) = self.s.unpack(data[start:end])
#                 self.amplitude[sample][beam] = amp
#                 self.phase[sample][beam] = phase
#                 start = end
#
#     def __str__(self):
#         s = []
#         s.append("(%s)\n" % self.name)
#         s.append("Sonar Id: %d\n" % self.sonarId)
#         s.append("Ping Number: %d\n" % self.pingNumber)
#         s.append("Multi-Ping Sequence: %d\n" % self.multiPingSequence)
#         s.append("Beams: %d\n" % self.beams)
#         s.append("Samples: %d\n" % self.samples)
#         s.append("Sample\tBeam\tAmplitude\tPhase\n")
#         for sample in range(self.samples):
#             for beam in range(self.beams):
#                 s.append("%d\t%d\t%d\t%d\n" %
#                          (sample, beam, self.amplitude[sample][beam], self.phase[sample][beam]))
#         return ''.join(s)


class FileHeaderRecord(Record):
    """
    First record of 7k data file.

    """
    RECORD_TYPE_IDENTIFIER = 7200
    NAME = "7k File Header"

    def __init__(self, data):
        self.name = self.NAME
        self.fileId = str(uuid.UUID(bytes_le=data[:16]))
        self.versionNumber = struct.unpack('<H', data[16:18])[0]
        self.SessionId = str(uuid.UUID(bytes_le=data[20:36]))
        self.recordDataSize = struct.unpack('<I', data[36:40])[0]
        self.numberOfDevices = struct.unpack('<I', data[40:44])[0]
        self.recordingName = struct.unpack('<64s', data[44:108])[0].split('\x00')[0]
        self.recordingProgramVersionNumber = struct.unpack('<64s', data[108:172])[0].split('\x00')[0]
        self.userDefinedName = struct.unpack('<64s', data[172:236])[0].split('\x00')[0]
        # Remaining portion of this packet seems to be missing.

    def __str__(self):
        s = []
        s.append("(%s)\n" % self.name)
        s.append("File identifier: %s\n" % self.fileId)
        s.append("Version Number: %d\n" % self.versionNumber)
        s.append("Session Identifier: %s\n" % self.SessionId)
        s.append("Record Data Size: %d\n" % self.recordDataSize)
        s.append("Number Of Devices: %d\n" % self.numberOfDevices)
        s.append("Recording Name: %s\n" % self.recordingName.strip())
        s.append("Recording Program Version Number: %s\n" % self.recordingProgramVersionNumber)
        s.append("User Defined Name: %s\n" % self.userDefinedName)
        return ''.join(s)


