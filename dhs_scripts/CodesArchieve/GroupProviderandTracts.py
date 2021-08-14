# -*- coding: utf-8 -*-
"""
Created on Fri Jun 18 13:59:49 2021
For Dr.Samarth- using evacuation points provided, computed the number of ED visits travelled from each census tract to the 
provider near the evacuation points
@author: balajiramesh
"""
import pandas as pd
import numpy as np
import geopandas
from datetime import timedelta, date,datetime
import fiona

#%%read ip op data
INPUT_IPOP_DIR=r'Z:\Balaji\DSHS ED visit data\CleanedMergedJoined'
#read_op
op=pd.read_pickle(INPUT_IPOP_DIR+'\\op')
op['op']=True
#sp=pd.read_pickle(INPUT_IPOP_DIR+r'\op')
#read_ip
ip=pd.read_pickle(INPUT_IPOP_DIR+'\\ip')
ip['op']=False
#merge Ip and OP
op=pd.concat([op,ip])
sp=op
del op,ip


#create tract id from block group id
sp.loc[:,'PAT_ADDR_CENSUS_TRACT']=(sp.PAT_ADDR_CENSUS_BLOCK_GROUP//10) 
#filter records for counties(NOT TRACTS) in required region
tractsToFilter=[48361,48041,48245,48157,48149,48477,48407,48481,48473,48457,48471,48167,48201,48239,48089,48185,48373,48287,48313,48291,48241,48071,48199,48039,48321,48015,48051,48455,48285,48339]
county_to_filter=pd.read_csv('Z:/Balaji/counties_inun.csv').GEOID.to_list()
sp=sp[(sp.PAT_ADDR_CENSUS_TRACT//1000000).isin(county_to_filter)].copy()
#dates to filter
sp=sp[((sp.STMT_PERIOD_FROM > 20170818) & (sp.STMT_PERIOD_FROM< 20170918))]


#counts per census tract
groupedTractCount=sp.groupby(['PAT_ADDR_CENSUS_TRACT']).size().reset_index().rename(columns={0:'TotalTractCounts'})
#create hospital name + zipcode filed
sp['ProviderAdrsWithZip']=sp.PROVIDER_NAME +sp.PROVIDER_ZIP.map(str)

#read points provided by Dr.Samarth and its associate provider and distance
fiona.listlayers(r'Z:\Balaji\arcProFiles\Project.gdb')
locsWithProvider=geopandas.read_file(r'Z:\Balaji\arcProFiles\Project.gdb',layer='DHSeDvisitProviderLocs').loc[:,['AddressWithZip', 'NEAR_DIST', 'label', 'WithinBoundary']]

#groupby provider and censustract
grouped=sp.groupby(['ProviderAdrsWithZip','PAT_ADDR_CENSUS_TRACT']).size().reset_index().rename(columns={0:'Counts'})

#join with provider the points
grouped=grouped.merge(locsWithProvider,how='left',left_on='ProviderAdrsWithZip',right_on='AddressWithZip')
#meege the ones that did not properly merge manually
for i in grouped.ProviderAdrsWithZip[pd.isna(grouped.AddressWithZip)].unique():
    grouped.loc[grouped.ProviderAdrsWithZip==i,'NEAR_DIST']=locsWithProvider.NEAR_DIST[locsWithProvider.AddressWithZip.str.contains(i)].iloc[0]
    grouped.loc[grouped.ProviderAdrsWithZip==i,'label']=locsWithProvider.label[locsWithProvider.AddressWithZip.str.contains(i)].iloc[0]
    grouped.loc[grouped.ProviderAdrsWithZip==i,'WithinBoundary']=locsWithProvider.WithinBoundary[locsWithProvider.AddressWithZip.str.contains(i)].iloc[0]


#filter only required censustracts using county ids
grouped=grouped[(grouped.PAT_ADDR_CENSUS_TRACT//1000000).isin(tractsToFilter)]

#remove providers that where withing the six points boundary / in the center of the points boundary
print( grouped.WithinBoundary.value_counts()) #most of the records are within boundary

grouped=grouped[~((grouped.WithinBoundary==1)&(grouped.NEAR_DIST>15000))]

#grouped by label and census tract
grouped=grouped.groupby(['label','PAT_ADDR_CENSUS_TRACT']).agg({'Counts':'sum'}).reset_index()

#merge it with the grouped census tracts
grouped=grouped.merge(groupedTractCount,how='left',on='PAT_ADDR_CENSUS_TRACT')
#compute fraction
grouped['fraction']=grouped.Counts/grouped.TotalTractCounts

#rename columns
grouped=grouped.rename(columns={'label':'points','Counts':'EDvisitsTowardsPointFromTract','TotalTractCounts':'TotalEDvisitsFromTract'})

(grouped.EDvisitsTowardsPointFromTract<16).value_counts()
#grouped.to_csv(r'Z:\Balaji\DSHS ED visit data\TractToPoints_DrSamarth.csv',index=False)


