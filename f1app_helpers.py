import numpy as np
import pandas as pd
import sqlite3


def get_year_labels(year_start, year_end):
    tm_years = [{'label': year, 'value': year} for year in np.arange(2018, 2024)]
    return tm_years

def get_init_raceId(year):
    query = 'SELECT raceId FROM races WHERE (year=? AND round=1)'
    with sqlite3.connect("data/f1db_lite.db") as cnx:
        raceId = pd.read_sql(query, cnx, params=(year,)).values[0, 0]
    return raceId

def get_event_labels(year):
    query = 'SELECT raceId, round, date, name  FROM races WHERE year=?'
    with sqlite3.connect("data/f1db_lite.db") as cnx:
        event_data_df = pd.read_sql(query, cnx, params=(year,))
    event_data_df['label'] = ('Round ' + event_data_df['round'].astype(str) +
                              ': ' + event_data_df['date'].astype(str) +
                              ' ' + event_data_df['name'].astype(str))
    event_data_df['value'] = event_data_df['raceId']
    event_data = event_data_df[['label', 'value']].to_dict('records')

    return event_data  #, event_data_df

def get_event(raceId):
    query_races = 'SELECT * FROM races WHERE raceID=?'
    with sqlite3.connect("data/f1db_lite.db") as cnx:
        current_race_df = pd.read_sql(query_races, cnx, params=(str(raceId),))
    column_mapper = {'year': 'Season', 'round': 'Round', 'name': 'Event',
                     'date': 'Race Date', 'time': 'Race Time',
                     'fp1_date': 'Practice 1 Date',
                     'fp1_time': 'Practice 1 Time',
                     'fp2_date': 'Practice 2 Date',
                     'fp2_time': 'Practice 2 Time',
                     'fp3_date': 'Practice 3 Date',
                     'fp3_time': 'Practice 3 Time',
                     'quali_date': 'Qualifier Date',
                     'quali_time': 'Qualifier Time',
                     'sprint_date': 'Sprint Date',
                     'sprint_time': 'Sprint Time'}
    event_df = current_race_df.rename(column_mapper, axis=1).T[0].dropna()
    return event_df

def get_event_header_str(event_df):
    event_header_str = (f'Season {event_df["Season"]} ' +
                        f'Round {event_df["Round"]}: ' +
                        f'{event_df["Event"]}')
    return event_header_str

def get_event_table(raceId):
    result_list = (['driverId', 'constructorId', 'positionOrder',
                    'positionText', 'laps', 'grid', 'time', 'statusId'])
    driver_list = ['driverRef', 'number', 'code', 'forename', 'surname','dob']
    driver_add = ([field + ' as driver_' + field
                   for field in ['nationality', 'url']])
    constructor_list = (['constructorId', 'constructorRef', 'name'])
    constructor_add = ([field + ' as const_' + field
                        for field in ['nationality', 'url']])

    result_select = ', '.join('r.' + result for result in result_list)
    driver_select = ', '.join('d.' + driver
                              for driver in driver_list + driver_add)
    constructor_select = ', '.join('c.' + constructor for constructor
                                   in constructor_list + constructor_add)

    qu_result_raceId = (
        f'SELECT {result_select} '
        f'FROM results r '
        f'WHERE raceID=?')
    qu_results_wstatus = (
        f'SELECT r.*, s.status '
        f'FROM ({qu_result_raceId}) r '
        f'LEFT JOIN status s USING (statusID)')
    qu_results_wst_dr = (
        f'SELECT r.*, {driver_select}'
        f' FROM ({qu_results_wstatus}) r '
        f'LEFT JOIN drivers d '
        f'USING (driverID)')
    query = (
        f'SELECT r.*, {constructor_select} '
        f'FROM ({qu_results_wst_dr}) r '
        f'LEFT JOIN constructors c '
        f'USING (constructorID)')

    with sqlite3.connect("data/f1db_lite.db") as cnx:
        results_expand_df = pd.read_sql(query, cnx, params=(str(raceId),))

    results_expand_df['Driver'] = results_expand_df['forename'].str.cat(
        results_expand_df['surname'], sep=' ')
    return results_expand_df

def condense_event_table(results_expand_df):
    condensed_df = results_expand_df[['positionText', 'code', 'number',
                                      'laps', 'Driver', 'name', 'time',
                                      'status']]
    column_mapper = {'positionText': 'Pos', 'code': 'Code', 'number': 'No',
                                      'laps': 'Laps', 'Driver': 'Driver',
                                      'name': 'Constructor', 'time': 'Time',
                                      'status': 'Status'}
    condensed_df = condensed_df.rename(column_mapper, axis=1)
    return condensed_df



