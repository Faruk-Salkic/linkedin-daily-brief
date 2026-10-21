import os
import urllib.request
import urllib.parse
import json
import xml.etree.ElementTree as ET

# 1. Konfiguracija
GEMINI_KEY = os.environ.get("GEMINI_API_KEY", "AQ.Ab8RN6I1V-QFmP5Jxqs3yRMGIjuTmFRq0-8_MF8doY2E09zG_w")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "8961489048:AAEbkkfrqHWhf85RmbCHndpbn2W6oSiZ5yc")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "8578372173")

def fetch_rss_news(query, hl="hr", gl="HR"):
    """Dohvata najnovije vijesti sa Google News RSS bez ikakvih eksternih biblioteka"""
    encoded_query = urllib.parse.quote(query)
    url = f"https://news.google.com/rss/search?q={encoded_query}&hl={hl}&gl={gl}&ceid={gl}:{hl}"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            xml_data = response.read()
            root = ET.fromstring(xml_data)
            items = []
            for item in root.findall(".//item")[:5]:
                title = item.find("title").text if item.find("title") is not None else ""
                link = item.find("link").text if item.find("link") is not None else ""
                items.append(f"- {title}\n  Link: {link}")
            return "\n".join(items) if items else "Nema novih specifičnih vijesti za danas."
    except Exception as e:
        return f"Greška pri dohvatanju vijesti: {e}"

def call_gemini(prompt):
    """Poziva Gemini API direktno preko standardnog REST poziva"""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={GEMINI_KEY}"
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }],
        "generationConfig": {
            "temperature": 0.7
        }
    }
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'}, method='POST')
    with urllib.request.urlopen(req, timeout=90) as response:
        result = json.loads(response.read().decode('utf-8'))
        return result['candidates'][0]['content']['parts'][0]['text']

def send_telegram(text):
    """Šalje formatiran tekst u Telegram chat"""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    
    # Telegram limit je 4096 karaktera, dijelimo ako je duže
    chunk_size = 4000
    for i in range(0, len(text), chunk_size):
        chunk = text[i:i+chunk_size]
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": chunk,
            "disable_web_page_preview": True
        }
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'}, method='POST')
        urllib.request.urlopen(req, timeout=10)

def main():
    print("Prikupljam vijesti...")
    vijesti_nekretnine = fetch_rss_news("nekretnine Hrvatska", hl="hr", gl="HR")
    vijesti_osiguranje = fetch_rss_news("Versicherung Deutschland", hl="de", gl="DE")
    vijesti_ai = fetch_rss_news("AI business automation digital transformation workflow", hl="en", gl="US")

    prompt = f"""
Ti si vrhunski B2B marketing strateg, savjetnik za digitalizaciju i LinkedIn copywriter.
Tvoj zadatak je da pripremiš po 3 ključne vijesti sa gotovim LinkedIn objavama/uglovima za svaku od 3 rubrike (ukupno 3 rubrike x 3 vijesti/objave).
Jezik: BHS (za publiku na Balkanu i u dijaspori).

DANAŠNJI IZVORI VIJESTI:

[RUBRIKA 1: NEKRETNINE U HRVATSKOJ]
{vijesti_nekretnine}

[RUBRIKA 2: OSIGURANJE U NJEMAČKOJ]
{vijesti_osiguranje}

[RUBRIKA 3: AI, AUTOMATIZACIJA I DIGITALIZACIJA BIZNISA (ZA MENE KAO SAVJETNIKA)]
{vijesti_ai}

UPUTSTVO ZA STRUKTURU:
Za svaku rubriku izvuci po 3 najvažnije vijesti/teme i za svaku napiši kratak, spreman LinkedIn post:

🏢 RUBRIKA 1: NEKRETNINE HRVATSKA (3 vijesti + postovi)
- 1.1 Vijest + LinkedIn ugao
- 1.2 Vijest + LinkedIn ugao
- 1.3 Vijest + LinkedIn ugao
(Fokus: cijene kvadrata, novi zakoni, investicije, savjeti za kupce/investitore)

🛡️ RUBRIKA 2: OSIGURANJE NJEMAČKA (3 vijesti + postovi)
- 2.1 Vijest + LinkedIn ugao
- 2.2 Vijest + LinkedIn ugao
- 2.3 Vijest + LinkedIn ugao
(Fokus: promjene premija, digitalizacija, zakonske reforme, savjeti za preduzetnike i građane u DE)

🤖 RUBRIKA 3: AI & DIGITALIZACIJA BIZNISA - MOJ AUTORITET (3 teme + postovi)
- 3.1 Tema + LinkedIn post
- 3.2 Tema + LinkedIn post
- 3.3 Tema + LinkedIn post
(KRITIČNO: NE prodajem web stranice! Pozicioniraj me kao eksperta za procesnu automatizaciju, AI agente i digitalnu transformaciju malih i srednjih firmi — kako firme gube novac na manuelni rad i kako moderni alati to rješavaju. Ton: autoritativan, edukativan, sa jasnim 'hook' početkom i pitanjem na kraju za komentare.)

Formatiraj sve čisto, sa emojijima, odvojenim linijama i hashtagovima, tako da samo mogu izabrati šta želim objaviti taj dan!
"""
    print("Generišem LinkedIn postove preko Gemini AI-ja...")
    postovi = call_gemini(prompt)

    print("Šaljem na Telegram...")
    zaglavlje = "☀️ DOBRO JUTRO! Tvoj današnji LinkedIn brifing je spreman:\n\n"
    send_telegram(zaglavlje + postovi)
    print("Uspješno poslato!")

if __name__ == "__main__":
    main()
