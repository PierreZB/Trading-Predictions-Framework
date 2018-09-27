# Trading Predictions Framework (TPF)

This project's goal is to set-up a framework to be able to
- pull trading data for different instruments at different granularities
- calculate a set of indicators
- join entry and exit strategies
- apply machine learning on the data set to get predictions, based on the indicators and the strategy

In this Phase 1 (started September 2018), we will use Oanda as a source for the trading data, python to extract and transform, and orange to build the predictive model.
Therefore, this GitHub project will gather python codes extracting from the Oanda API and transforming it, and storing the output into csv files.

# Project Phases:


Phase 1- POC
- Extract
    - extract raw data from any source
- Transform
    - format data and add basic indicators
- Predict
    - create at least one predictive model

Given those 3 main goals, everything can be done with a sample data only.
It can be stored in local files (csv, txt...) for the time being. The format doesn't matter.
The accuracy of the predictions doesn't matter at this stage; we only want to focus on building a solid methodology and initial framework.

Phase 2 - Strategies
- Manual Strategies
    - build a process to link manual strategies inputs to the transformed data
- Automated Strategies
    - build a framework and process to generate automated strategies
- Strategies performance evaluation
    - build a framework to calculate for each strategy critical indicators (evolution of capital, final capital, risk, deviation...)

Phase 3 - Scaling
- Store
    - store the transformed data in a db
- Scale
    - ensure the db can receive larger amount of data and be refreshed every 5 minutes
- Automate
    - automate the data collection, transformation and storage process

Phase 4 - Visualise
- Visualise Raw, Indicators, Strategies and Predictions
    - visualise in a chart the raw (o,h,l,c) + indicators (with ability to choose which to display) + strategies actions + predictions
- Visualise strategies performance
    - visualise the outputs of starts performance evaluations
- Visualise models accuracy
    - visualise the outputs of predictive models

The goal of this phase is to provide a tool to compare the strategies performance, and the accuracy of the models to help choosing strategies/models to apply or to tweak. A front-end is required to compare those.
Note that a scoring system will have to be established to get a "performance ranking".

Phase 5 - Expand
- Expand indicators library
- Expand strategies library
- Expand prediction models
