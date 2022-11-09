from bot.parse.config import main_url


def news(id_: int, href: str):
    return f"{main_url}news/{id_}/{href}"


def join_hyphen(text: str):
    if text is not None:
        return '-'.join(text.lower().split())


def event(event_id: int, event_name: str):
    return f"{main_url}events/{event_id}/{join_hyphen(event_name)}"


def match_or_analytics(type_: str,
                       match_id: int,
                       team1_name: str,
                       team2_name: str,
                       event_name: str):
    try:
        type_text = {'M': 'matches/', 'A': 'betting/analytics/'}[type_]
        return f"{main_url}{type_text}{match_id}/{join_hyphen(team1_name)}-vs-{join_hyphen(team2_name)}-{join_hyphen(event_name)}"
    except Exception:
        return main_url


def live_broadcast(match_id: int):
    return f"{main_url}live?=matchId{match_id}"


def team(team_id: int, team_name: str):
    return f"{main_url}team/{team_id}/{join_hyphen(team_name)}"


def player(player_id: int, player_nik_name: str):
    return f"{main_url}player/{player_id}/{join_hyphen(player_nik_name)}"
