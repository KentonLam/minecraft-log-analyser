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
    def errors(self):
        return self['ccl_errors']

    @errors.setter
    def errors(self, value):
        self['ccl_errors'] = value

    @property
    def days(self):
        return self['days']


class LogAnalyser:
    def __init__(self):
        self.players: t.DefaultDict[str, PlayerStats] = defaultdict(lambda: PlayerStats())
        self.online: t.Dict[str, t.Optional[dt.datetime]] = defaultdict(lambda: None)

        self.day = dt.date.min
        self.midnight = dt.datetime.min
        self.time = dt.time.min
    
    def get_time(self, line: str) -> dt.datetime:
        return dt.datetime.combine(self.day, 
            dt.datetime.strptime(line.split(' ')[0], '[%H:%M:%S]').time())

    def parse_log_text(self, file_object: t.IO[t.Any], day: dt.date):
        assert day >= self.day

        if day > self.day:
            self.new_day(day)
            self.day = day

        self.day = day
        self.midnight = dt.datetime.combine(day, dt.time.min)

        for i, line in enumerate(file_object):
            line = line.rstrip()
            if self.parse_line(line):
                new_time = self.get_time(line).time()
                assert new_time >= self.time # ensure time is moving forwards
                self.time = new_time
            
    def player_logoff(self, username: str, leave_time: dt.datetime):
        join_time = self.online[username]
        # assert join_time is not None
        if join_time is None:
            print('warning:', username, 'left without joining in', self.day)
        else:
            self.players[username].days[self.day] += (leave_time - join_time).total_seconds()/3600 # type: ignore
        self.online[username] = None

    def parse_line(self, line: str) -> bool:
        if line.endswith(' joined the game'):
            username = line[82:-16]
            assert self.online[username] is None 
            self.online[username] = self.get_time(line)
            return True 
        elif line.endswith(' left the game'):
            username = line[82:-14]

            leave_time = self.get_time(line)
            self.player_logoff(username, leave_time)
            return True
        elif line.endswith(' [net.minecraft.server.MinecraftServer]: Stopping server'):
            # server closing; everyone leaves
            print('closing server')
            close_time = self.get_time(line)
            for player, t in self.online.items():
                if t:
                    self.player_logoff(player, close_time)
            return True
        elif " Can't keep up! Did the system time change, or is the server overloaded? " in line:
            for player, t in self.online.items():
                if t:
                    self.players[player].errors += 1
        return False

    def new_day(self, new_day: dt.date):
        print('new day', new_day)
        new_midnight = dt.datetime.combine(new_day, dt.time.min)
        for user, join_time in self.online.items():
            if join_time is not None:
                self.player_logoff(user, new_midnight)
                self.online[user] = new_midnight
        self.time = dt.time.min

def main(folder: str):
    log_files = [x for x in os.listdir(folder) 
        if (x.endswith('.log.gz')) 
            and not (x.startswith('debug') or x.startswith('latest'))]

    analyser = LogAnalyser()

    for f in log_files:
        f_path = os.path.join(folder, f)

        date_part = '-'.join(f.split('-')[:3])
        day = dt.datetime.strptime(date_part, '%Y-%m-%d')

        if f.endswith('.gz'):
            if os.path.isfile(f_path[:-3]):
                print('using extracted', f)
                with open(f_path[:-3], 'r') as f_obj:
                    analyser.parse_log_text(f_obj, day.date())
            else:
                print('opening gzip', f)
                with gzip.open(f_path, 'rt') as f_obj2:
                    analyser.parse_log_text(f_obj2, day.date())


    print([x for x, y in analyser.online.items() if y])

    start = dt.date(2019, 2, 9)
    end = dt.date(2019, 2, 17)

    days = [start + dt.timedelta(days=i) for i in range((end-start).days + 1)]

    with open(os.path.join(folder, 'output.csv'), 'w') as out:
        out.write('Username,')
        out.write(','.join(map(lambda d: d.strftime('%Y-%m-%d'), days)))
        out.write(',Errors\n')
        
        for username, stats in analyser.players.items():
            out.write(username + ',')
            out.write(','.join(map(lambda d: str(stats.days[d]), days)))
            out.write(f',{stats.errors}\n')
        

if __name__ == "__main__":
    main('./tms')