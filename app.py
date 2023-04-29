#
# Heavily inspired by https://www.f1-tempo.com/
# Also this https://github.com/jessbuildsthings/f1-viz/

import pickle
import datetime as dt
import sqlite3
import visualization_helpers
import fastf1
# import f1app_helpers as f1
from data_loaders import options_loader
import dash_bootstrap_components as dbc
import numpy as np
import pandas as pd
from dash import Dash, dcc, html, Input, Output, State
from dash_bootstrap_templates import ThemeSwitchAIO
from dash_extensions.enrich import DashProxy, ServersideOutput, ServersideOutputTransform
import dash_mantine_components as dmc
import time
fastf1.Cache.enable_cache('data/cache')

dbc_css = (
    "https://cdn.jsdelivr.net/gh/AnnMarieW/dash-bootstrap-templates@V1.0.4/dbc.min.css"
)


# app = Dash(__name__, external_stylesheets=[dbc.themes.PULSE, dbc_css])
app = DashProxy(
    external_stylesheets=[dbc.themes.PULSE],
    title='Fun with F1',
    suppress_callback_exceptions=True,
    transforms=[ServersideOutputTransform()]
)

server = app.server



##############################################################################
# Main Page
##############################################################################

# initial data loader
ol = options_loader()


# current session year, round, and race storage
current_year = dcc.Store(id='curr-year', data=ol.year)
current_round = dcc.Store(id='curr-round', data=1)
current_race = dcc.Store(id='curr-race', data='R')
current_session = dcc.Store(id='curr-session', data=fastf1.get_session(ol.year, 1, 'R'))

# Main header
header = dbc.Col(html.H3("Formula 1 Telemetry Visualization",
                         className="bg-primary text-white p-4 mb-2"), md=10)

# Select the year to find a race,
# Should populate the current_year store and the event_dropdown
year_dropdown = dcc.Dropdown(
    id='year-dropdown',
    options=ol.tm_years,
    value=str(ol.year),
    multi=False,
    placeholder='Year'
)

# Select the round to find a race
# Should populate the event_header, event_table, and current_round store
# and any place that might need initial drivers
event_dropdown = dcc.Dropdown(
    id='event-dropdown',
    value=str(ol.raceId),
    multi=False
)

# Displays the currently selected round
# Triggered by the event_dropdown
event_header = dbc.Col(html.H4(children=ol.event_hdr, id='event-header',
                               className="bg-info text-white p-4 mb-2"), md=10)

# Pick which race from the selected event to load
# Should populate the current_race store
race_dropdown = dcc.Dropdown(
    id='race-dropdown',
    options=ol.race_labels,
    value=str(ol.year),
    multi=False,
    placeholder='Race'
)

# Press to load a session
# Should pass the session to curr_session store
# Session should be loaded before changing tabs
loading_spinner = html.Div(
    [
        dbc.Button("Load Selected Race", id="loading-button", n_clicks=0),
        dbc.Spinner(html.Div(id="loading-output"), color='info'),
    ]
)




##############################################################################
##############################################################################
# Tabs
##############################################################################
##############################################################################



#############################################################################
# Table tab
##############################################################################

# Table for race results
# Populated by selecting a year and Round
table_tab = dbc.Col(html.H6(children=dbc.Table.from_dataframe(
                                  ol.condensed_table, striped=True,
                                  bordered=True, hover=True
                                  ), id='event-table'
                              ), className="m-6 dbc", md=10
)



#############################################################################
# Compare Drivers tab
##############################################################################

# Dropdown for both drivers
# Populated after selecting a round, but shouldn't use until you
# load a session
dropdown_divs = html.Div([
    html.H1(children='F1 Dash View', style={
            'textAlign': 'center'}, className="header-text"),
    dcc.Dropdown(id='driver-1-dd'),
    dcc.Dropdown(id='driver-2-dd'),
])

# Driver comparison images.
# Populated by the
image_divs = html.Div(id="compare-img")

# Generate Images
# Disabled until drivers are selected

# Allows the user to select 2 drivers to compare
# Should only be clicked after a session is loaded
compare_tab = dbc.Container([
    dropdown_divs,
    dbc.Button(children='Load Drivers',
               id="compare-drivers-button",
               disabled=True, color="primary",
               n_clicks=0, className="btn m-3"),
    image_divs,
])


#############################################################################
# Compare Drivers tab - need to add something here
##############################################################################

statistics_tab = dbc.Card(
    dbc.CardBody(
        [
            html.P('Add some statistics', className="card-text")
        ]
    )
)

#############################################################################
# Compare Drivers tab - need to add Sakshi's visualizations
##############################################################################

visualizations_tab = dbc.Card(
    dbc.CardBody(
        [
            html.P('Add some visualizations', className="card-text")
        ]
    )
)


#############################################################################
# Tab Grouping
##############################################################################

tabs = html.Div(
    [
        dbc.Tabs(
            [
                dbc.Tab(table_tab, label='Table'),
                dbc.Tab(compare_tab, label='Compare Drivers'),
                dbc.Tab(statistics_tab, label='Statistics'),
                dbc.Tab(visualizations_tab, label='Visualizations')
            ],
            id='tabs', active_tab='Table'
        ),
        html.Div(id='content')
    ]
)


