# -*- coding: utf-8 -*-
"""
Created on Fri May 15 01:55:22 2020

@author: balajiramesh
"""


# -*- coding: utf-8 -*-
"""
Created on Fri Apr 10 00:25:12 2020

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
sp=sp.loc[:,['RECORD_ID','STMT_PERIOD_FROM','PAT_ADDR_CENSUS_BLOCK_GROUP','PAT_AGE_YEARS','SEX_CODE','RACE','PAT_STATUS','ETHNICITY','PAT_ZIP']]
#sp=pd.read_pickle(INPUT_IPOP_DIR+r'\op')

#read op/ip outcomes df
sp_outcomes=pd.read_csv(INPUT_IPOP_DIR+'\\'+sp_file+'_outcomes.csv')

#read flood ratio data
flood_data=geopandas.read_file(r'Z:/Balaji/FloodRatioJoinedAll_v1/FloodInund_AllJoined_v1.gpkg').drop('geometry',axis=1)

#read zip code flood ratio data
flood_data_zip=geopandas.read_file(r"Z:/Balaji/FloodInund_Zip_v1/FloodInund_Zip_v1.shp").loc[:,['ZCTA5CE10','DFO_R200']]
flood_data_zip.rename(columns={'ZCTA5CE10':'GEOID'},inplace=True)

#read svi data
SVI_df_raw=geopandas.read_file(r'Z:/Balaji/SVI_Raw/TEXAS.shp').drop('geometry',axis=1)
SVI_df_raw.FIPS=pd.to_numeric(SVI_df_raw.FIPS)

#read population data
demos=pd.read_csv(r'Z:/Balaji/Census_data_texas/ACS_17_5YR_DP05_with_ann.csv',low_memory=False,skiprows=1)
demos.Id2=demos.Id2.astype("Int64")

#read study area counties
county_to_filter=pd.read_csv('Z:/Balaji/counties_inun.csv').GEOID.to_list()
zip_to_filter=pd.read_csv('Z:/Balaji/DSHS ED visit data/AllZip_codes_in_study_area.csv').ZCTA5CE10.to_list()

#%%read the categories file
outcome_cats=pd.read_csv('Z:/GRAScripts/dhs_scripts/categories.csv')
outcome_cats.fillna('',inplace=True)
#%%predefine variable 
flood_cats_in=1
floodr_use="DFO_R200" #['DFO_R200','DFO_R100','LIST_R20','DFO_R20','DFOuLIST_R20']
nullAsZero="True" #null flood ratios are changed to 0
floodZeroSep="True" # zeros are considered as seperate class
#flood_data_zip=None

interv_dates=[20170825, 20170913, 20171014]
interv_dates_cats=['flood','PostFlood1','PostFlood2']
Dis_cat="Asthma"

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
    
#%%filter records for counties in study area or from zip codes
if flood_data_zip is None:
    sp=sp[(sp.PAT_ADDR_CENSUS_TRACT//1000000).isin(county_to_filter)].copy()
else:
    zip_codes=sp.PAT_ZIP
    zip_codes=zip_codes.astype(str).str[:5]
    sp.PAT_ZIP=pd.to_numeric(zip_codes,errors="coerce").astype('Int64')
    sp=sp[sp.PAT_ZIP.isin(zip_to_filter)]
    
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
svi=recalculateSVI(SVI_df_raw[SVI_df_raw.FIPS.isin(sp.PAT_ADDR_CENSUS_TRACT.unique())]).loc[:,["FIPS",'SVI']]
sp=sp.merge(svi,left_on="PAT_ADDR_CENSUS_TRACT",right_on="FIPS",how='left').drop("FIPS",axis=1)
#sp['SVI_Cat']=pd.cut(sp.SVI,bins=np.arange(0,1.1,1/4),include_lowest=True,labels=[1,2,3,4])

#%%merge flood ratio
flood_join_field='PAT_ADDR_CENSUS_TRACT'
if flood_data_zip is not None: 
    flood_data=flood_data_zip
    flood_join_field='PAT_ZIP'
FLOOD_QUANTILES=["NO","FLood_1"]
floodr=flood_data.copy()
floodr.GEOID=pd.to_numeric(floodr.GEOID).astype("Int64")
floodr=floodr.loc[:,['GEOID']+[floodr_use]]
floodr.columns=['GEOID','floodr']
sp=sp.merge(floodr,left_on=flood_join_field,right_on='GEOID',how='left')

#make tracts with null as zero flooding
if nullAsZero == "True": sp.loc[pd.isna(sp.floodr),'floodr']=0.0

#categorize floods as per quantiles
tractsfloodr=sp.loc[~sp.duplicated(flood_join_field),[flood_join_field,'floodr']]
tractsfloodr.floodr= tractsfloodr.floodr.round(2)
if floodZeroSep == "True":
    s=tractsfloodr.loc[tractsfloodr.floodr>0,'floodr']  
    flood_bins=s.quantile(np.arange(0,1.1,1/(len(FLOOD_QUANTILES)-1))).to_numpy()
    flood_bins[0]=1e-6
    flood_bins=np.append([0],flood_bins)
else:
    s=tractsfloodr.loc[tractsfloodr.floodr>-1,'floodr']
    flood_bins=s.quantile(np.arange(0,1.1,1/len(FLOOD_QUANTILES))).to_numpy()

# adjust if some bincenters were zero    
for i in range(1,len(FLOOD_QUANTILES)):
    flood_bins[i]=i*1e-6 if flood_bins[i]==0.0 else flood_bins[i]

sp.loc[:,'floodr']=pd.cut(sp.floodr,bins=flood_bins,right=True,include_lowest=True,labels=FLOOD_QUANTILES)
sp=sp.drop("GEOID",axis=1)
    
       
#%%function for looping
def run():
    #%%filter records for specific outcome
    df=sp
    if Dis_cat=="DEATH":df.loc[:,'Outcome']=filter_mortality(sp)
    if Dis_cat=="ALL":df.loc[:,'Outcome']=1
    if Dis_cat in outcome_cats.category.to_list():df.loc[:,'Outcome']=get_sp_outcomes(sp, Dis_cat)
    


    #%% bringing in intervention
    df.loc[:,'Time']=pd.cut(df.STMT_PERIOD_FROM,\
                                        bins=[0]+interv_dates+[20190101],\
                                        labels=['control']+[str(i) for i in interv_dates_cats]).cat.as_unordered()
    #set after 2018 as control
    df.loc[df.STMT_PERIOD_FROM>20180100,'Time']="control" if Dis_cat!="Psychiatric" else np.nan
    df=df.loc[~pd.isna(df.Time),]
    
    #%%controling for year month and week of the day
    df['year']=(df.STMT_PERIOD_FROM.astype('int32')//1e4).astype('category')
    df['month']=(df.STMT_PERIOD_FROM.astype('int32')//1e2%100).astype('category')
    df['weekday']=pd.to_datetime(df.STMT_PERIOD_FROM.astype('str'),format='%Y%m%d').dt.dayofweek.astype('category')
    
    #%%stratified model steps
    #df=df.loc[df.Time.isin(['control', '20171014']),]
    #df.Time.cat.remove_unused_categories(inplace=True)
    
    #%% save cross tab
     #counts_outcome=pd.DataFrame(df.Outcome.value_counts())
    outcomes_recs=df.loc[(df.Outcome>0),]
    counts_outcome=pd.crosstab(outcomes_recs.Time,outcomes_recs.floodr)
    counts_outcome.to_csv(Dis_cat+"_aux"+".csv")
    print(counts_outcome)
    
    #%%running the model
    #if Dis_cat!="ALL":offset=np.log(df.TotalVisits)
    offset=None
    if Dis_cat=="ALL":offset=np.log(df.Population)
    
    
    formula='Outcome'+' ~ '+' floodr * Time '+'+ year'+'+month'+'+weekday' + '+PAT_AGE_YEARS + SEX_CODE + RACE + ETHNICITY'
    model = smf.gee(formula=formula,groups=df[flood_join_field], data=df,offset=offset,missing='drop',family=sm.families.Poisson(link=sm.families.links.log()))
    #model = smf.logit(formula=formula, data=df,missing='drop')
    #model = smf.glm(formula=formula, data=df,missing='drop',family=sm.families.Binomial(sm.families.links.logit()))
    
    results=model.fit()
    # print(results.summary())
    # print(np.exp(results.params))
    # print(np.exp(results.conf_int())) 
    
    
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
    
   
    
    # counts_outcome.loc["flood_bins",'Outcome']=str(flood_bins)
    #return reg_table
    #%%write the output
    reg_table.to_csv(Dis_cat+"_reg"+".csv")
    reg_table_dev.to_csv(Dis_cat+"_dev"+".csv")
    
