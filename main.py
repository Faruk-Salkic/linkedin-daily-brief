import os
import urllib.request
import urllib.parse
import json
import xml.etree.ElementTree as ET
from datetime import datetime

# 1. Konfiguracija
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "8578372173")
DASHBOARD_URL = "https://faruk-salkic.github.io/linkedin-daily-brief/"

def fetch_rss_news(query, hl="hr", gl="HR"):
    """Dohvata najnovije vijesti sa Google News RSS"""
    encoded_query = urllib.parse.quote(query)
    url = f"https://news.google.com/rss/search?q={encoded_query}&hl={hl}&gl={gl}&ceid={gl}:{hl}"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    items = []
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            xml_data = response.read()
            root = ET.fromstring(xml_data)
            for item in root.findall(".//item")[:5]:
                title = item.find("title").text if item.find("title") is not None else ""
                link = item.find("link").text if item.find("link") is not None else ""
                items.append({"title": title, "link": link})
    except Exception as e:
        print(f"Greška pri dohvatanju RSS za {query}: {e}")
    return items

def call_gemini_json(prompt):
    """Poziva Gemini API i traži strogi JSON odgovor"""
    clean_key = GEMINI_KEY.strip() if GEMINI_KEY else ""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={clean_key}"
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }],
        "generationConfig": {
            "temperature": 0.7,
            "responseMimeType": "application/json"
        }
    }
    data = json.dumps(payload).encode('utf-8')
    headers = {
        'Content-Type': 'application/json',
        'x-goog-api-key': clean_key
    }
    
    # Probaj primarni model (gemini-2.5-flash), ako ne uspe probaj gemini-flash-latest
    for model_name in ["gemini-2.5-flash", "gemini-flash-latest"]:
        try:
            m_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={clean_key}"
            req = urllib.request.Request(m_url, data=data, headers=headers, method='POST')
            with urllib.request.urlopen(req, timeout=150) as response:
                result = json.loads(response.read().decode('utf-8'))
                raw_text = result['candidates'][0]['content']['parts'][0]['text']
                return json.loads(raw_text)
        except Exception as e:
            print(f"Upozorenje: Pokusaj sa {model_name} nije uspio ({e}). Pokusavam sledeci...")

    raise RuntimeError("Nijedan model nije vratio odgovor u predvidjenom vremenu.")

def send_telegram_summary(posts_data):
    """Šalje kratak, pregledan rezime na Telegram sa linkom do Dashboarda i dugmetom"""
    today_str = datetime.now().strftime("%d.%m.%Y")
    
    nekretnine = [p for p in posts_data if p.get("category") == "nekretnine"]
    osiguranje = [p for p in posts_data if p.get("category") == "osiguranje"]
    ai = [p for p in posts_data if p.get("category") == "ai"]

    msg = f"☀️ <b>DOBRO JUTRO FARUK!</b>\n"
    msg += f"Tvoj LinkedIn brifing za danas ({today_str}) je spreman na Dashboardu.\n\n"

    msg += "🏢 <b>NEKRETNINE (HRVATSKA):</b>\n"
    for i, p in enumerate(nekretnine[:3], 1):
        msg += f"• {p['title']}\n"

    msg += "\n🛡️ <b>OSIGURANJE (NJEMAČKA):</b>\n"
    for i, p in enumerate(osiguranje[:3], 1):
        msg += f"• {p['title']}\n"

    msg += "\n🤖 <b>AI & DIGITALIZACIJA (TVOJ AUTORITET):</b>\n"
    for i, p in enumerate(ai[:3], 1):
        msg += f"• {p['title']}\n"

    msg += f"\n👉 <b>Otvori Dashboard za kompletne postove i 1-klik copy:</b>\n{DASHBOARD_URL}"

    # Telegram API sa inline tipkom (button)
    telegram_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": msg,
        "parse_mode": "HTML",
        "disable_web_page_preview": False,
        "reply_markup": {
            "inline_keyboard": [[
                {"text": "🚀 Otvori Dashboard za Copy/Paste", "url": DASHBOARD_URL}
            ]]
        }
    }
    
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(telegram_url, data=data, headers={'Content-Type': 'application/json'}, method='POST')
    urllib.request.urlopen(req, timeout=10)

