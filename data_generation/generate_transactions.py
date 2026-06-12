"""
=============================================================
SYNTHETIC TRANSACTION GENERATOR
=============================================================
Cel: Generuje realistyczne transakcje kartowe dla 1000 klientów
     na przestrzeni 12 miesięcy. Dane trafiają do RAW layer.
 
Zasady realistyczności:
  1. Geografia       — transakcje osobiste w obrębie ~100km od domicile
                       wyjazdy są sekwencyjne (stacja paliw → hotel → restauracja)
                       transakcje online (S, K) mogą być z dowolnego miejsca
                       transakcje mobilne zagraniczne oznaczone jako D (Apple/Google Pay)
  2. Spending pattern — klient ma swoje ulubione merchanty i kategorie
                        zmiana wzorca (nowy merchant + duża kwota) = anomalia
  3. Retry pattern   — nieudana transakcja → retry 2-3x, czasem odpuszcza
  4. Czas transakcji — głównie południe i popołudnie, rzadko noc
                       anomalie: klient ranny nagle aktywny o 2:00
  5. Velocity        — normalnie 1-2 txn/dzień, anomalia: 8-10/godzinę
  6. Even dollar     — okrągłe kwoty jako sygnał fraud (card testing)
  7. Test auth       — mała kwota ($1-5) bez follow-up = sprawdzenie karty
  8. Increasing amt  — $1 → $5 → $50 → $500 w krótkim czasie
  9. Merchant hist   — nowy merchant + duża kwota = anomalia
  10. Card expiry    — transakcje kartą bliską wygaśnięcia
 
Warstwy BQ:
  raw.transactions   ← ten generator
  staging.transactions_clean
  marts.transaction_scores
 
Uruchomienie:
  python generate_transactions.py --output transactions.csv
  python generate_transactions.py --output transactions.csv --upload --project your-project
 
Wymagania:
  pip install faker pandas numpy google-cloud-bigquery
=============================================================
"""
 
from __future__ import annotations
 
import argparse
import csv
import logging
import math
import random
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional
 
import numpy as np
import pandas as pd
from faker import Faker
 
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)
 
fake = Faker("en_US")
Faker.seed(42)
random.seed(42)
np.random.seed(42)
 
# =============================================================
# STAŁE — wszystkie magic numbers w jednym miejscu
# =============================================================
 
NUM_CLIENTS        = 1_000
NUM_TRANSACTIONS   = 500_000
MONTHS_BACK        = 12
START_DATE         = datetime.now() - timedelta(days=365)
END_DATE           = datetime.now()
 
# Typy płatności i ich wagi (prawdopodobieństwo użycia)
PAYMENT_TYPES = {
    "V": 0.40,   # Chip read — najczęstszy w USA
    "D": 0.25,   # Contactless NFC
    "S": 0.20,   # Stripe (online)
    "K": 0.08,   # Keyed in — rzadki, wysokie ryzyko
    "B": 0.07,   # BLIK — mniej popularny w USA ale zostawiamy
}
 
# Waluty zagraniczne dla transakcji poza USA
FOREIGN_CURRENCIES = {
    "EUR": 1.08,   # kurs USD/EUR (przybliżony)
    "GBP": 1.27,   # kurs USD/GBP
    "CAD": 0.74,   # kurs USD/CAD
    "MXN": 0.058,  # kurs USD/MXN
}
 
# Stany USA z ich głównymi miastami i współrzędnymi
# Format: (city, state, lat, lon, zip_prefix)
US_CITIES = [
    ("Houston",       "TX", 29.76,  -95.37,  "770"),
    ("Dallas",        "TX", 32.78,  -96.80,  "752"),
    ("Austin",        "TX", 30.27,  -97.74,  "787"),
    ("San Antonio",   "TX", 29.42,  -98.49,  "782"),
    ("New York",      "NY", 40.71,  -74.01,  "100"),
    ("Los Angeles",   "CA", 34.05,  -118.24, "900"),
    ("Chicago",       "IL", 41.88,  -87.63,  "606"),
    ("Phoenix",       "AZ", 33.45,  -112.07, "850"),
    ("Philadelphia",  "PA", 39.95,  -75.17,  "191"),
    ("San Antonio",   "TX", 29.42,  -98.49,  "782"),
    ("San Diego",     "CA", 32.72,  -117.16, "921"),
    ("Jacksonville",  "FL", 30.33,  -81.66,  "322"),
    ("Austin",        "TX", 30.27,  -97.74,  "787"),
    ("Fort Worth",    "TX", 32.75,  -97.33,  "761"),
    ("Columbus",      "OH", 39.96,  -82.99,  "432"),
    ("Charlotte",     "NC", 35.23,  -80.84,  "282"),
    ("Indianapolis",  "IN", 39.77,  -86.16,  "462"),
    ("Seattle",       "WA", 47.61,  -122.33, "981"),
    ("Denver",        "CO", 39.74,  -104.98, "802"),
    ("Nashville",     "TN", 36.17,  -86.78,  "372"),
    ("Las Vegas",     "NV", 36.17,  -115.14, "891"),
    ("Portland",      "OR", 45.52,  -122.68, "972"),
    ("Memphis",       "TN", 35.15,  -90.05,  "381"),
    ("Louisville",    "KY", 38.25,  -85.76,  "402"),
    ("Baltimore",     "MD", 39.29,  -76.61,  "212"),
    ("Milwaukee",     "WI", 43.04,  -87.91,  "532"),
    ("Albuquerque",   "NM", 35.08,  -106.65, "871"),
    ("Tucson",        "AZ", 32.22,  -110.97, "857"),
    ("Fresno",        "CA", 36.74,  -119.77, "937"),
    ("Sacramento",    "CA", 38.58,  -121.49, "958"),
    ("Atlanta",       "GA", 33.75,  -84.39,  "303"),
    ("Miami",         "FL", 25.77,  -80.19,  "331"),
    ("Minneapolis",   "MN", 44.98,  -93.27,  "554"),
    ("Boston",        "MA", 42.36,  -71.06,  "021"),
]
 
