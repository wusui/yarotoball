# Copyright (C) 2023 Warren Usui, MIT License
"""
Return the stats for a game
"""
from functools import reduce
import requests
from bs4 import BeautifulSoup as bs
import pandas as pd

from cbs_get_sb_info import fmt_all_stats, stats_with_sb

def cbs_get_box_urls(yyyymmdd):
    """
    Given date in yyyymmdd format, return a list of urls of mlb boxscores for that
    date.
    """
    def get_url_for_date(date_str):
        return requests.get('https://www.cbssports.com/mlb/scoreboard/' +
                            f'{date_str}/', timeout=15)
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

def get_game_data(page):
    """
    Extract the url data into a list of tables, a soup version, and a list of
    team ids.
    """
    def ggs_pd(pd_page):
        if len(pd_page) < 8:
            return []
        return list(map(lambda a: pd_page[a], range(1,8,2)))
    def ggs_soup():
        return bs(requests.get(page, timeout=15).text, 'html.parser')
    def ggs_tm_ids():
        def find_at(sparts):
            if '@' in sparts[-1]:
                return sparts[-1]
            return sparts[-2]
        return find_at(page.strip('/').split('/')[-1].split('_')).split('@')
    return {'tables': ggs_pd(pd.read_html(page)),
            'soup': ggs_soup(), 'teams': ggs_tm_ids()}

def get_full_names_and_ids(game_data):
    """
    Extract player's full names and CBS player id's from the scraped data
    """
    def fmt_plyr_link(ext_inf):
        return [int(ext_inf[0][0]), {'fullname': ext_inf[0][1],
                                     'dispname': ext_inf[1]}]
    def get_ln_sn(ptable):
        def get_href_text(in_soup):
            def ght_inner(pinfo):
                return fmt_plyr_link([pinfo['href'].split('/')[-3:-1], pinfo.text])
            return ght_inner(in_soup.find("a"))
        return list(map(get_href_text, ptable.find_all('tr')[1:]))
    def get_links(s_links):
        if len(s_links) < 8:
            return []
        return list(map(lambda a: s_links[a], range(1,8,2)))
    def get_plr_info(soup):
        return list(map(get_ln_sn, get_links(soup.find_all('table'))))
    return get_plr_info(game_data['soup'])

def lnk_stts(all_info):
    """
    Link stats in raw stat manipulation
    """
    def lnk_stts_inner(tbl_indx):
        def stat_text(indx):
            return ['batting', 'pitching'][indx]
        def lnk_pl(indiv):
            return [all_info[0][tbl_indx][indiv][0], {'player':
                    all_info[0][tbl_indx][indiv][1], stat_text(tbl_indx // 2):
                    all_info[1]['tables'][tbl_indx].iloc[indiv].to_dict()}]
        return list(map(lnk_pl, list(range(len(all_info[0][tbl_indx])))))
    return [all_info[1], list(map(lnk_stts_inner, list(range(len(all_info[0])))))]

def get_raw_stats(page):
    """
    Extract raw stats (call nested from game extraction code)
    """
    def gg_info(game_data):
        def add_teams(players):
            def at_inner(indx):
                def add_tm_name(tm_name):
                    def tm_added(indv):
                        return [indv[0], indv[1] | {'team': tm_name}]
                    return list(map(tm_added, players[indx]))
                return add_tm_name(game_data['teams'][indx % 2])
            if not players:
                return []
            return list(map(at_inner, list(range(4))))
        return lnk_stts([add_teams(get_full_names_and_ids(game_data)), game_data])
    return gg_info(get_game_data(page))

def fmt_bat(raw_data):
    """
    Format batter statistics
    """
    def ifmt_bat(indx):
        def fix_bat(indiv):
            def fix_bat_stats(pline):
                return [indiv[0], {'player': indiv[1]['player']}, {'batting': {
                    'position': pline['HITTERS'].split(' ')[-1],
                    'AB': pline['AB'], 'R': pline['R'], 'H': pline['H'],
                    'RBI': pline['RBI'], 'HR': pline['HR']}}]
            return fix_bat_stats(indiv[1]['batting'])
        if not raw_data:
            return []
        return list(map(fix_bat, raw_data[indx]))
    return ifmt_bat(0) + ifmt_bat(1)

def fmt_pit(raw_data):
    """
    Format pitching statistics
    """
    def ifmt_pit(indx):
        def fix_pit(indiv):
            def fix_pit_stats(pline):
                def chk_ws(ws_ind):
                    if f'({ws_ind}' in pline['PITCHERS']:
                        return 1
                    return 0
                def ip_to_outs(ipval):
                    return int(ipval[0]) * 3 + int(ipval[1])
                return [indiv[0], {'player': indiv[1]['player']}, {'pitching': {
                    'Win': chk_ws('W'), 'Save': chk_ws('S'),
                    'Outs': ip_to_outs(f'{pline["IP"]}'.split('.')),
                    'WH': pline['H'] + pline['BB'], 'ER': pline['ER'],
                    'SO': pline['SO']}}]
            return fix_pit_stats(indiv[1]['pitching'])
        if not raw_data:
            return []
        return list(map(fix_pit, raw_data[indx]))
    return ifmt_pit(2) + ifmt_pit(3)

def extract_game_stats(page):
    """
    Main data extraction call
    """
    def xtract_game_stats(page):
        def xgs_inner(raw_stats):
            return fmt_all_stats([fmt_bat(raw_stats[1]),
                              fmt_pit(raw_stats[1])] +
                              [stats_with_sb(raw_stats)])
        return xgs_inner(get_raw_stats(page))
    def reorg(rdata):
        def reorg1(stat_group):
            def reorg2(indv):
                return [indv[0], indv[1] | indv[2]]
            return list(map(reorg2, stat_group))
        return list(map(reorg1, rdata))
    def xtract_ids(kdata):
        def xtract_ids2(kdata2):
            return list(map(lambda a: a[0], kdata2))
        return list(map(xtract_ids2, kdata))
    def gg_stats_inner(kdata):
        def mrg_stats(indv_id):
            def mrg_stats2(lin_data):
                def mrg_stts3(indvs):
                    if indvs[0] == indv_id:
                        return indvs[1]
                    return {}
                return [indv_id, reduce(lambda a, b : a | b, list(filter(
                        lambda a: a, list(map(mrg_stts3, lin_data)))), {})]
            return mrg_stats2(kdata[0] + kdata[1] + kdata[2])
        def gg_si2(id_value):
            return list(set(id_value[0] + id_value[1] + id_value[2]))
        return list(map(mrg_stats, gg_si2(xtract_ids(kdata))))
    return dict(gg_stats_inner(reorg(xtract_game_stats(page))))

def cbs_get_game_stats(url):
    """
    Tack game id in front of statistics.
    """
    def get_game_id(end_of_url):
        if end_of_url[1] == '':
            return end_of_url[0]
        return end_of_url[1]
    print(f'Processing {url}')
    return [get_game_id(url.split('/')[-2:]), extract_game_stats(url)]

if __name__ == "__main__":
    print(cbs_get_game_stats(
        "https://www.cbssports.com/mlb/gametracker/boxscore" + \
                    "/MLB_20230718_SF@CIN_2/"
    ))
