import os
import time
import pandas as pd
from bs4 import BeautifulSoup
from seleniumbase import Driver

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "transfermarkt")
os.makedirs(DATA_DIR, exist_ok=True)

BASE_URL = "https://www.transfermarkt.com"
LEAGUE_URL = f"{BASE_URL}/premier-league/startseite/wettbewerb/GB1/plus/?saison_id=2025"

def main():
    print(f"{'='*60}")
    print("Transfermarkt Veri Cekme Islemi Basliyor (Sezon: 25/26) [SeleniumBase Aktif]")
    print(f"{'='*60}")

    print("Tarayici baslatiliyor (Cloudflare asiliyor)...")
    driver = Driver(uc=True, headless=True)

    try:
        print("1. Takim listesi cekiliyor...")
        driver.uc_open_with_reconnect(LEAGUE_URL, 4)
        time.sleep(3)
        soup = BeautifulSoup(driver.page_source, 'html.parser')

        # Takim linklerini bul
        teams = []
        table = soup.find('table', class_='items')
        if not table:
            print("HATA: Takim tablosu bulunamadi! Cloudflare engeli olabilir.")
            return

        rows = table.find('tbody').find_all('tr', recursive=False)
        for row in rows:
            tds = row.find_all('td')
            if len(tds) > 1:
                a_tag = tds[1].find('a')
                if a_tag and 'href' in a_tag.attrs:
                    team_name = a_tag.get('title', a_tag.text.strip())
                    team_url = BASE_URL + a_tag['href'].replace('spielplan', 'kader') + "/plus/1"
                    teams.append({"name": team_name, "url": team_url})

        print(f"  -> {len(teams)} takim bulundu.")
        all_players = []

        print("\n2. Takim kadrolari ve oyuncu detaylari cekiliyor...")
        for i, team in enumerate(teams, 1):
            print(f"  [{i}/{len(teams)}] {team['name']} inceleniyor...")
            driver.uc_open_with_reconnect(team['url'], 4)
            time.sleep(2)
            team_soup = BeautifulSoup(driver.page_source, 'html.parser')

            squad_table = team_soup.find('table', class_='items')
            if not squad_table:
                print(f"    -> Tablo bulunamadi, atlaniyor.")
                continue
                
            tbody = squad_table.find('tbody')
            if not tbody:
                continue

            player_rows = tbody.find_all('tr', recursive=False)
            count = 0
            for row in player_rows:
                if 'bg_blau_20' in row.get('class', []):
                    continue

                try:
                    name_td = row.find('td', class_='hauptlink')
                    player_name = name_td.text.strip() if name_td else ""

                    inline_table = row.find('table', class_='inline-table')
                    position = inline_table.find_all('tr')[1].text.strip() if inline_table and len(inline_table.find_all('tr')) > 1 else ""

                    zentriert_tds = row.find_all('td', class_='zentriert')
                    
                    dob_age = zentriert_tds[1].text.strip() if len(zentriert_tds) > 1 else ""
                    nat_img = zentriert_tds[2].find('img') if len(zentriert_tds) > 2 else None
                    nationality = nat_img.get('title') if nat_img else ""
                    height = zentriert_tds[3].text.strip() if len(zentriert_tds) > 3 else ""
                    foot = zentriert_tds[4].text.strip() if len(zentriert_tds) > 4 else ""
                    joined = zentriert_tds[5].text.strip() if len(zentriert_tds) > 5 else ""
                    contract = zentriert_tds[7].text.strip() if len(zentriert_tds) > 7 else ""

                    market_value_td = row.find('td', class_='rechts hauptlink')
                    market_value = market_value_td.text.strip() if market_value_td else ""

                    if player_name:
                        all_players.append({
                            "team": team['name'],
                            "player": player_name,
                            "position": position,
                            "dob_age": dob_age,
                            "nationality": nationality,
                            "height": height,
                            "foot": foot,
                            "joined_date": joined,
                            "contract_expires": contract,
                            "market_value": market_value
                        })
                        count += 1
                except Exception as e:
                    pass
            print(f"    -> {count} oyuncu cekildi.")

        print(f"\nToplam {len(all_players)} oyuncu verisi basariyla cekildi.")
        
        df = pd.DataFrame(all_players)
        output_path = os.path.join(DATA_DIR, "players_market_data.csv")
        df.to_csv(output_path, index=False, encoding='utf-8-sig')
        print(f"Veriler suraya kaydedildi: {output_path}")

        print(f"\n{'='*60}")
        print("Transfermarkt Veri Cekme Islemi TAMAMLANDI!")
        print(f"{'='*60}")

    finally:
        driver.quit()

if __name__ == "__main__":
    main()