# Merchanty pogrupowane po kategoriach z typowymi kwotami
# Format: (nazwa, kategoria, avg_amount, std_amount)
MERCHANTS = {
    "gas_station": [
        ("Shell",           "gas_station",   45.0,  15.0),
        ("ExxonMobil",      "gas_station",   48.0,  14.0),
        ("Chevron",         "gas_station",   46.0,  13.0),
        ("BP",              "gas_station",   44.0,  12.0),
        ("Circle K",        "gas_station",   42.0,  11.0),
        ("QuikTrip",        "gas_station",   43.0,  12.0),
        ("Valero",          "gas_station",   41.0,  10.0),
        ("Sunoco",          "gas_station",   44.0,  11.0),
    ],
    "grocery": [
        ("Walmart",         "grocery",       87.0,  45.0),
        ("Target",          "grocery",       65.0,  35.0),
        ("Kroger",          "grocery",       72.0,  40.0),
        ("Costco",          "grocery",      145.0,  80.0),
        ("Whole Foods",     "grocery",       92.0,  50.0),
        ("Safeway",         "grocery",       68.0,  38.0),
        ("Publix",          "grocery",       74.0,  42.0),
        ("H-E-B",           "grocery",       80.0,  45.0),
        ("Aldi",            "grocery",       45.0,  25.0),
    ],
    "restaurant": [
        ("McDonald's",      "restaurant",    12.0,   5.0),
        ("Starbucks",       "restaurant",     7.5,   3.0),
        ("Chick-fil-A",     "restaurant",    14.0,   5.0),
        ("Chipotle",        "restaurant",    13.0,   4.0),
        ("Subway",          "restaurant",    10.0,   4.0),
        ("Taco Bell",       "restaurant",    11.0,   4.0),
        ("Burger King",     "restaurant",    12.0,   5.0),
        ("Panera Bread",    "restaurant",    14.0,   5.0),
        ("Olive Garden",    "restaurant",    35.0,  15.0),
        ("Applebee's",      "restaurant",    28.0,  12.0),
        ("Denny's",         "restaurant",    18.0,   8.0),
        ("IHOP",            "restaurant",    20.0,   9.0),
    ],
    "online_retail": [
        ("Amazon",          "online_retail", 65.0,  80.0),
        ("eBay",            "online_retail", 45.0,  60.0),
        ("Etsy",            "online_retail", 35.0,  30.0),
        ("Shopify Store",   "online_retail", 55.0,  70.0),
        ("Best Buy Online", "online_retail", 120.0, 150.0),
    ],
    "retail": [
        ("Home Depot",      "retail",        85.0,  90.0),
        ("Lowe's",          "retail",        75.0,  80.0),
        ("Best Buy",        "retail",       180.0, 200.0),
        ("Nike",            "retail",        95.0,  60.0),
        ("Apple Store",     "retail",       450.0, 350.0),
        ("TJ Maxx",         "retail",        45.0,  30.0),
        ("Ross",            "retail",        35.0,  25.0),
        ("Macy's",          "retail",        75.0,  80.0),
        ("Gap",             "retail",        55.0,  40.0),
    ],
    "pharmacy": [
        ("CVS",             "pharmacy",      28.0,  20.0),
        ("Walgreens",       "pharmacy",      25.0,  18.0),
        ("Rite Aid",        "pharmacy",      22.0,  15.0),
    ],
    "entertainment": [
        ("AMC Theaters",    "entertainment", 18.0,   8.0),
        ("Regal Cinemas",   "entertainment", 17.0,   7.0),
        ("Dave & Buster's", "entertainment", 45.0,  25.0),
        ("Bowling Alley",   "entertainment", 30.0,  15.0),
    ],
    "travel": [
        ("Marriott",        "hotel",        180.0,  80.0),
        ("Hilton",          "hotel",        195.0,  90.0),
        ("Holiday Inn",     "hotel",        120.0,  50.0),
        ("Airbnb",          "hotel",        145.0, 100.0),
        ("Delta Airlines",  "airline",      280.0, 200.0),
        ("United Airlines", "airline",      265.0, 190.0),
        ("Southwest",       "airline",      195.0, 150.0),
        ("Enterprise",      "car_rental",    85.0,  40.0),
        ("Hertz",           "car_rental",    95.0,  45.0),
    ],
    "subscription": [
        ("Netflix",         "subscription",  15.49,  0.0),
        ("Spotify",         "subscription",   9.99,  0.0),
        ("Hulu",            "subscription",  17.99,  0.0),
        ("Amazon Prime",    "subscription",  14.99,  0.0),
        ("Disney+",         "subscription",  13.99,  0.0),
        ("Apple iCloud",    "subscription",   2.99,  0.0),
    ],
    "high_risk": [
        # Kategorie które naturalnie generują więcej anomalii
        ("Luxury Jewelers",  "jewelry",     850.0, 600.0),
        ("Electronics Plus", "electronics", 650.0, 500.0),
        ("Pawn Shop",        "pawn",         95.0,  80.0),
        ("Western Union",    "wire_transfer",250.0, 200.0),
        ("MoneyGram",        "wire_transfer",220.0, 180.0),
    ],
}
 
