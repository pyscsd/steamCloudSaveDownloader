from . import err
from .err import err_enum
from bs4 import BeautifulSoup
import datetime

def get_tbody(soup):
    main_content = soup.find(id='main_content')

    if (main_content is None):
        raise err.err(err_enum.CANNOT_PARSE_LIST)

    if (not hasattr(main_content, "table")):
        raise err.err(err_enum.CANNOT_PARSE_LIST)

    return main_content.table.tbody

def parse_time(input:str) -> datetime.datetime:
    if '@' not in input:
        raise err.err(er_enum.CANNOT_PARSE_GAME_FILES)

    # Assume 'DD MMM [YYYY] @ HH:MM{a|p}m' format

    tokens = input.split(' ')
    datetime_ = None
    try:
        if len(tokens) == 4:
            now = datetime.datetime.now()
            year = now.year
            d = datetime.datetime.strptime(input, "%d %b @ %I:%M%p")
            datetime_ = datetime.datetime(year, d.month, d.day, d.hour, d.minute)
        elif len(tokens) == 5:
            datetime_ = datetime.datetime.strptime(input, "%d %b %Y %I:%M%p")
        else:
            raise err.err(er_enum.CANNOT_PARSE_GAME_FILES)
    except ValueError:
        raise err.err(er_enum.CANNOT_PARSE_GAME_FILES)

    return datetime_


class web_parser:
    def __init__(self):
        pass

    def parse_index(self, content):
        try:
            return self._parse_index(content)
        except err.err as e:
            e.print()
            exit(e.err_enum)

    def _parse_index(self, content):
        soup = BeautifulSoup(content, 'html.parser')

        tbody = get_tbody(soup)

        data = list()

        rows = tbody.find_all('tr')
        for row in rows:
            cols = row.find_all('td')
            data.append({"Game": cols[0].text.strip(), "Link": cols[3].a['href']})
        return data

    def parse_game_file(self, content):
        try:
            return self._parse_game_file(content)
        except err.err as e:
            e.print()
            exit(e.err_enum)

    def _parse_game_file(self, content):
        soup = BeautifulSoup(content, 'html.parser')

        tbody = get_tbody(soup)

        data = list()
        rows = tbody.find_all('tr')

        for row in rows:
            cols = row.find_all('td')
            data.append({
                "Filename": cols[1].text.strip(),
                "Time": parse_time(cols[3].text.strip()),
                "Link": cols[4].a['href']})
        return data

