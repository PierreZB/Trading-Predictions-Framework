# <editor-fold desc=" ===== Import Libraries ============================== ">
import datetime as dt
import pandas as pd
from datetime import datetime
from pathlib import Path
# </editor-fold>

# <editor-fold desc=" ===== Path variables ================================ ">
strategyFolder = 'swing'

projectPath = 'C:/Users/xau\OneDrive\GitHub\Trading-Predictions-Framework'
# projectPath = '/Users/mbp13/OneDrive/GitHub/Trading-Predictions-Framework'
# projectPath = '/Volumes/TPF_data'

scriptsPath = Path(projectPath + '/scripts')

dataRawExtracts = Path(
    projectPath + '/data/raw_extracts'
)
dataStrategy = Path(
    projectPath + '/data/strategy_raw/' + strategyFolder
)
dataStrategyBacktesting = Path(
    projectPath + '/data/strategy_backtesting/' + strategyFolder
)
dataStrategyBacktestingStats = Path(
    projectPath + '/data/strategy_backtesting_stats/' + strategyFolder
)
dataModelsRaw = Path(
    projectPath + '/data/models_raw/' + strategyFolder
)
dataModelsBacktesting = Path(
    projectPath + '/data/models_backtesting/' + strategyFolder
)
# </editor-fold>


# <editor-fold desc=" ===== Default values ================================ ">
# Start counting script reload time
startTime = datetime.now()
previousTime = startTime

# Define df for signalVariable and indicators scripts
df = pd.DataFrame([])

# Define default data frame structure
defaultColumnsList = [
    'ID',
    'timestamp',
    'volume',
    'open',
    'high',
    'low',
    'close',
    'buyingSignal',
    'sellingSignal',
    'closingSignal',
    'referencePriceHigher',
    'referencePriceLower'
]
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
        str(datetime.now() - startTime) + ' (+ ' +
        str(datetime.now() - previousTime) + ') | ' +
        str(file_name_printed)
    )

    previousTime = datetime.now()


# </editor-fold>
