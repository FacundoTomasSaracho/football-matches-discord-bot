# ⚽ Bot Promiedos → Discord + WhatsApp

Bot que scrapea **promiedos.com.ar** y avisa los partidos de **AFA del día** por Discord y/o WhatsApp.

---

## 📦 Instalación

### 1. Requisitos
- Python 3.10 o superior

### 2. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 3. Configurar canales de notificación

```bash
cp .env.example .env
```

Editá `.env` con tus datos (podés activar uno o ambos canales):

---

## 🔔 Configurar WhatsApp (CallMeBot)

1. Guardá el número **+34 644 67 86 33** en tus contactos (ej: "CallMeBot")
2. Mandále por WhatsApp el mensaje exacto:
   ```
   I allow callmebot to send me messages
   ```
3. En unos segundos recibirás tu `apikey` por WhatsApp
4. Completá en `.env`:
   ```
   CALLMEBOT_PHONE=5491112345678   ← tu número SIN el +
   CALLMEBOT_APIKEY=123456         ← la clave que te mandaron
   ```

> El número debe incluir código de país. Argentina: `549` + número sin 0 ni 15.
> Ejemplo: si tu número es 011-1234-5678 → `5491112345678`

---

## 💬 Configurar Discord (Webhook)

1. Abrí el canal de Discord donde querés recibir los avisos
2. **Editar Canal → Integraciones → Webhooks → Nuevo Webhook**
3. Copiá la URL y pegala en `.env`:
   ```
   DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
   ```

> Podés dejar Discord vacío si solo querés WhatsApp, y viceversa.

---

## 🚀 Uso

```bash
python bot.py
```

Al iniciar el bot:
- ✅ Muestra qué canales están configurados
- 📨 Manda el resumen del día inmediatamente
- 🕗 Programa el resumen diario a las **08:00** (configurable)
- ⏰ Revisa cada minuto si hay partidos en los próximos **30 minutos** y manda recordatorio

---

## 📬 Mensajes que envía

### Resumen matutino
Todos los partidos AFA del día agrupados por liga, con estado (en vivo / próximos / finalizados) y canales de TV.

### Recordatorio (30 min antes)
Un aviso individual por cada partido próximo con liga, equipos, hora y TV.

---

## ⚙️ Variables de configuración (`.env`)

| Variable | Por defecto | Descripción |
|---|---|---|
| `DISCORD_WEBHOOK_URL` | — | URL del webhook de Discord |
| `CALLMEBOT_PHONE` | — | Tu número con código país, sin + |
| `CALLMEBOT_APIKEY` | — | Clave de CallMeBot |
| `MORNING_HOUR` | `8` | Hora del resumen matutino |
| `MORNING_MINUTE` | `0` | Minutos del resumen matutino |
| `REMINDER_MINUTES_BEFORE` | `30` | Minutos antes del partido para avisar |

---

## 🖥️ Correr en segundo plano

**Linux/Mac:**
```bash
nohup python bot.py > bot.log 2>&1 &
tail -f bot.log   # ver logs en tiempo real
```

**Windows:**
```powershell
pythonw bot.py
```

---

## 📁 Estructura del proyecto

```
promiedos-bot/
├── bot.py            ← Script principal (scheduler + envíos)
├── scraper.py        ← Scraping de Promiedos via JSON de Next.js
├── whatsapp.py       ← Integración CallMeBot
├── requirements.txt
├── .env.example      ← Plantilla de configuración
├── .env              ← Tu configuración (no subir a git)
└── README.md
```
