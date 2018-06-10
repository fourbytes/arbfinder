import click
from utils import bittrex, cryptopia

BITTREX = 'bittrex'
CRYPTOPIA = 'cryptopia'

class InvalidExchange(Exception):
    pass

class AssetDoesNotExist(Exception):
    def __init__(self, exchange):
        self.exchange = exchange

def get_deposit_address(exchange, asset):
    if exchange == 'bittrex':
        return bittrex.deposit_address(asset)
    elif exchange == 'cryptopia':
        return cryptopia.request('GetDepositAddress', params={'currency': asset},
                            authenticate=True).json()
    else:
        raise InvalidExchange()

def withdraw_from(exchange, to):
    if exchange == BITTREX:
        pass
    elif exchange == CRYPTOPIA:
        pass
    else:
        raise InvalidExchange()

def get_balance(exchange, asset):
    if exchange == BITTREX:
        res = bittrex.wallet(currency=asset).json()
        print(res)
        if not res['success'] and res['message'] == 'INVALID_CURRENCY':
            raise AssetDoesNotExist(BITTREX)
        return res['result']['Available']

    elif exchange == CRYPTOPIA:
        res = cryptopia.wallet(currency=asset).json()
        print(res)
        if not res:
            raise AssetDoesNotExist(BITTREX)
        return res
    else:
        raise InvalidExchange()

@click.command()
@click.option('--src', required=True, help='Exchange to transfer from. (bittrex or cryptopia)')
@click.option('--dst', required=True, help='Exchange to transfer to.')
@click.option('--asset', required=True, help='The asset to transfer.')
@click.option('--amount', default=100, type=int, help='The amount as a percentage.')
def withdraw(src, dst, asset, amount):
    if amount < 0 or amount > 100:
        print(f'Amount ({amount}%) out of bounds, must be between 0 and 100.')
    asset = asset.strip().upper()

    src_balance = get_balance(src, asset)
    dst_balance = get_balance(dst, asset)

    print(f"{src.capitalize()} {asset} Available Balance: {src_balance}")
    print(f"{dst.capitalize()} {asset} Available Balance: {dst_balance}")

    deposit_address = get_deposit_address(dst, asset)
    print(f"Transfering from {src} to {dst} ({deposit_address})")

if __name__ == '__main__':
    withdraw()
