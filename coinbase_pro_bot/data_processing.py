from decimal import Decimal
import pandas as pd
import numpy as np
from datetime import datetime, timezone
from utilities import (
    STATE_DEFAULT,
    STATE_OVERBOUGHT,
    STATE_OVERSOLD,
    STATE_SELL_INDICATED,
    STATE_BUY_INDICATED,
    STATE_SELL,
    STATE_BUY,
    RSI_OVERBOUGHT_THRESHOLD,
    RSI_OVERSOLD_THRESHOLD,
)
from crypto_logger import logger


def datetime_from_timestamp(ts_str):
    return datetime.fromtimestamp(int(ts_str), tz=timezone.utc)


def decimal_from_value(value):
    d = "{:.2f}".format(value)
    return Decimal(d)


def list_to_dataframe(lst):
    rows = [[
            datetime_from_timestamp(a),
            decimal_from_value(b),
            decimal_from_value(c),
            decimal_from_value(d),
            decimal_from_value(e),
            decimal_from_value(f)
            ] for [a, b, c, d, e, f] in lst]
    rows.sort(key=lambda x: x[0])
    df = pd.DataFrame(rows, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    return df


# Check last column rsi
def check_rsi(df):
    rsi_val = df.loc[len(df)-1, 'rsi']
    logger.debug(f"RSI: {rsi_val}")
    return rsi_val


def check_macd_diff(df):
    macd_diff = df.loc[len(df)-1, 'macd']-df.loc[len(df)-1, 'macd_sig']
    logger.debug(f"Prev MACD diff: {df.loc[len(df)-2, 'macd']-df.loc[len(df)-2, 'macd_sig']}")
    logger.debug(f"MACD difference: {macd_diff}")
    return macd_diff


def determine_next_state(df, curr_state):

    next_state = curr_state

    if curr_state == STATE_DEFAULT:
        rsi_val = check_rsi(df)
        if rsi_val >= RSI_OVERBOUGHT_THRESHOLD:
            next_state = STATE_OVERBOUGHT
        elif rsi_val <= RSI_OVERSOLD_THRESHOLD:
            next_state = STATE_OVERSOLD
    elif curr_state == STATE_OVERBOUGHT:
        rsi_val = check_rsi(df)
        if rsi_val < RSI_OVERBOUGHT_THRESHOLD:
            next_state = STATE_SELL_INDICATED
    elif curr_state == STATE_OVERSOLD:
        rsi_val = check_rsi(df)
        if rsi_val > RSI_OVERSOLD_THRESHOLD:
            next_state = STATE_BUY_INDICATED
    elif curr_state == STATE_SELL_INDICATED:
        macd_diff_val = check_macd_diff(df)
        if macd_diff_val < 0:
            next_state = STATE_SELL
    elif curr_state == STATE_BUY_INDICATED:
        macd_diff_val = check_macd_diff(df)
        if macd_diff_val > 0:
            next_state = STATE_BUY
    return next_state



def calculate_ema(df, period, col_key, out_col_name):
    ema_name = out_col_name
    k = Decimal(2)/(Decimal(1) + Decimal(period))

    ema_df = pd.DataFrame([df.timestamp]).transpose()
    ema_col = [Decimal('nan') for i in range(len(ema_df))]
    ema_df[ema_name] = ema_col

    ema_df.loc[period-1, (ema_name)] = Decimal(np.mean(df[:period][col_key]))

    for i in range(period, len(ema_df)):
        ema_df.loc[i, (ema_name)] = Decimal(df.loc[i, col_key])*k + Decimal(ema_df.loc[i-1, ema_name])*(Decimal(1)-k)

    return ema_df


def calculate_macd(df):
    ema_12 = calculate_ema(df, 12, 'close', 'ema_12')
    ema_26 = calculate_ema(df, 26, 'close', 'ema_26')

    macd_df = pd.merge(ema_12, ema_26, on='timestamp')
    for i in range(len(macd_df)):
        assert isinstance((macd_df.loc[i, 'ema_12']), type(macd_df.loc[i, 'ema_26']))
    macd_df['macd'] = macd_df['ema_12']-macd_df['ema_26']

    drop_list = [i for i in range(len(macd_df)) if macd_df.loc[i, 'macd'].is_nan()]

    macd_df.drop(index=drop_list, inplace=True)
    macd_df.reset_index(drop=True, inplace=True)

    macd_signal_line = calculate_ema(macd_df, 9, 'macd', 'macd_sig')

    macd_df = pd.merge(macd_df, macd_signal_line, on='timestamp')

    macd_df['pos_hist'] = [x if x.compare(Decimal(0)) == Decimal(1) else Decimal(0) for x in macd_df.macd-macd_df.macd_sig]
    macd_df['neg_hist'] = [x if x.compare(Decimal(0)) == Decimal(-1) else Decimal(0) for x in macd_df.macd-macd_df.macd_sig]

    drop_list = [i for i in range(len(macd_df)) if macd_df.loc[i, 'macd_sig'].is_nan()]
    macd_df.drop(index=drop_list, inplace=True)
    macd_df.reset_index(drop=True, inplace=True)

    return macd_df


def calculate_rsi(df):
    period = 14
    rsi_df = pd.DataFrame([df.timestamp]).transpose()
    rsi_col = [Decimal('nan') for i in range(len(rsi_df))]
    close_data = df['close']
    rsi_df['rsi'] = rsi_col
    rsi_df['rsi_gains'] = rsi_col
    rsi_df['rsi_losses'] = rsi_col

    increase = [0]
    decrease = [0]

    for i in range(len(close_data)-1):
        change = close_data[i+1]-close_data[i]
        if change >= 0:
            increase.append(change)
            decrease.append(0)
        else:
            increase.append(0)
            decrease.append(-change)

    rsi_df.loc[period-1, 'rsi_gains'] = Decimal(np.mean([x for x in increase[:period]]))
    rsi_df.loc[period-1, 'rsi_losses'] = Decimal(np.mean([x for x in decrease[:period]]))

    for i in range(period, len(rsi_df)):
        rsi_df.loc[i, 'rsi_gains'] = (rsi_df.loc[i-1, 'rsi_gains']*(period-1)+increase[i])/period
        rsi_df.loc[i, 'rsi_losses'] = (rsi_df.loc[i-1, 'rsi_losses']*(period-1)+decrease[i])/period

    for i in range(len(rsi_df)):
        rsi_df.loc[i, 'rsi'] = 100 - (100/(1+(rsi_df.loc[i, 'rsi_gains']/rsi_df.loc[i, 'rsi_losses'])))

    drop_list = [i for i in range(len(rsi_df)) if rsi_df.loc[i, 'rsi'].is_nan()]
    rsi_df.drop(index=drop_list, inplace=True)
    rsi_df.reset_index(drop=True, inplace=True)

    return rsi_df


def gather_all_crypto_data(df):

    macd_df = calculate_macd(df)

    rsi_df = calculate_rsi(df)

    df = pd.merge(df, macd_df, on='timestamp')
    df = pd.merge(df, rsi_df, on='timestamp')

    macd_drop_list = [i for i in range(len(df)) if df.loc[i, 'macd'].is_nan()]
    rsi_drop_list = [i for i in range(len(df)) if df.loc[i, 'rsi'].is_nan()]
    df.drop(index=macd_drop_list, inplace=True)
    df.drop(index=rsi_drop_list, inplace=True)
    df.reset_index(drop=True, inplace=True)

    return df


def save_graphs(df):
    import matplotlib.pyplot as plt

    z = np.polyfit(df.index, [float(x) for x in df.close], 1)
    p = np.poly1d(z)

    fig, ax = plt.subplots(nrows=3, sharex=True)
    ax[0].xaxis_date()
    ax[1].xaxis_date()
    ax[2].xaxis_date()
    trend_line = ax[0].plot(df.timestamp, [p(x) for x in range(len(df))], color='red')
    real = ax[0].plot(df.timestamp, df.close, label='real')
    pos_bar = ax[1].bar(df.timestamp, df.pos_hist, width=.7/(len(df)), color='green')
    neg_bar = ax[1].bar(df.timestamp, df.neg_hist, width=.7/(len(df)), color='red')
    macd_sig = ax[1].plot(df.timestamp, df.macd_sig, label='macd signal', color='blue')
    macd = ax[1].plot(df.timestamp, df.macd, label='macd', color='orange')
    rsi_overbought = ax[2].plot(df.timestamp, [70 for _ in range(len(df))], color='red')
    rsi_oversold = ax[2].plot(df.timestamp, [30 for _ in range(len(df))], color='green')
    rsi = ax[2].plot(df.timestamp, df.rsi, color='black')

    # ax[0].legend((real), ('Price',))
    # ax[1].legend((macd, macd_sig, pos_bar, neg_bar), ('MACD', 'Signal Line', '', ''))
    # ax[2].legend((rsi, rsi_overbought, rsi_oversold), ('RSI', '', ''))

    plt.savefig('ETH_USD_3600.png')
