import sys
import os
import pathlib
import pandas as pd
import numpy as np
import json
import datetime
from matplotlib import pyplot as plt
from aax_api import AAX
from log import get_logger
from utils import save_json_object, load_json_object


logger = get_logger(__file__, 'INFO')

folder = '/trade_blotter/'
percentiles = [0.05, 0.5, 0.95]  # np.arange(10) * 0.1
contract_size_mapping = {
    # Record those with contract size not 1
    'BTCUSDTFP': 0.001,
    'BCHUSDTFP': 0.01,
    'COMPUSDTFP': 0.1,
    'ETHUSDTFP': 0.01,
}   
contract_multiplier = {
    # Record those with multiplier not 1
    'BCHUSDTFP': 0.01,
    'BTCUSDTFP': 0.001,
    'COMPUSDTFP': 0.1,
    'ETHUSDFP': 1e-6,
    'ETHUSDTFP': 0.01
}
settlement_type_mapping = {
    # Record those with settlement type not VANILLA
    'BTCUSDFP': 'INVERSE',
    'ETHUSDFP': 'QUANTO'
}
settlement_currency_mapping = {
    # Record those that are QUANTO
    'ETHUSDFP': 'BTC'
}
max_leverage = {
    # Record those with max_leverage not equal 5
}
to_curs = ['BTC', 'USDT']


def load_settlement_trade_blotter(from_date_str, to_date_str, symbols_include=None, symbols_exclude=None):
    """date_str is YYYYMMDD"""
    trades = pd.DataFrame()
    
    dates = pd.date_range(from_date_str, to_date_str, freq='D')
    for date_dt in dates:
        logger.debug(f'Loading trade blotter on {date_dt.date()}')
        
        start_date = str(date_dt).replace(':', '_')
        end_date = str(date_dt + datetime.timedelta(days=1)).replace(':', '_')
        
        fp = folder + f'{date_dt:%Y}/{date_dt:%m}/' + f'10KM_trade_blotter_{start_date}_{end_date}.csv'
    
        try:
            trade_blotter = pd.read_csv(fp)
        except FileNotFoundError:
            logger.info(f'Could not find {fp}')
            continue

        if symbols_include:
            trade_blotter = trade_blotter[trade_blotter['SYMBOL'].isin(symbols_include)]
            
        if symbols_exclude:
            trade_blotter = trade_blotter[~trade_blotter['SYMBOL'].isin(symbols_exclude)]

        trade_blotter['SIDED_QTY'] = trade_blotter['QTY'] * trade_blotter['DIRECTION'].apply(
            lambda direction: 1 if direction == 'BUY' else -1)
        
        # Contract size
        trade_blotter['CONTRACT_SIZE'] = trade_blotter['SYMBOL'].apply(
            lambda symbol: contract_size_mapping.get(symbol, 1))
        
        # Multiplier
        trade_blotter['MULTIPLIER'] = trade_blotter['SYMBOL'].apply(
            lambda symbol: contract_multiplier.get(symbol, 1))
        
        # Settlement type
        trade_blotter['SETTLE_TYPE'] = trade_blotter['SYMBOL'].apply(
            lambda symbol: settlement_type_mapping.get(symbol, 'VANILLA'))
        
        # Settlement currency
        trade_blotter['SETTLE_CUR'] = trade_blotter['QUOTE']
        cond = trade_blotter['SETTLE_TYPE'] == 'INVERSE'
        trade_blotter.loc[cond, 'SETTLE_CUR'] = trade_blotter.loc[cond, 'BASE']
        cond = trade_blotter['SETTLE_TYPE'] == 'QUANTO'
        trade_blotter.loc[cond, 'SETTLE_CUR'] = trade_blotter.loc[cond, 'SYMBOL'].apply(
            lambda symbol: settlement_currency_mapping.get(symbol, None))
        
        # Notional
        trade_blotter['NOTL'] = trade_blotter['QTY'] * trade_blotter['PRICE'] * trade_blotter['MULTIPLIER']
        cond = trade_blotter['SETTLE_TYPE'] == 'INVERSE'
        trade_blotter.loc[cond, 'NOTL'] = (trade_blotter.loc[cond, 'QTY'] 
                                           / trade_blotter.loc[cond, 'PRICE'] * trade_blotter.loc[cond, 'MULTIPLIER'])

        trade_blotter = trade_blotter.sort_values('TIME')
        trade_blotter['DATETIME'] = pd.to_datetime(trade_blotter['TIME'], unit='s')
        trade_blotter['DATE'] = trade_blotter['DATETIME'].dt.strftime(r'%Y-%m-%d')
        # trade_blotter = trade_blotter.set_index('DATETIME')
        
        trades = pd.concat([trades, trade_blotter], axis=0, sort=False)

    return trades


