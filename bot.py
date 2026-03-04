import os
import time
from datetime import datetime

import requests
import schedule
from dotenv import load_dotenv

from scraper import get_today_matches, format_matches_for_discord, format_reminder

load_dotenv()

# ── Discord ──────────────────────────────────────────────
WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "")

# ── WhatsApp / CallMeBot ─────────────────────────────────
WA_PHONE = os.getenv("CALLMEBOT_PHONE", "")  # ej: 5491112345678
WA_APIKEY = os.getenv("CALLMEBOT_APIKEY", "")  # ej: 123456

# ── Scheduler ────────────────────────────────────────────
MORNING_HOUR = int(os.getenv("MORNING_HOUR", "8"))
MORNING_MINUTE = int(os.getenv("MORNING_MINUTE", "0"))
REMINDER_MINUTES_BEFORE = int(os.getenv("REMINDER_MINUTES_BEFORE", "30"))

# Recordatorios ya enviados (para no repetir)
_sent_reminders: set[str] = set()


# ══════════════════════════════════════════════════════════
#  SENDERS
# ══════════════════════════════════════════════════════════

def send_discord(payload: dict) -> bool:
    """Envía un embed al webhook de Discord."""
    if not WEBHOOK_URL:
        print("[Discord] DISCORD_WEBHOOK_URL no configurada, saltando.")
        return False
    try:
        resp = requests.post(WEBHOOK_URL, json=payload, timeout=10)
        ok = resp.status_code in (200, 204)
        print(f"[Discord {'✅' if ok else '❌'}] HTTP {resp.status_code}")
        return ok
    except requests.RequestException as e:
        print(f"[Discord ❌] {e}")
        return False


# ══════════════════════════════════════════════════════════
#  JOBS
# ══════════════════════════════════════════════════════════

def job_morning_summary():
    """Resumen matutino: manda todos los partidos AFA del día."""
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"\n[{ts}] ── Resumen matutino ──")

    matches = get_today_matches()
    print(f"  → {len(matches)} partido(s) encontrado(s)")

    # Discord
    send_discord(format_matches_for_discord(matches, "Partidos de hoy"))


def job_check_reminders():
    """Cada minuto revisa si hay partidos próximos y manda recordatorio."""
    now = datetime.now()
    matches = get_today_matches()

    for match in matches:
        hora_str = match.get("hora", "")
        if not hora_str or hora_str == "Sin hora":
            continue
        try:
            h, m = map(int, hora_str.split(":"))
        except ValueError:
            continue

        match_time = now.replace(hour=h, minute=m, second=0, microsecond=0)
        diff_min = (match_time - now).total_seconds() / 60

        if 0 < diff_min <= REMINDER_MINUTES_BEFORE:
            key = f"{match['local']}-{match['visitante']}-{hora_str}"
            if key not in _sent_reminders:
                ts = now.strftime("%H:%M:%S")
                print(f"[{ts}] Recordatorio: {match['local']} vs {match['visitante']} a las {hora_str}")

                discord_ok = send_discord(format_reminder(match))

                if discord_ok:
                    _sent_reminders.add(key)


# ══════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════

def main():
    print("=" * 52)
    print("  🤖 Bot Promiedos → Discord + WhatsApp")
    print("=" * 52)

    # Mostrar estado de canales configurados
    discord_ok = bool(WEBHOOK_URL)

    print(f"  Discord   : {'✅ configurado' if discord_ok else '❌ no configurado'}")
    print(f"  Resumen   : {MORNING_HOUR:02d}:{MORNING_MINUTE:02d}")
    print(f"  Recordat. : {REMINDER_MINUTES_BEFORE} min antes")
    print("=" * 52)

    if not discord_ok:
        print("\n[ERROR] No hay ningún canal configurado.")
        return

    # Programar tareas
    morning_time = f"{MORNING_HOUR:02d}:{MORNING_MINUTE:02d}"
    schedule.every().day.at(morning_time).do(job_morning_summary)
    print(f"\n[OK] Resumen programado para las {morning_time}")

    schedule.every(1).minutes.do(job_check_reminders)
    print("[OK] Recordatorios: revisión cada 1 minuto")

    # Enviar resumen inmediato al arrancar
    print("\n[INFO] Enviando resumen inicial...")
    job_morning_summary()

    print("\n[INFO] Bot corriendo... Presioná Ctrl+C para detener.\n")
    while True:
        schedule.run_pending()
        time.sleep(30)


if __name__ == "__main__":
    main()
