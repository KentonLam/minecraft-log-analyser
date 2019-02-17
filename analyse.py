import datetime as dt 
from collections import defaultdict
import os
import gzip

import typing as t



class PlayerStats(dict):
    def __init__(self):
        self['ccl_errors'] = 0
        self['days']: t.Dict[dt.date, int] = defaultdict(lambda: 0)

    @property
    def ccl_errors(self):
        return self['ccl_errors']

    @ccl_errors.setter
    def ccl_errors(self, value):
        self['ccl_errors'] = value

    @property
    def days(self):
        return self['days']


class LogAnalyser:
    def __init__(self):
        self.players = defaultdict(lambda: PlayerStats())
        self.online: t.Dict[str, dt.datetime] = dict()
    
    def parse_log_text(self, file_object: t.TextIO, date: dt.date):
        midnight = dt.datetime.combine(date, dt.time.min)
        print(midnight)

        get_time = lambda line: dt.datetime.combine(date, 
            dt.datetime.strptime(line.split(' ')[0], '[%H:%M:%S]').time())

        for line in file_object:
            line = line.rstrip()
            if line.endswith(' joined the game'):
                print(get_time(line))
                print(line)
                break


def main(folder: str):
    log_files = [x for x in os.listdir(folder) 
        if (x.endswith('.log') or x.endswith('.log.gz')) 
            and not (x.startswith('debug') or x.startswith('latest'))]

    analyser = LogAnalyser()

    for f in log_files:
        f_path = os.path.join(folder, f)

        date_part = '-'.join(f.split('-')[:3])
        date = dt.datetime.strptime(date_part, '%Y-%m-%d')

        if f.endswith('.gz'):
            with gzip.open(f_path, 'rt') as f_obj:
                analyser.parse_log_text(f_obj, date.date())
        

if __name__ == "__main__":
    main('./tms')