def get_spot_balance(trades):
    spot_trades = trades[trades['TYPE'] == 'spot'].copy()

    base_qty = spot_trades[spot_trades['DIRECTION'] == 'BUY'].groupby(['DATE', 'BASE'])['QTY'].sum()
    base_qty = base_qty.unstack(level='BASE', fill_value=0)
    
    quote_qty = spot_trades[spot_trades['DIRECTION'] == 'SELL'].groupby(['DATE', 'QUOTE'])['NOTL'].sum()
    quote_qty = quote_qty.unstack(level='QUOTE', fill_value=0)
    
    spot_balance = base_qty.add(quote_qty, fill_value=0)
    
    return spot_balance


def get_spot_balance_percentiles(spot_balance, percentiles=[0.05, 0.1, 0.2, 0.5, 0.8, 0.9, 0.95]):
    percentiles_str = [f'{int(pct * 100)}%' for pct in percentiles]
    spot_balance_percentiles = spot_balance.describe(percentiles=percentiles).loc[percentiles_str,:].T.rename(
        columns={p: p + '_volume' for p in percentiles_str})
    spot_balance_percentiles.index.name = 'currency'
    return spot_balance_percentiles


def get_base_and_quote_currency(symbol):
    symbol = symbol[:-2] if symbol[-2:] == 'FP' else symbol

    if symbol[-4:] in ['USDT']:
        return symbol[:-4], symbol[-4:]
    elif symbol[-3:] in ['BTC', 'ETH', 'USD']:
        return symbol[:-3], symbol[-3:]


def get_futures_volume_percentiles(
        trades, 
        percentiles = [0.05, 0.1, 0.2, 0.5, 0.8, 0.9, 0.95],
        is_notional=True):
    col = 'NOTL' if is_notional else 'QTY'
    
    volume = trades[trades['TYPE'] == 'futures'].groupby(['DATE', 'SYMBOL'])[col].sum().unstack(
        level='SYMBOL', fill_value=0)
    
    percentiles_str = [f'{int(pct * 100)}%' for pct in percentiles]

    col_name = '_notional' if is_notional else '_volume'
    volume_percentiles = volume.describe(percentiles=percentiles).loc[percentiles_str,:].T.rename(
        columns={p: p + col_name for p in percentiles_str})
    
    volume_percentiles = pd.concat([volume_percentiles, 
                                    trades.groupby('SYMBOL')[['MULTIPLIER', 'SETTLE_TYPE', 'SETTLE_CUR']].last()],
                                   axis=1, join='inner')
    
    return volume_percentiles
    

def get_futures_capital(notional_percentiles):
    capital = notional_percentiles.copy()
    
    capital['max_leverage'] = capital.index.map(lambda symbol: max_leverage.get(symbol, 5.))
    
    notional_columns = [col for col in notional_percentiles if '%_notional' in col]
    for col in notional_columns:
        capital_col = col.replace('%_notional', '%_capital')
        capital[capital_col] = capital[col] * 2 / capital['max_leverage']
    
    capital_columns = [col for col in capital if f'%_capital' in col]
    capital = capital.groupby('SETTLE_CUR')[capital_columns].sum()

    return capital


