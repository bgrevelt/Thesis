import sqlite3
import datetime
import os

class NoStoredResultsError(Exception):
    pass

class StorageManager:
    def __init__(self):
        self.file_name = 'results.sqlite'
        self.conn = sqlite3.connect(self.file_name)
        self.cursor = self.conn.cursor()

    def store(self, results):
         table_name = 'results-{}'.format(datetime.datetime.now())
         create_string = '''CREATE TABLE IF NOT EXISTS "{}" (
                        File TEXT,
                        Algorithm TEXT,
                        "Compression ratio" REAL,
                        "Compression time" REAL,
                        "Decompression time" REAL,
                        "Lossless" INTEGER,
                        "Random access decompression time"  REAL,
                        'Real-time compression time' REAL,
                        "Real-time" REAL,
                        "Procesing" REAL,
                        "Cost" REAL
                         );'''

         self.cursor.execute(create_string.format(table_name))

         for algorithm, algorithm_results in results.items():
             for file, file_results in algorithm_results.items():
                insert_string = '''INSERT INTO "{table_name}" (File,Algorithm,"Compression ratio","Compression time","Decompression time","Lossless","Random access decompression time", 'Real-time compression time', "Real-time", "Procesing","Cost")
                VALUES("{file}","{algorithm}",{cr},{ct},{dt},{lossless}, {ra_dt}, {rt_ct}, {realtime}, {processing}, {cost})'''
                insert_string = insert_string.format( table_name=table_name,
                                      file=file,
                                      algorithm=algorithm,
                                      cr=file_results['Compression ratio'],
                                      ct=file_results['Compression time'],
                                      dt=file_results['Decompression time'],
                                      lossless='1' if file_results['Losslessness'] else '0',
                                      processing=file_results['Processing'],
                                      realtime=file_results['Real-time'],
                                      cost=file_results['Cost'],
                                      ra_dt = file_results['Random access decompression time'],
                                      rt_ct = file_results['Real-time compression time'])
                print(insert_string)
                self.cursor.execute(insert_string)
         self.conn.commit()

    def fetch_most_recent(self):
        table = self._get_most_recent_table()
        print(table)
        self.cursor.execute('SELECT * FROM "{}";'.format(table))
        rows = self.cursor.fetchall()
        metrics = {}
        for row in rows:
            file = row[0]
            algorithm = row[1]
            compression_ratio = row[2]
            compression_time = row[3]
            decompression_time = row[4]
            lossless = row[5]
            ra_decompression_time = row[6]
            rt_compression_time = row[7]
            real_time = row[8]
            processing = row[9]
            cost = row[10]

            if algorithm not in metrics:
                metrics[algorithm] = {}
            if file not in metrics[algorithm]:
                metrics[algorithm][file] = {}

            metrics[algorithm][file]['Compression ratio'] = compression_ratio
            metrics[algorithm][file]['Compression time'] = compression_time
            metrics[algorithm][file]['Decompression time'] = decompression_time
            metrics[algorithm][file]['Losslessness'] = False if lossless == 0 else True
            metrics[algorithm][file]['Random access decompression time'] = ra_decompression_time
            metrics[algorithm][file]['Real-time compression time'] = rt_compression_time
            metrics[algorithm][file]['Processing'] = processing
            metrics[algorithm][file]['Real-time'] = real_time
            metrics[algorithm][file]['Cost'] = cost

        return metrics

    def _get_most_recent_table(self):
        self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table';" )
        files = [result[0] for result in self.cursor.fetchall()]
        if len(files) is 0:
            raise NoStoredResultsError

        files = [(datetime.datetime.strptime(file[8:], '%Y-%m-%d %H:%M:%S.%f'), file) for file in files]
        files = sorted(files)
        return files[len(files) - 1][1]
