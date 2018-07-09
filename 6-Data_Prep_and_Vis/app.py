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

from blond import Blond, get_time_diff,increment_time

"""Read MEDAL and CLEAR data """
blond = Blond(date(2016,10,5))
##########################

def create_options(device):
    if device == "default":
        options={
            "duration":[{"label":"Duration in Seconds", "value":"None"}]+ [{"label":str(i)+" sec","value":i} for i in range(1,10 +1)],
            "seconds":[{"label":"Start Second", "value":"None"}]+[{"label":i,"value":i} for i in range(60)],
            "minutes":[{"label":"Start Minute", "value":"None"}]+[{"label":i,"value":i} for i in range(60)],
        }
        return options
    start_ts = blond.min_time_of_start["time"] ## maximum start time
    end_ts = blond.max_time_of_end["time"] ## minimum end time of the data. so these are boundaries
    print(start_ts)
    print(end_ts)
    if device == "clear":
        start_ts = blond.time_limits["clear"]["earliest"]
        end_ts = blond.time_limits["clear"]["latest"]
    options={
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

time_options ={"default": create_options("default"), "clear":create_options("clear"),"medals":create_options("medals")}

##########################

app = dash.Dash()

app.layout = html.Div(children=[
    html.H3(children='BLOND Dataset'),

    html.Div([
        html.Div([
            html.Div([
                dcc.Dropdown(
                    id="hour",
                    options=time_options["clear"]["hours"],
                    value = "None",
                ),
                ],
                style={"display":"inline-block", "width":"25%"}
            ),
            html.Div([
                dcc.Dropdown(
                    id="minute",
                    options=time_options["default"]["minutes"],
                    value = "None",
                ),
                ],
                style={"display":"inline-block", "width":"25%"}
            ),
            html.Div([
                dcc.Dropdown(
                    id="second",
                    options=time_options["default"]["seconds"],
                    value = "None",
                ),
                ],
                style={"display":"inline-block", "width":"25%"}
            ),
            html.Div([
                dcc.Dropdown(
                    id="duration",
                    options=time_options["default"]["duration"],
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
    Output("hour","options"),
    [
        Input("graph_type","value"),
    ]
)
def update_hour_options(graph_type):

    if graph_type == 1:
        return time_options["medals"]["hours"]

    return time_options["clear"]["hours"]
@app.callback(
    Output("minute","options"),
    [
        Input("hour","value"),
        Input("graph_type","value"),
    ]
)
def update_minute_options(hour,graph_type):

    max_of_start = {"time":blond.time_limits["clear"]["earliest"],"device":"clear"}
    min_of_end = {"time":blond.time_limits["clear"]["latest"],"device":"clear"}
    device = "clear"
    if graph_type == 1: ## individual signals
        ### here find minimum of the end times and maximum of the start times
        ### among all medals. Because we are showing all the medals data together
        ### we cannot show data beyond these times.
        max_of_start = blond.min_time_of_start
        min_of_end = blond.max_time_of_end
        device = "medals"

    if hour == max_of_start["time"].hour:
        return time_options[device]["critical"]["start"]["minutes"]
    elif hour == min_of_end["time"].hour:
        return time_options[device]["critical"]["end"]["minutes"]
    else:
        return time_options["default"]["minutes"]
@app.callback(
    Output("second", "options"),
    [
        Input("hour","value"),
        Input("minute","value"),
        Input("graph_type","value"),
    ]
)
def update_second_options(hour,minute,graph_type):
    start_ts = blond.time_limits["clear"]["earliest"]
    end_ts =blond.time_limits["clear"]["latest"]
    device = "clear"
    if graph_type == 1: ## individual signals
        ### here find minimum of the end times and maximum of the start times
        ### among all medals. Because we are showing all the medals data together
        ### we cannot show data beyond these times.
        start_ts = blond.min_time_of_start["time"]
        end_ts = blond.max_time_of_end["time"]
        device = "medals"

    if hour == start_ts.hour and minute == start_ts.minute:
        return time_options[device]["critical"]["start"]["seconds"]
    elif hour == end_ts.hour and minute == end_ts.minute:
        return time_options[device]["critical"]["end"]["seconds"]
    else:
        return time_options["default"]["seconds"]

@app.callback(
    Output("duration", "options"),
    [
        Input("hour","value"),
        Input("minute","value"),
        Input("second","value"),
        Input("graph_type","value"),
    ]
)
def update_duration_options(hour,minute,second,graph_type):
    if not(type(hour) == int and type(minute)==int and type(second) ==int) :
        return time_options["default"]["duration"]

    end_ts =blond.time_limits["clear"]["latest"]
    device = "clear"
    if graph_type == 1: ## individual signals
        end_ts = blond.max_time_of_end["time"]

    requested_time = time(hour,minute,second)
    distance_to_end = get_time_diff(requested_time, end_ts)
    if distance_to_end+1 < 10:
        max_duration = distance_to_end+1
        return [{"label":"Duration in Seconds", "value":"None"}]+ [{"label":str(i)+" sec","value":i} for i in range(1,max_duration+1)]
    else:
        return time_options["default"]["duration"]

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

    if not(type(hour) == int and type(minute)==int and type(second) ==int and type(duration) == int) :
        return 0
    the_mode= "markers+lines"
    title = ""
    devices = ""
    sps = 0
    #print(blond.list_files().keys())
    if graph_type == 0: ## aggregated signals
        title = "Aggregated Signals"
        devices = ["clear"]
        sps = 50000
    elif graph_type == 1: ## individual signals
        title = "Individual Signals"
        devices = [key for key in blond.list_files().keys() if key.startswith("medal")]
        print(devices)
        sps = 6400


    requested_time = time(hour,minute,second)
    end_time = increment_time(requested_time, seconds=duration)
    graph_list = []
    for device in devices:
        temp_data = blond.read_data( device=device,signal="current"+str(phase),start_ts=requested_time, end_ts=end_time)
        len_data = temp_data.shape[0]
        #print("length of "+device + "is:"+str(len_data))
        #print()
        temp_graph = go.Scatter(
            x = np.linspace(0,duration,len_data),
            y = temp_data[()],
            mode=the_mode,
            name=device.title()
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
    app.run_server(debug=False,port=8050)
