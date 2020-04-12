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
from datetime import timedelta, date,datetime

pio.renderers.default = "browser"

#%%read ip op data
INPUT_IPOP_DIR=r'Z:\Balaji\DSHS ED visit data\CleanedMergedJoined'
sp=pd.read_pickle(INPUT_IPOP_DIR+r'\ip')
#sp=pd.read_pickle(INPUT_IPOP_DIR+r'\op')
svi_floodr=geopandas.read_file(r'Z:/Balaji/SVI2016Rerank_floodRatio/SVI2016Rerank_floodRatio.shp')
demos=pd.read_csv(r'Z:/Balaji/Census_data_texas/ACS_17_5YR_DP05_with_ann.csv',low_memory=False,skiprows=1)

#%%variables 
interv_date=20170825
#DATE_GROUPS={"DAILY","WEEKLY","MONTHLY"}
DATE_GROUP="DAILY"
#flood quantiles
FLOOD_QUANTILES=["NO","FLood"]
#%%spatial dataframe
svi_floodr.GEOID=pd.to_numeric(svi_floodr.GEOID).astype("Int64")
svi_floodr=svi_floodr.loc[:,['GEOID','floodR200','SVI_StudyA']]
#%%read population data
demos.Id2=demos.Id2.astype("Int64")

#%%keep only the required fields and dates
df=sp.loc[:,['RECORD_ID','LCODE','STMT_PERIOD_FROM','PAT_ADDR_CENSUS_BLOCK_GROUP']].copy()
#remove records before 2016
df=df.loc[(~pd.isna(df.STMT_PERIOD_FROM))] 
df=df[((df.STMT_PERIOD_FROM > 20160700) & (df.STMT_PERIOD_FROM< 20161232))\
   | ((df.STMT_PERIOD_FROM > 20170400) & (df.STMT_PERIOD_FROM< 20171232))\
       | ((df.STMT_PERIOD_FROM > 20180700) & (df.STMT_PERIOD_FROM< 20181232))]
df=df[(df.STMT_PERIOD_FROM > 20160100)]
df_cp=df.copy(deep=True)

#%% state ment period to months or week
if DATE_GROUP=="DAILY":
    df.loc[:,'STMT_PERIOD_FROM_GROUPED']=df.STMT_PERIOD_FROM#(df.STMT_PERIOD_FROM//10)*10+2