# Zagraniczne lokalizacje do anomalii podróżnych
FOREIGN_LOCATIONS = [
    ("Paris",      "FR", 48.86,  2.35,  "750", "EUR"),
    ("London",     "GB", 51.51, -0.13,  "SW1", "GBP"),
    ("Toronto",    "CA", 43.65, -79.38, "M5V", "CAD"),
    ("Cancun",     "MX", 21.16, -86.85, "775", "MXN"),
    ("Amsterdam",  "NL", 52.37,  4.90,  "100", "EUR"),
    ("Berlin",     "DE", 52.52, 13.40,  "101", "EUR"),
    ("Rome",       "IT", 41.90, 12.50,  "001", "EUR"),
    ("Barcelona",  "ES", 41.39,  2.16,  "080", "EUR"),
]
 
# =============================================================
# DATACLASSES — struktury danych
# =============================================================
 
@dataclass
class Client:
    """Reprezentuje klienta banku z jego nawykami."""
    account_id: str
    home_city: str
    home_state: str
    home_lat: float
    home_lon: float
    home_zip_prefix: str
 
    # Nawyki czasowe — kiedy najczęściej płaci
    # "morning" / "afternoon" / "evening" / "mixed"
    time_preference: str
 
    # Ulubione kategorie merchantów (2-4 z listy)
    preferred_categories: list[str]
 
    # Karty klienta
    cards: list[dict] = field(default_factory=list)
 
    # Miesięczna aktywność — ile transakcji robi średnio
    monthly_activity: str = "medium"  # low/medium/high
 
    # Czy klient podróżuje (rzadko/często)
    traveler: bool = False
 
 
@dataclass
class Transaction:
    """Surowy rekord transakcji — RAW layer."""
    transaction_id: str
    account_id: str
    card_id: str
    card_type: str           # DEBIT / CREDIT
    card_expiry_date: str    # YYYY-MM
    merchant_id: str
    merchant_name: str
    merchant_city: str
    merchant_state: str
    merchant_country: str
    merchant_zip: str
    payment_type: str        # V/D/S/K/B
    original_amount: float
    original_currency: str
    amount_usd: float        # zawsze w USD (przewalutowanie)
    balance_after: float
    transaction_ts: str      # ISO format
    uploaded_at: str         # ISO format
    status: str              # accepted / rejected
 
 
# =============================================================
# HELPER FUNCTIONS
# =============================================================
 
