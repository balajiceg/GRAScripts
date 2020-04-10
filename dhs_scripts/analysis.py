# -*- coding: utf-8 -*-
"""
Created on Mon Mar 23 17:58:01 2020

@author: balajiramesh
"""

import pandas as pd
import numpy as np
import geopandas
import plotly.express as px
import plotly.io as pio
pio.renderers.default = "browser"

#%%read ip op data
INPUT_IPOP_DIR=r'\\vetmed2.vetmed.w2k.vt.edu\Blitzer\NASA project\Balaji\DSHS ED visit data\CleanedMergedJoined'
INPUT_IPOP_DIR=r'Z:'
ip=pd.read_pickle(INPUT_IPOP_DIR+r'\ip')
#op=pd.read_pickle(INPUT_IPOP_DIR+r'\op')


#%%spatial dataframe
svi_floodr=geopandas.read_file(r'D:/texas/spatial/SVI2016Rerank_floodRatio/SVI2016Rerank_floodRatio.shp')
svi_floodr.GEOID=pd.to_numeric(svi_floodr.GEOID).astype("Int64")
svi_floodr=svi_floodr.loc[:,['GEOID','floodR200','SVI_StudyA']]

#%%read population data
demos=pd.read_csv(r'D:/texas/Census_data_texas/ACS_17_5YR_DP05_with_ann.csv',low_memory=False,skiprows=1)
demos.Id2=demos.Id2.astype("Int64")


#%%keep only the required fields
df=ip.loc[:,['RECORD_ID','LCODE','STMT_PERIOD_FROM','PAT_ADDR_CENSUS_BLOCK_GROUP']].copy()
df_cp=df.copy(deep=True)
#cnesus block group to census tract
df.loc[:,'PAT_ADDR_CENSUS_TRACT']=(df.PAT_ADDR_CENSUS_BLOCK_GROUP//10)
# state ment period to 10 days
df.loc[:,'STMT_PERIOD_FROM_GROUPED']=df.STMT_PERIOD_FROM#(df.STMT_PERIOD_FROM//10)*10+2

#%%merge SVI and flood ratio and population
df=df.merge(svi_floodr,left_on="PAT_ADDR_CENSUS_TRACT",right_on='GEOID',how='left')

#%%categorize floods as per quantiles
s=svi_floodr.loc[svi_floodr.floodR200>-1,'floodR200']
flood_bins=s.quantile(np.arange(0,1.1,1/2)).to_numpy()
flood_bins[1]=1e-5 if flood_bins[1]==0.0 else flood_bins[1]
#flood_bins=np.insert(flood_bins,0,0)
df.loc[:,'floodR200']=pd.cut(df.floodR200,bins=flood_bins,right=False,labels=['min_flood','high_flood'])

#%%group by date floodR200 and censustract
grouped_tracts=df.groupby(['STMT_PERIOD_FROM_GROUPED', 'PAT_ADDR_CENSUS_TRACT','floodR200']).size().reset_index()
grouped_tracts.columns = [*grouped_tracts.columns[:-1], 'Counts']
grouped_tracts.STMT_PERIOD_FROM_GROUPED=grouped_tracts.STMT_PERIOD_FROM_GROUPED.apply(lambda x:x//100*100+22 if x%100==32 else x)

#%% total population for each flood group
demos_subset=demos.iloc[:,[1,3]]
demos_subset.columns=["Id2","TotalPop"]
tracts_floodR=df.loc[~df.duplicated("PAT_ADDR_CENSUS_TRACT"),:]
tracts_floodR=tracts_floodR.loc[~pd.isna(tracts_floodR.floodR200),tracts_floodR.columns[[4,7]]]
tracts_flodR_pop=tracts_floodR.merge(demos_subset,left_on='PAT_ADDR_CENSUS_TRACT',right_on="Id2")

pop_flood_levels=tracts_flodR_pop.groupby(["floodR200"])[['TotalPop']].sum()


#%% seperate classes of flooding 
#flooded tract
no_flood_tracts=grouped_tracts.loc[grouped_tracts.floodR200=="no_flood",["STMT_PERIOD_FROM_GROUPED","Counts"]]
min_flood_tracts=grouped_tracts.loc[grouped_tracts.floodR200=="min_flood",["STMT_PERIOD_FROM_GROUPED","Counts"]]
high_flood_tracts=grouped_tracts.loc[grouped_tracts.floodR200=="high_flood",["STMT_PERIOD_FROM_GROUPED","Counts"]]

#%% bins by dates and count
def mDateGroupby(fdf):
    fdf=fdf.copy()
    fdf=fdf.loc[fdf.STMT_PERIOD_FROM_GROUPED>20160100,:]
    fdf=fdf.groupby(['STMT_PERIOD_FROM_GROUPED']).sum().reset_index()
    fdf.loc[:,"STMT_PERIOD_FROM_GROUPED"]=pd.to_datetime(fdf.loc[:,"STMT_PERIOD_FROM_GROUPED"].astype(str))
    fdf.loc[:,"STMT_PERIOD_FROM_GROUPED"]=fdf.loc[:,"STMT_PERIOD_FROM_GROUPED"].astype(str)
    # bin_dates_s=["%04d-%02d-%02d"%(y,m,d) 
    #                          for y in (2016,2017,2018) 
    #                              for m in range(4,13) 
    #                                  for d in (1,10,20)]+["2018-12-31"]
    # bin_dates=pd.to_datetime(bin_dates_s)
    
    # fdf= fdf.groupby([pd.cut(fdf.STMT_PERIOD_FROM_GROUPED,bins=bin_dates,labels= bin_dates_s[:-1])])[['Counts']].sum().reset_index()
    return fdf
no_flood_tracts,min_flood_tracts,high_flood_tracts=map(mDateGroupby,[no_flood_tracts,min_flood_tracts,high_flood_tracts])

flooded_counts=no_flood_tracts.merge(min_flood_tracts,on='STMT_PERIOD_FROM_GROUPED',suffixes=('_no', '_min')).merge(high_flood_tracts,on='STMT_PERIOD_FROM_GROUPED')
#remove no flood
flooded_counts=min_flood_tracts.merge(high_flood_tracts,on='STMT_PERIOD_FROM_GROUPED',suffixes=('_min', '_high'))
#flooded_counts.columns=["Date","No","Min","High"]
flooded_counts.columns=["Date","Min","High"]
#%% sort the flooded counts and remove the unwanted quarters
flooded_counts=flooded_counts.sort_values(by='High',ignore_index=True)
flooded_counts_quarters=flooded_counts.iloc[:,:]

pop_normalized=flooded_counts_quarters.iloc[:,1:4]/pop_flood_levels.T.iloc[0,:].to_numpy()
pop_normalized=pd.concat([flooded_counts_quarters.Date,pop_normalized],axis=1).reset_index().iloc[:,1:]
pop_normalized=pop_normalized.sort_values(by='Date',ignore_index=True)
#%%plot
pop_plot_df=pop_normalized.melt(id_vars=['Date'],value_vars=list(pop_normalized.columns[1:]))
pop_plot_df['value'] = pop_plot_df.rolling(window=7).mean()
fig = px.line(pop_plot_df, x='Date', y='value',color='variable')
fig.show()

#%%
pop_normalized.to_csv(r'./Desktop/op_daily_2cat.csv')







