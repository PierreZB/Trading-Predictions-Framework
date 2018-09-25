import requests
import pandas as pd
import datetime as dt
from pandas.io.json import json_normalize
from headers import headers
from pathlib import Path
from extractionSettings import (
    instruments,
    granularities,
    dateFrom,
    dateTo
)

# Define file paths
dataFolder = Path("Data/")

# Generate empty data frames and lists
df_raw = pd.DataFrame()
df_candles = pd.DataFrame()
df_parsed = pd.DataFrame()
df_rawConcat = pd.DataFrame()
datesLoadList = []

# Generate list of date to load
while dateFrom <= dateTo:
    datesLoadList.append(dateFrom.strftime('%Y-%m-%d'))
    dateFrom = dateFrom + dt.timedelta(days=1)

for datesLoad in datesLoadList:
    for instrument in instruments:
        for granularity in granularities:

            # Calculate the dates from and to, based on the current loop
            dateAPIFrom = dt.datetime.strptime(datesLoad, '%Y-%m-%d')
            dateAPITo = dateAPIFrom + dt.timedelta(days=1)
            # print(dateAPIFrom)
            # print(dateAPITo)

            # Define the API GET address
            address = (
                'https://api-fxpractice.oanda.com/v3/instruments/' +
                str(instrument) + '/candles?price=A' +
                '&from=' + str(dateAPIFrom) +
                '&to=' + str(dateAPITo) +
                '&granularity=' + str(granularity) +
                '&smooth=True'
            )

            # Call API to retrieve JSON
            response = requests.get(address, headers=headers)
            response2object = response.json()
            '''print(response2object)'''

            # Check if query returned no errors
            if str(response2object)[2:7] != 'error':

                # Normalise the JSON response
                df_raw = json_normalize(
                    response2object, record_path=['candles'],
                    meta=['instrument', 'granularity'], sep='.'
                )

                # Check size of the nromalised JSON
                df_rawCount = df_raw['instrument'].count()

                # if the table has more than 0 records, process, else next loop
                if df_rawCount > 0:

                    # Extract the candles
                    df_candles = pd.DataFrame(
                        (d for idx, d in df_raw['ask'].iteritems())
                    ).fillna(0)

                    # concat both data sets created previously
                    df_parsed = pd.concat(
                        [df_raw.drop('ask', axis=1), df_candles], axis=1
                    )

                    # Remove values from df
                    df_raw.drop(df_raw.index, inplace=True)
                    df_candles.drop(df_candles.index, inplace=True)
                    df_raw, df_candles = pd.DataFrame(), pd.DataFrame()

                    # Generate date and time fields
                    df_parsed['timestamp'] = pd.to_datetime(
                        pd.Series(df_parsed['time']),
                        format="%Y-%m-%dT%H:%M:%S.000000000Z"
                        )
                    df_parsed['dateYYYMMDD'] = (
                        df_parsed['timestamp'].dt.strftime('%Y%m%d')
                        )
                    df_parsed['timeHHMMSS'] = (
                        df_parsed['timestamp'].dt.strftime('%H%M%S')
                        )

                    df_parsed['year'] = df_parsed['time'].str[:4]
                    df_parsed['month'] = df_parsed['time'].str[5:-23]
                    df_parsed['day'] = df_parsed['time'].str[8:-20]
                    df_parsed['hour'] = df_parsed['time'].str[11:-17]
                    df_parsed['minute'] = df_parsed['time'].str[14:-14]
                    df_parsed['second'] = df_parsed['time'].str[14:-14]

                    # Create an ID field
                    df_parsed['ID'] = (
                        df_parsed['instrument'] + '|' +
                        df_parsed['granularity'] + '|' +
                        df_parsed['year'] +
                        df_parsed['month'] +
                        df_parsed['day'] + '|' +
                        df_parsed['hour'] +
                        df_parsed['minute'] +
                        df_parsed['second']
                        )

                    # Change columns names and order
                    df_parsed = df_parsed.rename(
                        index=str,
                        columns={
                            "o": "open",
                            "h": "high",
                            "l": "low",
                            "c": "close"
                            }
                        )
                    df_parsed = df_parsed[[
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
                        'dateYYYMMDD',
                        'timeHHMMSS',
                        'year',
                        'month',
                        'day',
                        'hour',
                        'minute',
                        'second'
                        ]]

                    # Concatenate the output of each loop
                    df_rawConcat = pd.concat(
                        [df_rawConcat, df_parsed],
                        ignore_index=True,
                        sort=False
                    )

# Export output
print(df_rawConcat)
df_rawConcat.to_csv(dataFolder / "df_rawConcat.csv")
df_rawConcat.to_json(dataFolder / "df_rawConcat.json", orient='index')
