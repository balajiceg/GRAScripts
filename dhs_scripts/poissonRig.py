# -*- coding: utf-8 -*-
"""
Created on Fri Apr 10 00:25:12 2020

@author: balajiramesh
"""
import pandas as pd
import numpy as np
import geopandas
import plotly.express as px
import plotly.io as pio
import statsmodels.api as sm
import statsmodels.formula.api as smf

pio.renderers.default = "browser"

#%%read ip op data
INPUT_IPOP_DIR=r'Z:\Balaji\DSHS ED visit data\CleanedMergedJoined'
sp=pd.read_pickle(INPUT_IPOP_DIR+r'\ip')
#sp=pd.read_pickle(INPUT_IPOP_DIR+r'\op')
svi_floodr=geopandas.read_file(r'Z:/Balaji/SVI2016Rerank_floodRatio/SVI2016Rerank_floodRatio.shp')
demos=pd.read_csv(r'Z:/Balaji/Census_data_texas/ACS_17_5YR_DP05_with_ann.csv',low_memory=False,skiprows=1)

#%%variables 
interv_date=20170825


#%%spatial dataframe
svi_floodr.GEOID=pd.to_numeric(svi_floodr.GEOID).astype("Int64")
svi_floodr=svi_floodr.loc[:,['GEOID','floodR200','SVI_StudyA']]
#%%read population data
demos.Id2=demos.Id2.astype("Int64")
#%%keep only the required fields
df=sp.loc[:,['RECORD_ID','LCODE','STMT_PERIOD_FROM','PAT_ADDR_CENSUS_BLOCK_GROUP']].copy()
#remove records before 2016
df=df.loc[(~pd.isna(df.STMT_PERIOD_FROM))] 
df=df.loc[df.STMT_PERIOD_FROM>20160100]
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
#remove zero counts groups
grouped_tracts=grouped_tracts.loc[grouped_tracts['Counts']>0,]

#%% merge population
demos_subset=demos.iloc[:,[1,3]]
demos_subset.columns=["PAT_ADDR_CENSUS_TRACT","Population"]
grouped_tracts=grouped_tracts.merge(demos_subset,on="PAT_ADDR_CENSUS_TRACT",how='left')
grouped_tracts=grouped_tracts.loc[grouped_tracts.Population>0,]

#%% bringing in intervention
grouped_tracts.loc[:,'Time']=pd.cut(grouped_tracts.STMT_PERIOD_FROM_GROUPED,bins=[0,interv_date,20190101],labels=['before','after'])

#%%controling for year
grouped_tracts['year']=(grouped_tracts.STMT_PERIOD_FROM_GROUPED//1e4).astype('category')
grouped_tracts['month']=(grouped_tracts.STMT_PERIOD_FROM_GROUPED//1e2%100).astype('category')

#%%running the model
outcome='Counts'
offset=np.log(grouped_tracts.Population)
indes=['Time','floodR200']

formula=outcome+' ~ '+' * '.join(indes) +'+ year'
model = smf.glm(formula=formula,data=grouped_tracts,offset=offset,missing='drop',family=sm.families.Poisson(link=sm.families.links.log()))
results=model.fit()
print(results.summary())
print(np.exp(results.params))
print(np.exp(results.conf_int()))















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







