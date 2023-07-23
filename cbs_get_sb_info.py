# Copyright (C) 2023 Warren Usui, MIT License
"""
Stolen base data extraction.  This really seems bigger than it should be.
"""

def extract_sb(raw_soup):
    """
    Find stolen base text in boxsocre
    """
    def iex_sb(sb_data):
        if len(sb_data) == 0:
            return sb_data
        if len(sb_data) == 2:
            return [sb_data[0]]
        return sb_data[0:2]
    return list(map(lambda a: a.split('|')[0],
            iex_sb('|'.join(raw_soup.find_all(text=True)).split('|SB| - ')[1:])))

def stats_with_sb(raw_stats):
    """
    Return stolen base info in away/home order.  Return one entry if only one
    team stole any bases.  Called from cbs_get_game_stats
    """
    def fmt_sb(extracted_sb):
        def sb_list():
            def rfmt_sb(plist):
                def indv_sb(runner):
                    def indv_fmt(name_v):
                        def indv_fmt1(nm_numv):
                            if nm_numv.isnumeric():
                                return {'name': ' '.join(name_v.split()[0:-1]),
                                        'sb': int(nm_numv)}
                            return {'name': name_v, 'sb': 1}
                        return indv_fmt1(name_v.split()[-1])
                    return indv_fmt(runner.split('(')[0].strip())
                return list(map(indv_sb, plist.split(',')))
            return list(map(rfmt_sb, extracted_sb))
        return sb_list()
    return fmt_sb(extract_sb(raw_stats[0]['soup']))

def wrap_sb(stats):
    """
    Wrap display of stolen base statistics for fmt_all_stats
    """
    def id_team_dups(tlist):
        if len(tlist) == 1:
            return tlist[0][0]
        if len(tlist) == 0:
            return tlist
        return tlist[0]
    def ws_chk_tm(splayers):
        if len(stats[2]) == 2:
            return [stats[0][0][1]['player']['team'],
                    stats[0][-1][1]['player']['team']]
        def chk_pl(one_pl):
            def scan_plyrs(indiv):
                if indiv[1]['player']['dispname'] == one_pl['name']:
                    return indiv[1]['player']['team']
                return []
            return list(filter(lambda a: a, list(map(scan_plyrs, stats[0]))))
        return list(filter(lambda a: len(a) == 1, list(map(chk_pl, splayers))))
    return id_team_dups(list(map(ws_chk_tm, stats[2])))

def fmt_all_stats(stats):
    """
    Format baserunning entry and add to player's stats
    """
    def fas_inner(sb_teams):
        def handle_sb(indx):
            def conv_to_pstats(pdata):
                def cscan(each_pl):
                    if each_pl[1]['player']['dispname'] == pdata['name'] and \
                            each_pl[1]['player']['team'] == sb_teams[indx]:
                        return [each_pl[0], {'player': each_pl[1]['player']},
                                {'baserunning': {'sb': pdata['sb']}}]
                    return []
                return list(filter(lambda a: a, list(map(cscan, stats[0]))))[0]
            return list(map(conv_to_pstats, stats[2][indx]))
        if len(sb_teams) == 0:
            return []
        if len(sb_teams) == 1:
            return handle_sb(0)
        return handle_sb(0) + handle_sb(1)
    return [stats[0], stats[1], fas_inner(wrap_sb(stats))]
