# <editor-fold desc=" ===== Import Libraries ============================== ">
from scripts.project_settings import *
from ta import *
import numpy as np

pd.set_option('display.expand_frame_repr', False)
pd.set_option('display.max_rows', 50)

# </editor-fold>

# List of files on which you want to apply this strategy
strategyFileList = [
    # 'EURUSD_H1_20040101_20191026'
    'EURUSD_M15_20180101_20181231'
]

# Difference between close and open threshold per candle (per thousand)
threshold = 1
# numbers of periods to analyse around current candle
periodsToAnalyseAroundCandle = 24
periodsToAnalyseAfterCandle = 24 * 12
emaPeriods = 24 * 5
# set the maximum level of stop loss you can tolerate (per thousand)
maxSL = 0

# prepare those variables for the calculations
thresholdPerThsd = threshold / 1000
periodsToAnalyseCentered = periodsToAnalyseAroundCandle * 2 + 1
maxSLPerThsd = np.where(
    maxSL == 0,
    99_999,
    maxSL / 1000
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
            str('swingV02') + '_' +
            str(str(threshold).zfill(4)) + '-' +
            str(str(periodsToAnalyseAroundCandle).zfill(4)) + '-' +
            str(str(periodsToAnalyseAfterCandle).zfill(4)) + '-' +
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

    df['ema'] = df['close'].ewm(span=emaPeriods, min_periods=emaPeriods).mean()

    df['emaShifted'] = df['ema'].shift(-periodsToAnalyseAfterCandle)

    df['emaMaxNextP'] = df['emaShifted'].rolling(
        window=periodsToAnalyseAfterCandle, min_periods=0
    ).max()

    df['emaMinNextP'] = df['emaShifted'].rolling(
        window=periodsToAnalyseAfterCandle, min_periods=0
    ).min()

    df['emaMaxAround'] = df['ema'].rolling(
        window=periodsToAnalyseCentered, min_periods=0, center=True
    ).max()

    df['emaMinAround'] = df['ema'].rolling(
        window=periodsToAnalyseCentered, min_periods=0, center=True
    ).min()

    # </editor-fold>

    # <editor-fold desc=" ===== Buying/Selling/CLosing Signals ============ ">
    # Buy
    df['buyingSignal'] = np.where(
        ((df['ema'] == df['emaMinAround']) &
         ((df['emaMaxNextP'] / df['ema']) - 1 >= thresholdPerThsd) &
         (1 - (df['emaMinNextP'] / df['ema']) < maxSLPerThsd)
         ),
        1,
        0
    )

    # Sell
    df['sellingSignal'] = np.where(
        ((df['ema'] == df['emaMaxAround']) &
         (1 - (df['emaMinNextP'] / df['ema']) >= thresholdPerThsd) &
         ((df['emaMaxNextP'] / df['open']) - 1 < maxSLPerThsd)
         ),
        1,
        0
    )

    # </editor-fold>

    # Keep only default fields
    df = df[defaultColumnsList]
    df['ema'] = df['close'].ewm(span=emaPeriods, min_periods=emaPeriods).mean()

    # print(df)
    df.to_csv(outputFile, index=False)
    print_time_lapsed(file_name=outputFile)
    # </editor-fold>

print_time_lapsed(final=True)