elif DATE_GROUP=="MONTHLY":
    df.loc[:,'STMT_PERIOD_FROM_GROUPED']=(df.STMT_PERIOD_FROM//100)*100+1
elif DATE_GROUP=="WEEKLY":
    date1,date2=datetime.strptime('20160702','%Y%m%d'),datetime.strptime('20170101','%Y%m%d')
    weekly_bins=np.arange(date1,date2,timedelta(7))
    date1,date2=datetime.strptime('20170401','%Y%m%d'),datetime.strptime('20180101','%Y%m%d')
    weekly_bins=np.concatenate([weekly_bins,np.arange(date1,date2,timedelta(7))])
    date1,date2=datetime.strptime('20180630','%Y%m%d'),datetime.strptime('20190101','%Y%m%d')
    weekly_bins=np.concatenate([weekly_bins,np.arange(date1,date2,timedelta(7))])
    weekly_bins=pd.to_numeric(pd.Series(weekly_bins).dt.strftime("%Y%m%d"))
    df.loc[:,'STMT_PERIOD_FROM_GROUPED']=pd.cut(df.STMT_PERIOD_FROM,bins=weekly_bins,include_lowest=True,labels=weekly_bins[1:],right=True)
    #remove intermediate year records
    df.loc[(df.STMT_PERIOD_FROM==20170401) | (df.STMT_PERIOD_FROM==20180630),'STMT_PERIOD_FROM_GROUPED']=None
    df=df.loc[~pd.isna(df.STMT_PERIOD_FROM_GROUPED),]
    
    
    #%%cnesus block group to census tract
df.loc[:,'PAT_ADDR_CENSUS_TRACT']=(df.PAT_ADDR_CENSUS_BLOCK_GROUP//10)

#%%group by date and censustract
grouped_tracts=df.groupby(['STMT_PERIOD_FROM_GROUPED', 'PAT_ADDR_CENSUS_TRACT']).size().reset_index()
grouped_tracts.columns = [*grouped_tracts.columns[:-1], 'Counts']
#remove zero counts groups
grouped_tracts=grouped_tracts.loc[grouped_tracts['Counts']>0,]


#%% merge population
demos_subset=demos.iloc[:,[1,3]]
demos_subset.columns=["PAT_ADDR_CENSUS_TRACT","Population"]
grouped_tracts=grouped_tracts.merge(demos_subset,on="PAT_ADDR_CENSUS_TRACT",how='left')

grouped_tracts=grouped_tracts.loc[grouped_tracts.Population>0,]

#%%merge SVI and flood ratio
grouped_tracts=grouped_tracts.merge(svi_floodr,left_on="PAT_ADDR_CENSUS_TRACT",right_on='GEOID',how='left')

#%%categorize floods as per quantiles
s=svi_floodr.loc[svi_floodr.floodR200>-1,'floodR200']
flood_bins=s.quantile(np.arange(0,1.1,1/len(FLOOD_QUANTILES))).to_numpy()
flood_bins[1]=1e-5 if flood_bins[1]==0.0 else flood_bins[1]
#flood_bins=np.insert(flood_bins,0,0)
grouped_tracts.loc[:,'floodR200']=pd.cut(grouped_tracts.floodR200,bins=flood_bins,right=False,labels=FLOOD_QUANTILES)

#%% bringing in intervention
grouped_tracts.loc[:,'Time']=pd.cut(grouped_tracts.STMT_PERIOD_FROM_GROUPED,\
                                    bins=[0,interv_date,20171126,20190101],\
                                    labels=['before','after','after3m'])

#%%controling for year
grouped_tracts['year']=(grouped_tracts.STMT_PERIOD_FROM_GROUPED.astype('int32')//1e4).astype('category')
grouped_tracts['month']=(grouped_tracts.STMT_PERIOD_FROM_GROUPED.astype('int32')//1e2%100).astype('category')

#%%running the model
outcome='Counts'

offset=np.log(grouped_tracts.Population)
#offset=np.log(grouped_tracts.Counts)


indes=['Time','floodR200']

formula=outcome+' ~ '+' * '.join(indes) +'+ year'
model = smf.glm(formula=formula,data=grouped_tracts,offset=offset,missing='drop',family=sm.families.Poisson(link=sm.families.links.log()))
results=model.fit()
print(results.summary())
print(np.exp(results.params))
print(np.exp(results.conf_int()))

#%%plot the rate graph
plot_data={}
for item in FLOOD_QUANTILES:
    plot_data[item]=grouped_tracts.loc[grouped_tracts.floodR200==item,["STMT_PERIOD_FROM_GROUPED","Counts"]]
    plot_data[item]=plot_data[item].groupby(['STMT_PERIOD_FROM_GROUPED']).sum().reset_index()
    plot_data[item].loc[:,"STMT_PERIOD_FROM_GROUPED"]=pd.to_datetime(plot_data[item].loc[:,"STMT_PERIOD_FROM_GROUPED"].astype(str))

floodedCats=plot_data[FLOOD_QUANTILES[0]]
for i in range(1,len(FLOOD_QUANTILES)):
    floodedCats=floodedCats.merge(plot_data[FLOOD_QUANTILES[i]],on='STMT_PERIOD_FROM_GROUPED',suffixes=FLOOD_QUANTILES[i-1:i+1])
floodedCats.columns=["Date"]+FLOOD_QUANTILES

#find dinominator for computing rate
population=grouped_tracts.groupby(["floodR200"])[['Population']].sum()
flooded_visits=grouped_tracts.groupby(["floodR200"])[['Counts']].sum()
dinominator=population
#convert to rate
rate=floodedCats.loc[:,FLOOD_QUANTILES]/dinominator.T.iloc[0,:].to_numpy()
rate=pd.concat([floodedCats.Date,rate],axis=1).reset_index().iloc[:,1:]

rate=rate.sort_values(by='Date',ignore_index=True)
#%%plot
plot_df=rate.melt(id_vars=['Date'],value_vars=list(rate.columns[1:]))
plot_df['value'] = plot_df.value.rolling(window=7).mean()
fig = px.line(plot_df, x='Date', y='value',color='variable')
fig.show()    











