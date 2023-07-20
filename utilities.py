# Copyright (C) 2023 Warren Usui, MIT License
"""
Date and box score scraping utilities.
"""
from datetime import datetime
import requests
from bs4 import BeautifulSoup as bs
import pandas as pd

def fix_dates(day_value):
    """
    Convert 'yyyy-mm-dd' day_value to 'yyyymmdd' format
    """
    if '-' in day_value:
        return datetime.strptime(day_value, "%m-%d-%Y").strftime("%Y%m%d")
    return day_value

def get_box_dates(strt_date='03-30-2023'):
    """
    Return list of days this season
    """
    def get_date_range(strt_date):
        def gdr_inner(strt_seas):
            def days_so_far():
                return (datetime.now() - strt_seas).days
            return pd.date_range(strt_seas, periods=days_so_far())
        return gdr_inner(datetime.strptime(strt_date, "%m-%d-%Y"))
    return get_date_range(strt_date).strftime('%Y%m%d')

def get_box_urls(yyyymmdd):
    """
    Given date in yyyymmdd format, return a list of urls of mlb boxscores for that
    date.
    """
    def get_url_for_date(date_str):
        return requests.get(f'https://www.cbssports.com/mlb/scoreboard/{date_str}/',
                            timeout=15)
    def find_box(tag):
        if tag.has_attr('href'):
            if tag.get('href').startswith('/mlb/gametracker/boxscore/'):
                return True
        return False
    def get_soup_on_date(yyyymmdd):
        return bs(get_url_for_date(yyyymmdd).text, 'html.parser')
    def get_games_on_day(yyyymmdd):
        return get_soup_on_date(yyyymmdd).find_all(find_box)
    def filter_asg(games):
        if len(games) == 1 and 'NLA' in games[0]:
            return []
        return games
    return filter_asg(list(map(lambda a: ''.join(['https://cbssports.com',
                    a.get('href')]), get_games_on_day(yyyymmdd))))

if __name__ == "__main__":
    print(get_box_urls('20230714'))
    print(list(get_box_dates()))