def main():
    date = sys.argv[1][:-2]  # UTC date YYYYMMDD

    logger.info(f'Perform IMS analysis on {date}...')

    save_folder = "/home/mm/atom_data/restart/processed_data/ims_analysis/"+date[0:4]+"/"+date[4:6]+"/"+date
    os.makedirs(save_folder, exist_ok=True)

    # Load the latest trade blotters for a month, excluding AABUSDT
    logger.info('Loading trade blotter...')

    end_date_str = (datetime.datetime.strptime(date, r'%Y%m%d') - datetime.timedelta(days=1)).strftime(r'%Y%m%d')
    from_date_str = (datetime.datetime.strptime(date, r'%Y%m%d') - datetime.timedelta(days=30)).strftime(r'%Y%m%d')

    trades = load_settlement_trade_blotter(from_date_str, end_date_str, symbols_exclude=['AABUSDT'])


    # Load the rates_USDT and rates_BTC
    rates_dict = {}
    for to_cur in to_curs:
        logger.info(f'Loading rates_{to_cur}...')
        rates_dict[to_cur] = load_json_object(save_folder+'/rates_'+to_cur+'.json')

    # Calculate spot balance percentiles 
    logger.info('Getting spot balance and percentiles...')

    spot_balance = get_spot_balance(trades)
    spot_balance_percentiles = get_spot_balance_percentiles(spot_balance, percentiles)

    # Compare total spot balance with the spot balance percentiles
    logger.info('Loading total spot balance...')
    spot_balance_total = load_json_object(save_folder+'/spot_balance_total.json')

    logger.info('Comparing total spot balance with percentiles...')
    
    spot_balance_percentiles['balance'] = spot_balance_percentiles.index.map(
        lambda currency: spot_balance_total.get(currency, 0))
    for to_cur, rates in rates_dict.items():
        spot_balance_percentiles[f'balance_in_{to_cur}'] = spot_balance_percentiles.index.map(
            lambda currency: rates.get(currency, 0)) * spot_balance_percentiles['balance']
    spot_balance_percentiles['balance >? 95%_volume'] = (
        spot_balance_percentiles['balance'] > spot_balance_percentiles['95%_volume'])

    spot_balance_percentiles.to_csv(f'{save_folder}/spot_balance_percentiles.csv')

    # Add rates to USDT and BTC for spot_balance_total
    logger.info('Loading spot total available balance...')
    spot_balance_total = pd.read_csv(save_folder+'/df_all_spot_balance.csv', index_col=0)
    for to_cur, rates in rates_dict.items():
        spot_balance_total[f'rate_to_{to_cur}'] = spot_balance_total['coin'].apply(
            lambda currency: rates.get(currency, 0))
        spot_balance_total[f'free_in_{to_cur}'] = spot_balance_total['free'] * spot_balance_total[f'rate_to_{to_cur}']
        spot_balance_total[f'used_in_{to_cur}'] = spot_balance_total['free'] * spot_balance_total[f'rate_to_{to_cur}']
        spot_balance_total[f'total_in_{to_cur}'] = spot_balance_total['free'] * spot_balance_total[f'rate_to_{to_cur}']
    
    spot_balance_total.to_csv(save_folder+'/df_all_spot_balance.csv')

    # Calculate futures volume percentiles
    logger.info('Getting futures volume percentiles...')

    volume_percentiles = get_futures_volume_percentiles(trades, percentiles, is_notional=False)
    volume_percentiles.to_csv(save_folder+'/volume_percentiles.csv')

    # Calculate futures notional percentiles
    logger.info('Getting futures notional percentiles...')

    notional_percentiles = get_futures_volume_percentiles(trades, percentiles, is_notional=True)
    notional_percentiles.to_csv(save_folder+'/notional_percentiles.csv')

    logger.info('Estimating futures capital...')

    futures_capital = get_futures_capital(notional_percentiles)

    # Compare futures total available balance with the futures capital
    logger.info('Loading futures total available balance...')

    futures_balance_total = pd.read_csv(save_folder+'/df_all_futures_balance.csv', index_col=0)

    futures_balance_by_coin = futures_balance_total.groupby('coin')['free'].sum()

    futures_capital['available_balance'] = futures_capital.index.map(
        lambda currency: futures_balance_by_coin.get(currency, 0))
    for to_cur, rates in rates_dict.items():
        futures_capital[f'available_balance_in_{to_cur}'] = futures_capital.index.map(
            lambda currency: rates.get(currency, 0)) * futures_capital['available_balance']
    futures_capital['available_balance >? 95%_capital'] = (
        futures_capital['available_balance'] > futures_capital['95%_capital'])

    futures_capital.to_csv(f'{save_folder}/futures_capital.csv')

    # Add rates to USDT and BTC for futures_balance_total
    logger.info('Loading futures total available balance...')
    futures_balance_total = pd.read_csv(save_folder+'/df_all_futures_balance.csv', index_col=0)
    for to_cur, rates in rates_dict.items():
        futures_balance_total[f'rate_to_{to_cur}'] = futures_balance_total['coin'].apply(
            lambda currency: rates.get(currency, 0))
        futures_balance_total[f'free_in_{to_cur}'] = futures_balance_total['free'] * futures_balance_total[f'rate_to_{to_cur}']
        futures_balance_total[f'used_in_{to_cur}'] = futures_balance_total['used'] * futures_balance_total[f'rate_to_{to_cur}']
        futures_balance_total[f'total_in_{to_cur}'] = futures_balance_total['total'] * futures_balance_total[f'rate_to_{to_cur}']
    
    futures_balance_total.to_csv(save_folder+'/df_all_futures_balance.csv')


if __name__ == '__main__':
    main()
