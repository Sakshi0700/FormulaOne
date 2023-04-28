import numpy as np
import pandas as pd
import sqlite3
import datetime as dt


DB = "data/f1db_lite.db"
YEAR_START = 2018
class options_loader():

    def __init__(self):
        self.db = DB
        self.year_start = YEAR_START
        self.year = dt.date.today().year
        self.tm_years = self.set_tm_years()
        self.raceId = self.set_init_raceId()
        self.event_labels = self.get_event_labels(self.year)
        self.event = self.get_event(self.raceId)
        self.event_hdr = self.get_event_header_str(self.event)
        self.event_table = self.get_event_table(self.raceId)
        self.condensed_table = self.condense_event_table(self.event_table)
        self.radio_buttons = self.get_session_dict(self.event)


    def set_tm_years(self):
        tm_years = [{'label': year, 'value': year} for year in
                    np.arange(self.year_start, self.year + 1)]
        return tm_years

    def query(self, selection, table, condition):
        return f'select {selection} from {table} where {condition}'


    def query_join(self, selection, table, join, jtable, key):
        return f'select {selection} from {table} {join} join {jtable} using {key}'


    def exec_query(self, query, params):
        with sqlite3.connect(self.db) as cnx:
            df = pd.read_sql(query, cnx, params=params)
        return df


    def set_init_raceId(self):
        query = self.query('raceId', 'races', '(year=? AND round=?)')
        raceId = self.exec_query(query, (self.year, 1)).values[0, 0]
        return raceId

    def get_event_labels(self, year):
        query = self.query('raceId, round, date, name', 'races', 'year=?')
        event_data_df = self.exec_query(query, params=(year,))
        event_data_df['label'] = (
                    'Round ' + event_data_df['round'].astype(str) +
                    ': ' + event_data_df['date'].astype(str) +
                    ' ' + event_data_df['name'].astype(str))
        event_data_df['value'] = event_data_df['raceId']
        event_data = event_data_df[['label', 'value']].to_dict('records')
        return event_data

    def get_round(self, raceId):
        query = self.query('round', 'races', f'raceId={raceId}')
        round = self.exec_query(query, raceId).iat[0,0]

    def get_event(self, raceId):
        query = self.query('*', 'races', 'raceID=?')
        current_race_df = self.exec_query(query, params=(str(raceId),))
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

    def get_event_header_str(self, event_df):
        event_header_str = (f'Season {event_df["Season"]} ' +
                            f'Round {event_df["Round"]}: ' +
                            f'{event_df["Event"]}')
        return event_header_str

    def get_session_dict(self, event_df):
        current_sessions = [session[:-5] for session
                            in event_df.index
                            if session.endswith("Date")]
        session_dict = {'Race': 'R', 'Practice 1': 'FP1', 'Practice 2': 'FP2',
                        'Practice 3': 'FP3', 'Qualifier': 'Q', 'Sprint': 'S'}
        session_dict_list = [{'label': session, 'value': session_dict[session]}
                             for session in current_sessions]
        return session_dict_list

    def get_event_table(self, raceId):
        result_list = (['driverId', 'constructorId', 'positionOrder',
                        'positionText', 'laps', 'grid', 'time', 'statusId'])
        driver_list = ['driverRef', 'number', 'code', 'forename', 'surname',
                       'dob']
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

        qu_result_raceId = self.query(f'{result_select}', 'results r', 'raceID=?')
        qu_results_wstatus = self.query_join('r.*, s.status',
                                             f'({qu_result_raceId}) r',
                                             'left',
                                             'status s',
                                             '(statusID)')
        qu_results_wst_dr = self.query_join(f'r.*, {driver_select}',
                                            f'({qu_results_wstatus}) r',
                                            'left',
                                            'drivers d',
                                            '(driverID)')
        query = self.query_join(f'r.*, {constructor_select}',
                                f'({qu_results_wst_dr}) r',
                                'left',
                                'constructors c',
                                '(constructorID)')
        results_expand_df = self.exec_query(query, params=(str(raceId),))
        results_expand_df['Driver'] = results_expand_df['forename'].str.cat(
            results_expand_df['surname'], sep=' ')
        return results_expand_df

    def condense_event_table(self, results_expand_df):
        condensed_df = results_expand_df[['positionText', 'code', 'number',
                                          'laps', 'Driver', 'name', 'time',
                                          'status']]
        column_mapper = {'positionText': 'Pos', 'code': 'Code', 'number': 'No',
                         'laps': 'Laps', 'Driver': 'Driver',
                         'name': 'Constructor', 'time': 'Time',
                         'status': 'Status'}
        condensed_df = condensed_df.rename(column_mapper, axis=1)
        return condensed_df





