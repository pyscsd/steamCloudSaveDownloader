import steamCloudSaveDownloader.parser as parser

import datetime
from zoneinfo import ZoneInfo
import os
import pytest

@pytest.fixture(scope='session')
def html_dir():
    return os.path.join(os.path.dirname(__file__), "html_data")

@pytest.fixture(scope='session')
def web_parser():
    return parser.web_parser()

def _read_html(html_dir, filename):
    with open(os.path.join(html_dir, filename), encoding="utf-8") as f:
        return f.read()

def _current_year_time(time_str):
    now = datetime.datetime.now(tz=datetime.timezone.utc)
    parsed = datetime.datetime.strptime(time_str + " 2024", "%d %b @ %I:%M%p %Y")
    datetime_ = parsed.replace(year=now.year, tzinfo=datetime.timezone.utc)
    if datetime_ > now:
        datetime_ = parsed.replace(year=now.year - 1, tzinfo=datetime.timezone.utc)
    return datetime_

class TestParse:
    def test_parse_index_game_names(self, html_dir, web_parser):
        games = web_parser.parse_index(_read_html(html_dir, "list.html"))
        assert [game["name"] for game in games] == [
            "Steam Client",
            "",
            "LEGO® Star Wars™ III: The Clone Wars™",
            "ibb & obb",
            "South Park™: The Stick of Truth™",
            "eden*",
            "htoL#NiQ: The Firefly Diary",
            "Kingdom Come: Deliverance (For large amount of files)",
            "永遠消失的幻想鄉 ～ The Disappearing of Gensokyo",
            "STEINS;GATE 0",
            "TouHou Makuka Sai ~ Fantastic Danmaku Festival",
            "LEGO® Star Wars™: The Skywalker Saga",
            "Röki",
            "Senren＊Banka",
            "Pâquerette Down the Bunburrows Demo",
            "Dōkyūsei: Bangin' Summer",
            "Thank Goodness You're Here!",
            "",
        ]

    def test_parse_game_single_page(self, html_dir, web_parser):
        files, next_page = web_parser.parse_game_file(_read_html(html_dir, "game_single_page.html"))
        assert next_page is None
        assert files == [
            {
                "filename": "config.dat",
                "path": "My Games/mages_steam/STEINS GATE 0/zht",
                "time": datetime.datetime(2020, 8, 6, 23, 49, tzinfo=datetime.timezone.utc),
                "link": "https://cdn.steamusercontent.com/filedownload/12312123123",
            },
            {
                "filename": "SAVEDATA.DAT",
                "path": "My Games/mages_steam/STEINS GATE 0/zht",
                "time": datetime.datetime(2020, 8, 16, 20, 40, tzinfo=datetime.timezone.utc),
                "link": "https://cdn.steamusercontent.com/filedownload/123123",
            },
        ]

    def test_parse_game_multiple_page_0(self, html_dir, web_parser):
        files, next_page = web_parser.parse_game_file(_read_html(html_dir, "game_multiple_page_0.html"))
        assert next_page == "https://store.steampowered.com/account/remotestorageapp?appid=379430&index=50"
        assert files == [
            {
                "filename": "autosave2465.whs",
                "path": "kingdomcome/saves/playline0",
                "time": _current_year_time("6 Apr @ 1:06pm"),
                "link": "https://cdn.steamusercontent.com/filedownload/abcdef",
            },
            {
                "filename": "autosave2466.whs",
                "path": "kingdomcome/saves/playline0",
                "time": _current_year_time("6 Apr @ 1:09pm"),
                "link": "https://cdn.steamusercontent.com/filedownload/deadbeef1",
            },
        ]

    def test_parse_game_multiple_page_1(self, html_dir, web_parser):
        files, next_page = web_parser.parse_game_file(_read_html(html_dir, "game_multiple_page_1.html"))
        assert next_page is None
        assert files == [
            {
                "filename": "save2482.whs",
                "path": "kingdomcome/saves/playline0",
                "time": _current_year_time("6 Apr @ 2:07pm"),
                "link": "https://cdn.steamusercontent.com/filedownload/asdfasddfsf",
            },
            {
                "filename": "switch52014.whs",
                "path": "kingdomcome/saves/playline0",
                "time": _current_year_time("29 Mar @ 1:24am"),
                "link": "https://cdn.steamusercontent.com/filedownload/sdfsdfsd",
            },
        ]

    def test_parse_time_fails_with_appended_timezone(self):
        from steamCloudSaveDownloader.parser import parse_time
        from steamCloudSaveDownloader.err import err

        # Should parse normally without a timezone
        try:
            parse_time("12 Oct, 2022 @ 3:08pm")
        except Exception as e:
            pytest.fail(f"Valid time failed to parse: {e}")

        # Should fail if Valve adds a timezone abbreviation
        with pytest.raises(err) as exc_info:
            parse_time("12 Oct, 2022 @ 3:08pm PST")
        from steamCloudSaveDownloader.err import err_enum
        assert exc_info.value.err_enum == err_enum.CANNOT_PARSE_GAME_FILES

        with pytest.raises(err) as exc_info:
            parse_time("12 Oct, 2022 @ 3:08pm UTC")
        from steamCloudSaveDownloader.err import err_enum
        assert exc_info.value.err_enum == err_enum.CANNOT_PARSE_GAME_FILES
