# Copyright (C) 2023 Warren Usui, MIT License
"""
Main routines
"""
import os
import json
from utilities import fix_dates, get_box_urls, get_box_dates

from get_game_stats import get_game_stats

def get_day_stats(day_value):
    """
    Collect the stats for the day specified
    """
    def gds_game(url):
        return get_game_stats(url)
    return list(map(gds_game, get_box_urls(fix_dates(day_value))))

def update_day(day_value, override=True):
    """
    Update a day's stat file
    """
    def upd_day(fname):
        if not override and os.path.exists(fname):
            return False
        with open(fname, 'w', encoding='utf-8') as ofd:
            ofd.write(json.dumps(dict(get_day_stats(day_value))))
        return True
    return upd_day(os.sep.join(
            ['stats', f'a{fix_dates(day_value)}.json']))

def find_empty_dates():
    """
    Scan the saved stats folder for all days that do not have their data saved
    """
    def fed_mkf(bday):
        return os.sep.join(['stats', f'a{bday}.json'])
    def fed_inner(ifile):
        if os.path.exists(ifile):
            return False
        return True
    def cleanup(fname):
        return fname.split(os.sep)[-1].strip('.json')[1:]
    return list(map(cleanup,
                    list(filter(fed_inner, list(map(fed_mkf, get_box_dates()))))))

def update_first_empty(count=1):
    """
    Scan the saved stats, find the first {count} days that are not saved, and
    fill in the stats for those days
    """
    list(map(update_day, find_empty_dates()[0:count]))

if __name__ == "__main__":
    update_first_empty(count=3)
