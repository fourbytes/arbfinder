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


class NotEnoughMarketsException(Exception):
    pass


class Pair(object):
    def __init__(self, base, asset):
        self.base = base.upper()
        self.asset = asset.upper()

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

    def __hash__(self):
        return hash(repr(self))


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
                 ask: float, last: float, volume: float, exchange: str,
                 wallet_active: bool = True):
        self.pair = pair
        self.bid = bid
        self.ask = ask
        self.last = last
        self.volume = volume
        self.exchange = exchange
        self.wallet_active = wallet_active

    def get_ticker(self):
        return f"{self.exchange}:{self.get_pair()}"

    def __repr__(self):
        return f'Market<{repr(self.pair)} Exchange<{self.exchange}>>'


class PairMarkets(object):
    def __init__(self, pair: Pair):
        self.pair = pair
        self.markets = []

    def get_acceptable_markets(self, min_volume: float = 5.0):
        return filter(lambda m: m.volume >= min_volume, self.markets)

    def get_best_arbitrage(self):
        markets_by_price = sorted(self.get_acceptable_markets(),
                                  key=lambda x: x.last)
        if len(markets_by_price) < 2:
            return None

        buy_market = markets_by_price[0]
        sell_market = markets_by_price[-1]
        mid_markets = markets_by_price[1:-1] if len(markets_by_price) >= 3 else []
        
        diff = abs(buy_market.ask - sell_market.bid)
        diff_pct = diff / abs((buy_market.ask + sell_market.bid) / 2)
        
        # Returns: tuple(Market<buy>, Market<sell>)
        return ArbitrageOpportunity(buy_market, sell_market, mid_markets, diff_pct)


class ArbitrageOpportunity(object):
    def __init__(self, buy_market: Market, sell_market: Market,
                 mid_markets: [Market], diff_pct: float):
        self.buy_market = buy_market
        self.sell_market = sell_market
        self.mid_markets = mid_markets
        self.diff_pct = diff_pct
    
    @property
    def pair(self):
        return self.buy_market.pair

    def print(self):
        if self.pair.base == 'BTC':
            format_base = format_btc
        elif self.pair.base in ('USDT', 'USD'):
            format_base = lambda v: f"{self.pair.base}${round(v, 2)}"
        else:
            format_base = lambda v: f"{v}{self.pair.base}"

        # Header
        print(f"{BOLD}{self.pair} +{round(self.diff_pct * 100, 2)}%{END}")

        # Buy Market
        print(f" {GREEN}+ {self.buy_market.exchange}: ask: {format_base(self.buy_market.ask)} (vol {format_base(round(self.buy_market.volume, 2))}){END}")
        
        for m in self.mid_markets:
            print(f" * {m.exchange}: ask: {format_base(m.ask)} (vol {format_base(round(m.volume, 2))}){END}")

        # Sell Market
        print(f" {RED}- {self.sell_market.exchange}: bid: {format_base(self.sell_market.bid)} (vol {format_base(round(self.sell_market.volume, 2))}){END}")


def format_btc(price):
    if price < 0.001:
        return f"{round(price/0.00000001)}sats"
    return f"{round(price, 4)}BTC"
