import sys
import os
import logging
import sqlite3
from collections import namedtuple
from .Kongsberg.Kongsberg_all import KongsbergAllParser
from .Reson.Reson_s7k import Reson7kParser
from .QPS.db_reader import DbReader
from .R2Sonic.Reader import R2sReader

water_column_file = namedtuple('water_column_file', 'path size manufacturer device')

class WcdParserCollection:
    def __init__(self):
        self.parsers = {}
        parsers = [Reson7kParser(), KongsbergAllParser(), DbReader(), R2sReader()]
        for parser in parsers:
            for ext in parser.GetSupportedExtensions():
                self.parsers[ext] = parser

        self.opened_file = None

    def IsPotentialWcdFile(self, path):
        ext = os.path.splitext(path)[1]
        return ext in self.parsers

    def ContainsWcd(self, path):
        ext = os.path.splitext(path)[1]
        if ext not in self.parsers:
            return False

        if self.opened_file == None:
            self._OpenFile(path)
        elif self.opened_file[0] != path: #New file to open
            self._CloseFile()
            self._OpenFile(path)

        assert(self.opened_file != None)

        return self.opened_file[1].ContainsWcd()

    def AnalyzeFile(self, path):
        if not self.ContainsWcd(path):
            return water_column_file(path, os.path.getsize(path), "Unknown", "Unknown")
        else:
            assert(self.opened_file != None)
            make, model = self.opened_file[1].GetMakeAndModel()
            return water_column_file(path, os.path.getsize(path), make, model )

    def Water_column_packets(self, path):
        if not self.ContainsWcd(path):
            raise ValueError
        else:
            assert(self.opened_file != None)
            return self.opened_file[1].water_column_packets()

    def _OpenFile(self, path):
        ext = os.path.splitext(path)[1]
        parser = self.parsers[ext]
        parser.Open(path)
        self.opened_file = (path, parser)

    def _CloseFile(self):
        self.Close()

    def Close(self):
        assert(self.opened_file != None)
        self.opened_file[1].Close()
        self.opened_file = None
