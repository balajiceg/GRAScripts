"""
Created on Fri Mar 20 03:11:56 2020

@author: balajiramesh
"""
import pandas as pd
import numpy as np
import geopandas as gpd

merged_ip=pd.read_pickle('./trial.zip')
df=merged_ip

required=df.loc[:,['RECORD_ID','LCODE','STMT_PERIOD_FROM','PAT_ADDR_CENSUS_BLOCK_GROUP']].copy()

#count number of reccords that census tract could have be got
xx=required.LCODE.str.slice(0,2)=="ZT"
xx.value_counts()


required.loc[:,'STMT_PERIOD_FROM_MONTH']=(required.STMT_PERIOD_FROM//10)*10+1
required.loc[:,'PAT_ADDR_CENSUS_TRACT']=(required.PAT_ADDR_CENSUS_BLOCK_GROUP//10)




grouped=required.groupby(['STMT_PERIOD_FROM_MONTH', 'PAT_ADDR_CENSUS_TRACT']).size().reset_index()
grouped.rename(columns={0:"COUNTS"},inplace=True)

#grouped.to_excel('./Ip_agg.xlsx')
grouped.to_csv('./Ip_agg.csv')


#counting with bins

new_date=required.loc[:,"STMT_PERIOD_FROM"]
new_date=new_date.dropna().astype(int).astype(str)
new_date=pd.to_datetime(new_date)


bins=["%04d-%02d-%02d"%(y,m,d) 
                         for y in (2016,2017,2018) 
                             for m in range(4,13) 
                                 for d in (1,10,20)]+["2018-12-30"]
bin_dates=pd.to_datetime(bins)



counts_time=pd.cut(new_date,bins=bin_dates,labels=bins[:-1]).value_counts().reset_index()

counts_time.columns=["startDate","counts"]
counts_time.loc[:,"startDate"]=pd.to_datetime(counts_time.startDate)
counts_time.plot("startDate","counts")
