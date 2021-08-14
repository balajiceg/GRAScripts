# -*- coding: utf-8 -*-
"""
Created on Sat Aug 15 23:18:33 2020

@author: balajiramesh

Computing average distance travelled to ED visit from each block group along with confidence intervals
"""

import pandas as pd
import numpy as np
import geopandas
import statsmodels.api as sm
import statsmodels.formula.api as smf
from datetime import timedelta, date,datetime
from dateutil import parser
import geopandas as gpd
import sys
sys.path.insert(1, r'Z:\GRAScripts\dhs_scripts')
from recalculate_svi import recalculateSVI
import math


import plotly.express as px
import plotly.io as pio
import plotly.graph_objects as go
pio.renderers.default='browser'

#%%read ip op data
INPUT_IPOP_DIR=r'Z:\Balaji\DSHS ED visit data\CleanedMergedJoined'
#read_op
op=pd.read_pickle(INPUT_IPOP_DIR+'\\op')
op=op.loc[:,['RECORD_ID','STMT_PERIOD_FROM','PAT_ADDR_CENSUS_BLOCK_GROUP','PAT_AGE_YEARS','SEX_CODE','RACE','PAT_STATUS','ETHNICITY','PAT_ZIP','PROVIDER_NAME', 'PROVIDER_ZIP']]
op['op']=True
#sp=pd.read_pickle(INPUT_IPOP_DIR+r'\op')
#read_ip
ip=pd.read_pickle(INPUT_IPOP_DIR+'\\ip')
ip=ip.loc[:,['RECORD_ID','STMT_PERIOD_FROM','PAT_ADDR_CENSUS_BLOCK_GROUP','PAT_AGE_YEARS','SEX_CODE','RACE','PAT_STATUS','ETHNICITY','PAT_ZIP','PROVIDER_NAME', 'PROVIDER_ZIP']]
ip['op']=False
#merge Ip and OP
op=pd.concat([op,ip])
sp=op
del op,ip

#read population data
demos=pd.read_csv(r'Z:/Balaji/Census_data_texas/ACS_17_5YR_DP05_with_ann.csv',low_memory=False,skiprows=1)
demos.Id2=demos.Id2.astype("Int64")

#read study area counties
county_to_filter=pd.read_csv('Z:/Balaji/counties_inun.csv').GEOID.to_list()



#%%cleaing for age, gender and race and create census tract
#age
sp.loc[:,'PAT_AGE_YEARS']=pd.to_numeric(sp.PAT_AGE_YEARS,errors="coerce")
sp.loc[:,'PAT_AGE_YEARS']=sp.loc[:,'PAT_AGE_YEARS'].astype('float')

#bin ages
#sp.loc[:,'PAT_AGE_YEARS']=pd.cut(sp.PAT_AGE_YEARS,bins=[0,1,4,11,16,25,64,150],include_lowest=True,labels=(0,1,4,11,16,25,64)) 

#gender
sp.loc[~sp.SEX_CODE.isin(["M","F"]),'SEX_CODE']=np.nan
sp.SEX_CODE=sp.SEX_CODE.astype('category').cat.reorder_categories(['M','F'],ordered=False)

#ethinicity
sp.loc[:,'ETHNICITY']=pd.to_numeric(sp.ETHNICITY,errors="coerce")
sp.loc[~sp.ETHNICITY.isin([1,2]),'ETHNICITY']=np.nan
sp.ETHNICITY=sp.ETHNICITY.astype('category').cat.reorder_categories([2,1],ordered=False)
sp.ETHNICITY.cat.rename_categories({2:'Non_Hispanic',1:'Hispanic'},inplace=True)
#race
sp.loc[:,'RACE']=pd.to_numeric(sp.RACE,errors="coerce")
sp.loc[(sp.RACE<=0) | (sp.RACE>5),'RACE']=np.nan
sp.loc[sp.RACE<=2,'RACE']=5
sp.RACE=sp.RACE.astype('category').cat.reorder_categories([4,3,5],ordered=False)
sp.RACE.cat.rename_categories({3:'black',4:'white',5:'other'},inplace=True)

