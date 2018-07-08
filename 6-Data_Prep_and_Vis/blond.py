import pandas as pd
import numpy as np
import h5py
import os, glob
import re
from datetime import datetime, date, time
from six import iteritems

class Blond(object):
    """
        class blond: attributes: date, list of files
    """
    _SD_centered = []
    _SD_calibrated = []

    def __init__(self, date, start_ts, end_ts,day_data = {}):
        self.date = date
        self._day_data = day_data
        self.time_stamps = {}
        self.start_ts=start_ts
        self.end_ts=end_ts


    def list_files(self):
        return self._day_data


    @staticmethod
    def _regex_map(pattern, strings_list):

        regex_func = lambda f: re.search(pattern, f)
        filter_list = map(regex_func, strings_list)
        filter_list = filter(lambda x: x is not None, list(filter_list))
        filter_list = map(lambda x: x.group(1), list(filter_list))
        return list(filter_list)


    def find_corresponding_file(self, the_time,all_timestamps):
        current_ts = all_timestamps[0]
        i=1
        try:
            while the_time >= current_ts:
                current_ts = all_timestamps[i]
                i+=1
        except: # in case requested time is in the last index of the list, we will have a error in [i]. so this except makes the index work.
            i+=1

        return i-2
    def _read_files_from_folder(self, files,path_to_files,is_clear = 0):
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
        timestamps.sort()

        """ get the first file timestamp"""
        file_index = self.find_corresponding_file(self.start_ts,timestamps)
        #print("start file index:"+str(file_index))
        if file_index < 0 or self.end_ts>timestamps[-1]: #no file found
            print("The requested time frame is not found in the files of " + path_to_files)
            return [],[]

        del timestamps[0:file_index] # remove the files before our start files
        """add first file to the rest"""
        res_timestamps = [timestamps[0]] + [ts for ts in timestamps if self.start_ts <= ts <= self.end_ts]
        timestamps_filter= map(lambda ts: datetime.combine(self.date, ts).strftime(time_format), list(res_timestamps))

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

        return data , res_timestamps


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
        self._day_data['clear'], self.time_stamps["clear"] = self._read_files_from_folder(files_all,path_to_clear,is_clear=1)
        #self._day_data['clear'] = [h5py.File(path_to_clear + file_name,'r+') for file_name in target_files]



        """READING MEDAL UNITS"""

        path_to_medals = './data/medal*/'
        folders_list =glob.glob(path_to_medals)
        folders_list.sort()
        for folder in folders_list:
            files_all = next(os.walk(folder))[2]
            medal_name = re.search(r'(medal-\d+)', folder).group(1)
            self._day_data[medal_name], self.time_stamps[medal_name] = self._read_files_from_folder(files_all,folder)
            #self._day_data[medal_name] = [h5py.File(folder + file_name,'r+') for file_name in target_files]


    """ center_inplace and calibrate inplace read file-by-file, do the corresponding operations and write back
        good thing: we can process much more files like that and not be bounded by memory since each file is less than 3 GB
        bad thing: we can't coerse from int to float
        We do not use them.
    """
    def read_data(self, start_ts, end_ts):

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
