import matplotlib.pyplot as plt
import pandas as pd
import yfinance as yf

tickers = pd.read_csv('spy/tickers.csv', header=None)[1].tolist()

# calcola il prodotto cumulativo della media di tutti i rendimenti giornalieri
# ovvero simulare una crescita di $1 pesando equamente tutti gli attuali
# componenti dell'indice S&P 500
sim_rsp = (
    (pd.concat(
        [pd.read_csv(f"spy/{ticker}.csv", index_col='date', parse_dates=True)[
            'close'
        ].pct_change()
        for ticker in tickers],
        axis=1,
        sort=True,
    ).mean(axis=1, skipna=True) + 1)
    .cumprod()
    .rename("SIM")
)

# scarida i dati di RSP
rsp = (
    (yf.download("RSP", sim_rsp.index[0], sim_rsp.index[-1])[
        "Adj Close"
    ].pct_change() + 0.002 / 252 + 1)  # ER annuale del 0.20%
    .cumprod()
    .rename("RSP")
)

sim_rsp.plot(legend=True, title="RSP vs. Survivorship-Biased Strategy", figsize=(12, 9))
rsp.plot(legend=True)
plt.show()


import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import json

# request di una pagina
html = requests.get("https://www.ishares.com/us/products/239726/#tabsAll").content
soup = BeautifulSoup(html)

# cerca le date disponibili
holdings = soup.find("div", {"id": "holdings"})
dates_div = holdings.find_all("div", "component-date-list")[1]
dates_div.find_all("option")
dates = [option.attrs["value"] for option in dates_div.find_all("option")]

# scarica i costituenti per ogni data
constituents = pd.Series()
for date in dates:
    resp = requests.get(
        f"https://www.ishares.com/us/products/239726/ishares-core-sp-500-etf/1467271812596.ajax?tab=all&fileType=json&asOfDate={date}"
    ).content[3:]
    tickers = json.loads(resp)
    tickers = [(arr[0], arr[1]) for arr in tickers['aaData']]
    date = datetime.strptime(date, "%Y%m%d")
    constituents[date] = tickers

constituents = constituents.iloc[::-1] # inverte in ordine cronologico
constituents.head()

wiki = pd.read_csv("WIKI_PRICES.csv", parse_dates=True)
wiki = dict(tuple(wiki.groupby('ticker')))
for ticker in wiki:
    wiki[ticker].set_index("date", inplace=True)


import time
import re

def quandl_data(ticker, start, end):
    if ticker in wiki:
        df = wiki[ticker][start:end]
    else:
        ticker = fix_ticker(ticker)
        if ticker in wiki:
            df = wiki[ticker][start:end]
        else:
            return None
    df = df.drop(['open','high','low','close', 'volume','ex-dividend','split_ratio', 'ticker'], axis=1)
    df = df.rename(index=str, columns={"adj_open": "open",
                                       "adj_high": "high",
                                       "adj_low": "low",
                                       "adj_close": "close",
                                       "adj_volume": "volume"})
    return df

def yahoo_data(ticker, start, end):
    ticker = fix_ticker(ticker)
    try:
        df =yf.download(ticker, start, end)
    except:
        time.sleep(1)
        try:
            df = yf.download(ticker, start, end)
        except:
            return None
    # aggiustare i dati ohlc usando adj close
    adjfactor = df["Close"] / df["Adj Close"]
    df["Open"] /= adjfactor
    df["High"] /= adjfactor
    df["Low"] /= adjfactor
    df["Close"] = df["Adj Close"]
    df["Volume"] *= adjfactor
    df = df.drop(["Adj Close"], axis=1)
    df = df.rename(str.lower, axis='columns')
    df.index.rename('date', inplace=True)
    return df

def fix_ticker(ticker):
    rename_table = {
        "-": "LPRAX", # BlackRock LifePath Dynamic Retirement Fund
        "8686": "AFL", # AFLAC
        "4XS": "ESRX", # Express Scripts Holding Company
        "AAZ": "APC", # Anadarko Petroleum Corporation
        "AG4": "AGN", # Allergan plc
        "BFB": "BF_B", # Brown-Forman Corporation
        "BF.B": "BF_B", # Brown-Forman Corporation
        "BF/B": "BF_B", # Brown-Forman Corporation
        "BLD WI": "BLD", # TopBuild Corp.
        "BRKB": "BRK_B", # Berkshire Hathaway Inc.
        "CC WI": "CC", # The Chemours Company
        "DC7": "DFS", # Discover Financial Services
        "GGQ7": "GOOG", # Alphabet Inc. Class C
        "HNZ": "KHC", # The Kraft Heinz Company
        "LOM": "LMT", # Lockheed Martin Corp.
        "LTD": "LB", # L Brands Inc.
        "LTR": "L", # Loews Corporation
        "MPN": "MPC", # Marathon Petroleum Corp.
        "MWZ": "MET", # Metlife Inc.
        "MX4A": "CME", # CME Group Inc.
        "NCRA": "NWSA", # News Corporation
        "NTH": "NOC", # Northrop Grumman Crop.
        "PA9": "TRV", # The Travelers Companies, Inc.
        "QCI": "QCOM", # Qualcomm Inc.
        "RN7": "RF", # Regions Financial Corp
        "SLBA": "SLB", # Schlumberger Limited
        "SYF-W": "SYF", # Synchrony Financial
        "SWG": "SCHW", # The Charles Schwab Corporation
        "UAC/C": "UAA", # Under Armour Inc Class A
        "UBSFT": "UBSFY", # Ubisoft Entertainment
        "USX1": "X", # United States Steel Corporation
        "UUM": "UNM", # Unum Group
        "VISA": "V", # Visa Inc
    }
    if ticker in rename_table:
        fix = rename_table[ticker]
    else:
        fix = re.sub(r'[^A-Z]+', '', ticker)
    return fix

data = {}
skips = set()

constituents = constituents['2013-02-28':'2018-02-28']

for i in range(0, len(constituents) - 1):
    start = str(constituents.index[i].date())
    end = str((constituents.index[i + 1].to_pydatetime() - timedelta(days=1)).date())
    for company in constituents[i]:
        if company in skips:
            continue
        df = quandl_data(company[0], start, end)
        if df is None:
            df = yahoo_data(company[0], start, end)
        if df is None:
            skips.add(company)
            continue
        if company[0] in data:
            data[company[0]] = data[company[0]].append(df)
        else:
            data[company[0]] = df

for ticker, df in data.items():
    df = df.reset_index().drop_duplicates(subset='date').set_index('date')
    df.to_csv(f"survivorship-free/{fix_ticker(ticker)}.csv")
    data[ticker] = df
tickers = [fix_ticker(ticker) for ticker in data.keys()]
pd.Series(tickers).to_csv("survivorship-free/tickers.csv")


sim_rsp = (
    (pd.concat(
        [pd.read_csv(f"survivorship-free/{ticker}.csv", index_col='date', parse_dates=True)[
            'close'
        ].pct_change()
        for ticker in tickers],
        axis=1,
        sort=True,
    ).mean(axis=1, skipna=True) + 1)
    .cumprod()
    .rename("SIM")
)

rsp = (
    (yf.download("RSP", sim_rsp.index[0], sim_rsp.index[-1])[
        "Adj Close"
    ].pct_change() + 0.002 / 252 + 1)  # ER annuale del 0.20%
    .cumprod()
    .rename("RSP")
)

sim_rsp.plot(legend=True, title="RSP vs. Un-Survivorship-Biased Strategy", figsize=(12, 9))
rsp.plot(legend=True)