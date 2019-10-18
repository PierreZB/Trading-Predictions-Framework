# <editor-fold desc=" ===== Import Libraries ============================== ">
import re
import numpy as np
from os import listdir
from scripts.project_settings import *

# Change pandas display options to show full tables
pd.set_option('display.expand_frame_repr', False)

""" Note: other pandas display options
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 500)
pd.set_option('display.max_rows', 500)
# """

# </editor-fold>

dfConcat = pd.DataFrame([])

outputFile = (str(dataStrategyBacktestingStats) + '/' + '_statsDetailed.csv')
outputFilePnL = (str(dataStrategyBacktestingStats) + '/' + '_statsPnL.csv')


# Get list of files in directory with specific extension
def list_files(directory, extension, exclude):
    return (
        f for f in listdir(directory) if (
            (f.endswith('.' + extension)) &
            (f.rfind(exclude))
        )
    )


# Generate list of csv files in dataStrategyBacktestingStats
filesList = list_files(str(dataStrategyBacktestingStats), 'csv', '_stats')

for inputFileName in filesList:

    # Define file paths
    inputFile = (
            str(dataStrategyBacktestingStats) + '/' +
            str(inputFileName)
    )

    # Load file
    df = pd.read_csv(inputFile, sep=",", encoding='utf-8', engine='c')

    # Concatenate the output of each loop
    dfConcat = pd.concat(
        [dfConcat, df],
        ignore_index=True,
        sort=False
    )

# <editor-fold desc=" ===== Calculate additional fields =============== ">
# PnL
dfConcat.loc[dfConcat['profitLossOnClose'] > 0, 'positivePnL'] = (
    dfConcat['profitLossOnClose']
)
dfConcat.loc[dfConcat['profitLossOnClose'] <= 0, 'negativePnL'] = (
    dfConcat['profitLossOnClose']
)

# PnL (+/-) per Position (Buying/Selling)
dfConcat['positiveBuyingPnL'] = (
        dfConcat['positivePnL'] * dfConcat['buyingPosition']
)

dfConcat['negativeBuyingPnL'] = (
        dfConcat['negativePnL'] * dfConcat['buyingPosition']
)

dfConcat['positiveSellingPnL'] = (
        dfConcat['positivePnL'] * dfConcat['sellingPosition']
)

dfConcat['negativeSellingPnL'] = (
        dfConcat['negativePnL'] * dfConcat['sellingPosition']
)

dfConcat['buyingPnL'] = (
        dfConcat['profitLossOnClose'] * dfConcat['buyingPosition']
)

dfConcat['sellingPnL'] = (
        dfConcat['profitLossOnClose'] * dfConcat['sellingPosition']
)

# Round PnL fields
dfConcat = dfConcat.round({
    'profitLossOnClose': 5,
    'positivePnL': 5,
    'negativePnL': 5,
    'positiveBuyingPnL': 5,
    'negativeBuyingPnL': 5,
    'positiveSellingPnL': 5,
    'negativeSellingPnL': 5,
    'buyingPnL': 5,
    'sellingPnL': 5
})

# Parse Timestamp
dfConcat['timestamp'] = pd.to_datetime(
        pd.Series(dfConcat['timestamp']), format="%Y-%m-%dT%H:%M:%S"
    )
# dfConcat['year'] = dfConcat['timestamp'].str[:4]
# dfConcat['month'] = dfConcat['timestamp'].str[5:-23]
# dfConcat['day'] = dfConcat['timestamp'].str[8:-20]
# dfConcat['hour'] = dfConcat['timestamp'].str[11:-17]
# dfConcat['minute'] = dfConcat['timestamp'].str[14:-14]
# dfConcat['second'] = dfConcat['timestamp'].str[17:-11]

dfConcat['year'] = dfConcat['timestamp'].dt.year
dfConcat['month'] = dfConcat['timestamp'].dt.month
dfConcat['day'] = dfConcat['timestamp'].dt.day
dfConcat['hour'] = dfConcat['timestamp'].dt.hour
dfConcat['weekday'] = dfConcat['timestamp'].dt.dayofweek

dfConcat['strategyName'] = (
    dfConcat['sourceFile'].
    str.replace('QV_', '', regex=True).
    str.split(pat="_", n=5, expand=False).str[-1].
    str.rsplit(pat="_", n=2, expand=False).str[0]
)

dfConcat['instrument'] = (
    dfConcat['sourceFile'].
    str.replace('QV_', '', regex=True).
    str.rsplit(pat="_", n=7, expand=False).str[0]
)

# Adjust value of TP SL to help ratios and visualisation
dfConcat['takeProfit'] = np.where(
    dfConcat['takeProfit'] == 99_999,
    -1,
    dfConcat['takeProfit']
)
dfConcat['stopLoss'] = np.where(
    dfConcat['stopLoss'] == 99_999,
    -1,
    dfConcat ['stopLoss']
)

# Create another data frame grouped by strategy backtest file
dfPnL = (
    dfConcat.groupby([
        'sourceFile', 'strategyName', 'instrument', 'year',
        'takeProfit', 'stopLoss'
    ]).
    agg({
        'profitLossOnClose': [
            'sum', 'count', 'mean', 'median', 'min', 'max', 'std',
        ],
        'positivePnL': ['sum', 'count', 'mean'],
        'negativePnL': ['sum', 'count', 'mean'],
        'buyingPnL': ['sum', 'count', 'mean'],
        'sellingPnL': ['sum', 'count', 'mean'],
        'positiveBuyingPnL': ['sum', 'count', 'mean'],
        'negativeBuyingPnL': ['sum', 'count', 'mean'],
        'positiveSellingPnL': ['sum', 'count', 'mean'],
        'negativeSellingPnL': ['sum', 'count', 'mean'],
        'hitTakeProfit': ['sum'],
        'hitStopLoss': ['sum'],
        'hitTakeProfitAndStopLoss': ['sum'],
        'numberOfPeriods': ['sum', 'count', 'mean'],
        'noActionTaken': ['sum']
    }).reset_index()
)

# Merge the column multi index
dfPnL.columns = dfPnL.columns.map('_'.join)

# rename group by fields
dfPnL = dfPnL.rename(columns={
    'sourceFile_': 'sourceFile',
    'strategyName_': 'strategyName',
    'instrument_': 'instrument',
    'year_': 'year',
    'takeProfit_': 'takeProfit',
    'stopLoss_': 'stopLoss'
})

# noActionTakenRatio
dfPnL['noActionTakenRatio'] = round(
    dfPnL['noActionTaken_sum'] / dfPnL['profitLossOnClose_count'],
    3
)

# Add calculated fields
dfPnL['profitLossRatio'] = (
    dfPnL['positivePnL_sum'] / (-1 * dfPnL['negativePnL_sum'])
)
dfPnL['winRate'] = (
    dfPnL['positivePnL_count'] /
    (dfPnL['negativePnL_count'] + dfPnL['positivePnL_count'])
)
dfPnL['riskRewardRatio'] = np.where(
    (dfPnL['takeProfit'] == -1) | (dfPnL['stopLoss'] == -1),
    0,
    dfPnL['takeProfit'] / dfPnL['stopLoss']
)

# Round floats
dfPnL = dfPnL.round(5)
dfPnL = dfPnL.round({
    'profitLossRatio': 2,
    'riskRewardRatio': 2
})

# Export both outputs
dfConcat.to_csv(outputFile, index=False)
dfPnL.to_csv(outputFilePnL, header=True, index=False)

print_time_lapsed(final=True)
