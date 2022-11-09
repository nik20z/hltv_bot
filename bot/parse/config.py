main_url = 'https://www.hltv.org/'

part_links = {"events": "events#tab-ALL",
              "matches": "matches",
              "results": "results",
              "news": lambda year, month: f"/news/archive/{year}/{month}",
              "stats_teams": "stats/teams?minMapCount=0",
              "stats_players": "stats/players"  #?minMapCount=0"
              }

headers_hltv = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 OPR/77.0.4054.203 (Edition Campaign 34)'
    }

# SMILES
# 🌐
# Jordan
# Montenegro
flag_smiles = {'Albania': '🇦🇱',
               'Argentina': '🇦🇷',
               'Asia': '🌏',
               'Australia': '🇦🇺',
               'Austria': '🇦🇹',
               'Azerbaijan': '',
               'Belgium': '🇧🇪',
               'Belarus': '🇧🇾',
               'Bosnia and Herzegovina': '🇧🇦',
               'Brazil': '🇧🇷',
               'Bulgaria': '🇧🇬',
               'Canada': '🇨🇦',
               'China': '🇨🇳',
               'CIS': 'CIS',
               'Cyprus': '🇨🇾',
               'Czech Republic': '🇨🇿',
               'Denmark': '🇩🇰',
               'Estonia': '🇪🇪',
               'Europe': '🇪🇺',
               'Finland': '🇫🇮',
               'France': '🇫🇷',
               'Germany': '🇩🇪',
               'Guatemala': '🇬🇹',
               'Hong Kong': '🇭🇰',
               'Hungary': '🇭🇺',
               'Iceland': '🇮🇸',
               'Indonesia': '🇮🇩',
               'Ireland': '🇮🇪',
               'Israel': '🇮🇱',
               'Italy': '🇮🇹',
               'Japan': '🇯🇵',
               'Korea': '🇰🇷',
               'Kazakhstan': '🇰🇿',
               'Lithuania': '🇱🇹',
               'Latvia': '🇱🇻',
               'Macedonia': '🇲🇰',
               'Malaysia': '🇲🇾',
               'Malta': '🇲🇹',
               'Mexico': '🇲🇽',
               'Mongolia': '🇲🇳',
               'Netherlands': '🇳🇱',
               'New Zealand': '🇳🇿',
               'North America': '🇨🇦 🇺🇸',
               'Norway': '🇳🇴',
               'Oceania': '🇳🇿',
               'Poland': '🇵🇱',
               'Portugal': '🇵🇹',
               'Romania': '🇷🇴',
               'Russia': '🇷🇺',
               'Singapore': '🇸🇬',
               'Slovakia': '🇸🇰',
               'South Africa': '🌍',
               'South America': '🌎',
               'Serbia': '🇷🇸',
               'Spain': '🇪🇸',
               'Sweden': '🇸🇪',
               'Switzerland': '🇨🇭',
               'Taiwan': '🇹🇼',
               'Thailand': '🇹🇭',
               'Turkey': '🇹🇷',
               'Ukraine': '🇺🇦',
               'United Kingdom': '🇬🇧',
               'United States': '🇺🇸',
               'Uruguay': '🇺🇾',
               'Uzbekistan': '🇺🇿'
               }

# 🍂
seasons_smile = {
    'January': '🎄',
    'February': '❄',
    'March': '☀',
    'April': '☀',
    'May': '☀',
    'June': '🌳',
    'July': '🌳',
    'August': '🌳',
    'September': '🍁',
    'October': '🍁',
    'November': '🍁',
    'December': '⛄',
}


def get_season_smile(season):
    return seasons_smile.get(season, '')


def get_flag_smile(location):
    return flag_smiles.get(location.strip(), '🌐')
