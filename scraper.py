import requests
import json
from bs4 import BeautifulSoup
from datetime import datetime

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

# IDs y nombres de ligas argentinas en Promiedos
AFA_LEAGUE_IDS = {
    "hc":   "Liga Profesional Argentina",
    "ebj":  "Primera Nacional",
    "gea":  "Copa Argentina",
    "hcbe": "Copa de la Liga",
}

LIVE_STATUSES   = {"1°", "2°", "ET", "Pen"}
FUTURE_STATUSES = {"Prog.", "Demorado"}
FINAL_STATUSES  = {"Final", "Fin"}


def get_today_matches() -> list[dict]:
    """
    Scrapea promiedos.com.ar leyendo el JSON de Next.js embebido en la pagina.
    Retorna los partidos de ligas AFA del dia.
    """
    url = "https://www.promiedos.com.ar/"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"[ERROR] No se pudo conectar a Promiedos: {e}")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    script_tag = soup.find("script", {"id": "__NEXT_DATA__"})
    if not script_tag:
        print("[ERROR] No se encontro el JSON de Next.js en la pagina.")
        return []

    try:
        data = json.loads(script_tag.string)
        leagues = data["props"]["pageProps"]["data"]["leagues"]
    except (json.JSONDecodeError, KeyError) as e:
        print(f"[ERROR] Fallo al parsear JSON: {e}")
        return []

    matches = []
    for league in leagues:
        league_id = league.get("id", "")
        if league_id not in AFA_LEAGUE_IDS:
            continue

        league_display = AFA_LEAGUE_IDS[league_id]

        for game in league.get("games", []):
            teams = game.get("teams", [])
            if len(teams) < 2:
                continue

            local     = teams[0].get("name", "?")
            visitante = teams[1].get("name", "?")

            start_raw = game.get("start_time", "")
            hora = "Sin hora"
            try:
                dt = datetime.strptime(start_raw, "%d-%m-%Y %H:%M")
                hora = dt.strftime("%H:%M")
            except ValueError:
                pass

            status_info = game.get("status", {})
            status      = status_info.get("short_name", "")

            scores = game.get("scores")
            score_str = f"{scores[0]}-{scores[1]}" if scores and len(scores) == 2 else None

            tv_networks = game.get("tv_networks", [])
            tv_str = ", ".join(t["name"] for t in tv_networks) if tv_networks else None

            matches.append({
                "liga":      league_display,
                "local":     local,
                "visitante": visitante,
                "hora":      hora,
                "status":    status,
                "score":     score_str,
                "tv":        tv_str,
            })

    def sort_key(m):
        s = m["status"]
        if s in LIVE_STATUSES:   return (0, m["hora"])
        if s in FUTURE_STATUSES: return (1, m["hora"])
        return (2, m["hora"])

    matches.sort(key=sort_key)
    return matches


def format_matches_for_discord(matches: list[dict], title: str) -> dict:
    today = datetime.now().strftime("%d/%m/%Y")

    if not matches:
        return {
            "embeds": [{
                "title": f"⚽ {title}",
                "description": "No hay partidos de AFA programados para hoy.",
                "color": 0x3498db,
                "footer": {"text": f"Promiedos.com.ar • {today}"}
            }]
        }

    live   = [m for m in matches if m["status"] in LIVE_STATUSES]
    future = [m for m in matches if m["status"] in FUTURE_STATUSES]
    finals = [m for m in matches if m["status"] in FINAL_STATUSES]

    def _game_line(m: dict) -> str:
        if m["status"] in LIVE_STATUSES:
            score_part = f" **{m['score']}**" if m["score"] else ""
            return f"🔴 `EN VIVO` **{m['local']}**{score_part} vs **{m['visitante']}**"
        elif m["status"] in FUTURE_STATUSES:
            tv_part = f" _(📺 {m['tv']})_" if m["tv"] else ""
            return f"🕐 `{m['hora']}` — **{m['local']}** vs **{m['visitante']}**{tv_part}"
        else:
            score_part = f" `{m['score']}`" if m["score"] else ""
            return f"✅ ~~{m['hora']}~~ — {m['local']}{score_part} {m['visitante']}"

    def _group_by_liga(ml):
        g = {}
        for m in ml:
            g.setdefault(m["liga"], []).append(m)
        return g

    fields = []
    if live:
        for liga, ms in _group_by_liga(live).items():
            fields.append({"name": f"🔴 EN VIVO — {liga}", "value": "\n".join(_game_line(m) for m in ms), "inline": False})
    if future:
        for liga, ms in _group_by_liga(future).items():
            fields.append({"name": f"🏆 {liga}", "value": "\n".join(_game_line(m) for m in ms), "inline": False})
    if finals:
        for liga, ms in _group_by_liga(finals).items():
            fields.append({"name": f"✅ {liga} (Finalizados)", "value": "\n".join(_game_line(m) for m in ms), "inline": False})

    return {
        "embeds": [{
            "title": f"⚽ {title}",
            "description": f"📅 **{today}** — {len(matches)} partido(s) de AFA",
            "color": 0x1abc9c,
            "fields": fields[:25],
            "footer": {"text": "ByFacundoSaracho"}
        }]
    }


def format_reminder(match: dict) -> dict:
    tv_part = f"\n📺 **{match['tv']}**" if match.get("tv") else ""
    return {
        "embeds": [{
            "title": "⏰ ¡Partido en 30 minutos!",
            "description": (
                f"🏆 **{match['liga']}**\n\n"
                f"**{match['local']}** 🆚 **{match['visitante']}**\n"
                f"🕐 Hora: **{match['hora']}**"
                f"{tv_part}"
            ),
            "color": 0xe74c3c,
            "footer": {"text": "ByFacundoSaracho"}
        }]
    }
