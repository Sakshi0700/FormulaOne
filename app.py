#
# Heavily inspired by https://www.f1-tempo.com/
# Also this https://github.com/jessbuildsthings/f1-viz/


import datetime as dt
import sqlite3

import fastf1

# import f1app_helpers as f1
from data_loaders import options_loader
import dash_bootstrap_components as dbc
import numpy as np
import pandas as pd
from dash import Dash, dcc, html, Input, Output, State
from dash_bootstrap_templates import ThemeSwitchAIO
import dash_mantine_components as dmc

dbc_css = (
    "https://cdn.jsdelivr.net/gh/AnnMarieW/dash-bootstrap-templates@V1.0.4/dbc.min.css"
)


app = Dash(__name__, external_stylesheets=[dbc.themes.PULSE, dbc_css])

ol = options_loader()


this_year = ol.year    #dt.date.today().year
init_raceId = ol.raceId    #f1.get_init_raceId(this_year)
init_event = ol.event   #f1.get_event(init_raceId)
init_event_hdr = ol.event_hdr   #f1.get_event_header_str(init_event)
init_event_table = ol.event_table   #f1.get_event_table(init_raceId)
init_condensed_table = ol.condensed_table   #f1.condense_event_table(init_event_table)
init_radio_button_options = ol.radio_buttons   #f1.get_session_dict(init_event)


current_year = dcc.Store(id='curr-year', data=this_year)
current_round = dcc.Store(id='curr-round', data=1)
current_race = dcc.Store(id='curr-race', data='R')

def get_drivers_table(drivers):
    return dbc.Col(html.H6(children=dbc.Table.from_dataframe(
            drivers, striped=True,
            bordered=True, hover=True
            ), id='drivers'), className="m-6 dbc", md=10)

header = dbc.Col(html.H3("Formula 1 Telemetry Visualization",
                         className="bg-primary text-white p-4 mb-2"), md=10)

year_dropdown = dcc.Dropdown(
    id='year-dropdown',
    options=ol.tm_years,
    value=str(this_year),
    multi=False,
    placeholder='Year'
)

event_dropdown = dcc.Dropdown(
    id='event-dropdown',
    value=str(init_raceId),
    # placeholder='Event',
    multi=False
)

# placeholder = dbc.Col([dbc.Placeholder(color="info", className="me-1 mt-1 w-100")]
# )




event_header = dbc.Col(html.H4(children=init_event_hdr, id='event-header',
                               className="bg-info text-white p-4 mb-2"), md=10)

button_group = dbc.Col(html.Div(
    [
        dbc.RadioItems(
            id="load-radios",
            className="btn-group",
            inputClassName="btn-check",
            labelClassName="btn btn-outline-primary",
            labelCheckedClassName="active",
            options=init_radio_button_options,
            value='R'
        ),
        dbc.Button(id="load-button", children='Load Race', value='R',
                   color="primary", className="btn m-3"),
    ],
    className="radio-group"
))


event_table = dbc.Col(html.H6(children=dbc.Table.from_dataframe(
                        init_condensed_table, striped=True,
                        bordered=True, hover=True
                        ), id='event-table'), className="m-6 dbc", md=10
)


tab1_content = dbc.Card(
    dbc.CardBody(
        [
            html.H4('Add some visualizations', className="card-text"),
            dbc.Col(get_drivers_table(pd.DataFrame([])), id='drivers')
        ]
    )
)

tab2_content = dbc.Card(
    dbc.CardBody(
        [
            html.P('Add some statistics', className="card-text")
        ]
    )
)

tabs = html.Div(
    [
        dbc.Tabs(
            [
                dbc.Tab(event_table, label='Table'),
                dbc.Tab(tab1_content, label='Visualizations'),
                dbc.Tab(tab2_content, label='Statistics')
            ],
            id='tabs', active_tab='Table'
        ),
        html.Div(id='content')
    ]
)



@app.callback(
    [Output('event-dropdown', 'options'),
     Output('curr-year', 'data')],
    [Input('year-dropdown', 'value')]
)

def update_events(year):
    return ol.get_event_labels(year), year

@app.callback(
    [Output('event-header', 'children'),
     Output('event-table', 'children'),
     Output('curr-round', 'data')],
    [Input('event-dropdown', 'value')]
)

def update_event_hdr(raceId):
    event_df = ol.get_event(raceId)
    event_header = ol.get_event_header_str(event_df)
    event_table_expand = ol.get_event_table(raceId)
    event_table_condensed = ol.condense_event_table(event_table_expand)
    event_table = dbc.Table.from_dataframe(
                        event_table_condensed, striped=True,
                        bordered=True, hover=True
                        )
    round = event_df['Round']
    print(round)
    return event_header, event_table, round



@app.callback(
    [Output('drivers', 'value')],
    [State('curr-year', 'data'),
     State('curr-round', 'data'),
     State('load-radios', 'value'),
     Input('load-button', 'n_clicks')]
)

def load_session(year, round, race, nclicks):
    if nclicks:
        session = fastf1.get_session(int(year), int(round), race)
        session.load()
        drivers = pd.DataFrame(session.get_drivers())
    else:
        drivers = pd.DataFrame(['No Race Selected'])
    return get_drivers_table(drivers)



@app.callback(Output("content", "children"),
              [Input("tabs", "active_tab")])
def switch_tab(at):
    if at == "Table":
        return event_table
    elif at == "Vizualizations":
        return tab1_content
    elif at == 'Statistics':
        return tab2_content
    return html.P("This shouldn't ever be displayed...")



row1 = html.Div(
    [ThemeSwitchAIO(aio_id="theme", themes=[dbc.themes.PULSE, dbc.themes.QUARTZ]),
        dbc.Row(
            [
                dbc.Col(year_dropdown, md=4),
                dbc.Col(event_dropdown, md=6)
                # dbc.Col(session_dropdown, md=4)
            ]),
        dbc.Row(
            [
                dbc.Col(event_header, className="md=10")
            ]),
        dbc.Row(
            [
                dbc.Col(button_group, className="w-40", align='left')
            ], className="md=10",)
    ]
)



app.layout = dbc.Container([current_year, current_race, current_round,
                            header, row1, tabs], fluid=True, className="m-4 dbc")


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