import logging
from itertools import groupby

import requests
from icecream import ic

from utils import (
    format_btc, Market, ArbitrageOpportunity,
    GREEN, RED, END, BLUE, BOLD, PURPLE,
    cryptopia, bittrex, binance, Pair, PairMarkets
)


log = logging.getLogger(__name__)

logging.basicConfig(level=logging.INFO)

BASE_CURRENCIES = ['BTC', 'ETH']
TRANSFER_CURRENCIES = ['DOGE', 'LTC', 'ETH', 'DASH', 'BITB', 'XMR', 'ZEC', 'XRP', 'NEO']

pair_markets = {}

def get_or_create_pm(pair):
    for p, pm in pair_markets.items():
        if p == pair:
            return pm
    pair_markets[pair] = PairMarkets(pair=pair)
    return pair_markets[pair]

try:
    tradeogre_data = requests.get('https://tradeogre.com/api/v1/markets').json()
except e:
    logging.exception('Error retrieving markets from tradeogre.')
else:
    for market in tradeogre_data:
        pair, market_data = list(market.items())[0]
        base, asset = pair.split('-')
        pair = Pair(base, asset)

        get_or_create_pm(pair).markets.append(Market(
            pair,
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
    pair = Pair(base, asset)

    get_or_create_pm(pair).markets.append(Market(
        pair,
        market['BidPrice'],
        market['AskPrice'],
        market['LastPrice'],
        market['BaseVolume'],
        'cryptopia'
    ))

bittrex_markets = bittrex.request('public/getmarketsummaries').json()['result']
for market in bittrex_markets:
    base, asset = market['MarketName'].split('-')
    pair = Pair(base, asset)

    get_or_create_pm(pair).markets.append(Market(
        pair,
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

    pair = Pair(base, asset)

    get_or_create_pm(pair).markets.append(Market(
        pair,
        bid_price,
        ask_price,
        avg_price,
        base_qty,
        'binance'
    ))


#arb_opportunities = []
#for pair in markets_pairs:
#    if len(pair) < 2:
#        log.debug(f'length of markets too low: {pair}')
#        continue
#    if pair[0].pair.base not in BASE_CURRENCIES:
#        log.debug(f'base not in BASE_CURRENCIES: {pair[0].pair.base}')
#        continue
#
#    price_sorted = sorted(pair, key=lambda x: x.last)
#    market1 = price_sorted[0]
#    market2 = price_sorted[-1]
#
#    if market1.volume < MIN_VOLUME or market2.volume < MIN_VOLUME:
#        log.debug(f'volume too low: {market1.volume} | {market2.volume}')
#        continue
#
#    diff = abs(market1.last - market2.last)
#    diff_pct = diff / max(market1.last, market2.last)
#
#    arb_opportunities.append(ArbitrageOpportunity(market1, market2, diff_pct))

if __name__ == "__main__":
    arbs = []
    for pm in pair_markets.values():
        arb = pm.get_best_arbitrage()
        if arb:
            arbs.append(arb)
    
    for arb in sorted(arbs, key=lambda a: a.diff_pct, reverse=True)[:7]:
        arb.print()
    lowest_b = sorted(arbs, key=lambda a: a.diff_pct)
    lowest = filter(lambda y: y.pair.asset in TRANSFER_CURRENCIES and y.pair.base == 'BTC', lowest_b)

    print()
    print(f'-: {len(lowest_b)}')
    print()
    for arb in list(lowest)[:3]:
        print(f"{BOLD}{arb.pair.asset} {round(arb.diff_pct * 100, 2)}%{END}")
        print(f"{BLUE} * {arb.buy_market.exchange}: {format_btc(arb.buy_market.last)} {END}")
        print(f"{BLUE} * {arb.sell_market.exchange}: {format_btc(arb.sell_market.last)} {END}")
