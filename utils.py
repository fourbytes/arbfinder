from bitex import Bittrex, Cryptopia, Binance

from config import CRYPTOPIA_API_KEY, CRYPTOPIA_API_SECRET, BITTREX_API_KEY, BITTREX_API_SECRET


cryptopia = Cryptopia(key=CRYPTOPIA_API_KEY, secret=CRYPTOPIA_API_SECRET)
binance = Binance()
bittrex = Bittrex(key=BITTREX_API_KEY, secret=BITTREX_API_SECRET)

GREEN = '\033[92m'
RED = '\033[91m'
BLUE = '\033[34m'
BOLD = '\033[1m'
PURPLE = '\033[35m'

END = '\033[0m'


class Pair(object):
    def __init__(self, base, asset):
        self.base = base
        self.asset = asset

    def ab(self):
        return sorted([self.base, self.asset])

    #def matches(self, pair):
    #    if self.base == pair.base:
    #        return self.asset == pair.asset
    #    elif self.base == pair.asset:
    #        return self.asset == pair.base

    def __eq__(self, op):
        return op.base == self.base and op.asset == self.asset

    def __repr__(self):
        return f'Pair<{self.__str__()}>'

    def __str__(self):
        return f'{self.base}/{self.asset}'


class Exchange(object):
    def __init__(self, name):
        self.name = name
        self.markets = []

    def get_by_pair(self, pair):
        for m in markets:
            if m.pair == pair:
                return m


class Market(object):
    def __init__(self, pair: Pair, bid: float,
                 ask: float, last: float, volume: float, exchange: str):
        self.pair = pair
        self.bid = bid
        self.ask = ask
        self.last = last
        self.volume = volume
        self.exchange = exchange

    def get_ticker(self):
        return f"{self.exchange}:{self.get_pair()}"

    def __repr__(self):
        return f'Market<{repr(self.pair)} Exchange<{self.exchange}>>'


class ArbitrageOpportunity(object):
    def __init__(self, market1, market2, diff_pct):
        self.market1 = market1
        self.market2 = market2
        self.diff_pct = diff_pct
    
    @property
    def pair(self):
        return self.market1.pair


def format_btc(price):
    if price < 0.001:
        return f"{round(price/0.00000001)}sats"
    return f"{round(price, 4)}BTC"