#create tract id from block group id
sp.loc[:,'PAT_ADDR_CENSUS_TRACT']=(sp.PAT_ADDR_CENSUS_BLOCK_GROUP//10)
    
#%%filter records for counties in study area 
sp=sp[(sp.PAT_ADDR_CENSUS_TRACT//1000000).isin(county_to_filter)].copy()

#%%keep only the dates we requested for

#remove records before 2016
sp=sp.loc[(~pd.isna(sp.STMT_PERIOD_FROM))&(~pd.isna(sp.PAT_ADDR_CENSUS_BLOCK_GROUP))] 

sp=sp[((sp.STMT_PERIOD_FROM > 20160700) & (sp.STMT_PERIOD_FROM< 20161232))\
    | ((sp.STMT_PERIOD_FROM > 20170400) & (sp.STMT_PERIOD_FROM< 20171232))\
        | ((sp.STMT_PERIOD_FROM > 20180700) & (sp.STMT_PERIOD_FROM< 20181232))]

#%% find unique providers
provider_zip=sp.loc[~sp.duplicated(['PROVIDER_NAME','PROVIDER_ZIP'],keep='first'),['PROVIDER_NAME','PROVIDER_ZIP']]
zip_codes=provider_zip.PROVIDER_ZIP
zip_codes=zip_codes.astype(str).str[:5]
provider_zip["ZIP5"]=pd.to_numeric(zip_codes,errors="coerce").astype('Int64')

provider_zip=provider_zip[~provider_zip.duplicated(['PROVIDER_NAME','ZIP5'],keep='first')]
    
provider_zip["STATE"]= "TX"

#%%import bg centroid and geocoded hospitals and compute cross distance
providers_loc=gpd.read_file(r"Z:\Balaji\arcProFiles\Default.gdb",layer="providers_Zips5_GeocodeAddreProjected")
providers_loc['s_no']=range(providers_loc.shape[0])
bg_centroids=gpd.read_file(r"Z:\Balaji\arcProFiles\Default.gdb",layer="tx_bg_centroid_proj")

merge_df=[]
#compute distance from each point to other
for i in range(providers_loc.shape[0]):
    dis=bg_centroids.distance(providers_loc.iloc[i,:].geometry)   
    df=bg_centroids.copy()
    df['DistanceToProvider']=dis
    df['provider_s_no']=providers_loc.iloc[i,:].s_no
    df["Provider_X"]=providers_loc.iloc[i,:].geometry.x
    df["Provider_Y"]=providers_loc.iloc[i,:].geometry.y
    merge_df.append(df)
    print(i)
    
merge_df=pd.concat(merge_df)


merge_df=merge_df.loc[:,['GEOID','provider_s_no','DistanceToProvider','Provider_X','Provider_Y']]
merge_df=merge_df.merge(providers_loc.loc[:,['USER_PROVIDER_NAME','USER_PROVIDER_ZIP','s_no']],left_on="provider_s_no",right_on="s_no",how='left')
    
    
#%% combine merge_df with the op ip df
merge_df.GEOID=pd.to_numeric(merge_df.GEOID).astype('Int64')
sp=sp.merge(merge_df,left_on=['PROVIDER_NAME','PROVIDER_ZIP','PAT_ADDR_CENSUS_BLOCK_GROUP'],right_on=['USER_PROVIDER_NAME','USER_PROVIDER_ZIP','GEOID'],how='left')

sp=sp.loc[:,['RECORD_ID', 'STMT_PERIOD_FROM', 'PAT_ADDR_CENSUS_BLOCK_GROUP','DistanceToProvider','Provider_X','Provider_Y','op','provider_s_no']]    
#save this as pickle 
sp.to_csv(r"Z:\Balaji\DSHS ED visit data\Provider_bg_dis.csv",index=False)

#%%merge innundation data
#%%group by stment period , flooded non flooded
#read blocks innundation
blocks_flood=gpd.read_file(r"Z:\Balaji\arcProFiles\Default.gdb",layer="tx_bg_Project_inundation").loc[:,["GEOID","flood_cell_count"]]
blocks_flood.GEOID=pd.to_numeric(blocks_flood.GEOID).astype('int64')
blocks_flood.flood_cell_count=(blocks_flood.flood_cell_count>0)

#merge inundation data
sp=sp.merge(blocks_flood,left_on="PAT_ADDR_CENSUS_BLOCK_GROUP",right_on="GEOID",how='left')
sp.DistanceToProvider=sp.DistanceToProvider/1000

#groupd by date, flooded/not
grp_df=sp.loc[:,['STMT_PERIOD_FROM','flood_cell_count','DistanceToProvider']].groupby(['STMT_PERIOD_FROM','flood_cell_count']).agg(['mean', 'count', 'std'])

#compute conf interval

ci95_hi = []
ci95_lo = []

for i in grp_df.index:
    m, c, s = grp_df.loc[i]
    ci95_hi.append(m + 1.96*s/math.sqrt(c))
    ci95_lo.append(m - 1.96*s/math.sqrt(c))

grp_df['ci95_hi'] = ci95_hi
grp_df['ci95_lo'] = ci95_lo

grp_df.reset_index(inplace=True)
grp_df["date"]=pd.to_datetime( pd.Series(grp_df.STMT_PERIOD_FROM,dtype='str'))
grp_df['avg']=grp_df.DistanceToProvider['mean']
#rolling mean
grp_df_cpy=grp_df.copy()
#%%draw plots
grp_df=grp_df_cpy.copy()
grp_df.loc[:,['ci95_hi','ci95_lo','avg']]=grp_df.loc[:,['ci95_hi','ci95_lo','avg']].rolling(window=1).mean()

fig=go.Figure()
df=grp_df[grp_df.flood_cell_count]
fig.add_trace(go.Scatter(x=df.date, y=df.avg,mode='lines+markers',name='flooded',marker_color="red"))
fig.add_trace(go.Scatter(x=df.date, y=df.ci95_hi,line=dict(color='red',dash='dot')))
fig.add_trace(go.Scatter(x=df.date, y=df.ci95_lo,line=dict(color='red',dash='dot')))

df=grp_df[~grp_df.flood_cell_count]
fig.add_trace(go.Scatter(x=df.date, y=df.avg,mode='lines+markers',name='non_flooded',marker_color="blue"))
fig.add_trace(go.Scatter(x=df.date, y=df.ci95_hi,line=dict(color='blue',dash='dot')))
fig.add_trace(go.Scatter(x=df.date, y=df.ci95_lo,line=dict(color='blue',dash='dot')))
fig.add_shape(dict(type="rect",x0='2017-08-26',y1=grp_df.ci95_hi.max()+5,x1='2017-09-13',y0=grp_df.ci95_lo.min()-5,opacity=0.4,fillcolor='#ffff00',line=dict(width=0) ))
fig.update_layout(plot_bgcolor='white')
fig.update_xaxes( gridcolor='rgb(210,210,210)',gridwidth=.5)
fig.update_yaxes(gridcolor='rgb(210,210,210)',gridwidth=.5)
fig.show()
#%%
grp_df=grp_df.rename(columns={0:"counts"})
grp_df = gpd.GeoDataFrame(grp_df, geometry=gpd.points_from_xy(grp_df.Provider_X, grp_df.Provider_Y))
grp_df.to_file('new')
    
    
    
    
    
    
    
    
    
    
    
    
