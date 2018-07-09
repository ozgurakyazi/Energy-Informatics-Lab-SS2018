import pandas as pd
import numpy as np
import h5py
import os, glob
import re
from datetime import datetime, date, time,timedelta
from six import iteritems

def get_time_diff(t1,t2):
    """
    Here we take time difference of 2 datetime.time objects and return it as seconds.
    """
    t1_s = (t1.hour*60*60 + t1.minute*60 + t1.second)
    t2_s = (t2.hour*60*60 + t2.minute*60 + t2.second)

    delta_s = max([t1_s, t2_s]) - min([t1_s, t2_s])
    return delta_s

def increment_time(t1,minutes=0,seconds=0):
    """
    Input of t1 datetime.time object is incremented 'minutes' and 'seconds'
    As a special case, if the final time does belong to the next day, then we return time as 23:59:59
    since in this application, we are only working on one specific day's data.
    """
    prev_date = datetime.combine(date.today(), t1)
    new_date=  prev_date + timedelta(minutes = minutes,seconds=seconds)

    if prev_date.date() != new_date.date(): ## this means that, the minute increment yielded a date change. So we should return 23:59:59 as the time
        return time(23,59,59)

    return new_date.time()
class Blond(object):
    """
        This class contains all the input output operations with the hdf5 files, residing under
        "./data/" folder.
    """
    _SD_centered = []
    _SD_calibrated = []

    def __init__(self, date,day_data = {}):
        self.path_to_files = './data/'
        self.data_structure = {}
        self.date = date
        self._day_data = day_data
        self.time_stamps = {}
        self.sps = {"clear":50000, "medals":6400}
        self.time_limits = {}
        self.minute_per_file = {"clear":5,"medals":15}
        self._get_paths()
        self._determine_limits()

    ## list file names for each device
    def list_files(self):
        return self._day_data
    # get structure of the data, like signals for each device.
    def get_data_structure(self):
        return self.data_structure


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
        """
        For a given datetime.time object called the_time, we search for the belonging timestamp from the all_timestamps
        Actually, this all_timestamps are the timestamps from a device, and when we are looking for a time value in the
        files of the device, we are using this function.
        """
        current_ts = all_timestamps[0]
        i=1
        try:
            while the_time >= current_ts:
                current_ts = all_timestamps[i]
                i+=1
        except: # in case requested time is in the last index of the list, we will have a error in [i]. so this except makes the index work.
            i+=1

        return i-2
    def _extract_timestamps(self, files,is_clear = 0):
        """
        This method extracts timestamps from a given Blond dataset's hdf5 file names.

        How it works:
        1. gets a list of files in the folder
        2. extracts timestamps with _regex_map() method and converts it to datetime.time()
        3. sorts the timestamps
        4. sorts file name lists, to make the indexes of timestamps and file names comparable.
        5. returns both reordered file names and timestamps
        """

        pattern = r'(\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2})'
        timestamps = self._regex_map(pattern, files)
        time_format = '%Y-%m-%dT%H-%M-%S'
        timestamps = list(map(lambda ts: datetime.strptime(ts, time_format ).time(), timestamps))
        timestamps.sort()


        """add first file to the rest"""
        timestamps_filter= map(lambda ts: datetime.combine(self.date, ts).strftime(time_format), list(timestamps))

        res_list = []
        for ts in timestamps_filter: ## we are doing this step, because we need the file paths to be in the same order with timestamp
            res_list += [f for f in files if ts in f]

        return res_list , timestamps


    def _get_paths(self):
        """
        _get_paths() method scans the relevant folders and saves the relevant information into the class variables.
        """

        """READING CLEAR UNIT"""
        path_to_clear = self.path_to_files + 'clear/'
        files_all = next(os.walk(path_to_clear))[2]
        ##### save clear file names and filestamps#####
        self._day_data['clear'], self.time_stamps["clear"] = self._extract_timestamps(files_all,is_clear=1)
        ###############################################
        ##### extract data structure from one of the clear files
        temp_data = h5py.File(self.path_to_files+"/clear/" + self._day_data["clear"][0], 'r')
        self.data_structure["clear"] = list(temp_data.keys()) ## signal names are saved here.
        temp_data.close()
        #########################################################

        ##### determine time limits for the clear device ########################
        latest_possible_time = self.time_stamps["clear"][-1]
        ## get the latest possible time from the files.
        latest_possible_time = increment_time(t1=latest_possible_time,minutes=self.minute_per_file["clear"],seconds=-1) # minus 1 second, because last second of the file is exclusive already.
        self.time_limits["clear"] = {"latest":0,"earliest":0}
        self.time_limits["clear"]["latest"] = latest_possible_time
        self.time_limits["clear"]["earliest"] = self.time_stamps["clear"][0]
        #########################################################################


        """READING MEDAL UNITS"""

        path_to_medals = './data/medal*/'
        folders_list =glob.glob(path_to_medals)
        folders_list.sort()
        for folder in folders_list:
            files_all = next(os.walk(folder))[2]
            medal_name = re.search(r'(medal-\d+)', folder).group(1)

            ##### save clear file names and filestamps from the current medal device#####
            self._day_data[medal_name], self.time_stamps[medal_name] = self._extract_timestamps(files_all)
            ###############################################

            ## extract the data structure from one of the medal files.###################
            temp_data = h5py.File(self.path_to_files+"/"+medal_name+"/" + self._day_data[medal_name][0], 'r')
            self.data_structure[medal_name] = list(temp_data.keys())
            temp_data.close()
            #########################################################

            ##### determine time limits for the clear device ########################
            latest_possible_time = self.time_stamps[medal_name][-1]
            ## get the latest possible time from the files.
            latest_possible_time = increment_time(t1=latest_possible_time,minutes=self.minute_per_file["medals"],seconds=-1)
            self.time_limits[medal_name] = {"latest":0,"earliest":0}
            self.time_limits[medal_name]["earliest"]= self.time_stamps[medal_name][0]
            self.time_limits[medal_name]["latest"] = latest_possible_time


    def _get_data_from_file(self,device,signal,file_index,calibrate=True ):
        """
        This is the function to read the data from the 'device' with the signal 'signal'
        whose file index is 'file_index'. Indexing the files work without any problem since we save them
        with the exactly same order of time stamps.
        """
        file = self._day_data[device][file_index]## get the file name
        all_data=h5py.File(self.path_to_files+"/"+device+"/" + file, 'r')## open the file description
        result_data = 0
        if calibrate:
            DC_offset = 0
            if device != "clear": # no offset for clear
                DC_offset = all_data[signal].attrs['removed_offset']

            factor = all_data[signal].attrs['calibration_factor']
            result_data = ((all_data[signal][:] + DC_offset) * factor).astype("<f4")
        else:
            result_data = all_data[signal][:]
        all_data.close()
        return result_data

    def read_data(self, device,signal,start_ts, end_ts,calibrate=True):

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
            file_name = self._day_data[device][start_file_index]
            the_data = self._get_data_from_file(device,signal,start_file_index,calibrate)
            result_data = the_data[range_start:range_end]
            return result_data

        result_data = self._get_data_from_file(device,signal,start_file_index)[range_start:].tolist()
        for temp_index in res_timestamps_ind:
            result_data += self._get_data_from_file(device,signal,temp_index,calibrate)[:].tolist()


        result_data += self._get_data_from_file(device,signal,end_file_index)[0:range_end].tolist()
        return np.array(result_data)
