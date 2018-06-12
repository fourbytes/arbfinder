import logging
from itertools import groupby

import requests
from icecream import ic

from utils import (
    format_btc, Market, ArbitrageOpportunity,
    GREEN, RED, END, BLUE, BOLD, PURPLE,
    cryptopia, bittrex, binance, Pair
)


log = logging.getLogger(__name__)

logging.basicConfig(level=logging.INFO)

MIN_VOLUME = 5
BASE_CURRENCIES = ['BTC', 'ETH']
TRANSFER_CURRENCIES = ['DOGE', 'LTC', 'ETH', 'DASH', 'BITB', 'XMR', 'ZEC', 'XRP', 'NEO']

markets = []

try:
    tradeogre_data = requests.get('https://tradeogre.com/api/v1/markets').json()
except e:
    logging.exception('Error retrieving markets from tradeogre.')
else:
    for market in tradeogre_data:
        pair, market_data = list(market.items())[0]
        base, asset = pair.split('-')

        markets.append(Market(
            Pair(base, asset),
            bid=float(market_data['bid']),
            ask=float(market_data['ask']),
            last=float(market_data['price']),
            volume=float(market_data['volume']),
            exchange='tradeogre'
        ))

cryptopia_markets = cryptopia.request('GetMarkets').json()['Data']
for market in cryptopia_markets:
    elements = market['Label'].split('/')
    asset, base = '/'.join(elements[:-1]), elements[-1]
    markets.append(Market(
        Pair(base, asset),
        market['BidPrice'],
        market['AskPrice'],
        market['LastPrice'],
        market['BaseVolume'],
        'cryptopia'
    ))

bittrex_markets = bittrex.request('public/getmarketsummaries').json()['result']
for market in bittrex_markets:
    base, asset = market['MarketName'].split('-')
    markets.append(Market(
        Pair(base, asset),
        market['Bid'],
        market['Ask'],
        market['Last'],
        market['BaseVolume'],
        'bittrex'
    ))

binance_markets = binance.request('GET', 'v1/ticker/allBookTickers').json()
for market in binance_markets:
    if market['symbol'].endswith('USDT'):
        base = 'USDT'
    else:
        base = market['symbol'][-3:]
    asset = market['symbol'][:-3]

    bid_price = float(market['bidPrice'])
    ask_price = float(market['askPrice'])

    avg_price = (bid_price + ask_price) / 2

    bid_qty = float(market['bidQty'])
    ask_qty = float(market['askQty'])
    base_qty = (((bid_qty + ask_qty) / 2) * avg_price) * 100

    markets.append(Market(
        Pair(base, asset),
        bid_price,
        ask_price,
        avg_price,
        base_qty,
        'binance'
    ))

markets_pairs = [
    list(v) for l,v in groupby(
        sorted(markets, key=lambda x: str(x.pair)),
        lambda x: str(x.pair))]

arb_opportunities = []
for pair in markets_pairs:
    if len(pair) < 2:
        log.debug(f'length of markets too low: {pair}')
        continue
    if pair[0].pair.base not in BASE_CURRENCIES:
        log.debug(f'base not in BASE_CURRENCIES: {pair[0].pair.base}')
        continue

    price_sorted = sorted(pair, key=lambda x: x.last)
    market1 = price_sorted[0]
    market2 = price_sorted[-1]

    if market1.volume < MIN_VOLUME or market2.volume < MIN_VOLUME:
        log.debug(f'volume too low: {market1.volume} | {market2.volume}')
        continue

    diff = abs(market1.last - market2.last)
    diff_pct = diff / max(market1.last, market2.last)

    arb_opportunities.append(ArbitrageOpportunity(market1, market2, diff_pct))

if __name__ == "__main__":
    f_arb_opportunities = arb_opportunities
    SRC = None # "bittrex"  #"bittrex"
    if SRC:
        f_arb_opportunities = list(
            filter(lambda a: a.market1.exchange == SRC,
                   arb_opportunities))

    for arb in sorted(f_arb_opportunities, key=lambda a: a.diff_pct, reverse=True)[:7]:
        print(f"{BOLD}{arb.pair} +{round(arb.diff_pct * 100, 2)}%{END}")
        m1color = RED if arb.market1.last > arb.market2.last else GREEN
        m2color = GREEN if arb.market1.last >= arb.market2.last else RED
        print(f" {m1color}+ {arb.market1.exchange}: last: {format_btc(arb.market1.last)} (vol {round(arb.market1.volume, 2)}BTC){END}")
        print(f" {m2color}- {arb.market2.exchange}: last: {format_btc(arb.market2.last)} (vol {round(arb.market2.volume, 2)}BTC){END}")

    lowest_b = sorted(arb_opportunities, key=lambda a: a.diff_pct)
    lowest = filter(lambda y: y.pair.asset in TRANSFER_CURRENCIES and y.pair.base == 'BTC', lowest_b)

    print()
    print(f'-: {len(lowest_b)}')
    print()
    for arb in list(lowest)[:3]:
        print(f"{BOLD}{arb.pair.asset} {round(arb.diff_pct * 100, 2)}%{END}")
        print(f"{BLUE} * {arb.market1.exchange}: {format_btc(arb.market1.last)} {END}")
        print(f"{BLUE} * {arb.market2.exchange}: {format_btc(arb.market2.last)} {END}")