def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Oblicza odległość między dwoma punktami geograficznymi w km.
    Wzór Haversine — standardowy dla małych odległości.
    """
    R = 6371  # promień Ziemi w km
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
 
    a = (math.sin(dphi / 2) ** 2
         + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2)
 
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
 
 
def nearby_location(
    base_lat: float,
    base_lon: float,
    max_km: float = 100.0
) -> tuple[float, float]:
    """
    Generuje losową lokalizację w promieniu max_km od punktu bazowego.
    Używamy do transakcji osobistych blisko domu klienta.
    """
    # Stopień szerokości ≈ 111 km, długości zależy od szerokości
    lat_delta = (random.uniform(-max_km, max_km)) / 111.0
    lon_delta = (random.uniform(-max_km, max_km)) / (111.0 * math.cos(math.radians(base_lat)))
 
    return base_lat + lat_delta, base_lon + lon_delta
 
 
def pick_payment_type(is_online: bool, is_foreign_mobile: bool = False) -> str:
    """
    Wybiera typ płatności bazując na kontekście transakcji.
 
    - Online → S (Stripe) lub K (Keyed in)
    - Zagraniczna mobilna → D (Apple/Google Pay dodana do telefonu)
    - Osobista → V/D/K/B według normalnych wag
    """
    if is_foreign_mobile:
        return "D"  # Reguła 1 — zagranica przez telefon = Contactless
 
    if is_online:
        # Online: głównie Stripe, czasem Keyed in (ryzykowny)
        return random.choices(["S", "K"], weights=[0.75, 0.25])[0]
 
    # Osobista: normalne wagi bez S
    # K (Keyed-in) celowo niska waga — wysoki risk, rzadki w praktyce
    types  = ["V", "D", "K", "B"]
    weights = [0.58, 0.32, 0.04, 0.06]
    return random.choices(types, weights=weights)[0]
 
 
def pick_transaction_time(
    date: datetime,
    time_preference: str,
    is_anomaly: bool = False
) -> datetime:
    """
    Generuje timestamp transakcji zgodnie z nawykami klienta.
 
    Reguła 4: Transakcje głównie w określonych porach.
    Anomalia: klient ranny nagle aktywny w nocy.
    """
    if is_anomaly:
        # Anomalia czasowa — środek nocy
        hour = random.randint(1, 4)
    elif time_preference == "morning":
        hour = int(np.random.normal(9, 1.5))
        hour = max(6, min(12, hour))
    elif time_preference == "afternoon":
        hour = int(np.random.normal(14, 2.0))
        hour = max(11, min(18, hour))
    elif time_preference == "evening":
        hour = int(np.random.normal(19, 1.5))
        hour = max(17, min(23, hour))
    else:  # mixed
        # Bimodalny rozkład — południe i wieczór
        if random.random() < 0.5:
            hour = int(np.random.normal(12, 1.5))
        else:
            hour = int(np.random.normal(18, 1.5))
        hour = max(8, min(22, hour))
 
    minute = random.randint(0, 59)
    second = random.randint(0, 59)
 
    return date.replace(hour=hour, minute=minute, second=second)
 
 
def generate_amount(
    merchant_tuple: tuple,
    is_even_dollar: bool = False,
    is_test_auth: bool = False,
    multiplier: float = 1.0
) -> float:
    """
    Generuje kwotę transakcji.
 
    is_even_dollar: Reguła 6 — okrągła kwota (fraud signal)
    is_test_auth:   Reguła 7 — mała kwota $1-5 (card testing)
    multiplier:     Reguła 8 — rosnące kwoty
    """
    _, _, avg, std = merchant_tuple
 
    if is_test_auth:
        return round(random.uniform(0.50, 5.00), 2)
 
    if is_even_dollar:
        # Okrągłe kwoty: $50, $100, $200, $500
        options = [50, 100, 150, 200, 250, 500, 1000]
        return float(random.choice(options))
 
    if std == 0:
        # Stałe opłaty (subskrypcje)
        return avg
 
    amount = np.random.normal(avg * multiplier, std)
    return max(0.50, round(amount, 2))
 
 
# =============================================================
# GENERATOR KLIENTÓW
# =============================================================
 
def generate_clients(n: int) -> list[Client]:
    """
    Generuje N klientów z realistycznymi profilami.
    Każdy klient dostaje:
    - Lokalizację domową (miasto + współrzędne)
    - Preferencje czasowe
    - Ulubione kategorie merchantów
    - 1-2 karty (debit zawsze, credit opcjonalnie)
    - Poziom aktywności
    - Czy podróżuje
    """
    clients = []
 
    all_categories = list(MERCHANTS.keys())
 
    for i in range(n):
        # Losowe miasto domowe
        city_data = random.choice(US_CITIES)
        city, state, lat, lon, zip_prefix = city_data
 
        # Dodaj małe odchylenie — klient nie mieszka dokładnie w centrum
        home_lat = lat + random.uniform(-0.3, 0.3)
        home_lon = lon + random.uniform(-0.3, 0.3)
 
        # Preferencje czasowe
        time_pref = random.choices(
            ["morning", "afternoon", "evening", "mixed"],
            weights=[0.20, 0.40, 0.25, 0.15]
        )[0]
 
        # Ulubione kategorie (każdy klient ma 3-5 stałych)
        num_categories = random.randint(3, 5)
        preferred = random.sample(all_categories, num_categories)
 
        # Poziom aktywności — wpływa na liczbę transakcji
        activity = random.choices(
            ["low", "medium", "high"],
            weights=[0.30, 0.50, 0.20]
        )[0]
 
        # Czy podróżuje (10% klientów to podróżnicy)
        traveler = random.random() < 0.10
 
        # Generuj karty
        cards = []
 
        # Każdy klient ma kartę debetową
        expiry_months = random.randint(3, 48)  # ważność 3-48 miesięcy od teraz
        expiry_date = (datetime.now() + timedelta(days=30 * expiry_months))
        cards.append({
            "card_id":   f"CRD_{uuid.uuid4().hex[:8].upper()}",
            "card_type": "DEBIT",
            "expiry":    expiry_date.strftime("%Y-%m"),
            "balance":   round(random.uniform(500, 15000), 2),
        })
 
        # 60% klientów ma też kartę kredytową
        if random.random() < 0.60:
            expiry_months_cc = random.randint(6, 60)
            expiry_date_cc = (datetime.now() + timedelta(days=30 * expiry_months_cc))
            cards.append({
                "card_id":   f"CRD_{uuid.uuid4().hex[:8].upper()}",
                "card_type": "CREDIT",
                "expiry":    expiry_date_cc.strftime("%Y-%m"),
                "balance":   round(random.uniform(2000, 20000), 2),
            })
 
        clients.append(Client(
            account_id=f"ACC_{i+1:05d}",
            home_city=city,
            home_state=state,
            home_lat=home_lat,
            home_lon=home_lon,
            home_zip_prefix=zip_prefix,
            time_preference=time_pref,
            preferred_categories=preferred,
            cards=cards,
            monthly_activity=activity,
            traveler=traveler,
        ))
 
        if (i + 1) % 100 == 0:
            logger.info(f"Wygenerowano {i+1}/{n} klientów")
 
    return clients
 
 
# =============================================================
# GENERATOR TRANSAKCJI
# =============================================================
 
def generate_transactions_for_client(
    client: Client,
    target_total: int,
    all_merchant_ids: dict[str, str],
) -> list[Transaction]:
    """
    Generuje transakcje dla jednego klienta.
    Większość to normalne wzorce, część to anomalie.
 
    Anomalie generowane:
    - Zmiana spending pattern (nowy merchant, duża kwota)
    - Retry pattern (declined → retry)
    - Anomalia czasowa (noc)
    - Velocity spike (card testing)
    - Podróż zagraniczna
    - Even dollar amounts
    - Increasing amount pattern
    """
    transactions = []
 
    # Ile transakcji dla tego klienta zależy od aktywności
    activity_map = {"low": 0.4, "medium": 1.0, "high": 2.0}
    multiplier = activity_map[client.monthly_activity]
    client_txn_count = int(target_total * multiplier / NUM_CLIENTS)
    client_txn_count = max(20, min(client_txn_count, 1500))
 
    # Obecne saldo — śledzimy przez życie klienta
    card = client.cards[0]  # główna karta
    balance = card["balance"]
 
    # Precompute: merchanty ulubione przez klienta
    favorite_merchants = []
    for cat in client.preferred_categories:
        if cat in MERCHANTS:
            favorite_merchants.extend(MERCHANTS[cat])
 
    # Rozkład dat — losowe daty w ciągu 12 miesięcy
    date_range_days = (END_DATE - START_DATE).days
    transaction_dates = sorted([
        START_DATE + timedelta(days=random.uniform(0, date_range_days))
        for _ in range(client_txn_count)
    ])
 
    # Czy ten klient będzie miał anomalie
    has_time_anomaly     = random.random() < 0.15   # 15% klientów
    has_velocity_anomaly = random.random() < 0.10   # 10% klientów
    has_travel_anomaly   = client.traveler or random.random() < 0.05
    has_pattern_change   = random.random() < 0.20   # 20% klientów
 
    # Wybierz losowy dzień na anomalie
    anomaly_date_idx = random.randint(
        len(transaction_dates) // 2,
        len(transaction_dates) - 1
    ) if transaction_dates else 0
 
    i = 0
    while i < len(transaction_dates):
        txn_date = transaction_dates[i]
 
        # =========================================================
        # ANOMALIA: Velocity spike — card testing
        # Reguła 5 + 7 + 8: seria małych → rosnących transakcji
        # =========================================================
        if (has_velocity_anomaly
                and i == anomaly_date_idx
                and random.random() < 0.7):
 
            logger.debug(f"Generuję velocity anomalię dla {client.account_id}")
 
            # Test auth — mała kwota sprawdzająca kartę
            test_amounts = [1.00, 2.50, 5.00]
            for j, test_amt in enumerate(test_amounts):
                ts = txn_date + timedelta(minutes=j * 3)
 
                # Wybierz losowego online merchanta
                online_merch = random.choice(MERCHANTS["online_retail"])
                m_name = online_merch[0]
                m_id   = all_merchant_ids.get(m_name, f"MERCH_{uuid.uuid4().hex[:6].upper()}")
 
                txn = Transaction(
                    transaction_id   = f"TXN_{uuid.uuid4().hex[:12].upper()}",
                    account_id       = client.account_id,
                    card_id          = card["card_id"],
                    card_type        = card["card_type"],
                    card_expiry_date = card["expiry"],
                    merchant_id      = m_id,
                    merchant_name    = m_name,
                    merchant_city    = "Online",
                    merchant_state   = "N/A",
                    merchant_country = "US",
                    merchant_zip     = "00000",
                    payment_type     = "S",  # online
                    original_amount  = test_amt,
                    original_currency= "USD",
                    amount_usd       = test_amt,
                    balance_after    = round(balance - test_amt, 2),
                    transaction_ts   = ts.isoformat(),
                    uploaded_at      = (ts + timedelta(seconds=random.randint(1, 30))).isoformat(),
                    status           = "accepted",
                )
                balance -= test_amt
                transactions.append(txn)
 
            # Po test auth — duża transakcja (increasing pattern)
            big_amount = random.choice([200.0, 500.0, 1000.0])  # even dollar
            ts_big = txn_date + timedelta(minutes=12)
            big_merch = random.choice(MERCHANTS["high_risk"])
            m_name = big_merch[0]
            m_id   = all_merchant_ids.get(m_name, f"MERCH_{uuid.uuid4().hex[:6].upper()}")
 
            txn = Transaction(
                transaction_id   = f"TXN_{uuid.uuid4().hex[:12].upper()}",
                account_id       = client.account_id,
                card_id          = card["card_id"],
                card_type        = card["card_type"],
                card_expiry_date = card["expiry"],
                merchant_id      = m_id,
                merchant_name    = m_name,
                merchant_city    = "Online",
                merchant_state   = "N/A",
                merchant_country = "US",
                merchant_zip     = "00000",
                payment_type     = "K",  # Keyed in — wysoki risk
                original_amount  = big_amount,
                original_currency= "USD",
                amount_usd       = big_amount,
                balance_after    = round(balance - big_amount, 2),
                transaction_ts   = ts_big.isoformat(),
                uploaded_at      = (ts_big + timedelta(seconds=random.randint(1, 30))).isoformat(),
                status           = "accepted",
            )
            balance -= big_amount
            transactions.append(txn)
            i += 1
            continue
 
        # =========================================================
        # ANOMALIA: Podróż zagraniczna
        # Reguła 1: zagranica = typ D (dodana karta do telefonu)
        # =========================================================
        if (has_travel_anomaly
                and i == anomaly_date_idx + 2
                and random.random() < 0.6):
 
            foreign_loc = random.choice(FOREIGN_LOCATIONS)
            f_city, f_country, f_lat, f_lon, f_zip, f_currency = foreign_loc
 
            # Seria transakcji za granicą — realny wyjazd
            travel_merchants = (
                MERCHANTS["restaurant"][:3]
                + MERCHANTS["travel"][:3]
                + MERCHANTS["retail"][:2]
            )
 
            for j in range(random.randint(3, 8)):
                ts = txn_date + timedelta(hours=j * 4)
                t_merch = random.choice(travel_merchants)
                m_name  = t_merch[0]
                m_id    = all_merchant_ids.get(m_name, f"MERCH_{uuid.uuid4().hex[:6].upper()}")
 
                amt_local = generate_amount(t_merch)
                usd_rate  = FOREIGN_CURRENCIES.get(f_currency, 1.0)
                amt_usd   = round(amt_local * usd_rate, 2)
 
                txn = Transaction(
                    transaction_id   = f"TXN_{uuid.uuid4().hex[:12].upper()}",
                    account_id       = client.account_id,
                    card_id          = card["card_id"],
                    card_type        = card["card_type"],
                    card_expiry_date = card["expiry"],
                    merchant_id      = m_id,
                    merchant_name    = m_name,
                    merchant_city    = f_city,
                    merchant_state   = "N/A",
                    merchant_country = f_country,
                    merchant_zip     = f_zip,
                    payment_type     = "D",  # Reguła 1 — zagraniczne = D
                    original_amount  = amt_local,
                    original_currency= f_currency,
                    amount_usd       = amt_usd,
                    balance_after    = round(balance - amt_usd, 2),
                    transaction_ts   = ts.isoformat(),
                    uploaded_at      = (ts + timedelta(seconds=random.randint(1, 60))).isoformat(),
                    status           = "accepted",
                )
                balance -= amt_usd
                transactions.append(txn)
 
            i += 1
            continue
 
        # =========================================================
        # NORMALNA TRANSAKCJA z okazjonalnymi mniejszymi anomaliami
        # =========================================================
 
        # Wybierz merchantа — 80% z ulubionych, 20% nowy (Reguła 2)
        is_new_merchant = (
            has_pattern_change
            and i == anomaly_date_idx + 4
            and random.random() < 0.5
        )
 
        if is_new_merchant:
            # Nowy merchant spoza ulubionych kategorii — anomalia
            all_cats = list(MERCHANTS.keys())
            new_cats = [c for c in all_cats if c not in client.preferred_categories]
            if new_cats:
                new_cat = random.choice(new_cats)
                merch_tuple = random.choice(MERCHANTS[new_cat])
            else:
                merch_tuple = random.choice(MERCHANTS["high_risk"])
        elif favorite_merchants:
            merch_tuple = random.choice(favorite_merchants)
        else:
            merch_tuple = random.choice(MERCHANTS["restaurant"])
 
        m_name     = merch_tuple[0]
        m_category = merch_tuple[1]
        m_id       = all_merchant_ids.get(m_name, f"MERCH_{uuid.uuid4().hex[:6].upper()}")
 
        # Czy online? (kategorie online lub S/K payment)
        is_online = m_category in ("online_retail", "subscription")
 
        # Lokalizacja merchantа
        if is_online:
            m_city    = "Online"
            m_state   = "N/A"
            m_country = "US"
            m_zip     = "00000"
            m_lat, m_lon = client.home_lat, client.home_lon
        else:
            # Reguła 1: osobiste transakcje w promieniu ~100km
            m_lat, m_lon = nearby_location(
                client.home_lat, client.home_lon,
                max_km=random.uniform(5, 100)
            )
            # Znajdź najbliższe miasto z listy
            nearest = min(US_CITIES, key=lambda c: haversine_km(m_lat, m_lon, c[2], c[3]))
            m_city    = nearest[0]
            m_state   = nearest[1]
            m_country = "US"
            m_zip     = f"{nearest[4]}{random.randint(10, 99)}"
 
        # Typ płatności
        payment = pick_payment_type(is_online=is_online)
 
        # Timestamp z nawykami czasowymi
        is_time_anomaly = (
            has_time_anomaly
            and i == anomaly_date_idx + 1
            and random.random() < 0.5
        )
        ts = pick_transaction_time(txn_date, client.time_preference, is_time_anomaly)
 
        # Kwota
        is_even = (payment == "K" and random.random() < 0.25)  # Keyed in → częstsze okrągłe
        amount  = generate_amount(merch_tuple, is_even_dollar=is_even)
 
        # Nowy merchant + duża kwota = anomalia (Reguła 2)
        if is_new_merchant:
            amount = amount * random.uniform(1.5, 3.0)
            amount = round(amount, 2)
 
        # =========================================================
        # ANOMALIA: Retry pattern (Reguła 3)
        # Transakcja nie przechodzi → klient próbuje ponownie
        # =========================================================
        num_attempts = 1
        if random.random() < 0.08:  # 8% transakcji ma retry
            num_attempts = random.choices([2, 3], weights=[0.70, 0.30])[0]
 
        for attempt in range(num_attempts):
            attempt_ts = ts + timedelta(minutes=attempt * random.randint(1, 5))
 
            # Pierwsze próby mogą być rejected
            if attempt < num_attempts - 1:
                # Nie ostatnia próba — może być rejected
                attempt_status = random.choices(
                    ["rejected", "accepted"],
                    weights=[0.70, 0.30]
                )[0]
            else:
                # Ostatnia próba — częściej accepted (ale nie zawsze)
                attempt_status = random.choices(
                    ["accepted", "rejected"],
                    weights=[0.75, 0.25]
                )[0]
 
            new_balance = round(balance - amount, 2) if attempt_status == "accepted" else balance
 
            txn = Transaction(
                transaction_id   = f"TXN_{uuid.uuid4().hex[:12].upper()}",
                account_id       = client.account_id,
                card_id          = card["card_id"],
                card_type        = card["card_type"],
                card_expiry_date = card["expiry"],
                merchant_id      = m_id,
                merchant_name    = m_name,
                merchant_city    = m_city,
                merchant_state   = m_state,
                merchant_country = m_country,
                merchant_zip     = m_zip,
                payment_type     = payment,
                original_amount  = round(amount, 2),
                original_currency= "USD",
                amount_usd       = round(amount, 2),
                balance_after    = new_balance,
                transaction_ts   = attempt_ts.isoformat(),
                uploaded_at      = (attempt_ts + timedelta(seconds=random.randint(1, 30))).isoformat(),
                status           = attempt_status,
            )
 
            if attempt_status == "accepted":
                balance = new_balance
 
            transactions.append(txn)
 
        i += 1
 
    return transactions
 
 
# =============================================================
# GŁÓWNA FUNKCJA
# =============================================================
 
def generate_all(output_path: str) -> pd.DataFrame:
    """
    Generuje wszystkich klientów i transakcje,
    zapisuje do CSV i zwraca DataFrame.
    """
    logger.info(f"Start generowania: {NUM_CLIENTS} klientów, ~{NUM_TRANSACTIONS} transakcji")
 
    # Krok 1: Wygeneruj klientów
    clients = generate_clients(NUM_CLIENTS)
    logger.info(f"Wygenerowano {len(clients)} klientów")
 
    # Krok 2: Stwórz słownik merchant_id (każdy merchant ma stały ID)
    all_merchant_ids: dict[str, str] = {}
    for cat_merchants in MERCHANTS.values():
        for merch_tuple in cat_merchants:
            m_name = merch_tuple[0]
            if m_name not in all_merchant_ids:
                all_merchant_ids[m_name] = f"MERCH_{uuid.uuid4().hex[:8].upper()}"
 
    # Krok 3: Generuj transakcje dla każdego klienta
    all_transactions: list[Transaction] = []
 
    for idx, client in enumerate(clients):
        client_txns = generate_transactions_for_client(
            client=client,
            target_total=NUM_TRANSACTIONS,
            all_merchant_ids=all_merchant_ids,
        )
        all_transactions.extend(client_txns)
 
        if (idx + 1) % 100 == 0:
            logger.info(
                f"Przetworzono {idx+1}/{NUM_CLIENTS} klientów "
                f"| Transakcji do tej pory: {len(all_transactions):,}"
            )
 
    logger.info(f"Łącznie wygenerowano {len(all_transactions):,} transakcji")
 
    # Krok 4: Konwertuj do DataFrame i zapisz CSV
    records = [vars(t) for t in all_transactions]
    df = pd.DataFrame(records)
 
    # Sortuj po czasie — tak jak wpływają do systemu
    df = df.sort_values("transaction_ts").reset_index(drop=True)
 
    df.to_csv(output_path, index=False, quoting=csv.QUOTE_NONNUMERIC)
    logger.info(f"Zapisano do {output_path} ({len(df):,} rekordów)")
 
    # Pokaż statystyki
    logger.info("\n=== STATYSTYKI ===")
    logger.info(f"Unikalne konta:      {df['account_id'].nunique():,}")
    logger.info(f"Unikalne karty:      {df['card_id'].nunique():,}")
    logger.info(f"Unikalne merchanty:  {df['merchant_id'].nunique():,}")
    logger.info(f"Status accepted:     {(df['status']=='accepted').sum():,}")
    logger.info(f"Status rejected:     {(df['status']=='rejected').sum():,}")
    logger.info(f"Transakcje zagraniczne: {(df['merchant_country']!='US').sum():,}")
    logger.info(f"Keyed-in (K):        {(df['payment_type']=='K').sum():,}")
 
    return df
 
 
# =============================================================
# UPLOAD DO BIGQUERY (opcjonalny)
# =============================================================
 
def upload_to_bigquery(df: pd.DataFrame, project: str, dataset: str = "raw") -> None:
    """
    Ładuje DataFrame do BigQuery raw layer.
    Wymaga: google-cloud-bigquery, uwierzytelnienia GCP.
    """
    try:
        from google.cloud import bigquery
    except ImportError:
        logger.error("Zainstaluj: pip install google-cloud-bigquery")
        return
 
    client = bigquery.Client(project=project)
    table_ref = f"{project}.{dataset}.transactions"
 
    job_config = bigquery.LoadJobConfig(
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
        autodetect=True,  # BQ sam wykryje schemat
    )
 
    logger.info(f"Ładuję {len(df):,} rekordów do {table_ref}...")
 
    job = client.load_table_from_dataframe(df, table_ref, job_config=job_config)
    job.result()  # czekaj na zakończenie
 
    logger.info(f"Upload zakończony: {table_ref}")
 
 
# =============================================================
# ENTRY POINT
# =============================================================
 
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fraud Detection — Generator danych syntetycznych")
    parser.add_argument("--output",  default="transactions.csv", help="Ścieżka do pliku CSV")
    parser.add_argument("--upload",  action="store_true",        help="Czy uploadować do BigQuery")
    parser.add_argument("--project", default=None,               help="GCP Project ID")
    parser.add_argument("--dataset", default="raw",              help="BQ dataset (default: raw)")
    args = parser.parse_args()
 
    df = generate_all(output_path=args.output)
 
    if args.upload:
        if not args.project:
            logger.error("Podaj --project gdy używasz --upload")
        else:
            upload_to_bigquery(df, project=args.project, dataset=args.dataset)
 
    logger.info("Generator zakończył pracę.")