#############################################################################
# Callback Section
##############################################################################

# Updates the events and the current year from the year dropdown
@app.callback(
    [Output('event-dropdown', 'options'),
     Output('curr-year', 'data')],
    [Input('year-dropdown', 'value')]
)
def update_year(year):
    return ol.get_event_labels(year), year


# Populates the event header, results table, race dropdown, and drivers
# from the round dropdown, stores the round
@app.callback(
    [Output('event-header', 'children'),
     Output('event-table', 'children'),
     Output('curr-round', 'data'),
     Output('driver-1-dd','options'),
     Output('driver-2-dd','options')],
    [Input('event-dropdown', 'value')]
)

def update_event(raceId):
    event_df = ol.get_event(raceId)
    event_header = ol.get_event_header_str(event_df)
    event_table_expand = ol.get_event_table(raceId)
    event_table_condensed = ol.condense_event_table(event_table_expand)
    event_table = dbc.Table.from_dataframe(
        event_table_condensed, striped=True,
        bordered=True, hover=True
    )
    curr_round = event_df['Round']
    drivers = ol.get_drivers(event_table_condensed)
    return event_header, event_table, curr_round, drivers, drivers


# Loads a fastf1 session after clicking the load selected race.
# Session is cached so it is faster to load the visualizations.
# After it stops spinning and says race is loaded, you can move
# on to other tabs
@app.callback(
    [Output("loading-output", "children"),
     Output("loading-button", "n_clicks")],
    [State("curr-year", "data"),
     State("curr-round", "data"),
     State("curr-race", "data"),
     Input("loading-button", "n_clicks")]
)
def load_output(curr_year, curr_round, curr_race, n):
    if n:
        time.sleep(1)
        session = fastf1.get_session(int(curr_year), int(curr_round), curr_race)
        session.load()
        return f"Race loaded", 0
    return "Race not loaded yet", 0


# Tab switching callback
@app.callback(Output("content", "children"),
              [Input("tabs", "active_tab")])

def switch_tab(at):
    if at == "Table":
        return table_tab
    elif at == "Compare Drivers":
        return compare_tab
    elif at == 'Statistics':
        return statistics_tab
    elif at == 'Visualizations':
        return visualizations_tab
    return


# Driver Selection callback
# Once drivers are selected, the compare drivers button is enabled
@app.callback([Output("compare-drivers-button", "disabled"),
               Output("compare-drivers-button", "children")],
              [Input('driver-1-dd','value'),
               Input('driver-2-dd','value')])

def enable_compare(driver1, driver2):
    if (driver1 and driver2):
        return False, "Compare Drivers"
    return True, "Load Drivers"


# Compare drivers button call back
# When clicked it reloads a session from cache and creates the
# comparison plots.
@app.callback(
    [
        Output('compare-img', 'children'),
    ],
    [
        State('curr-year', 'data'),
        State('curr-round', 'data'),
        State('curr-race', 'data'),
        State('driver-1-dd', 'value'),
        State('driver-2-dd', 'value'),
        Input('compare-drivers-button', 'n_clicks')
    ])


def compareDrivers(curr_year, curr_round, curr_race, driver1, driver2, n_clicks):
    if n_clicks:
        session = fastf1.get_session(int(curr_year), int(curr_round),
                                     curr_race)
        session.load()
        lapL = session.laps.pick_driver(driver1).pick_fastest()
        lapR = session.laps.pick_driver(driver2).pick_fastest()

        left_1 = visualization_helpers.get_data_for_ngear(lapL, session)
        right_1 = visualization_helpers.get_data_for_ngear(lapR, session)

        left_2 = visualization_helpers.get_data_for_rpm(lapL, session)
        right_2 = visualization_helpers.get_data_for_rpm(lapR, session)
        output = [
            html.Img(src=left_1),
            html.Img(src=right_1),
            html.Img(src=left_2),
            html.Img(src=right_2)
        ]
        return output  # left_1, right_1, left_2, right_2
    else:
        return []


row1 = html.Div(
    [ThemeSwitchAIO(aio_id="theme", themes=[dbc.themes.PULSE, dbc.themes.QUARTZ]),
        dbc.Row(
            [
                dbc.Col(year_dropdown, md=4),
                dbc.Col(event_dropdown, md=6)
            ]),
        dbc.Row(
            [
                dbc.Col(event_header, className="md=10")
            ]),
        dbc.Row(
            [
                dbc.Col(race_dropdown, md=4),
                dbc.Col(loading_spinner, md=4)
            ], className="md=10",)
     ]
)


app.layout = dbc.Container([current_year, current_race, current_round,
                            header, row1, tabs],
                           fluid=True, className="m-4 dbc")


# @app.callback(
#     # Output("pie-chart", "figure"),
#     Output("year-dropdown", "value"),
#     Output("event-dropdown", "value"),
#     Input(ThemeSwitchAIO.ids.switch("theme"), "value"),
# )
# def generate_chart(toggle):
#     template = "minty" if toggle else "cyborg"
#     fig = px.pie(df, values=value, names="day", template=template)
#     return fig

if __name__ == "__main__":
    app.run_server(debug=True)
