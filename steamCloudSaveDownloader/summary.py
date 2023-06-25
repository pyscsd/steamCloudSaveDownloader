from . import err
from .err import err_enum
from enum import IntEnum
import datetime
from zoneinfo import ZoneInfo

g_truncate_max = 1000

'''
[
    {
        'name': game_name0
        'files': [
            {
                'filename': file_name0,
                'old_time': time_str
                'new_time': time_str
            },
            {
                'filename': file_name1,
                'old_time': time_str
                'new_time': time_str
            },
            ...
        ]
    },
    {
        ...
    },
]
'''

class level_e(IntEnum):
    NONE = 0
    GAME = 1
    FILE = 2
    TIME = 3

class summary:
    def __init__(self, level:int):
        self.data = list()
        self.level = level
        # Steam timezone is in PST
        self.local_tz = datetime.datetime.now().astimezone().tzinfo
        self.server_tz = ZoneInfo("America/Los_Angeles")

    def add_game(self, game_name:str):
        if len(self.data) != 0 and self.data[-1]['name'] == game_name:
            return
        self.data.append({'name': game_name, 'files': list()})

    def add_game_file(
            self,
            game_name:str,
            file_name:str,
            timestamp_old,
            timestamp_new:str):

        if self.data[-1]['name'] != game_name:
            return

        def to_string(time):
            if time is None:
                return None

            target_time = time.replace(tzinfo=self.server_tz).astimezone(self.local_tz).replace(tzinfo=None)

            now = datetime.datetime.now()

            if target_time.year == now.year:
                return target_time.strftime("%m-%d %H:%M")
            else:
                return target_time.isoformat(' ', 'minutes')

        self.data[-1]['files'].append(
            {
                'filename': file_name,
                'old_time': to_string(timestamp_old),
                'new_time': to_string(timestamp_new)
            })


    def has_changes(self):
        return len(self.data) != 0

    def get(self):
        if len(self.data) == 0:
            return None
        if self.level == level_e.NONE:
            return None
        text = "Execute summary:\n"

        for game in self.data:
            text += f"- {game['name']}\n"

            if (len(text) > g_truncate_max):
                text += "Truncated...\n"
                return text

            if self.level < level_e.FILE:
                continue

            for file in game['files']:
                text += f"  - {file['filename']}"

                if (len(text) > g_truncate_max):
                    text += "\nTruncated...\n"
                    return text

                if self.level < level_e.TIME:
                    text += "\n"
                    continue
                if file['old_time']:
                    text += f" ({file['old_time']} -> {file['new_time']})\n"
                else:
                    text += f" (new {file['new_time']})\n"

        return text
