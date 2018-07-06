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

##########################
class Blond(object):
    """
        class blond: attributes: date, list of files
    """
    _SD_centered = []
    _SD_calibrated = []

    def __init__(self, date, day_data = {}):
        self.date = date
        self._day_data = day_data


    def list_files(self):
        return self._day_data


    @staticmethod
    def _regex_map(pattern, strings_list):

        regex_func = lambda f: re.search(pattern, f)
        filter_list = map(regex_func, strings_list)
        filter_list = filter(lambda x: x is not None, list(filter_list))
        filter_list = map(lambda x: x.group(1), list(filter_list))
        return list(filter_list)


    def _read_files_from_folder(self, files, start_ts, end_ts,path_to_files):
        """This method gets file in the folder w.r.t. to the timeframe start_ts - end_ts

            How it works:
            1. gets a list of files in the folder
            2. extracts timestamps with _regex_map() method and converts it to datetime.time()
            3. fetch the first file which fits the timeframe
            4. add the remaining files by the filter start_timestamp <= file_timestamp <= end_timestamp

        """
        pattern = r'(\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2})'
        timestamps = self._regex_map(pattern, files)
        time_format = '%Y-%m-%dT%H-%M-%S'
        timestamps = list(map(lambda ts: datetime.strptime(ts, time_format ).time(), timestamps))

        """ get the first file timestamp"""
        current_ts = timestamps[0]
        i=1
        while start_ts >= current_ts:
            current_ts = timestamps[i]
            i+=1

        """add first file timestamp to the rest"""
        timestamps = [timestamps[i-2]] + [ts for ts in timestamps if start_ts <= ts <= end_ts]
        timestamps_filter= map(lambda ts: datetime.combine(self.date, ts).strftime(time_format), list(timestamps))

        res_list = []
        for ts in timestamps_filter:
            res_list += [f for f in files if ts in f]

        data = []
        for a_file in res_list:
            try:
                data.append(h5py.File(path_to_files + a_file,'r+'))
            except:
                temp_file = h5py.File(path_to_files + a_file, 'r')
                temp_file.close()
                data.append(h5py.File(path_to_files + a_file,'r+'))

        return data


    def read_files(self, start_ts, end_ts):
        """ read_files() method scans the relevant folders and return a dictionary
            with the files relevant to the timeframe (start_ts, end_ts)
                {'clear'  : [files],
                 'medal-1': [files],
                 'medal-2': [files],
                    ...
                }
        """

        """READING CLEAR UNIT"""
        path_to_clear = './data/clear/'
        files_all = next(os.walk(path_to_clear))[2]
        self._day_data['clear'] = self._read_files_from_folder(files_all, start_ts, end_ts,path_to_clear)
        #self._day_data['clear'] = [h5py.File(path_to_clear + file_name,'r+') for file_name in target_files]



        """READING MEDAL UNITS"""

        path_to_medals = './data/medal*/'
        for folder in glob.glob(path_to_medals):
            files_all = next(os.walk(folder))[2]
            medal_name = re.search(r'(medal-\d+)', folder).group(1)
            self._day_data[medal_name] = self._read_files_from_folder(files_all, start_ts, end_ts,folder)
            #self._day_data[medal_name] = [h5py.File(folder + file_name,'r+') for file_name in target_files]


    """ center_inplace and calibrate inplace read file-by-file, do the corresponding operations and write back
        good thing: we can process much more files like that and not be bounded by memory since each file is less than 3 GB
        bad thing: we can't coerse from int to float
        We do not use them.
    """
    def center_inplace(self, device, signal):
        if device+signal in self._SD_centered:
            print("Signal '{}' for '{}' has been already centered.".format(signal, device))
            return
        else:
            self._SD_centered.append(device+signal)
            data_list = self._day_data[device]
            if device != 'clear': #NO OFFSET FOR CLEAR DEVICE
                for i, data_file in enumerate(data_list):
                    DC_offset = data_file[signal].attrs['removed_offset']
                    #print(DC_offset)
                    data_file[signal][:] = data_file[signal][:] + DC_offset
                    self._day_data[device][i] = data_file


    def calibrate_inplace(self, device, signal):
        if device+signal in self._SD_calibrated:
            print("Signal '{}' for '{}' has been already calibrated.".format(signal, device))
            return
        else:
            self._SD_calibrated.append(device+signal)
            data_list = self._day_data[device]
            for i, data_file in enumerate(data_list):
                factor = data_file[signal].attrs['calibration_factor']
                #print(factor)
                data_file[signal][:] = (data_file[signal][:] * factor)
                self._day_data[device][i] = data_file


    def dict_read_signal(self, device, signal):
        """reads the signal of the corresponding device and writes it to the dictionary"""
        files = self._day_data[device]
        return {'signal': device+'_'+signal,
                'attributes': list(map(lambda f: {'DC_offset': 0 if device == 'clear' else f[signal].attrs['removed_offset'],
                              'calibration_factor': f[signal].attrs['calibration_factor'],
                              'values': f[signal][:]
                             }, files))

               }

    def center_and_calibrate(self, dict_signal):
        """reads the dictionary from the dict_read_signal() method, then centers and calibrates it"""
        data_calibrated = {}
        signal_data = dict_signal['attributes']
        for data in signal_data:
            data_calibrated[dict_signal['signal']] = ((data['values'] + data['DC_offset']) * data['calibration_factor']).astype("<f4")

        return data_calibrated
