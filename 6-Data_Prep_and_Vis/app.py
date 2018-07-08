import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
import pandas as pd
import numpy as np
import h5py
import os, glob
import re
from datetime import datetime, date, time
from six import iteritems

from blond import Blond

##########################
def get_time_diff(t1,t2):
    t1_s = (t1.hour*60*60 + t1.minute*60 + t1.second)
    t2_s = (t2.hour*60*60 + t2.minute*60 + t2.second)

    delta_s = max([t1_s, t2_s]) - min([t1_s, t2_s])
    return delta_s
##########################
"""Read MEDAL and CLEAR data """
blond = Blond(date(2016,10,5),start_ts=time(0,50,0),end_ts=time(1,10,10))



"""Checking if files have been retrieved"""
print("list the files:")
print(blond.list_files())

##########################
"""signals acquisited by MEDAL"""
print("Files from Medal 1")
medal_file = blond.list_files()['medal-2'][0]
print(type(medal_file["current1"]))
print([key for key in medal_file.keys()])
##########################
"""signals acquisited by CLEAR"""
print("Keys from CLEAR")
clear_file = blond.list_files()['clear'][0]
print([key for key in clear_file.keys()])
##########################
device = 'medal-2'
signal = 'current1'

"""Raw signal with offset and calibration factor attributes"""
dict_signal = blond.dict_read_signal(device, signal)
print(dict_signal)


"""calibrated signal"""
blond.center_and_calibrate(dict_signal)
##########################

def create_options():
    seconds = get_time_diff(start_ts,end_ts)
    minutes = int(seconds/60)
    hours = int(minutes/60)

    options={
        "duration":[{"label":"Duration in Seconds", "value":"None"}]+ [{"label":str(i/10.0)+" sec","value":i/10.0} for i in range(1,101)],
        "seconds":[{"label":"Start Second", "value":"None"}]+[{"label":i,"value":i} for i in range(60)],
        "minutes":[{"label":"Start Minute", "value":"None"}]+[{"label":i,"value":i} for i in range(60)],
        "hours":[{"label":"Start Hour", "value":"None"}]+[{"label":i,"value":i} for i in range(start_ts.hour,end_ts.hour+1)],
        "critical":{
            "start":{
                "minutes":[],
                "seconds":[]
            },
            "end":{
                "minutes":[],
                "seconds":[]
            }
        }
    }

    if start_ts.hour != end_ts.hour:
        options["critical"]["start"]["minutes"] = [{"label":"Start Minute", "value":"None"}]+ [{"label":i,"value":i} for i in range(start_ts.minute,60)]
        options["critical"]["end"]["minutes"] = [{"label":"Start Minute", "value":"None"}]+ [{"label":i,"value":i} for i in range(0,end_ts.minute+1)]
        if start_ts.minute != end_ts.minute:
            options["critical"]["start"]["seconds"] = [{"label":"Start Second", "value":"None"}]+[{"label":i,"value":i} for i in range(start_ts.second,60)]
            options["critical"]["end"]["seconds"] = [{"label":"Start Second", "value":"None"}]+[{"label":i,"value":i} for i in range(0,end_ts.second+1)]
        else:
            options["critical"]["start"]["seconds"] = [{"label":"Start Second", "value":"None"}]+[{"label":i,"value":i} for i in range(start_ts.second,end_ts.second+1)]

    else:
        options["critical"]["start"]["minutes"] = [{"label":"Start Minute", "value":"None"}]+[{"label":i,"value":i} for i in range(start_ts.minute,end_ts.minute+1)]
        # in this case, hour values are same, we do not need critical end, because we will always see that, hour of time will always be equal to hour of start time

    return options

time_options = create_options()
##########################

app = dash.Dash()

app.layout = html.Div(children=[
    html.H3(children='BLOND Dataset'),

    html.Div([
        html.Div([
            html.Div([
                dcc.Dropdown(
                    id="hour",
                    options=time_options["hours"],
                    value = "None",
                ),
                ],
                style={"display":"inline-block", "width":"25%"}
            ),
            html.Div([
                dcc.Dropdown(
                    id="minute",
                    options=time_options["minutes"],
                    value = "None",
                ),
                ],
                style={"display":"inline-block", "width":"25%"}
            ),
            html.Div([
                dcc.Dropdown(
                    id="second",
                    options=time_options["seconds"],
                    value = "None",
                ),
                ],
                style={"display":"inline-block", "width":"25%"}
            ),
            html.Div([
                dcc.Dropdown(
                    id="duration",
                    options=time_options["duration"],
                    value = "None",
                ),
                ],
                style={"display":"inline-block", "width":"25%"}
            ),

        ],
        style= {"width":"50%", "display":"inline-block"}
        ),
        html.Div([
            html.Div([
                dcc.Dropdown(
                    id='graph_type',
                    options=[{"label":"Aggregated Signals","value":0},{"label":"Individual Signals","value":1}],
                    value=0,
                ),
            ],
            style={"display":"inline-block", "width":"15%"}
            ),
            html.Div([
                dcc.Dropdown(
                    id="phases",
                    value = 1,
                ),
            ],
            style={"display":"inline-block", "width":"15%"}
            ),
        ],
        )
        ],
    ),
    # dcc.RangeSlider(
    #     id="timerange",
    #     count=1,
    #     min=-5,
    #     max=10,
    #     step=0.5,
    #     value=[-3, 7]
    # ),
    dcc.Graph(
        id='graph',
    )
])