def main():
    if not GEMINI_KEY:
        raise ValueError("Nedostaje GEMINI_API_KEY environment varijabla! Postavi je u GitHub Secrets.")
    if not TELEGRAM_TOKEN:
        raise ValueError("Nedostaje TELEGRAM_BOT_TOKEN environment varijabla! Postavi je u GitHub Secrets.")

    print("Prikupljam najnovije vijesti...")
    vijesti_nekretnine = fetch_rss_news("nekretnine Hrvatska", hl="hr", gl="HR")
    vijesti_osiguranje = fetch_rss_news("Versicherung Deutschland", hl="de", gl="DE")
    vijesti_ai = fetch_rss_news("AI business automation digital transformation workflow", hl="en", gl="US")

    prompt = f"""
Ti si vrhunski B2B marketing strateg, savjetnik za digitalizaciju i LinkedIn copywriter.
Tvoj zadatak je da pripremiš po 3 ključne vijesti sa gotovim LinkedIn objavama za svaku od 3 rubrike (ukupno tačno 9 postova).
Jezik postova: BHS (za publiku na Balkanu i u dijaspori).

IZVORI VIJESTI:
Nekretnine HR: {json.dumps(vijesti_nekretnine, ensure_ascii=False)}
Osiguranje DE: {json.dumps(vijesti_osiguranje, ensure_ascii=False)}
AI & Biznis: {json.dumps(vijesti_ai, ensure_ascii=False)}

UPUTSTVA PO RUBRIKAMA:
1. category "nekretnine": 3 posta o cijenama kvadrata, novim zakonima, porezima ili investicijama u HR.
2. category "osiguranje": 3 posta o njemačkom osiguranju (premije, digitalizacija, regulative, savjeti za preduzetnike u DE).
3. category "ai": 3 posta za lični brend marketera/savjetnika:
   - KRITIČNO: NE prodajem web stranice!
   - Pozicioniraj me kao eksperta za procesnu optimizaciju, AI agente i digitalnu transformaciju malih i srednjih firmi (kako smanjiti troškove, eliminisati manuelni rad).
   - Ton: Autoritativan, edukativan, hook na početku, praktičan primjer i pitanje na kraju.
   - Dužina svakog posta: oko 100 do 150 riječi (koncizno, udarno, bez prazne priče).

VRATI ISKLJUČIVO JSON u ovom formatu:
{{
  "date": "{datetime.now().strftime('%Y-%m-%d')}",
  "date_formatted": "{datetime.now().strftime('%d. %B %Y')}",
  "posts": [
    {{
      "id": "nekretnine-1",
      "category": "nekretnine",
      "title": "Kratak i jasan naslov vijesti",
      "source_url": "link izvora ako postoji",
      "content": "Puni LinkedIn post spreman za objavu sa emotikonima, jasnim pasusima i hashtagovima"
    }}
  ]
}}
Za 'posts' vrati tačno 9 stavki (3 za 'nekretnine', 3 za 'osiguranje', 3 za 'ai').
"""
    print("Pozivam Gemini AI za strukturisane podatke...")
    data = call_gemini_json(prompt)

    # Sačuvaj u docs/data.json za Dashboard
    os.makedirs("docs", exist_ok=True)
    with open("docs/data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print("Sačuvano u docs/data.json!")

    # Pošalji Telegram rezime sa dugmetom
    print("Šaljem jutarnji sažetak na Telegram...")
    send_telegram_summary(data.get("posts", []))
    print("Uspješno završeno!")

if __name__ == "__main__":
    main()
