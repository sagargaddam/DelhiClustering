#!/usr/bin/env python
# coding: utf-8

# In[8]:


from os import listdir
from os.path import isfile, join
import sys
#param

if len(sys.argv)<3:
    print("Enter valid query folder and data metric flag as argument")
    sys.exit()
elif len(sys.argv)>3:
    print("Invalid Arguments")
    sys.exit()
elif sys.argv[2] != '-ds1' and sys.argv[2] != '-ds2':
	print('Enter valid flag -ds1 , -ds2 ')

	sys.exit()
    

    

# query_folder = "query_data/"
query_folder = sys.argv[1]
# metric_flag = '-ds1'
metric_flag = sys.argv[2]


if metric_flag == '-ds1':
    if not isfile('Results/ds1_stats.csv') :
        print(' First generate ds1_stats running python script generate_stats_for_ds_1.py ')
        sys.exit()
if metric_flag == '-ds2':
    if not isfile('Results/ds2_stats.csv') :
        print(' First generate ds2_stats running python script generate_stats_for_ds_2.py ')
        sys.exit()
onlyfiles = [f for f in listdir(query_folder) if isfile(join(query_folder, f)) and "_bme" in f]
# print(onlyfiles)
dates = []
for f in onlyfiles:
    date = f.split("_")[0]
    dates.append(date)
# print(dates)


# In[1]:


import pandas as pd
import numpy as np 
import matplotlib.pyplot as plt
import os
#get_ipython().run_line_magic('matplotlib', 'inline')
plt.style.use("seaborn-talk")

import seaborn as sns
from dateutil import tz
import pytz 
import tqdm

from sklearn.neighbors import KernelDensity
from scipy.stats import entropy
from scipy.spatial.distance import jensenshannon

import folium
from branca.element import Figure
from folium.plugins import HeatMapWithTime, HeatMap
from folium.plugins import MarkerCluster

# reading and preprocessing related functions
def read_raw(folder,date):
    """
    Reads in the data. Does not remove any row. 
    """
#     if len(str(date[8:])) == 2:
    df_bme = pd.read_csv(folder + "/" + date + "_bme.csv", index_col= 0)
    df_gps = pd.read_csv(folder + "/" + date + "_gps.csv", index_col = 0)
    df_pol = pd.read_csv(folder + "/" + date + "_pol.csv", index_col = 0)
#     else:
#         df_bme = pd.read_csv("data/" + date + "_bme.csv", index_col= 0)
#         df_gps = pd.read_csv("data/" + date + "_gps.csv", index_col = 0)
#         df_pol = pd.read_csv("data/" + date + "_pol.csv", index_col = 0)
    return df_bme, df_gps, df_pol

def handle_dateTime(df_all):
    ## change dateTime column from type "object" to "datetime"
    df_all["dateTime"] = pd.to_datetime(df_all.dateTime)    
    # convert to India timing
    to_zone = tz.gettz('Asia/Kolkata')
    df_all.dateTime = df_all.dateTime.apply(lambda x: pytz.utc.localize(x, is_dst=None).astimezone(to_zone))
    return df_all

def make_time_cols(df_all):
    df_all["hour"] = df_all.dateTime.dt.hour
    df_all["minute"] = df_all.dateTime.dt.minute    
    return df_all

def preprocess(df_tuple):
    """
    Combines all other functions
    """
    df_bme, df_gps, df_pol = df_tuple
    
    # drop duplicates
    df_bme = df_bme.drop_duplicates(subset ="uid" )
    df_gps = df_gps.drop_duplicates(subset = "uid")
    df_pol = df_pol.drop_duplicates(subset = "uid")
    
    # merge on key columns
    key_cols = ["uid", "dateTime", "deviceId"]
    df_all = pd.merge(df_bme, df_gps, on = key_cols)
    df_all = pd.merge(df_all, df_pol , on = key_cols)
    
    # rename lng to long and shorten device IDs
    df_all = df_all.rename(columns = {"lng":"long"})
    df_all.deviceId = df_all.deviceId.str[-5:]
    
    # handle dateTime and time related columns
    df_all = handle_dateTime(df_all)
    df_all = make_time_cols(df_all)
    
    # some final stuff 
    df_all = df_all.sort_values("dateTime")
    df_all = df_all.reset_index(drop = True)
    return df_all


def plot_plotwise_for_all_dates():
    result = []
    counter = 1
    print('Generating ds_1 stats for dates',dates)
    print('Progress ',0,'of',len(dates))
    for dt in dates :
        df_bme, df_gps, df_pol = read_raw(query_folder,dt)
        df_all = preprocess((df_bme, df_gps, df_pol))
        sensor_order = df_all.deviceId.unique()
        sensor_order.sort()
        
        sub = df_all.groupby(["deviceId", "hour", "minute"]).size().reset_index()
#         fig, ax = plt.subplots(1, 1, figsize = (15, 5))
#             print(sub.describe())
#         print(sub.groupby(["deviceId"])[0].describe())
        result.append(sub.groupby(["deviceId"])[0].describe())
#         g = sns.boxplot(y = 0, data = sub, x= "deviceId", order = sensor_order)
#         g.set_ylabel("Samples Recorded per Minute")
#         g.set_title(dt+ ": Boxplots for Sampling Rate (Samples Recorded per Minute)")

#         plt.show()
        
        print('Progress ',counter,'of',len(dates))
        counter +=1
        
    return result


# In[ ]:


query_result = plot_plotwise_for_all_dates()


# In[2]:


ds1_stats = pd.read_csv('Results/ds1_stats.csv',index_col='metric')
stats = ds1_stats.to_dict()
print('Finding anomaly based ob below stats : ')
print(ds1_stats)
print('-----------------------------------------------------')
# ds1_stats['lower_limit']['median']
lower_median = stats['lower_limit']['25th_percentile']
upper_median = stats['upper_limit']['75th_percentile']
lower_25th = stats['lower_limit']['25th_percentile']
upper_25th = stats['upper_limit']['75th_percentile']
lower_75th = stats['lower_limit']['25th_percentile']
upper_75th = stats['upper_limit']['75th_percentile']

from os import listdir
from os.path import isfile, join
mypath = "query_data/"
onlyfiles = [f for f in listdir(mypath) if isfile(join(mypath, f)) and "_bme" in f]
# print(onlyfiles)
dates = []
for f in onlyfiles:
    date = f.split("_")[0]
    dates.append(date)
# print(dates)


# merge with upper cell
anamolus_flag = False
# print(len(query_result))
for idx,date in enumerate(query_result):
    for device in range(len(date)):
        anomalous_score = 0
        device_median = date.iloc[device]['50%']
        device_25th = date.iloc[device]['25%']
        device_75th = date.iloc[device]['75%']
        if lower_median> device_median or device_median > upper_median:
            anomalous_score +=1
        if lower_25th> device_25th or device_25th > upper_25th:
            anomalous_score +=1
        if lower_75th> device_75th or device_75th > upper_75th:
            anomalous_score +=1
        
        # anamolus detection logic
        if anomalous_score >= 2 : 
            deviceName = query_result[0].index.values[device]
            print('deviceID : ',deviceName,'is behaving anamolusly on date:',dates[idx],'for metric ds_1')
            anamolus_flag = True
#             result = print_stats_for_date(dt)
            print('Below are ds_1 stats for date',dates[idx])
            print(query_result[idx])
        
if not anamolus_flag:
    print('No anamolus device for metric ds_1 on dates',dates)
        


# In[ ]:


# print(query_result[0])


# In[ ]:


# print(query_result[0].iloc[0])


# In[ ]:


# query_result[0].index.values[0]


# In[ ]:




