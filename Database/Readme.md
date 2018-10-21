# TPF Database Architecture

This is an explanation of the dependencies needed to run the codes in this folder.

Things you'll need for Python (PIP):

* [MySQL Connector](https://dev.mysql.com/doc/connector-python/en/connector-python-installation-binary.html)
* [SQL Alchemy](https://www.sqlalchemy.org/)
* [Pandas](https://pandas.pydata.org/)

## Installation

> pip install mysql-connector-python

> pip install sqlalchemy

> pip install pandas

## Usage

### Stage 1

- `S1_dbDesign.py` establishes a connection to a MYSQL server and creates a table for the raw extract.

### Stage 2
- `S2_dbImport.py` loads data in a dataframe and uses sqlalchemy to import to MYSQL table created in stage 1. 
