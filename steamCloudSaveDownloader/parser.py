from . import err
from .notifier import notifier
from .err import err_enum
from bs4 import BeautifulSoup
import datetime
import os
import logging

logger = logging.getLogger('scsd')

g_language_specifier = "l=english"

def get_tbody(soup):
    main_content = soup.find(id='main_content')

    if (main_content is None):
        raise err.err(err_enum.CANNOT_PARSE_LIST)

    if (not hasattr(main_content, "table")):
        raise err.err(err_enum.CANNOT_PARSE_LIST)

    return main_content.table.tbody

def parse_time(input:str) -> datetime.datetime:
    dm_format = "%d %b @ %I:%M%p"
    md_format = "%b %d @ %I:%M%p"
    dmy_format = "%d %b, %Y @ %I:%M%p"
    mdy_format = "%b %d, %Y @ %I:%M%p"

    def is_dm_format(tokens):
        return tokens[0].isdigit()

    if '@' not in input:
        raise err.err(err_enum.CANNOT_PARSE_GAME_FILES)

    # Assume 'DD MMM [YYYY] @ HH:MM{a|p}m' format

    tokens = input.split(' ')
    datetime_ = None
    try:
        if len(tokens) == 4:
            now = datetime.datetime.now(tz=datetime.timezone.utc)
            year = now.year
            if is_dm_format(tokens):
                d = datetime.datetime.strptime(input, dm_format)
            else:
                d = datetime.datetime.strptime(input, md_format)
            datetime_ = d.replace(year=year, tzinfo=datetime.timezone.utc)
        elif len(tokens) == 5:
            if is_dm_format(tokens):
                datetime_ = datetime.datetime.strptime(input, dmy_format).replace(tzinfo=datetime.timezone.utc)
            else:
                datetime_ = datetime.datetime.strptime(input, mdy_format).replace(tzinfo=datetime.timezone.utc)
        else:
            logger.error(f"Unable to parse time token {input}")
            raise err.err(err_enum.CANNOT_PARSE_GAME_FILES)
    except ValueError:
        logger.error(f"Unable to parse time token {input}")
        raise err.err(err_enum.CANNOT_PARSE_GAME_FILES)

    return datetime_

def get_appid(link:str) -> int:
    appid_token = 'appid='
    appid_location = link.find(appid_token)

    if (appid_location == -1):
        return -1

    return int(link[appid_location + len(appid_token):])

class web_parser:
    def __init__(self):
        pass

    def parse_index(self, content):
        try:
            return self._parse_index(content)
        except err.err as e:
            print('There are a few possibilities:\n 1. Your cookie has expired.\n 2. It seems like Steam has update the webpage. Please update to the latest version or notify the author.')
            raise e

    def _parse_index(self, content):
        soup = BeautifulSoup(content, 'html.parser')

        tbody = get_tbody(soup)

        data = list()

        rows = tbody.find_all('tr')
        for row in rows:
            cols = row.find_all('td')
            data.append({
                "name": cols[0].text.strip(),
                "link": f"{cols[3].a['href']}&{g_language_specifier}",
                "app_id": get_appid(cols[3].a['href'])
            })
        return data

    def parse_game_file(self, content) -> tuple:
        soup = BeautifulSoup(content, 'html.parser')

        tbody = get_tbody(soup)

        data = list()
        rows = tbody.find_all('tr')

        for row in rows:
            cols = row.find_all('td')
            path, filename = os.path.split(cols[1].text.strip())
            time_str = cols[3].text.strip()
            parsed_time = parse_time(time_str)
            logger.debug(f"Parse {filename} time '{time_str}' as '{parsed_time.isoformat()}'")
            data.append({
                "filename": filename,
                "path": path,
                "time": parsed_time,
                "link": cols[4].a['href']})

        has_next = soup.find('a', text='next >>')

        if (has_next is None):
            return (data, None)
        else:
            return (data, has_next['href'])
