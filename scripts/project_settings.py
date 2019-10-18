# <editor-fold desc=" ===== Import Libraries ============================== ">
import datetime as dt
import pandas as pd
from datetime import datetime
from pathlib import Path

# Start counting script reload time
startTime = datetime.now()
previousTime = startTime

# Define df for signalVariable and indicators scripts
df = pd.DataFrame([])

# </editor-fold>

# <editor-fold desc=" ===== Extraction Settings =========================== ">
'''----------------------------------------------------------------
Variables defining the scope of data to extract
Note that for now, you can only load granularity from H5
This is due to the fact that the API call is restricted to 500 recs
and the script is currently written to extract 1 day of data at a time
(S5 to M2 will not load the complete data set)
----------------------------------------------------------------'''

# I am still looking for a way to extract the list of
# instruments available on the platform
instruments_load_list = ['GBP_USD', 'EUR_USD']

# 'S5', 'S10', 'S15', 'S30', 'M1', 'M2', 'M5',
# 'M10', 'M15', 'M30', 'H1', 'H2', 'H3', 'H4', 'H5', 'H6', 'H8', 'H12', 'D',
# 'W', 'M'
granularity_load_list = [
    'H1', 'M10'
]

# Date range - data is extracted 1 day at a time
dateFrom = dt.date(2018, 1, 1)
dateTo = dt.date(2018, 12, 31)
# </editor-fold>

# <editor-fold desc=" ===== backTestStrategy Settings ====================== ">

# (
#   'csv file name',
#   (Take Profit Min value, Take Profit Max Value, Take Profit Step),
#   (Stop Loss Min value, Stop Loss Max Value, Stop Loss Step)
# )
backtestStrategyFileList = [
    ('GBP_USD_M10_20080101_20081231_50pipsADay_StratThld002', (10, 250, 10), (10, 100, 10))
]

# </editor-fold>

# <editor-fold desc=" ===== Indicators Settings =========================== ">

# Note: only input csv files here
indicatorsFileList = [
    'insertFileNameHere'
]

# List of EMA to calculate
emaPeriods_list = [10, 20, 50, 100, 200, 400]

# List of RSI to calculate
rsiPeriods_List = [14]

# Cartesian product to get list of ema crossover
emaPeriodsCartesian_list = [
    (emaPeriods_X1, emaPeriods_X2)
    for emaPeriods_X1 in emaPeriods_list
    for emaPeriods_X2 in emaPeriods_list if emaPeriods_X1 < emaPeriods_X2
    ]

# </editor-fold>

# <editor-fold desc=" ===== Path variables ================================ ">
projectPath = '/Users/mbp13/OneDrive/GitHub/Trading-Predictions-Framework'

scriptsPath = Path(projectPath + '/scripts')

dataRawExtracts = Path(projectPath + '/data/raw_extracts')
dataStrategies = Path(projectPath + '/data/strategies')
dataStrategyBacktesting = Path(projectPath + '/data/strategy_backtesting')
# dataStrategyBacktestingStats = Path(projectPath + '/data/strategy_backtesting_stats')
dataStrategyBacktestingStats = Path('/Volumes/TPF_data/strategy_backtesting_stats/50pipsADay_2008_2018_Thld002_Thld010')
dataIndicators = Path(projectPath + '/data/indicators')
dataModelBacktesting = Path(projectPath + '/data/model_backtesting')
# </editor-fold>


# <editor-fold desc=" ===== Functions ===================================== ">
def sort_deduplicate_reindex_data_frame(
        data_frame, index_field, csv_source_file=False
):
    """
    Sorts the data frame indicated in data_frame parameter
    based on the field indicated in parameter index_field
    and then rebuilds the index
    :param data_frame: data frame on which you will apply this function
    if the data frame doesn't exist yet, add a csv_source_file to give
    the source for your data frame
    :param index_field: field used to sort data an rebuild index
    :param csv_source_file: if creating the data frame from a csv,
    indicate here the source csv file path and name, otherwise set a False
    :return:
    """
    import pandas as pd
    if csv_source_file is not False:
        data_frame = pd.read_csv(
            csv_source_file, sep=",", encoding='utf-8', engine='c'
        )
    data_frame = data_frame.sort_values(
        by=[str(index_field)], ascending=True, na_position='first'
    )
    data_frame = data_frame.drop_duplicates(subset=index_field)
    data_frame = data_frame.reset_index(drop=True)
    data_frame = data_frame.round({
        # 'volume': 0,
        'open': 5,
        'high': 5,
        'low': 5,
        'close': 5
    })
    return data_frame


def print_time_lapsed(file_name=False, final=False):
    """
    Print the time lapsed since script started. The argument file_name allows
    the user to add the last exported file name to the print statement.
    :param file_name: Last exported file name
    (optional, defaults to False)
    :param final: Set as True to specify it is the last time lapsed statement
    (optional, defaults to False)
    :return:
    """
    global previousTime

    if file_name is not False:
        file_name_printed = str(file_name) + str(" ")
    else:
        file_name_printed = str('')

    if final is not False:
        final_printed = str('TOTAL Time Lapsed: ')
    else:
        final_printed = str('Time lapsed: ')

    time_lapsed_since_beginning = datetime.now() - startTime
    time_lapsed_since_last_call = datetime.now() - startTime

    # TODO [3] remove milliseconds in print_time_lapsed
    print(
        str(final_printed) +
        str(file_name_printed) +
        str(datetime.now() - startTime) + ' (+ ' +
        str(datetime.now() - previousTime) + ')'
    )

    previousTime = datetime.now()


# </editor-fold>
