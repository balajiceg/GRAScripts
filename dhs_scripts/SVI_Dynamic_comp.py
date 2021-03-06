# -*- coding: utf-8 -*-
"""
Created on Thu Jun 11 19:15:05 2020

@author: balajiramesh
"""


# -*- coding: utf-8 -*-
"""
Created on Fri May 15 01:55:22 2020

@author: balajiramesh
"""

import pandas as pd
import numpy as np
import geopandas
import statsmodels.api as sm
import statsmodels.formula.api as smf
from datetime import timedelta, date,datetime
from dateutil import parser
import os

import sys
sys.path.insert(1, r'Z:\GRAScripts\dhs_scripts')
from recalculate_svi import recalculateSVI

#%%functions
def filter_mortality(df):
    pat_sta=df.PAT_STATUS.copy()
    pat_sta=pd.to_numeric(pat_sta,errors="coerce")
    return pat_sta.isin([20,40,41,42]).astype('int') #status code for died

def get_sp_outcomes(sp,Dis_cat):
    global sp_outcomes
    return sp.merge(sp_outcomes.loc[:,['RECORD_ID',Dis_cat]],on='RECORD_ID',how='left')[Dis_cat].values
    

#%%read ip op data
INPUT_IPOP_DIR=r'Z:\Balaji\DSHS ED visit data\CleanedMergedJoined'
sp_file='op'
sp=pd.read_pickle(INPUT_IPOP_DIR+'\\'+sp_file)
sp=sp.loc[:,['RECORD_ID','STMT_PERIOD_FROM','PAT_ADDR_CENSUS_BLOCK_GROUP','PAT_AGE_YEARS','SEX_CODE','RACE','PAT_STATUS','ETHNICITY']]

#sp=pd.read_pickle(INPUT_IPOP_DIR+r'\op')
#read op/ip outcomes df
sp_outcomes=pd.read_csv(INPUT_IPOP_DIR+'\\'+sp_file+'_outcomes.csv')


#read flood ratio data
flood_data=geopandas.read_file(r'Z:/Balaji/FloodRatioJoinedAll_v1/FloodInund_AllJoined_v1.gpkg')

#read svi data
SVI_df_raw=geopandas.read_file(r'Z:/Balaji/SVI_Raw/TEXAS.shp').drop('geometry',axis=1)
SVI_df_raw.FIPS=pd.to_numeric(SVI_df_raw.FIPS)

#read population data
demos=pd.read_csv(r'Z:/Balaji/Census_data_texas/ACS_17_5YR_DP05_with_ann.csv',low_memory=False,skiprows=1)
demos.Id2=demos.Id2.astype("Int64")

#read study area counties
county_to_filter=-1# pd.read_csv('Z:/Balaji/counties_inun.csv').GEOID.to_list()

#read dynamic svi
SVI_dyn=pd.read_csv('Z:/Balaji/Dynamic_SVI/SPL_Themes_1_2_3.csv').iloc[:,1:]
SVI_dyn.FIPS=SVI_dyn.FIPS.astype("Int64")
#%%read the categories file
outcome_cats=pd.read_csv('Z:/GRAScripts/dhs_scripts/categories.csv')
outcome_cats.fillna('',inplace=True)
#%%predefine variable 
flood_cats_in=1
floodr_use="DFO_R200" #['DFO_R200','DFO_R100','LIST_R20','DFO_R20','DFOuLIST_R20']
nullAsZero="True" #null flood ratios are changed to 0
floodZeroSep="True" # zeros are considered as seperate class

interv_dates=[20170825, 20170913]
Dis_cat="DEATH"

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
sp.ETHNICITY=sp.ETHNICITY.astype('category')

#race
sp.loc[:,'RACE']=pd.to_numeric(sp.RACE,errors="coerce")
sp.loc[(sp.RACE<=0) | (sp.RACE>5),'RACE']=np.nan
sp.loc[sp.RACE<=2,'RACE']=5
sp.RACE=sp.RACE.astype('category').cat.reorder_categories([4,3,5],ordered=False)
sp.RACE.cat.rename_categories({3:'black',4:'white',5:'other'},inplace=True)

