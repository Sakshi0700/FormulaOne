import sqlite3

import pandas as pd

con = sqlite3.connect("data/f1db_lite.db")
cur = con.cursor()

raceId=1098


result_list = (['resultId', 'raceId', 'driverId', 'constructorId',
                'positionOrder', 'laps', 'time', 'fastestLap', 'rank',
               'fastestLapTime', 'fastestLapSpeed', 'statusId'])

driver_list = (['driverRef', 'number', 'code', 'forename', 'surname', 'dob'])
driver_add = ([field + ' as driver_' + field
               for field in ['nationality', 'url']])

constructor_list = (['constructorId', 'constructorRef', 'name'])
constructor_add = ([field + ' as const_' + field
                    for field in ['nationality', 'url']])


result_select = ', '.join('r.' + result for result in result_list)
driver_select = ', '.join('d.' + driver for driver in driver_list + driver_add)
constructor_select = ', '.join('c.' + constructor
                               for constructor
                               in constructor_list + constructor_add)

raceid_query = ('SELECT *  ' +
                'FROM results ' +
                'LEFT JOIN status ' +
                'ON results.statusId=status.statusId ' +
                f'WHERE raceId={raceId}')

result_raceId_query = (f'SELECT {result_select} ' +
                       'FROM results r ' +
                       f'WHERE raceID={raceId}')
qu_results_wstatus = (f'SELECT r.*, s.status ' +
                      f'FROM ({result_raceId_query}) r ' +
                      f'LEFT JOIN status s ' +
                      f'USING (statusID)')
qu_results_wst_dr = (f'SELECT r.*, {driver_select} ' +
                     f'FROM ({qu_results_wstatus}) r ' +
                     'LEFT JOIN drivers d USING (driverID)')
qu_results_wst_dr_cn = (f'SELECT r.*, {constructor_select} ' +
                        f'FROM ({qu_results_wst_dr}) r ' +
                        'LEFT JOIN constructors c ' +
                        'USING (constructorID)')


race_result = pd.read_sql(qu_results_wst_dr_cn, con)

def get_event_labels(year):
    with msql.connect(user='root', host='localhost', database='f1db') as cnx:
        cursor = cnx.cursor()
        query = (f'SELECT raceId, round, date, name  FROM races WHERE year={year}')
        cursor.execute(query)
        rows = cursor.fetchall()
        event_data_df = pd.DataFrame(rows, columns=describe_races[0].values)
        rows = cursor.fetchall()
    event_data = [{'label': f'Round {round}: {date} {name}', 'value': raceId}
                  for (raceId, round, date, name) in rows]
    return event_data, event_data_df


year=2023
query = "SELECT raceId, round, date, name  FROM races WHERE year=?"
event_data_df = pd.read_sql(t, con, params=(year,))
event_data_df['label'] = ('Round ' + event_data_df['round'].astype(str) +
                          ': ' + event_data_df['date'].astype(str) +
                          ' ' + event_data_df['name'].astype(str))
event_data_df['value'] = event_data_df['raceId']
event_data = event_data_df[['label', 'value']].to_dict('records')

query = 'SELECT raceId, round, date, name  FROM races WHERE year=?'
with sqlite3.connect("data/f1db_lite.db") as cnx:
    event_data_df = pd.read_sql(query, cnx, params=(year,))
event_data_df['label'] = ('Round ' + event_data_df['round'].astype(str) +
                          ': ' + event_data_df['date'].astype(str) +
                          ' ' + event_data_df['name'].astype(str))
event_data_df['value'] = event_data_df['raceId']
event_data = event_data_df[['label', 'value']].to_dict('records')

result_list = (['driverId', 'constructorId', 'positionOrder', 'positionText'
               'laps', 'grid', 'time', 'statusId'])
driver_list = (['driverRef', 'number', 'code', 'forename', 'surname',
               'dob'])
driver_add = ([field + ' as driver_' + field for field in ['nationality', 'url']])
constructor_list = (['constructorId', 'constructorRef', 'name'])
constructor_add = ([field + ' as const_' + field for field in ['nationality', 'url']])



result_select = ', '.join('r.' + result for result in result_list)
driver_select = ', '.join('d.' + driver for driver in driver_list + driver_add)
constructor_select = ', '.join('c.' + constructor for constructor in constructor_list + constructor_add)

result_raceId_query = (f'SELECT {result_select} FROM results r WHERE raceID={raceId}')
qu_results_wstatus = (f'SELECT r.*, s.status FROM ({result_raceId_query}) r LEFT JOIN status s USING (statusID)')
qu_results_wst_dr = (f'SELECT r.*, {driver_select} FROM ({qu_results_wstatus}) r LEFT JOIN drivers d USING (driverID)')
qu_results_wst_dr_cn = (f'SELECT r.*, {constructor_select} FROM ({qu_results_wst_dr}) r LEFT JOIN constructors c USING (constructorID)')
cursor.execute(qu_results_wst_dr_cn)
results_expand_df = pd.DataFrame(cursor.fetchall(), columns=pd.DataFrame(cursor.description)[0])
results_expand_df['Driver'] = results_expand_df['forename'].str.cat(results_expand_df['surname'], sep=' ')

raceId = 1098
query_races =  'SELECT * FROM races WHERE raceID=?'
current_race_df = pd.read_sql(query_races, con, params=(raceId,))
current_race_df.columns
print(current_race_df.T.to_string())
Index(['raceId', 'year', 'round', 'circuitId', 'name', 'date', 'time', 'url',
       'fp1_date', 'fp1_time', 'fp2_date', 'fp2_time', 'fp3_date', 'fp3_time',
       'quali_date', 'quali_time', 'sprint_date', 'sprint_time'],
      dtype='object')

column_mapper = {'year': 'Season', 'round':'Round', 'name': 'Event',
                 'date': 'Race Date', 'time': 'Race Time',
                 'fp1_date': 'Practice 1 Date', 'fp1_time': 'Practice 1 Time',
                 'fp2_date': 'Practice 2 Date', 'fp2_time': 'Practice 2 Time',
                 'fp3_date': 'Practice 3 Date', 'fp3_time': 'Practice 3 Time',
                 'quali_date': 'Qualifier Date', 'quali_time': 'Qualifier Time',
                 'sprint_date': 'Sprint Date', 'sprint_time': 'Sprint Time'}
active_sessions = current_race_df.rename(column_mapper, axis=1).T[0].dropna()

year=2023
query = 'SELECT raceId FROM races WHERE (year=? AND round=1)'
with sqlite3.connect("data/f1db_lite.db") as cnx:
    raceId = pd.read_sql(query, cnx, params=(year,)).values[0, 0]
