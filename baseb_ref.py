# Copyright (C) 2023 Warren Usui, MIT License
"""
Baseball reference parser
"""
import requests
from bs4 import Comment, BeautifulSoup as bs

def reind(indv):
    """
    Isolate unique player id (LLLLLFFNN) from shtml link
    """
    return indv.split('/')[-1].split('.')[0]

def make_number(value):
    """
    Convert character to int value (handling empty as 0)
    """
    if value == '':
        return 0
    return int(value)

def add_cols(p_dict):
    """
    Take a batter's stats and and SB and HR fields if none were set.
    """
    def add_col_inn(klist):
        def add_zero_flds(indv):
            #import pdb; pdb.set_trace()
            if 'SB' not in list(p_dict[indv]['batting'].keys()):
                return [reind(indv), {'name': p_dict[indv]['name'],
                                      'team': p_dict[indv]['team'],
                                      'position': p_dict[indv]['position'],
                                      'batting': dict(list(
                                          p_dict[indv]['batting'].items()) +
                                          [('HR', 0), ('SB',0)])
                                      }]
            return [reind(indv), p_dict[indv]]
        return dict(list(map(add_zero_flds, klist)))
    return add_col_inn(list(p_dict.keys()))

def br_get_game_stats(page):
    """
    Main section of code to parse a game's stats
    """
    def indx_to_tm(indx):
        return {1: 'visitor', 2: 'home'}[indx]
    def get_teams(tinfo):
        def gt_inner(tnames):
            return {'visitor': tnames[0], 'home': tnames[1].strip()}
        return gt_inner(tinfo.split('Box Score:')[0].split(' vs '))
    def sb_hr_data(in_text):
        def sbhr_inner(stat):
            def fsentry(astat):
                if astat.strip().endswith(stat):
                    if astat.strip().startswith(stat):
                        return [stat, '1']
                    return [stat, astat.strip()[0]]
                return [stat, '0']
            def filtsbhr(text):
                return 'SB' in text or 'HR' in text
            return list(map(fsentry, list(filter(filtsbhr, in_text.split(',')))))
        return sbhr_inner
    def xtract_tms(soup):
        def get_plists(teams):
            def get_pls(indx):
                def gen_bstat(player):
                    def got_pos(position):
                        def bparse(pstats):
                            slist1 = list(map(lambda a: [a['data-stat'],
                                        make_number(a.text)],
                                        list(filter(lambda a: a['data-stat'] in
                                        ['AB', 'H', 'R', 'RBI'], pstats))))
                            return slist1 + sb_hr_data(pstats[-1].text)('HR'
                                        ) + sb_hr_data(pstats[-1].text)('SB')
                        def stat_line(pdata):
                            return [pdata['href'], {'name': pdata.text,
                                        'team': teams[indx_to_tm(indx)],
                                        'position': position,
                                        'batting': dict(
                                            bparse(player.find_all('td')))}]
                        return stat_line(player.find('th').find('a'))
                    return got_pos(player.find('th').text.split(' ')[-1])
                def get_stt(slines):
                    def rm_spaces():
                        return list(filter(lambda a: not a.has_attr('class'),
                                           slines))
                    return list(map(gen_bstat, rm_spaces()))
                return get_stt(soup[0][indx].find_all('tbody')[0].find_all('tr'))
            def mk_dict(pinfo):
                return dict(pinfo[0]) | dict(pinfo[1])
            return mk_dict(list(map(get_pls, [1, 2])))
            #return merge_bp(handle_pitching(soup[0]))
        return [get_plists(get_teams(soup[1])), handle_pitching(soup[0])]
    def merge_bp(all_data):
        def mbp_inner(bat_data):
            def bp_merge(pit_data):
                def mrg_w_pit(player):
                    if player not in pit_data.keys():
                        return [player, bat_data[player]]
                    return [player, bat_data[player] |
                            {'pitching': pit_data[player]}]
                return dict(list(map(mrg_w_pit, bat_data)))
            return bp_merge(all_data[1])
        return mbp_inner(add_cols(all_data[0]))
    return merge_bp(xtract_tms(br_parse_com(page)))

def handle_pitching(raw_soup):
    """
    Parse the pitching table information
    """
    def hp_inner(pit_recs):
        def mk_one_dict(two_dicts):
            return two_dicts[0] | two_dicts[1]
        def hp_team_br(tm_info):
            def hp_plyr_br(pl_info):
                def get_ws_stats(ws_info):
                    def wls_set(wlv):
                        if f', {wlv}' in ws_info:
                            return [[wlv, 1]]
                        return [[wlv, 0]]
                    return wls_set('W') + wls_set('S')
                def get_ratio_stats(stats):
                    def mk_numeric(cstats):
                        def conv_cstat(astat):
                            def ip_to_outs(ip_chr):
                                def pinnings(iparts):
                                    return int(iparts[0]) * 3 + int(iparts[1])
                                if '.' not in ip_chr:
                                    return 3 * int(ip_chr)
                                return pinnings(ip_chr.split('.'))
                            if astat[0] == 'IP':
                                return ['Outs', ip_to_outs(astat[1])]
                            return [astat[0], int(astat[1])]
                        return list(map(conv_cstat, cstats))
                    def gss_inner(rstats):
                        return list(zip(
                                    list(map(lambda a: a['data-stat'], rstats)),
                                    list(map(lambda a: a.text, rstats))
                               ))
                    return mk_numeric(gss_inner(list(
                                        filter(lambda a: a['data-stat'] in
                                        ['IP', 'H', 'ER', 'BB', 'SO'], stats))))
                return [reind(pl_info.find('a')['href']),
                        dict(get_ws_stats(pl_info.find('th').text) +
                        get_ratio_stats(pl_info.find_all('td')))]
            return dict(list(map(hp_plyr_br, tm_info)))
        return mk_one_dict(list(map(hp_team_br, pit_recs)))
    return hp_inner(list(map(lambda a: a.find_all('tr'),
                             raw_soup[3].find_all('tbody'))))

def br_parse_com(page):
    """
    Return Beautiful Soup data for a box score and a dict naming the visiting
    and home teams.
    """
    def bggs_inner(soup):
        def bggs_uncom(com):
            def bggs_tcom(tcom):
                return list(map(lambda a: bs(a, 'html.parser'), tcom))
            return bggs_tcom(list(filter(lambda a: '<table' in a, com)))
        return [bggs_uncom(soup(text=lambda text: isinstance(text, Comment))),
                soup.find('title').text]
    return bggs_inner(bs(requests.get(page, timeout=15).text, 'html.parser'))

def br_parse_day(url):
    """
    Get a list of baseball reference box score links for this day
    """
    def findg(tag):
        if tag['href'].endswith('.shtml'):
            if tag['href'].startswith('/boxes/'):
                return True
        return False
    def make_soup():
        return bs(requests.get(url, timeout=15).text,
                  'html.parser').find_all('a', href=True)
    return list(map(lambda a: 'https://www.baseball-reference.com' +
                    a['href'], list(filter(findg, make_soup()))))


def br_get_box_urls(yyyymmdd):
    """
    Given date in yyyymmdd format, return a list of urls of mlb boxscores for that
    date.
    """
    def br_conv_date(yyyymmdd):
        return 'https://www.baseball-reference.com/boxes/?' + \
                f'year={yyyymmdd[0:4]}&month={yyyymmdd[4:6]}&day={yyyymmdd[6:8]}'

    return br_parse_day(br_conv_date(yyyymmdd))

if __name__ == "__main__":
    print(br_get_game_stats(
            'https://www.baseball-reference.com/boxes/PIT/PIT202304260.shtml'))
