from . import err
from .notifier import notifier
from .err import err_enum
from lxml import html
import datetime
import os
import logging

logger = logging.getLogger('scsd')

g_language_specifier = "l=english"

def get_tbody(tree):
    main_content = tree.xpath('//*[@id="main_content"]')

    if not main_content:
        raise err.err(err_enum.CANNOT_PARSE_LIST)

    tbody = main_content[0].xpath('.//table//tbody')
    if not tbody:
        raise err.err(err_enum.CANNOT_PARSE_LIST)

    return tbody[0]

def parse_time(input:str) -> datetime.datetime:
    dm_format = "%d %b @ %I:%M%p %Y"
    md_format = "%b %d @ %I:%M%p %Y"
    dmy_format = "%d %b, %Y @ %I:%M%p"
    mdy_format = "%b %d, %Y @ %I:%M%p"

    def is_dm_format(tokens):
        return tokens[0].isdigit()

    if '@' not in input:
        logger.error(f"Unable to parse time token '{input}'")
        raise err.err(err_enum.CANNOT_PARSE_GAME_FILES)

    # Assume 'DD MMM [YYYY] @ HH:MM{a|p}m' format

    tokens = input.split(' ')
    datetime_ = None
    try:
        if len(tokens) == 4:
            now = datetime.datetime.now(tz=datetime.timezone.utc)
            year = now.year

            # strptime treat date as 1900, with no Feb 29, set to
            # leap year to circulate this problem
            if is_dm_format(tokens):
                d = datetime.datetime.strptime(input + " 2024", dm_format)
            else:
                d = datetime.datetime.strptime(input + " 2024", md_format)
            datetime_ = d.replace(year=year, tzinfo=datetime.timezone.utc)

            # Check if future during year change
            if datetime_ > now:
                logger.debug(f"Parse time is future {datetime_} vs {now}")
                datetime_ = datetime_.replace(year=year - 1)
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
        tree = html.fromstring(content)

        tbody = get_tbody(tree)

        data = list()

        rows = tbody.xpath('.//tr')
        for row in rows:
            cols = row.xpath('.//td')
            if len(cols) < 4:
                logger.warning(f"Row skipped in index: Expected at least 4 columns, found {len(cols)}.")
                continue
                
            a_tag = cols[3].xpath('.//a')
            if not a_tag:
                logger.warning("Row skipped in index: Missing anchor link in the 4th column.")
                continue
                
            href = a_tag[0].get('href', '')
            data.append({
                "name": cols[0].text_content().strip(),
                "link": f"{href}&{g_language_specifier}",
                "app_id": get_appid(href)
            })
        return data

    def parse_game_file(self, content) -> tuple:
        tree = html.fromstring(content)

        tbody = get_tbody(tree)

        data = list()
        rows = tbody.xpath('.//tr')

        for row in rows:
            cols = row.xpath('.//td')
            if len(cols) < 5:
                logger.warning(f"Row skipped in game file: Expected at least 5 columns, found {len(cols)}.")
                continue
                
            path, filename = os.path.split(cols[1].text_content().strip())
            time_str = cols[3].text_content().strip()
            parsed_time = parse_time(time_str)
            logger.debug(f"Parse {filename} time '{time_str}' as '{parsed_time.isoformat()}'")
            
            a_tag = cols[4].xpath('.//a')
            if not a_tag:
                logger.warning(f"Row warning in game file '{filename}': Missing anchor link in the 5th column.")
                
            href = a_tag[0].get('href', '') if a_tag else ''
            data.append({
                "filename": filename,
                "path": path,
                "time": parsed_time,
                "link": href
            })

        has_next = tree.xpath('//a[text()="next >>"]')

        if (not has_next):
            return (data, None)
        else:
            return (data, has_next[0].get('href'))
