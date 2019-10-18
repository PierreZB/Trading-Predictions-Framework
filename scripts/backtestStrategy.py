# <editor-fold desc=" ===== Import Libraries ============================== ">
import sys
sys.path.append('/Users/mbp13/OneDrive/GitHub/Trading-Predictions-Framework')

import numpy as np
from scripts.project_settings import *

# Change pandas display options to show full tables
pd.set_option('display.expand_frame_repr', False)
pd.set_option('display.max_rows', 1000)

""" Note: other pandas display options
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 500)
# """

print('import libraries')
print_time_lapsed()
# </editor-fold>

# <editor-fold desc=" ===== Complete settings list ======================== ">

# Read the backtestStrategyFileList and create cartesian list with all
# settings to backtest
backtestStrategySettingsList = []

for fileTuple in backtestStrategyFileList:
    fileName_X, takeProfit_X, stopLoss_X = fileTuple
    takeProfitFrom, takeProfitTo, takeProfitRange = takeProfit_X
    stopLossFrom, stopLossTo, stopLossRange = stopLoss_X

    takeProfitList = []

    while takeProfitFrom <= takeProfitTo:
        takeProfitList.append(takeProfitFrom)
        takeProfitFrom = takeProfitFrom + takeProfitRange

    # Add a TP high enough to replicate no TP behaviour
    takeProfitList.append(99_999)

    stopLossList = []

    while stopLossFrom <= stopLossTo:
        stopLossList.append(stopLossFrom)
        stopLossFrom = stopLossFrom + stopLossRange

    # Add a SL high enough to replicate no SL behaviour
    stopLossList.append(99_999)

    # Cartesian product of TP and SL lists
    TPSLList = [
        (fileName_X, a, b) for a in takeProfitList for b in stopLossList
    ]

    backtestStrategySettingsList = backtestStrategySettingsList + TPSLList

print('Complete settings list')
print_time_lapsed()
# </editor-fold>

# <editor-fold desc=" ===== Load Maps for actions ===================== ">

# TODO [3] Create an interactive matrix window to avoid having to use Excel
#  or editing the script

# TODO [1] Check if this section can be moved outside of the for loop

dfSituationToAction = pd.read_excel(
    # str(scriptsPath) + '/' + 'backtestingModel.xlsx',
    str(scriptsPath) + '/' + 'backtestStrategy.xlsx',
    sheet_name='Actions',
    index_col=0, usecols='J:K', header=None, skiprows=1,
    names=['situationCode', 'actionCode']
)

print('dfSituationToAction')
print_time_lapsed()

dctSituationToAction = dfSituationToAction.to_dict()

print('dctSituationToAction')
print_time_lapsed()

dfActionToUpdatedPosition = pd.read_excel(
    str(scriptsPath) + '/' + 'backtestStrategy.xlsx',
    sheet_name='ActionsMap',
    index_col=0, usecols='F:L', header=None, skiprows=1,
    names=[
        'actionCode', 'codeForUpdatedPosition',
        'codeForPriceOnOpen', 'codePnLOnClose',
        'noActionTaken',
        'buyingSignalText', 'sellingSignalText'
    ]
)

print('dfActionToUpdatedPosition')
print_time_lapsed()

dctActionToUpdatedPosition = dfActionToUpdatedPosition.to_dict()

print('dctActionToUpdatedPosition')
print_time_lapsed()
# </editor-fold>


