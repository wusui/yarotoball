import requests
from bs4 import BeautifulSoup as bs

def br_get_game_stats(page):
    import pdb; pdb.set_trace()
    pass

def br_conv_date(yyyymmdd):
    return 'https://www.baseball-reference.com/boxes/?' + \
            f'year={yyyymmdd[0:4]}&month={yyyymmdd[4:6]}&day={yyyymmdd[6:8]}'

def br_parse_day(url):
    def findg(tag):
        if tag['href'].endswith('.shtml'):
            if tag['href'].startswith('/boxes/'):
                return True
        return False
    def make_soup():
        return bs(requests.get(url).text, 'html.parser').find_all('a', href=True)
    return list(map(lambda a: 'https://www.baseball-reference.com' +
                    a['href'], list(filter(findg, make_soup()))))


def br_get_box_urls(yyyymmdd):
    return br_parse_day(br_conv_date(yyyymmdd))