##########################
blond = Blond(date(2016,10,5))

""" Define a timeframe"""
start_ts = time(0,10,0) # start_hours_minutes
end_ts   = time(0,10,10)

"""Read MEDAL and CLEAR data """
blond.read_files(start_ts, end_ts)


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

##########################

app = dash.Dash()

app.layout = html.Div(children=[
    html.H3(children='BLOND Dataset'),

    # html.Div(children='''
    #     Dash: A web application framework for Python.
    # '''),
    html.Div([
        html.Div([
            html.Div([
                dcc.Dropdown(
                    id="hour",
                    options=[{"label":i,"value":i} for i in range(24)],
                    value = "Start Hour:",
                ),
                ],
                style={"display":"inline-block", "width":"33%"}
            ),
            html.Div([
                dcc.Dropdown(
                    id="minute",
                    options=[{"label":i,"value":i} for i in range(60)],
                    value = "Start Minute:",
                ),
                ],
                style={"display":"inline-block", "width":"33%"}
            ),
            html.Div([
                dcc.Dropdown(
                    id="second",
                    options=[{"label":i,"value":i} for i in range(60)],
                    value = "Start Seconds:",
                ),
                ],
                style={"display":"inline-block", "width":"33%"}
            ),
            dcc.Dropdown(
                id='graph_type',
                options=[{"label":"Aggregated Signals","value":0},{"label":"Individual Signals","value":1}],
                value=0,
            ),
        ],
        style= {"width":"30%", "display":"inline-block"}
        ),
        html.Div([
            dcc.Dropdown(
                id="phases",
                value = 1,
            ),
        ],
        style= {"width":"30%", "display":"inline-block"}
        )
        ],
    ),
    dcc.RangeSlider(
        id="timerange",
        count=1,
        min=-5,
        max=10,
        step=0.5,
        value=[-3, 7]
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
    Output("graph", "figure"),
    [
        Input("graph_type","value"),
        Input("phases", "value"),
        Input("hour","value"),
        Input("minute","value"),
        Input("second","value"),
    ]
)
def update_graph(graph_type,phase,hour,minute,second):
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

    graph_list = []
    for data_field in data_fields:
        temp_data = blond.list_files()[data_field][0]["current"+str(phase)][0:sps*10]
        len_data = temp_data.shape[0]
        print("length of "+data_field + "is:"+str(len_data))
        print()
        temp_graph = go.Scatter(
            x = np.linspace(1,15,len_data),
            y = temp_data[()],
            mode=the_mode,
            name=data_field.title()
        )
        graph_list.append(temp_graph)

    print("returning from update graph")
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
    app.run_server(debug=True,port=8051)
