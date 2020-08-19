# -*- coding: utf-8 -*-
"""
Created on Sat Aug 15 23:18:33 2020

@author: balajiramesh
"""

import pandas as pd
import numpy as np
import geopandas
import statsmodels.api as sm
import statsmodels.formula.api as smf
from datetime import timedelta, date,datetime
from dateutil import parser

import sys
sys.path.insert(1, r'Z:\GRAScripts\dhs_scripts')
from recalculate_svi import recalculateSVI


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
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