#create tract id from block group id
sp.loc[:,'PAT_ADDR_CENSUS_TRACT']=(sp.PAT_ADDR_CENSUS_BLOCK_GROUP//10)
    
#%%filter records for counties in study area
if county_to_filter != -1:
    sp=sp[(sp.PAT_ADDR_CENSUS_TRACT//1000000).isin(county_to_filter)].copy()

#%%keep only the dates we requested for

#remove records before 2016
sp=sp.loc[(~pd.isna(sp.STMT_PERIOD_FROM))&(~pd.isna(sp.PAT_ADDR_CENSUS_BLOCK_GROUP))] 

sp=sp[((sp.STMT_PERIOD_FROM > 20160700) & (sp.STMT_PERIOD_FROM< 20161232))\
    | ((sp.STMT_PERIOD_FROM > 20170400) & (sp.STMT_PERIOD_FROM< 20171232))\
        | ((sp.STMT_PERIOD_FROM > 20180700) & (sp.STMT_PERIOD_FROM< 20181232))]

#%% merge population
demos_subset=demos.iloc[:,[1,3]]
demos_subset.columns=["PAT_ADDR_CENSUS_TRACT","Population"]
sp=sp.merge(demos_subset,on="PAT_ADDR_CENSUS_TRACT",how='left')
sp=sp.loc[sp.Population>0,]

#%% merge SVI after recategorization
svi=recalculateSVI(SVI_df_raw[SVI_df_raw.FIPS.isin(sp.PAT_ADDR_CENSUS_TRACT.unique())]).loc[:,["FIPS",'RPL_THEMES_1','RPL_THEMES_2','RPL_THEMES_3']]
sp=sp.merge(svi,left_on="PAT_ADDR_CENSUS_TRACT",right_on="FIPS",how='left').drop("FIPS",axis=1)
#sp.loc[:,'SVI']=pd.cut(sp.SVI,bins=np.arange(0,1.1,1/4),include_lowest=True,labels=[1,2,3,4])

 #%%controling for year month and week of the day
sp['year']=(sp.STMT_PERIOD_FROM.astype('int32')//1e4).astype('category')
sp['month']=(sp.STMT_PERIOD_FROM.astype('int32')//1e2%100).astype('category')
sp['weekday']=pd.to_datetime(sp.STMT_PERIOD_FROM.astype('str'),format='%Y%m%d').dt.dayofweek.astype('category')

#%%combine dynamic SVI
sp=sp.merge(SVI_dyn,left_on=['PAT_ADDR_CENSUS_TRACT','weekday'],right_on=["FIPS",'Day_of_week']).drop([ 'FIPS', 'Day_of_week'],axis=1)
sp.rename(columns={"Theme_1": "dyn_RPL_THEMES_1","Theme_2": "dyn_RPL_THEMES_2","Theme_3": "dyn_RPL_THEMES_3"},inplace=True)

#categorize both
# for i in ["1","2","3"]:
#     sp.loc[:,'RPL_THEMES_'+i]=pd.cut(sp["RPL_THEMES_"+i],bins=np.arange(0,1.1,1/4),include_lowest=True,labels=[1,2,3,4])
#     sp.loc[:,'dyn_RPL_THEMES_'+i]=pd.cut(sp["dyn_RPL_THEMES_"+i],bins=np.arange(0,1.1,1/4),include_lowest=True,labels=[1,2,3,4])

#%%function for looping
def run():
    #%%filter records for specific outcome
    df=sp
    if Dis_cat=="DEATH":df.loc[:,'Outcome']=filter_mortality(sp)
    if Dis_cat=="ALL":df.loc[:,'Outcome']=1
    if Dis_cat in outcome_cats.category.to_list():df.loc[:,'Outcome']=get_sp_outcomes(sp, Dis_cat)
    
#%%fun model 
    
    for theme in ["RPL_THEMES_","dyn_RPL_THEMES_"]:     
        #%%running the model
        #if Dis_cat!="ALL":offset=np.log(df.TotalVisits)
        offset=None
        if Dis_cat=="ALL":offset=np.log(df.Population)
        
        formula = theme+'1 + '+theme+'2 + '+theme+'3 '
        #formula='Outcome'+' ~ '+' floodr + Time * '+ theme + '+ year'+'+month'+'+weekday' + '+PAT_AGE_YEARS + SEX_CODE + RACE'
        formula='Outcome'+' ~ '+ formula + '+ year + month + weekday + PAT_AGE_YEARS + SEX_CODE + RACE + ETHNICITY'
        model = smf.gee(formula=formula,groups=df.PAT_ADDR_CENSUS_TRACT, data=df,offset=offset,missing='drop',family=sm.families.Poisson(link=sm.families.links.log()))
        #model = smf.logit(formula=formula, data=df,missing='drop')
        #model = smf.glm(formula=formula, data=df,missing='drop',family=sm.families.Binomial(sm.families.links.logit()))
        
        results=model.fit()
        # print(results.summary())
        # print(np.exp(results.params))
        # print(np.exp(results.conf_int())) 
        print(results.qic(scale=1))
        
        #%% creating result dataframe tables
        results_as_html = results.summary().tables[1].as_html()
        reg_table=pd.read_html(results_as_html, header=0, index_col=0)[0].reset_index()
        reg_table.loc[:,'coef']=np.exp(reg_table.coef)
        reg_table.loc[:,['[0.025', '0.975]']]=np.exp(reg_table.loc[:,['[0.025', '0.975]']])
        reg_table=reg_table.loc[~(reg_table['index'].str.contains('month') 
                                  | reg_table['index'].str.contains('month')
                                  | reg_table['index'].str.contains('weekday')
                                  #| reg_table['index'].str.contains('year')
                                  #| reg_table['index'].str.contains('PAT_AGE_YEARS')
                                  
                                  ),]
        reg_table['index']=reg_table['index'].str.replace("\[T.",'_').str.replace('\]','')
        reg_table_dev=pd.read_html(results.summary().tables[0].as_html())[0]
        
        counts_outcome=pd.DataFrame(df.Outcome.value_counts())
        #outcomes_recs=df.loc[(df.Outcome>0) & (df.Time!='control'),:]
        #counts_outcome=pd.DataFrame(outcomes_recs.floodr.value_counts())
        
        # counts_outcome.loc["flood_bins",'Outcome']=str(flood_bins)
        
        #%%write the output
        # if not os.path.exists(theme):os.makedirs(theme)
        
        # reg_table.to_csv(theme+"/"+Dis_cat+"_reg"+".csv")
        # reg_table_dev.to_csv(theme+"/"+Dis_cat+"_dev"+".csv")
        # counts_outcome.to_csv(theme+"/"+Dis_cat+"_aux"+".csv")
        
        print(Dis_cat)
        print(theme)
        print(counts_outcome)
        print("-"*30)
