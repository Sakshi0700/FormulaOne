#
# Heavily inspired by https://www.f1-tempo.com/
# Also this https://github.com/jessbuildsthings/f1-viz/


import datetime as dt
import sqlite3
import f1app_helpers as f1
import dash_bootstrap_components as dbc
import numpy as np
import pandas as pd
from dash import Dash, dcc, html, Input, Output
from dash_bootstrap_templates import ThemeSwitchAIO

dbc_css = (
    "https://cdn.jsdelivr.net/gh/AnnMarieW/dash-bootstrap-templates@V1.0.4/dbc.min.css"
)


app = Dash(__name__, external_stylesheets=[dbc.themes.PULSE, dbc_css])


this_year = dt.date.today().year
init_raceId = f1.get_init_raceId(this_year)
init_event = f1.get_event(init_raceId)
init_event_hdr = f1.get_event_header_str(init_event)
init_event_table = f1.get_event_table(init_raceId)
init_condensed_table = f1.condense_event_table(init_event_table)
init_radio_button_options = f1.get_session_dict(init_event)


header = dbc.Col(html.H3("Formula 1 Telemetry Visualization",
                         className="bg-primary text-white p-4 mb-2"), md=10)

year_dropdown = dcc.Dropdown(
    id='year-dropdown',
    options=f1.get_year_labels(2018, 2024),
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

placeholder = dbc.Col([dbc.Placeholder(color="info", className="me-1 mt-1 w-100")]
)

button_group = html.Div(
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
        dbc.Button(id="load-button", children='Load Race', value='R', color="primary", className="btn m-3"),
    ],
    className="radio-group"
)

# load_button = dbc.Col(dbc.Button(id="load-button", children='Load Race', value='R',
#                    color="primary", className="me-1")),

event_header = dbc.Col(html.H4
                           (children=init_event_hdr, id='event-header',
                               className="bg-info text-white p-4 mb-2"),
                            md=10)
event_table = dbc.Col(html.H6(children=dbc.Table.from_dataframe(
                        init_condensed_table, striped=True,
                        bordered=True, hover=True
                        ), id='event-table'), className="m-6 dbc", md=10
)



# button_group = html.Div(
#     [
#         dbc.RadioItems(
#             id="load-radios",
#             className="btn-group",
#             inputClassName="btn-check",
#             labelClassName="btn btn-outline-primary",
#             labelCheckedClassName="active",
#             options=init_radio_button_options,
#             value='R',
#         ),
#         dbc.Button("Load Session", color="primary", className="me-1"),
#     ],
#     className="radio-group",
# )

@app.callback(
    Output('event-dropdown', 'options'),
    [Input('year-dropdown', 'value')]
)

def update_events(year):
    return f1.get_event_labels(year)

@app.callback(
    [Output('event-header', 'children'),
     Output('event-table', 'children')],
    [Input('event-dropdown', 'value')]
)

def update_event_hdr(raceId):
    event_df = f1.get_event(raceId)
    event_header = f1.get_event_header_str(event_df)
    event_table_expand = f1.get_event_table(raceId)
    event_table_condensed = f1.condense_event_table(event_table_expand)
    event_table = dbc.Table.from_dataframe(
                        event_table_condensed, striped=True,
                        bordered=True, hover=True
                        )
    return event_header, event_table
#
# def update_selected_event(raceId):


row1 = html.Div(
    [ThemeSwitchAIO(aio_id="theme", themes=[dbc.themes.PULSE, dbc.themes.QUARTZ]),
        dbc.Row(
            [
                dbc.Col(year_dropdown, md=4),
                dbc.Col(event_dropdown, md=6)
                # dbc.Col(session_dropdown, md=4)
            ]
        ),
    ]
)




app.layout = dbc.Container([header, row1, event_header, button_group, event_table], fluid=True, className="m-4 dbc")
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