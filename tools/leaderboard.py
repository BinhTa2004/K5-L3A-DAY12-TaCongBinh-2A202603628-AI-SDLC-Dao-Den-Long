"""Validated, atomic local leaderboard shared by the GUI and export CLI."""
from datetime import datetime, timezone
import json
from pathlib import Path
import re
from threading import RLock


class Leaderboard:
    def __init__(self, directory):
        self.path = Path(directory)/'leaderboard.json'
        self.lock = RLock()

    def read(self):
        with self.lock:
            if not self.path.exists():
                return []
            data = json.loads(self.path.read_text(encoding='utf-8'))
            return sorted(data['entries'], key=lambda e: (-e['score'], e['achieved_at']))[:10]

    def add(self, value):
        if not isinstance(value, dict) or not re.fullmatch(r'[A-Za-z0-9_]{3,12}', str(value.get('name',''))):
            raise ValueError('Ten can 3-12 ky tu A-Z, a-z, 0-9 hoac _.')
        for key in ['score','nights_won','seed']:
            if type(value.get(key)) is not int:
                raise ValueError(key+' must be an integer')
        if value['score']<0 or not 0<=value['nights_won']<=3:
            raise ValueError('Invalid score/nights_won')
        entry = {key:value[key] for key in ['name','score','nights_won','seed']}
        entry['achieved_at'] = datetime.now(timezone.utc).isoformat(timespec='microseconds')
        with self.lock:
            entries=self.read()+[entry]
            entries=sorted(entries,key=lambda e:(-e['score'],e['achieved_at']))[:10]
            self.path.parent.mkdir(parents=True,exist_ok=True)
            temporary=self.path.with_suffix('.json.tmp')
            temporary.write_text(json.dumps({'entries':entries},ensure_ascii=False,indent=2),encoding='utf-8')
            temporary.replace(self.path)
        return entries

    def export(self, destination):
        Path(destination).write_text(json.dumps({'entries':self.read()},ensure_ascii=False,indent=2),encoding='utf-8')
