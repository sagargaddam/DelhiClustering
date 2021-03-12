#!/usr/bin/env python
# coding: utf-8

# In[23]:


from os import listdir
from os.path import isfile, join
import sys
#param

if len(sys.argv)<2:
    print("Enter valid data folder as argument")
    sys.exit()
elif len(sys.argv)>2:
    print("Invalid Arguments")
    sys.exit()
    

# data_folder = "test_data/"
data_folder = sys.argv[1]


onlyfiles = [f for f in listdir(data_folder) if isfile(join(data_folder, f)) and "_bme" in f]
# print(onlyfiles)
dates = []
for f in onlyfiles:
    date = f.split("_")[0]
    dates.append(date)
#print(dates)


# In[24]:


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
        df_bme, df_gps, df_pol = read_raw(data_folder,dt)
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


# In[20]:


result = plot_plotwise_for_all_dates()


# In[21]:


# print(result[0])
dist_medians = []
dist_75 = []
dist_25 = []
for df in result:
#     print(df.size())
    for i in range(len(df)):
#         print(df.iloc[i]['50%'])
        dist_medians.append(df.iloc[i]['50%'])
        dist_75.append(df.iloc[i]['75%'])
        dist_25.append(df.iloc[i]['25%'])
#     print('dome')

# print(dist_medians)
stats =  {'medians': dist_medians, 
        '25th': dist_25, '75th' : dist_75}  
stats = pd.DataFrame.from_dict(stats) 
# print(stats.describe())
stats = stats.describe()
# print(stats_df['medians']['count'])
lower_median = stats['medians']['25%']
upper_median = stats['medians']['75%']
lower_25th = stats['25th']['25%']
upper_25th = stats['25th']['75%']
lower_75th = stats['75th']['25%']
upper_75th = stats['75th']['75%']
# print(lower_median)
metric = ['median','25th_percentile','75th_percentile']
lower = [lower_median,lower_25th,lower_75th]
upper = [upper_median,upper_25th,upper_75th]
result_dict = {'metric': metric, 'lower_limit': lower, 'upper_limit': upper} 
result_df = pd.DataFrame(result_dict)
# print(result_dict)
result_df.to_csv('Results/ds1_stats.csv',index = False)

print('stats written to Results/ds1_stats.csv ')


# In[ ]:




