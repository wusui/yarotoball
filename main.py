# Copyright (C) 2023 Warren Usui, MIT License
"""
Main routines
"""
from datetime import datetime
import os
import json
import pandas as pd

from cbs_get_game_stats import cbs_get_game_stats, cbs_get_box_urls
from baseb_ref import br_get_game_stats, br_get_box_urls

def statdir(website):
    """
    Switch returning data directory
    """
    return {'cbs': 'cbs_stats', 'br': 'br_stats'}[website]

def box_read(website):
    """
    Switch returning game statistics routine
    """
    return {'cbs': cbs_get_game_stats, 'br': br_get_game_stats}[website]

def box_url(website):
    """
    switch returning urls of boxscores
    """
    return {'cbs': cbs_get_box_urls, 'br': br_get_box_urls}[website]

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

def update_first_empty(website):
    """
    Scan the saved stats, find the first {count} days that are not saved, and
    fill in the stats for those days
    """
    def get_day_stats(day_value):
        """
        Collect the stats for the day specified
        """
        def gds_game(url):
            return box_read(website)(url)
        return list(map(gds_game, box_url(website)(fix_dates(day_value))))
    def update_day(day_value, override=True):
        """
        Update a day's stat file
        """
        def upd_day(fname):
            if not override and os.path.exists(fname):
                return False
            with open(fname, 'w', encoding='utf-8') as ofd:
                if fname.startswith('br_stats'):
                    ofd.write(json.dumps(get_day_stats(day_value)))
                    return True
                ofd.write(json.dumps(dict(get_day_stats(day_value))))
                return True
        return upd_day(os.sep.join(
                [statdir(website), f'a{fix_dates(day_value)}.json']))
    def find_empty_dates(website):
        """
        Scan the saved stats folder for all days that do not have their data saved
        """
        def fed_mkf(bday):
            return os.sep.join([statdir(website), f'a{bday}.json'])
        def fed_inner(ifile):
            if os.path.exists(ifile):
                return False
            return True
        def cleanup(fname):
            return fname.split(os.sep)[-1].strip('.json')[1:]
        return list(map(cleanup,
                    list(filter(fed_inner, list(map(fed_mkf, get_box_dates()))))))
    def update_inner(count=1):
        list(map(update_day, find_empty_dates(website)[0:count]))
    update_inner(count=1)

if __name__ == "__main__":
    update_first_empty('br')
