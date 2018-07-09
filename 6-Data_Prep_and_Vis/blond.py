import pandas as pd
import numpy as np
import h5py
import os, glob
import re
from datetime import datetime, date, time,timedelta
from six import iteritems

def get_time_diff(t1,t2):
    t1_s = (t1.hour*60*60 + t1.minute*60 + t1.second)
    t2_s = (t2.hour*60*60 + t2.minute*60 + t2.second)

    delta_s = max([t1_s, t2_s]) - min([t1_s, t2_s])
    return delta_s

def increment_time(t1,minutes=0,seconds=0):
    prev_date = datetime.combine(date.today(), t1)
    new_date=  prev_date + timedelta(minutes = minutes,seconds=seconds)

    if prev_date.date() != new_date.date(): ## this means that, the minute increment yielded a date change. So we should return 23:59:59 as the time
        return time(23,59,59)

    return new_date.time()
class Blond(object):
    """
        class blond: attributes: date, list of files
    """
    _SD_centered = []
    _SD_calibrated = []

    def __init__(self, date,day_data = {}):
        self.date = date
        self._day_data = day_data
        self.time_stamps = {}
        self.sps = {"clear":50000, "medals":6400}
        self.time_limits = {}
        self.minute_per_file = {"clear":5,"medals":15}
        self._read_files()
        self._determine_limits()

    def list_files(self):
        return self._day_data


    def _determine_limits(self):
        """
        This function determines maximum of the end times and minimum of the start times
        among all medals. Because in dashboard application,
        we show all the medal data together, we have to decide on the strict
        bounds on the time. For example, after 23:30:30 none of the medals contain
        any data. We can only show the data until 23:30:30.
        """
        min_of_start = {"time":time(23,59,59),"device":"None"}
        max_of_end = {"time":time(0,0,0),"device":"None"}
        for temp_device in self.time_limits.keys():
            if temp_device == "clear": ## here we are determining time limits for the medals. so clear is excluded
                continue
            if min_of_start["time"]>self.time_limits[temp_device]["earliest"]:
                min_of_start["time"] = self.time_limits[temp_device]["earliest"]
                min_of_start["device"]=temp_device
            if max_of_end["time"]<self.time_limits[temp_device]["latest"]:
                max_of_end["time"] = self.time_limits[temp_device]["latest"]
                max_of_end["device"]=temp_device

        self.min_time_of_start = min_of_start
        self.max_time_of_end = max_of_end
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


        """add first file to the rest"""
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
        return data , timestamps


    def _read_files(self):
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

        latest_possible_time = self.time_stamps["clear"][-1]
        ## get the latest possible time from the files.
        latest_possible_time = increment_time(t1=latest_possible_time,minutes=self.minute_per_file["clear"],seconds=-1)
        self.time_limits["clear"] = {"latest":0,"earliest":0}
        self.time_limits["clear"]["latest"] = latest_possible_time
        self.time_limits["clear"]["earliest"] = self.time_stamps["clear"][0]

        """READING MEDAL UNITS"""

        path_to_medals = './data/medal*/'
        folders_list =glob.glob(path_to_medals)
        folders_list.sort()
        for folder in folders_list:
            files_all = next(os.walk(folder))[2]
            medal_name = re.search(r'(medal-\d+)', folder).group(1)

            self._day_data[medal_name], self.time_stamps[medal_name] = self._read_files_from_folder(files_all,folder)
            latest_possible_time = self.time_stamps[medal_name][-1]
            ## get the latest possible time from the files.
            latest_possible_time = increment_time(t1=latest_possible_time,minutes=self.minute_per_file["medals"],seconds=-1)
            # print("latest possible.")
            # print(latest_possible_time)
            self.time_limits[medal_name] = {"latest":0,"earliest":0}
            self.time_limits[medal_name]["earliest"]= self.time_stamps[medal_name][0]
            self.time_limits[medal_name]["latest"] = latest_possible_time
            # print(medal_name)
            # print(self.time_limits[medal_name])
            #self._day_data[medal_name] = [h5py.File(folder + file_name,'r+') for file_name in target_files]

    def read_data(self, device,signal,start_ts, end_ts):
        # print("device:"+device)
        # print("start:"+str(start_ts))
        # print("end:"+str(end_ts))
        #
        # print("limit start:"+str(self.time_limits[device]["earliest"]))
        # print("limit end:"+str(self.time_limits[device]["latest"]))

        if start_ts<self.time_limits[device]["earliest"] or increment_time(end_ts,seconds=-1)>self.time_limits[device]["latest"]: # if the requested times are not between possible latest and earliest times
            print("No data is returned, since the requested time interval exceeds the possible times in your "+ device + " data")
            print("Please try provide more data under "+ device)
            return np.array([])

        current_sps = self.sps["medals"]
        if device == "clear":
            current_sps = self.sps["clear"]
        start_file_index = self.find_corresponding_file(start_ts,self.time_stamps[device])
        start_diff = get_time_diff(start_ts, self.time_stamps[device][start_file_index]) # calculate how many seconds to ignore in the first file
        res_timestamps_ind =[i for i,ts in enumerate(self.time_stamps[device]) if start_ts < ts <= end_ts] ##
        end_file_index = 0
        if len(res_timestamps_ind)==0: ## this means we only read from 1 file. all the data asked is stored in one file.
            end_file_index = start_file_index
        else:
            end_file_index = res_timestamps_ind[-1]
            del res_timestamps_ind[-1]

        end_diff = get_time_diff(end_ts, self.time_stamps[device][end_file_index]) # calculate how many seconds to include in the last file
        range_start =  start_diff*current_sps
        range_end =  (end_diff)*current_sps
        if start_file_index==end_file_index: ## if we will be reading from only 1 file
            return self._day_data[device][start_file_index][signal][range_start:range_end]

        result_data = self._day_data[device][start_file_index][signal][range_start:].tolist()
        for temp_index in res_timestamps_ind:
            result_data += self._day_data[device][temp_index][signal][:].tolist()


        result_data += self._day_data[device][end_file_index][signal][0:range_end].tolist()
        return np.array(result_data)
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

    def center_and_calibrate_all(self):
        for medal_name in self.list_files().keys():
            for i in range(1,7):
                if medal_name == "clear": ## in clear, we only of current1..3,
                    if i==4:
                        break
                print("Centering and Calibrating: "+ medal_name + " current"+str(i) )
                """Raw signal with offset and calibration factor attributes"""
                dict_signal = self.dict_read_signal(medal_name, "current"+str(i))
                """calibrated signal for clear"""
                self.center_and_calibrate(dict_signal)
