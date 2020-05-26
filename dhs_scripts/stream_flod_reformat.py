# -*- coding: utf-8 -*-
"""
Created on Sun May 24 15:12:03 2020

@author: balajiramesh
"""
import pandas as pd
import numpy as np
#import jenkspy
import geopandas

#%%read stram flow stations
stations=pd.read_csv(r"Z:/Balaji/stram_flow/stream_flow_sites",sep="\t").drop(0)

file_in = open(r'Z:/Balaji/stram_flow/stage_ht_2015_2019', 'r')
lines=file_in.readlines()+["#"]
file_in.close()


merged_df=pd.DataFrame()
temp_str=""
for l in lines:
    if "#" in l:
        if temp_str!="":
            df=pd.DataFrame([x.split('\t') for x in temp_str.split('\n')])
            df=df[~df[2].isna()]
            df.columns=df.iloc[0,:]
            df=df.iloc[2:,:]
            try:
                mean_flow_col=df.columns[df.columns.str.contains("_00060_00003")][0]
            except IndexError:
                mean_flow_col="x_00060_00003"
                df[mean_flow_col]=np.nan
            
            try:
                mean_gage_ht_col=df.columns[df.columns.str.contains("_00065_00003")][0]
            except IndexError:
                mean_gage_ht_col="x_00065_00003"
                df[mean_gage_ht_col]=np.nan
            
            new_df=df.loc[:,["site_no","datetime",mean_flow_col,mean_gage_ht_col]]
            
            new_df.rename(columns={mean_flow_col:"MeanDischarge",mean_gage_ht_col:'MeanGageHt'},inplace=True)
            
            merged_df=pd.concat([merged_df,new_df])
            
            #print(new_df.shape)
            temp_str=""
        continue
    else:
        temp_str+=l
        
stations['county_fips']='48'+stations.county_cd.astype('str')
#stations.to_csv("Z:/Balaji/stram_flow/stations.csv")

merged_df=merged_df.merge(stations[["site_no","county_fips"]],how='left',on='site_no')
merged_df.site_no=merged_df.site_no.astype('str')

#merge flood stage
flood_stages=pd.read_csv(r"Z:/Balaji/stram_flow/floodstages.csv",dtype={'site_no':str})

merged_df= merged_df.merge(flood_stages,on="site_no",how="left")
merged_df.to_csv(r"Z:/Balaji/stram_flow/flow_gage_ht_2015_2019.csv")


#%%for 118 counties i study
county_to_filter=pd.read_csv('Z:/Balaji/counties_inun.csv').GEOID.to_list()
std_df=merged_df[merged_df.county_fips.astype(int).isin(county_to_filter)]

#filter those only with flood stage
std_df=std_df[~std_df.flood_stage.isna()]

std_df.MeanGageHt=pd.to_numeric(std_df.MeanGageHt,errors='coerce')
std_df["excced_flood_stage"]=(std_df.MeanGageHt >= std_df.flood_stage).astype(int)


std_df.to_csv(r"Z:/Balaji/stram_flow/flow_gage_ht_study_area2.csv")
