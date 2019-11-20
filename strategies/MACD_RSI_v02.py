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
macdFast = 12
macdSlow = 26
macdSignalSmoothing = 9
rsiSignal = 14

# Difference between close and open threshold per candle (per ten thousand)
threshold = 5
# numbers of periods to analyse around current candle
periodsToAnalyseForTP = 2
periodsToAnalyseForSL = 1
# set the maximum level of stop loss you can tolerate (per ten thousand)
maxSL = 1

# prepare those variables for the calculations
thresholdPerThsd = threshold / 10000
maxSLPerThsd = np.where(
    maxSL == 0,
    99_999,
    maxSL / 10000
)

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
            str('macdRsiV02') + '_' +
            str(str(offsetMacdRsi).zfill(4)) + '-' +
            str(str(macdFast).zfill(4)) + '-' +
            str(str(macdSlow).zfill(4)) + '-' +
            str(str(macdSignalSmoothing).zfill(4)) + '-' +
            str(str(rsiSignal).zfill(4)) +
            str(str(threshold).zfill(4)) + '-' +
            str(str(periodsToAnalyseForTP).zfill(4)) + '-' +
            str(str(periodsToAnalyseForSL).zfill(4)) + '-' +
            str(str(maxSL).zfill(4)) +
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

    # optimisation settings
    df['closeShiftedTP'] = df['close'].shift(-periodsToAnalyseForTP)
    df['openShiftedTP'] = df['open'].shift(-periodsToAnalyseForTP)

    df['closeShiftedSL'] = df['close'].shift(-periodsToAnalyseForSL)
    df['openShiftedSL'] = df['open'].shift(-periodsToAnalyseForSL)

    df['maxNextTP'] = df['closeShiftedTP'].rolling(
        window=periodsToAnalyseForTP, min_periods=0
    ).max()

    df['minNextTP'] = df['closeShiftedTP'].rolling(
        window=periodsToAnalyseForTP, min_periods=0
    ).min()

    df['maxNextSL'] = df['closeShiftedSL'].rolling(
        window=periodsToAnalyseForSL, min_periods=0
    ).max()

    df['minNextSL'] = df['closeShiftedSL'].rolling(
        window=periodsToAnalyseForSL, min_periods=0
    ).min()

    df['currentCandleOC'] = np.where(
        df['close'] > df['open'],
        1,
        0
    )

    # MACD and RSI
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
    df['buyingSignalToShift'] = np.where(
        ((df['currentCandleOC'] == 1) &
         ((df['maxNextTP'] / df['open']) - 1 >= thresholdPerThsd) &
         (1 - (df['minNextSL'] / df['open']) < maxSLPerThsd) &
         (df['macdDiffOffset'] < 0) &
         (df['rsiOffset'] < 50)
         ),
        1,
        0
    )

    df['buyingSignalTmp'] = np.where(
        ((df['currentCandleOC'] == 0) &
         ((df['maxNextTP'] / df['close']) - 1 >= thresholdPerThsd) &
         (1 - (df['minNextSL'] / df['close']) < maxSLPerThsd) &
         (df['macdDiffOffset'] < 0) &
         (df['rsiOffset'] < 50)
         ),
        1,
        0
    )

    df['buyingSignal'] = np.where(
        (df['buyingSignalTmp'] == 1) |
        (df['buyingSignalToShift'].shift(-1) == 1),
        1,
        0
    )

    # Sell
    df['sellingSignalToShift'] = np.where(
        ((df['currentCandleOC'] == 0) &
         (1 - (df['minNextTP'] / df['open']) >= thresholdPerThsd) &
         ((df['maxNextSL'] / df['open']) - 1 < maxSLPerThsd) &
         (df['macdDiffOffset'] < 0) &
         (df['rsiOffset'] < 50)
         ),
        1,
        0
    )

    df['sellingSignalTmp'] = np.where(
        ((df['currentCandleOC'] == 1) &
         (1 - (df['minNextTP'] / df['close']) >= thresholdPerThsd) &
         ((df['maxNextSL'] / df['close']) - 1 < maxSLPerThsd) &
         (df['macdDiffOffset'] < 0) &
         (df['rsiOffset'] < 50)
         ),
        1,
        0
    )

    df['sellingSignal'] = np.where(
        (df['sellingSignalTmp'] == 1) |
        (df['sellingSignalToShift'].shift(-1) == 1),
        1,
        0
    )

    # df['closingSignal'] = 1

    # </editor-fold>

    # Keep only default fields
    df = df[defaultColumnsList]

    # print(df)
    df.to_csv(outputFile, index=False)
    print_time_lapsed(file_name=outputFile)
    # </editor-fold>

print_time_lapsed(final=True)
