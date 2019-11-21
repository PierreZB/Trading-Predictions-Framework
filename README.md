# 2019-11-18 TPF Documentation

# Introduction
The Trading Prediction Framework (TPF) project main goal is to have a tool mainly based on python which enables users to backtest trading strategies and create predictive models thanks to supervised clustering machine learning tools.
As of now, the goal of those predictive models is to predict trading decisions (when to buy, hold or sell); this means that the goal is not to predict the price itself, but instead, in a way, focusing on the general trend and momentum.

As of now, the project isn’t fully automated, and still relies on csv files stored in folders (instead of a database).

This document will explain how this project can be used as it is now.

Main process flow:
* Extracting data (with Oanda’s API)
* Write an ROI optimisation strategy and backtest it
* Calculate technical indicators and machine learning target
* Use a clustering algorithm to make predictions on trading actions

# Before you start
## Requirements
*TO BE COMPLETED*
* Oanda API Token: [https://developer.oanda.com](https://developer.oanda.com)
* Python packages:
	* pandas 0.24.2
	* numpy 1.17.3
	* ta 0.4.7
	* tpot 0.10.2
	* scikit-learn 0.21.3
	* scikit-mdr 0.4.4
	* dask 2.7.0
	* dask-core 2.7.0
	* dask-glm 0.2.0
	* dask-ml 1.1.1
	* …

## Software you may need
* Orange (data mining; can be installed with Anaconda)
* Knime (data mining)
* Tableau (BI/Visualisation)
* QlikView (BI/Visualisation)
* Qlik Sense (BI/Visualisation)

## Make sure you have created the following folders
* data\raw_extracts
* data\strategy_raw
* data\strategy_backtesting
* data\models_raw

# Update oanda_api_headers.py
Open "scripts\oanda_api_headers.py" and update the Authorization key with your own.

## Update projects_settings.py
Open "scripts\project_settings.py"

And update projectPath to suite your needs. There are currently 3 examples paths
Windows local folders:
projectPath = 'C:/Users/username\OneDrive\GitHub\Trading-Predictions-Framework'

macOS local folder:
projectPath = '/Users/username/OneDrive/GitHub/Trading-Predictions-Framework'

macOS external folder:
projectPath = '/Volumes/TPF_data'

If you already know what strategy you will want to test, you can also update right away the `strategyFolder` variable, and create this folder under each of these directories:

* data\strategy_raw\
* data\strategy_backtesting\
* data\models_raw\
* models\

# Data extraction
Open "scripts\extractionOanda.py" and update the following variables to suit your needs:

## List of instruments you will extract
`instruments_load_list`

Note:
* A list of all available instruments will be provided in an upcoming update

## List of different granularity you want to extract
`granularity_load_list`

Notes:
* As of now, there’s a limitation to the list of granularity that can be extracted because of the methodology used and the maximum number of records that can be pulled from Oanda at once with a free account.
* Currently you cannot load a granularity below M10 (10 minutes).

## Date range you want to extract
Update the `dateFrom` and `dateTo` variables to define the scope of your extraction.
The date format will be (YYYY, MM, DD).

Notes:
* `dateTo` should be before or equal to today’s date, otherwise the script will fail.


### Notes about the data extraction process
* if a file with similar parameters already exists, the data set will be extracted again and will overwrite this file; there is no option to change this behaviour at the moment
* the data extraction will be stored as a csv file in "data\raw_extracts"
* the format of the outputted file name will be INSTRUMENT_GRANULARITY_DATEFROM_DATETO.csv

# Optimisation strategy
If you haven’t done it yet, decide on your strategy name, and update in the projects_settings.py the “strategyFolder” variable, and create a folder with this same name under each of these directories:

* data\strategy_raw\{myStrategy}
* data\strategy_backtesting\{myStrategy}
* data\models_raw\{myStrategy}
* models\{myStrategy}

Go to the strategies folder and create your strategy script: myStrategy.py

In this file, apply any strategy you want; make sure your output contains at least those fields:

```
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
```

These fields are the same as the ones you get from the extraction process.

You can use the following line of code to easily reduce the list of saved fields to match with this requirement:
```
# Keep only default fields
df = df[defaultColumnsList]
```

By default these fields have been generated containing only “0” in the extraction process:
```
    'buyingSignal',
    'sellingSignal',
    'closingSignal',
    'referencePriceHigher',
    'referencePriceLower'
```

It is therefore critical that your strategy updates them according to your needs.
They will all be used for the backtesting process.

The 3 first fields, should be boolean “0” or “1”
```
    'buyingSignal',
    'sellingSignal',
    'closingSignal'
```

If `buyingSignal` contains a “1”, the backtest process will read it as a buying signal, and potentially open a buying position (this will depend on a set of rules which we will review in the backtesting section).

The 2 last fields should contain 0 (if the reference price is the closing price at the moment the position is opening) or the price value that the strategy requires to use
```
    'referencePriceHigher',
    'referencePriceLower'
```

This was implemented for strategies where a Take Profit and Stop Loss rules are required, but based on different reference.
For instance, in a buying position, the 7amUK strategy sets a take profit at x pips above the high of the 7 am candle, and a stop loss x pips below the low of the 7 am candle.

You output file should be a csv, stored into this folder:
"data\strategy_raw\{myOutputFile}"

The format of the file should be:
INSTRUMENT_GRANULARITY_DATEFROM_DATETO_strategyName{_strategy-settings-values}.csv

Where the strategy settings values are the parameters related to your strategy, for instance, if your strategy relies on a MACD 12, 26, 9 you may want to record these settings in the file name to avoid overwriting your strategy output file, and keep track of the different versions of your strategy output files.

# Backtesting
Before backtesting anything, we need to define what actions to take depending on the signal defined by the strategy.
For instance: what to do if the strategy happened to deliver at the same time a buying signal and a selling signal while we have a buying position running?

These behaviours can be defined in the excel spreadsheet “backtestStrategy.xlsx”.

* Tab “Actions”
	* Columns A to F define the current situation.
	* Column G sets the action to take. Each cell in this column has a drop-down menu from which you can select what action to take.
	* Columns H to P can help you to check faster if the actions you set make sense.
* Tab “ActionsMap”
	* This tab defines the codes and label that are applied for each action
	* I recommend not to change those settings unless you are sure to understand how it works
	* The only fields that you may want to update here are the 3 last columns, the signals dedicated to machine learning.


Now that this is done, open the "scripts\backtestStrategy.py" file.

By default, this file back tests all strategy outputs in the strategy folder you are currently using, unless you comment out the section to define the files list manually.

If you go with the default, update the following variables
```
takeProfitFrom = 50
takeProfitTo = 100
takeProfitStep = 10

stopLossFrom = 10
stopLossTo = 100
stopLossStep = 10
```

By default, the process will also calculate a backtest without a take profit and without a stop loss (this will be done by setting the TP/SL values to 99,999).

If you want to backtest your strategy without take profit and stop loss, set those variables this way:
```
takeProfitFrom = 99_999
takeProfitTo = 99_999
takeProfitStep = 1

stopLossFrom = 99_999
stopLossTo = 99_999
stopLossStep = 1
```

*DO NOT* define the settings as follows, or the processing time will be excessively long:
```
takeProfitFrom = 10
takeProfitTo = 99_999
takeProfitStep = 10

stopLossFrom = 10
stopLossTo = 99_999
stopLossStep = 1
```


If you want to define the files to backtest manually, you will have to uncomment the related section, and follow the pattern indicated:
```
"""
# # Use this section if you prefer to define manually
# ('csv file name', (Take Profit Min value, Take Profit Max Value, Take Profit Step), (Stop Loss Min value, Stop Loss Max Value, Stop Loss Step))
backtestStrategyFileList = [
    # ('outputFileName', (50, 50, 1), (10, 10, 1))
    ('EURUSD_H1_20190101_20191026_swingV01_0005-0006-0024-0000', (99_999, 99_999, 1), (10, 50, 10))
]
# """
```

Now that you have produced your backtest files, you might want to compare their performance. I haven’t built a tool to do this automatically, so it’s up to you to use which ever tool you want. I found Tableau, QlikView and Qlik Sense very good tools for visualising those data sets quickly.

Notes:
* As of now, the backtest process is slow as it loops through the records of a pandas data frame, and I haven’t found a faster way to reach this result.
* I have have written the backtest logic in python (backtestStrategy.py) and QlikView (backtestStrategy.qvs) and the QlikView file is much faster. However, some differences might still exist between those 2 processes, the python file is the most up to date.


# Technical indicators
## Automated process

Before heading for predictions, you may want to create variables that will help the machine learning algorithm to take decisions.

The "scripts\quickModelling.py" will help you in this process; with this script, you can choose amongst other things 
* which file (from the "data\strategy_backtesting" folder) you want to process
* how many variables you want to use (you can specify up to 3 levels of correlation you are ready to accept for these variables)
* what type of target you want to test (swing buy/sell signals, sell/hold/buy signals, buy/close only signals, sell/close only signals)

The script will generate a list of technical indicators, keep only the most relevant ones and feed a neural network with to them to make predictions.
The predictions will be made on the latest dates from your source data set so you can get a rough idea of the accuracy you can expect for your future production predictions.
The predictions scoring will be printed at the end opf the script. 

The output of this file will be another csv with ID, timestamp, target and all the indicators selected by the script, and will be stored in "data\models_raw\{mymodelsRawFile}". 

Keep in mind that the score displayed with this script isn't optimised and could obviously get much better. The purpose here is to give a general idea of the quality of the input data and how it can help and algorithm to classify the targets.

## Manual process
In "models\{myStrategyIndicators}" you can create a python file which purpose will be to generate those variables, create a new `target` field which will be the target your machine learning algorithm will try to reach, and output this file into "data\models_raw\{mymodelsRawFile}"

In my scripts I have chosen to use the “ta” python package to automatically calculate a bunch of technical indicators.
I also define the `target` field in two different ways depending on my needs:
* sometimes I simply convert the `signalLabel` field into a boolean value (0 = sell, 1 = buy); this results in a pure swing trading strategy (“binary”)
* sometimes, I create 3 values ("true3"), based on the `buyingSignal`, `sellingSignal` and `closingSignal`; this results in 3 values: 0 = sell, 1 = hold, 2 = buy
* you can obviously choose to generate the `target` field as you wish (for instance a binary target with only buying and closing buy signals…)

# Predictions
To make predictions, I used 3 different tools:
* Knime
* Orange
* TPOT

First, I load the "data\models_raw\{myModelsRawFile}" created previously in Knime, and analyse the correlations between my target field and all of the other variables.

Usually, if none of the variables has an absolute correlation with the target greater than 50%, I go back to the strategy process as the predictions will very probably be poor.

Then, I open Orange, and use the “prediction_template.ows” workflow to do a quick predictions test:
* load the file "data\models_raw\{myModelsRawFile}"
	* ID -> Text
	* timestamp -> Date
	* target -> Categorical
	* all other fields (variables) -> Numeric
* select columns:
	* move the variables you found relevant under “features”
	* move “target” under “target variable”
	* move “ID” and “timestamp” under “Meta Attributes”
* for the first run, I usually prefer to filter out most of the records on the timestamp so orange can process data faster and I can make sure every part of the workflow is working as expected.
* apply the pre-process method you find relevant to your data
* choose the model/s relevant to your data
* link the model/s to the prediction and Test and Score widgets
* analyse the accuracy in the confusion matrix

Usually, this gives me a good idea of the quality of the data I input.
If I’m curious enough at that stage, I can save the predictions, and manually load them into a strategy file ("data\strategy_raw\{myStrategy}") and then backtest it.

Finally, if I am satisfied with the accuracy of the predictions, I use the python package TPOT to find the model that fits the best the data, and gives the best predictions.

As of now, I use TPOT with dask to parallelise the tasks, and I noticed it works the best in a Jupyter notebook.
So I create a Jupyter notebook under "models\{myJupyterNotebook}" and run it in Jupyter Lab.

-----

# 2018-11-01 TPF Documentation

# Trading Predictions Framework (TPF)

This project's goal is to set-up a framework to be able to
- pull trading data for different instruments at different granularity
- calculate a set of indicators
- join entry and exit strategies
- apply machine learning on the data set to get predictions, based on the indicators and the strategy
- evaluate the strategies performance, as well as the predictions accuracy


# Project Phases


## Phase 1 - POC
- Extract
    - extract raw data from any source
- Transform
    - format data and add basic indicators
- Predict
    - create at least one predictive model

Given those 3 main goals, everything can be done with a sample data only.
It can be stored in local files (csv, txt...) for the time being. The format doesn't matter.
The accuracy of the predictions doesn't matter at this stage; we only want to focus on building a solid methodology and initial framework.

In this Phase 1 (started September 2018), we will use Oanda as a source for the trading data, python to extract and transform, and orange to build the predictive model.
Therefore, this GitHub project will gather python codes extracting from the Oanda API and transforming it, and storing the output into csv files.

## Phase 2 - Strategies
- Manual Strategies
    - build a process to link manual strategies inputs to the transformed data
- Automated Strategies
    - build a framework and process to generate automated strategies
- Strategies performance evaluation
    - build a framework to calculate for each strategy critical indicators (evolution of capital, final capital, risk, deviation...)

## Phase 3 - Scaling
- Store
    - store the transformed data in a db
- Scale
    - ensure the db can receive larger amount of data and be refreshed every 5 minutes
- Automate
    - automate the data collection, transformation and storage process

## Phase 4 - Visualise
- Visualise Raw, Indicators, Strategies and Predictions
    - visualise in a chart the raw (o,h,l,c) + indicators (with ability to choose which to display) + strategies actions + predictions
- Visualise strategies performance
    - visualise the outputs of starts performance evaluations
- Visualise models accuracy
    - visualise the outputs of predictive models

The goal of this phase is to provide a tool to compare the strategies performance, and the accuracy of the models to help choosing strategies/models to apply or to tweak. A front-end is required to compare those.
Note that a scoring system will have to be established to get a "performance ranking".

## Phase 5 - Expand
- Expand indicators library
- Expand strategies library
- Expand prediction models
