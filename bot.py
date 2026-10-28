import os
import requests

# Pobieranie tokenów bezpiecznie z ukrytych ustawień GitHuba
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

BTC_PROG_SPADKU = -8.0   # Próg spadku BTC od szczytu 30d
ZLOTO_PROG_SPADKU = -3.0 # Próg spadku Złota od szczytu 30d

def oblicz_rsi(ceny_zamkniecia, okres=14):
    if len(ceny_zamkniecia) <= okres:
        return 50.0
    zyski, straty = [], []
    ceny = list(reversed(ceny_zamkniecia[:okres + 1]))
    for i in range(1, len(ceny)):
        roznica = ceny[i] - ceny[i - 1]
        zyski.append(max(roznica, 0))
        straty.append(max(-roznica, 0))
    sredni_zysk = sum(zyski) / okres
    srednia_strata = sum(straty) / okres
    if srednia_strata == 0:
        return 100.0
    rs = sredni_zysk / srednia_strata
    return 100.0 - (100.0 / (1.0 + rs))

def pobierz_dane(symbol):
    url = f"https://api-pub.bitfinex.com/v2/candles/trade:1D:{symbol}/hist?limit=30"
    r = requests.get(url, timeout=10).json()
    if not isinstance(r, list) or len(r) == 0:
        raise ValueError(f"Błąd danych giełdowych: {r}")
    
    aktualna = float(r[0][2])
    wczorajsza = float(r[1][2])
    szczyt_30d = max(float(dzien[3]) for dzien in r)
    zamkniecia = [float(dzien[2]) for dzien in r]
    
    zmiana_24h = ((aktualna - wczorajsza) / wczorajsza) * 100
    spadek_30d = ((aktualna - szczyt_30d) / szczyt_30d) * 100
    rsi = oblicz_rsi(zamkniecia, 14)
    return aktualna, zmiana_24h, szczyt_30d, spadek_30d, rsi

def wyslij_telegram(tekst):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": CHAT_ID, "text": tekst, "parse_mode": "Markdown"}, timeout=15)

def uruchom():
    aktywa = {
        "Bitcoin (BTC)": {"symbol": "tBTCUSD", "prog": BTC_PROG_SPADKU},
        "Złoto (XAU)": {"symbol": "tXAUT:UST", "prog": ZLOTO_PROG_SPADKU}
    }
    
    for nazwa, cfg in aktywa.items():
        cena, zmiana_24h, szczyt_30d, spadek_30d, rsi = pobierz_dane(cfg["symbol"])
        
        # Warunek wysłania powiadomienia: spadek przekroczył próg LUB RSI pokazuje panikę
        if spadek_30d <= cfg["prog"] or rsi <= 35.0:
            wiadomosc = (
                f"🚨 *OKAZJA INWESTYCYJNA NA REVOLUCIE* 🚨\n"
                f"Aktywo: *{nazwa}*\n\n"
                f"💡 *Sygnał:* Wyraźna przecena na rynku! Sprawdź aplikację.\n\n"
                f"📉 *Odchylenie od szczytu (30d):* `{spadek_30d:+.2f}%`\n"
                f"⏱ *Zmiana w 24h:* `{zmiana_24h:+.2f}%`\n"
                f"🌡 *Wskaźnik paniki RSI:* `{rsi:.1f}/100`\n"
                f"💵 *Aktualna cena:* `${cena:,.2f}` *(Szczyt 30d: ${szczyt_30d:,.2f})*"
            )
            wyslij_telegram(wiadomosc)

if __name__ == "__main__":
    uruchom()
