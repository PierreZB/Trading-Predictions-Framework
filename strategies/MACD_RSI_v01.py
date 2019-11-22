# <editor-fold desc=" ===== Import Libraries ============================== ">
from scripts.project_settings import *
from ta import *
import numpy as np

pd.set_option('display.expand_frame_repr', False)
pd.set_option('display.max_rows', 500)

# </editor-fold>

# List of files on which you want to apply this strategy
strategyFileList = [
    'EURUSD_H1_20050101_20191026',
    # 'BCOUSD_H1_20050101_20191026',
    # 'EURUSD_H1_20180101_20181231',
    # 'BCOUSD_H1_20180101_20181231',
    # 'EURUSD_M15_20040101_20191026'
]

# MACD and RSI settings
offsetMacdRsi = 1
macdFast = 12 * 3
macdSlow = 26 * 3
macdSignalSmoothing = 9 * 3
rsiSignal = 14 * 3

for strategyFile in strategyFileList:

    # <editor-fold desc=" ===== Load data ================================= ">
    # Define file paths
    inputFile = (
            str(dataRawExtracts) + "/" +
            str(strategyFile) + str(".csv")
    )

    outputFile = (
            str(dataStrategy) + "/" +
            str(strategyFile) + '_' +
            str('macdRsiV01') + '_' +
            str(str(offsetMacdRsi).zfill(4)) + '-' +
            str(str(macdFast).zfill(4)) + '-' +
            str(str(macdSlow).zfill(4)) + '-' +
            str(str(macdSignalSmoothing).zfill(4)) + '-' +
            str(str(rsiSignal).zfill(4)) +
            str(".csv")
    )

    # Load csv, sort by ID, remove duplicates based on ID, reset the index
    df = sort_deduplicate_reindex_data_frame(
        data_frame=df, index_field='ID',
        csv_source_file=inputFile
    )
    # </editor-fold>

    # <editor-fold desc=" ===== prepare roll max/min and shift values ===== ">

    # Convert timestamp from UTC to Europe/London
    df['timestamp'] = pd.to_datetime(
        pd.Series(df['timestamp']), format="%Y-%m-%dT%H:%M:%S"
    )

    # df['timestamp'] = df['timestamp'].dt.tz_convert('Europe/London')

    df['macdDiff'] = macd_diff(
        df['close'], n_fast=macdFast, n_slow=macdSlow,
        n_sign=macdSignalSmoothing, fillna=False
    )

    df['rsi'] = rsi(df['close'], n=rsiSignal, fillna=False)

    df['macdDiffOffset'] = df['macdDiff'].shift(-offsetMacdRsi)
    df['rsiOffset'] = df['rsi'].shift(-offsetMacdRsi)

    # </editor-fold>

    # <editor-fold desc=" ===== Buying/Selling/CLosing Signals ============ ">
    # Buy
    df['buyingSignal'] = np.where(
        (df['macdDiffOffset'] > 0) &
        (df['rsiOffset'] > 50),
        1,
        0
    )

    # Sell
    df['sellingSignal'] = np.where(
        (df['macdDiffOffset'] < 0) &
        (df['rsiOffset'] < 50),
        1,
        0
    )

    # df['closingSignal'] = 1

    # </editor-fold>

    # Keep only default fields
    df = df[defaultColumnsList]

    # print(df)
    df.to_csv(outputFile, index=False)
    print_time_lapsed(section=outputFile)
    # </editor-fold>

print_time_lapsed(final=True)