for backtestStrategyTuple in backtestStrategySettingsList:

    # <editor-fold desc=" ===== Load data ================================= ">
    inputFileName, takeProfitPips, stopLossPips = backtestStrategyTuple

    takeProfit = takeProfitPips / 10_000
    stopLoss = stopLossPips / 10_000

    # Define file paths
    inputFile = (
            str(dataStrategies) + '/' +
            str(inputFileName) + str('.csv')
    )

    outputFile = (
            str(dataStrategyBacktesting) + '/' +
            str(inputFileName) + "_" +
            str("TP") + str(takeProfitPips).zfill(5) + "_" +
            str("SL") + str(stopLossPips).zfill(5) +
            str('.csv')
    )

    outputStatsFile = (
            str(dataStrategyBacktestingStats) + '/' +
            str(inputFileName) + "_" +
            str("TP") + str(takeProfitPips).zfill(5) + "_" +
            str("SL") + str(stopLossPips).zfill(5) +
            str("_Stats") +
            str('.csv')
    )

    # Load csv, sort by ID, remove duplicates based on ID, reset the index
    df = sort_deduplicate_reindex_data_frame(
        data_frame=df, index_field='ID', csv_source_file=inputFile
    )

    # Limit df records to make tests quicker
    # df = df.head(1082)

    # Ensure signals are filled with 0 and 1 values only; if not, fill with 0
    signalsList = ['buyingSignal', 'sellingSignal', 'closingSignal']
    for signalX in signalsList:
        df[signalX] = pd.to_numeric(df[signalX], errors='coerce').fillna(0)
        df[signalX] = df[signalX].astype(int)
        df[signalX] = df[signalX].apply(lambda x: x if x == 1 or x == 0 else 0)
    del signalsList

    # TODO [3] Rename user created fields; add 'userIndicator_' prefix

    # </editor-fold>

    # <editor-fold desc=" ===== backtestingModel ===================== ">

    # TODO [1] Check the roundings:
    #  I noticed a small difference between Excel Model
    #  without ROUND(x, 5) and this script

    # TODO [3] optimisation: move all fields that can be outside of the loop

    # Create the temporary fields, set at 0 by default
    tempFields = [
        'currentPosition', 'priceOnOpenPosition', 'numberOfPeriods',
        'hitTakeProfit', 'hitStopLoss',
        'situationCode', 'actionCode', 'noActionTaken'
        'profitLossOnClose'
    ]

    for tempField in tempFields:
        df[tempField] = 0

    print('Load and prepare main df')
    print_time_lapsed()

    # Loop through data frame records
    for i in range(0, len(df)):
        # calculate current and previous record number
        CurrentRecord = int(i)
        PreviousRecord = int(
            np.where(CurrentRecord == 0, 0, CurrentRecord - 1)
        )

        """
        !!! The order in which the following fields are calculated is critical
        as they are interdependent!
        """

        # currentPosition
        if CurrentRecord == 0:
            df.at[CurrentRecord, 'currentPosition'] = 0
        else:
            df.at[CurrentRecord, 'currentPosition'] = (
                dctActionToUpdatedPosition.
                get('codeForUpdatedPosition', {}).
                get(df.at[PreviousRecord, 'actionCode'], 0)
            )

        # priceOnOpenPosition
        if (
            dctActionToUpdatedPosition.get('codeForPriceOnOpen', {}).
                get(df.at[PreviousRecord, 'actionCode'], 9999)
        ) == 2:
            df.at[CurrentRecord, 'priceOnOpenPosition'] = (
                df.at[PreviousRecord, 'priceOnOpenPosition']
            )
        elif (
            dctActionToUpdatedPosition.get('codeForPriceOnOpen', {}).
                get(df.at[PreviousRecord, 'actionCode'], 9999)
        ) == 1:
            df.at[CurrentRecord, 'priceOnOpenPosition'] = (
                df.at[CurrentRecord, 'open']
            )
        else:
            df.at[CurrentRecord, 'priceOnOpenPosition'] = (
                None
            )

        # Update price reference
        # TODO [2] double check condition "if refPrice == 0" (100% accurate?)
        df.at[CurrentRecord, 'referencePriceHigherUpdated'] = np.where(
            (df.at[CurrentRecord, 'referencePriceHigher'] == 0),
            df.at[CurrentRecord, 'priceOnOpenPosition'],
            df.at[CurrentRecord, 'referencePriceHigher']
        )

        df.at[CurrentRecord, 'referencePriceLowerUpdated'] = np.where(
            (df.at[CurrentRecord, 'referencePriceLower'] == 0),
            df.at[CurrentRecord, 'priceOnOpenPosition'],
            df.at[CurrentRecord, 'referencePriceLower']
        )

        # numberOfPeriods
        if (
            dctActionToUpdatedPosition.get('codeForPriceOnOpen', {}).
                get(df.at[PreviousRecord, 'actionCode'], 9999)
        ) == 2:
            df.at[CurrentRecord, 'numberOfPeriods'] = (
                df.at[PreviousRecord, 'numberOfPeriods'] + 1
            )
        elif (
            dctActionToUpdatedPosition.get('codeForPriceOnOpen', {}).
                get(df.at[PreviousRecord, 'actionCode'], 9999)
        ) == 1:
            df.at[CurrentRecord, 'numberOfPeriods'] = (
                1
            )
        else:
            df.at[CurrentRecord, 'numberOfPeriods'] = (
                None
            )

        # hit Take Profit
        if (
            (
                (df.at[CurrentRecord, 'currentPosition'] == 1) &
                (df.at[CurrentRecord, 'high'] -
                 df.at[CurrentRecord, 'referencePriceHigherUpdated']
                 >= takeProfit)
            ) |
            (
                (df.at[CurrentRecord, 'currentPosition'] == 2) &
                (df.at[CurrentRecord, 'referencePriceLowerUpdated'] -
                 df.at[CurrentRecord, 'low']
                 >= takeProfit)
            )
        ):
            df.at[CurrentRecord, 'hitTakeProfit'] = 1
        else:
            df.at[CurrentRecord, 'hitTakeProfit'] = 0

        # hit Stop Loss
        if (
            (
                (df.at[CurrentRecord, 'currentPosition'] == 1) &
                (df.at[CurrentRecord, 'referencePriceLowerUpdated'] -
                 df.at[CurrentRecord, 'low']
                 >= stopLoss)
            ) |
            (
                (df.at[CurrentRecord, 'currentPosition'] == 2) &
                (df.at[CurrentRecord, 'high'] -
                 df.at[CurrentRecord, 'referencePriceHigherUpdated']
                 >= stopLoss)
            )
        ):
            df.at[CurrentRecord, 'hitStopLoss'] = 1
        else:
            df.at[CurrentRecord, 'hitStopLoss'] = 0

        # situationCode
        df.at[CurrentRecord, 'situationCode'] = (
            9_000_000 +
            (100_000 * df.at[CurrentRecord, 'currentPosition']) +
            (10_000 * df.at[CurrentRecord, 'buyingSignal']) +
            (1_000 * df.at[CurrentRecord, 'sellingSignal']) +
            (100 * df.at[CurrentRecord, 'closingSignal']) +
            (10 * df.at[CurrentRecord, 'hitTakeProfit']) +
            (1 * df.at[CurrentRecord, 'hitStopLoss'])
        )

        # actionCode
        df.at[CurrentRecord, 'actionCode'] = (
            dctSituationToAction['actionCode'][
                df.at[CurrentRecord, 'situationCode']
            ]
        )

    print('End of Loop through records')
    print_time_lapsed()

    # buyingSignalText & sellingSignalText
    dfCodePnLOnClose = dfActionToUpdatedPosition[[
        'codePnLOnClose'
    ]]

    df = pd.merge(df, dfCodePnLOnClose, on='actionCode', how='left')
    del dfCodePnLOnClose

    df.loc[df['codePnLOnClose'] == 1, 'profitLossOnClose'] = (
        df['close'] - df['referencePriceHigherUpdated']
    )

    df.loc[df['codePnLOnClose'] == 2, 'profitLossOnClose'] = (
        df['referencePriceLowerUpdated'] - df['close']
    )

    df.loc[df['codePnLOnClose'] == 3, 'profitLossOnClose'] = (
        takeProfit
    )

    df.loc[df['codePnLOnClose'] == 4, 'profitLossOnClose'] = (
        ((df['referencePriceHigherUpdated'] -
          df['referencePriceLowerUpdated']) +
         stopLoss) * -1
    )

    # # Had an issue with this field; still don't know why
    # # I kept the "non-working" version in comments below
    # df.loc[df['codePnLOnClose'] == 5, 'profitLossOnClose'] = np.where(
    #     np.random.random(1) > 0.5,
    #     takeProfit,
    #     ((df['referencePriceHigherUpdated'] -
    #       df['referencePriceLowerUpdated']) +
    #      stopLoss) * -1
    # )
    df.loc[
        (df['codePnLOnClose'] == 5) &
        (np.random.random(1) >= 0.5),
        'profitLossOnClose'] = (
            ((df['referencePriceHigherUpdated'] -
             df['referencePriceLowerUpdated']) +
             stopLoss) * -1
    )

    df.loc[
        (df['codePnLOnClose'] == 5) &
        (pd.isna(df['profitLossOnClose'])),
        'profitLossOnClose'] = (
            takeProfit
    )

    # Prepare column for statistics file
    df['tradingPositionTmp'] = np.where(
        df['profitLossOnClose'] < 999_999,
        df['currentPosition'],
        0
    )

    # buyingSignalText & sellingSignalText
    dfSignalText = dfActionToUpdatedPosition[[
        'buyingSignalText',
        'sellingSignalText',
        'noActionTaken'
    ]]

    df = pd.merge(df, dfSignalText, on='actionCode', how='left')
    del dfSignalText

    # SourceFile
    df['sourceFile'] = (
            str(inputFileName) + "_" +
            str("TP") + str(takeProfitPips).zfill(5) + "_" +
            str("SL") + str(stopLossPips).zfill(5)
    )

    # <editor-fold desc=" ===== Prepare Stats fields ====================== ">

    # Positions
    df.loc[df['tradingPositionTmp'] == 1, 'statsBuyingPosition'] = 1
    df.loc[df['tradingPositionTmp'] == 2, 'statsSellingPosition'] = 1

    # Take Profit / Stop Loss triggers
    df.loc[
        (df['hitTakeProfit'] == 1) &
        (df['hitStopLoss'] == 0) &
        ((df['statsBuyingPosition'] == 1) | (df['statsSellingPosition'] == 1)),
        'statsHitTakeProfit'
    ] = 1

    df.loc[
        (df['hitTakeProfit'] == 0) &
        (df['hitStopLoss'] == 1) &
        ((df['statsBuyingPosition'] == 1) | (df['statsSellingPosition'] == 1)),
        'statsHitStopLoss'
    ] = 1

    df.loc[
        (df['hitTakeProfit'] == 1) &
        (df['hitStopLoss'] == 1) &
        ((df['statsBuyingPosition'] == 1) | (df['statsSellingPosition'] == 1)),
        'statsHitTakeProfitAndStopLoss'
    ] = 1

    df.loc[
        (df['numberOfPeriods'] > 0) &
        ((df['statsBuyingPosition'] == 1) | (df['statsSellingPosition'] == 1)),
        'statsNumberOfPeriods'
    ] = df['numberOfPeriods']

    # Risk/Reward
    df['takeProfit'] = takeProfitPips
    df['stopLoss'] = stopLossPips

    # Round floats
    df = df.round({'profitLossOnClose': 5})

    print('Additional Fields')
    print_time_lapsed()
    # </editor-fold>

    # <editor-fold desc=" ===== Prepare Stats Fields ====================== ">
    # Generate the data frame dedicated to aggregated statistics
    dfStats = df[[
        'ID',
        'sourceFile',
        'granularity',
        'timestamp',
        'takeProfit',
        'stopLoss',
        'profitLossOnClose',
        'statsBuyingPosition',
        'statsSellingPosition',
        'statsHitTakeProfit',
        'statsHitStopLoss',
        'statsHitTakeProfitAndStopLoss',
        'statsNumberOfPeriods',
        'noActionTaken'
    ]]

    dfStats = dfStats.rename(columns={
        'statsBuyingPosition': 'buyingPosition',
        'statsSellingPosition': 'sellingPosition',
        'statsHitTakeProfit': 'hitTakeProfit',
        'statsHitStopLoss': 'hitStopLoss',
        'statsHitTakeProfitAndStopLoss': 'hitTakeProfitAndStopLoss',
        'statsNumberOfPeriods': 'numberOfPeriods'
    })

    # Keep only records where the position was closed (drop empty rows)
    dfStats = dfStats[
        (dfStats['profitLossOnClose'] < 999_999) |
        (dfStats['noActionTaken'].astype(int) == 1)
    ]

    # </editor-fold>

    # <editor-fold desc=" ===== Cleanse df ================================ ">

    df = df[[
        'ID',
        'instrument',
        'granularity',
        'timestamp',
        'volume',
        'open',
        'high',
        'low',
        'close',
        'complete',
        'dateYYYYMMDD',
        'timeHHMMSS',
        'year',
        'month',
        'day',
        'hour',
        'minute',
        'second',
        'buyingSignal',
        'sellingSignal',
        'closingSignal',
        'buyingSignalText',
        'sellingSignalText',
        'profitLossOnClose'
    ]]

    print('Stats DF & cleanup')
    print_time_lapsed()

    # TODO [1] Performance: Drop useless fields and round numeric fields
    # </editor-fold>

    # <editor-fold desc=" ===== Export Output ============================= ">

    df.to_csv(outputFile, index=False)
    dfStats.to_csv(outputStatsFile, index=False)
    print_time_lapsed(file_name=outputFile)

    print('write out files')
    print_time_lapsed()
    # </editor-fold>

print_time_lapsed(final=True)