app.scripts.config.serve_locally = True
app.css.config.serve_locally = True

from dash.dependencies import Input, Output

@app.callback(
    Output("phases", "options"),
    [
        Input("graph_type","value"),
    ]
)
def update_phases_options(graph_type):
    if graph_type == 0: ## aggregated signals
        return [{"label":"Phase:"+str(i), "value":i} for i in range(1,4)]
    elif graph_type == 1: ## individual signals
        return [{"label":"Phase:"+str(i), "value":i} for i in range(1,7)]


@app.callback(
    Output("minute","options"),
    [
        Input("hour","value"),
    ]
)
def update_minute_options(hour):
    if hour == start_ts.hour:
        return time_options["critical"]["start"]["minutes"]
    elif hour == end_ts.hour:
        return time_options["critical"]["end"]["minutes"]
    else:
        return time_options["minutes"]
@app.callback(
    Output("second", "options"),
    [
        Input("hour","value"),
        Input("minute","value"),
    ]
)
def update_second_options(hour,minute):
    if hour == start_ts.hour and minute == start_ts.minute:
        return time_options["critical"]["start"]["seconds"]
    elif hour == end_ts.hour and minute == end_ts.minute:
        return time_options["critical"]["end"]["seconds"]
    else:
        return time_options["seconds"]

@app.callback(
    Output("duration", "options"),
    [
        Input("hour","value"),
        Input("minute","value"),
        Input("second","value"),
    ]
)
def update_duration_options(hour,minute,second):
    if not(type(hour) == int and type(minute)==int and type(second) ==int) :
        return time_options["duration"]

    requested_time = time(hour,minute,second)
    distance_to_end = get_time_diff(requested_time, end_ts)
    if distance_to_end+1 < 10:
        max_duration = distance_to_end+1
        return [{"label":"Duration in Seconds", "value":"None"}]+ [{"label":str(i/10.0)+" sec","value":i/10.0} for i in range(1,(max_duration*10)+1)]
    else:
        return time_options["duration"]

@app.callback(
    Output("graph", "figure"),
    [
        Input("graph_type","value"),
        Input("phases", "value"),
        Input("hour","value"),
        Input("minute","value"),
        Input("second","value"),
        Input("duration","value")
    ]
)
def update_graph(graph_type,phase,hour,minute,second,duration):

    if not(type(hour) == int and type(minute)==int and type(second) ==int and type(duration) == float) :
        return 0
    the_mode= "markers+lines"
    title = ""
    data_fields = ""
    sps = 0
    #print(blond.list_files().keys())
    if graph_type == 0: ## aggregated signals
        title = "Aggregated Signals"
        data_fields = ["clear"]
        sps = 50000
    elif graph_type == 1: ## individual signals
        title = "Individual Signals"
        data_fields = [key for key in blond.list_files().keys() if key.startswith("medal")]
        sps = 6400


    requested_time = time(hour,minute,second)
    graph_list = []
    for data_field in data_fields:
        file_index = blond.find_corresponding_file(requested_time, blond.time_stamps[data_field])
        time_diff = get_time_diff(requested_time , blond.time_stamps[data_field][file_index])
        data_index_shift = time_diff * sps
        temp_data = blond.list_files()[data_field][file_index]["current"+str(phase)][data_index_shift:data_index_shift + int(sps*duration)]
        len_data = temp_data.shape[0]
        #print("length of "+data_field + "is:"+str(len_data))
        #print()
        temp_graph = go.Scatter(
            x = np.linspace(1,15,len_data),
            y = temp_data[()],
            mode=the_mode,
            name=data_field.title()
        )
        graph_list.append(temp_graph)

    #print("returning from update graph")
    return go.Figure(
        data = graph_list,
        layout = go.Layout(
            title = title,
            showlegend = True,
            legend = go.Legend(
                x = 0,
                y = 1.0
            ),
            margin = go.Margin(
                l=80, r=80, t=60, b=30
            ),
        ),
    )


if __name__ == '__main__':
    app.run_server(debug=False,port=8051)
