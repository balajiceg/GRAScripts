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
import glob
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
    return sp.merge(sp_outcomes.loc[:,['RECORD_ID','op',Dis_cat]],on=['RECORD_ID','op'],how='left')[Dis_cat].values

#%%read ip op data
INPUT_IPOP_DIR=r'Z:\Balaji\DSHS ED visit data\CleanedMergedJoined'
#read_op
op=pd.read_pickle(INPUT_IPOP_DIR+'\\op')
op=op.loc[:,['RECORD_ID','STMT_PERIOD_FROM','PAT_ADDR_CENSUS_BLOCK_GROUP','PAT_AGE_YEARS','SEX_CODE','RACE','PAT_STATUS','ETHNICITY','PAT_ZIP']]
op['op']=True
#sp=pd.read_pickle(INPUT_IPOP_DIR+r'\op')
#read_ip
ip=pd.read_pickle(INPUT_IPOP_DIR+'\\ip')
ip=ip.loc[:,['RECORD_ID','STMT_PERIOD_FROM','PAT_ADDR_CENSUS_BLOCK_GROUP','PAT_AGE_YEARS','SEX_CODE','RACE','PAT_STATUS','ETHNICITY','PAT_ZIP']]
ip['op']=False
#merge Ip and OP
op=pd.concat([op,ip])
sp=op
del op,ip


#read op/ip outcomes df
sp_outcomes=pd.read_csv(INPUT_IPOP_DIR+'\\ip_op_outcomes.csv')

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

#read household income data 
income=pd.read_csv(r'Z:/Balaji/Census_data_texas/ACSST5Y2017.S1903_data_with_overlays_2020-10-14T202327.csv',low_memory=False,skiprows=1)
income.id=pd.to_numeric(income.id.str.replace("1400000US",'')).astype("Int64")

#read study area counties
#county_to_filter=pd.read_csv('Z:/Balaji/counties_evacu_order.csv').GEOID.to_list()
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
flood_data_zip=None

interv_dates=[20170825, 20170913, 20171014] #lower bound excluded
washout_period=[20170819,20170825] #including the dates specified
interv_dates_cats=['flood','PostFlood1','PostFlood2']
Dis_cat="ALL"

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

#remove data in washout period
sp= sp[~((sp.STMT_PERIOD_FROM >= washout_period[0]) & (sp.STMT_PERIOD_FROM <= washout_period[1]))]
#%% merge population and economy
demos_subset=demos.iloc[:,[1,3]]
demos_subset.columns=["PAT_ADDR_CENSUS_TRACT","Population"]
sp=sp.merge(demos_subset,on="PAT_ADDR_CENSUS_TRACT",how='left')
sp=sp.loc[sp.Population>0,]

# economy_subset=income.loc[:,['id','Estimate!!Median income (dollars)!!HOUSEHOLD INCOME BY RACE AND HISPANIC OR LATINO ORIGIN OF HOUSEHOLDER!!Households']]
# economy_subset.columns=["PAT_ADDR_CENSUS_TRACT","Median_H_Income"]
# sp=sp.merge(economy_subset,on="PAT_ADDR_CENSUS_TRACT",how='left')
# sp.loc[sp.Median_H_Income=='250,000+',"Median_H_Income"]=250000
# sp.Median_H_Income=pd.to_numeric(sp.Median_H_Income,errors='coerce')
#%% merge SVI after recategorization
svi=recalculateSVI(SVI_df_raw[SVI_df_raw.FIPS.isin(sp.PAT_ADDR_CENSUS_TRACT.unique())])#.loc[:,["FIPS",'SVI',]]
sp=sp.merge(svi,left_on="PAT_ADDR_CENSUS_TRACT",right_on="FIPS",how='left').drop("FIPS",axis=1)
sp['SVI_Cat']=pd.cut(sp.SVI,bins=np.arange(0,1.1,1/4),include_lowest=True,labels=[1,2,3,4])

# #do same for the for cats
for i in ['1','2','3','4']:
    sp['SVI_Cat_T'+i]=pd.cut(sp['RPL_THEMES_'+i],bins=np.arange(0,1.1,1/4),include_lowest=True,labels=[1,2,3,4])

#%%filter SVI cat for stratified analysis
#sp=sp[sp.SVI_Cat==4]
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

if floodZeroSep == "True":
    #tractsfloodr.floodr= tractsfloodr.floodr.round(4)
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

sp['floodr_cat']=pd.cut(sp.floodr,bins=flood_bins,right=True,include_lowest=True,labels=FLOOD_QUANTILES)
sp=sp.drop("GEOID",axis=1)
    
#%%calculating total visits for offset
vists_per_tract=sp.groupby(['PAT_ADDR_CENSUS_TRACT','STMT_PERIOD_FROM'])\
                  .size().reset_index().rename(columns={0:'TotalVisits'})
sp=sp.merge(vists_per_tract,on=['PAT_ADDR_CENSUS_TRACT','STMT_PERIOD_FROM'],how='left')

#%%creating day from start for CITS
day_from_start=pd.DataFrame({'STMT_PERIOD_FROM':pd.date_range('2016-07-01', '2018-12-31', freq='d').astype('str').str.replace('-','').astype('int64')}).reset_index().rename(columns={'index':'DayFromStart'})
sp=sp.merge(day_from_start,on='STMT_PERIOD_FROM',how='left')
#%%pat age categoriy based on SVI theme  2  <=17,18-64,>=65
sp.loc[:,'AGE_cat']=pd.cut(sp.PAT_AGE_YEARS,bins=[-1,17,64,200],labels=['0-17','18-64','>64']).cat.reorder_categories(['18-64','0-17','>64'])
#%%function for looping
SVI_COL='SVI_Cat_T2'
def run():
    #print(cuts[i])
    #sp.loc[:,'floodr_cat']=pd.cut(sp.floodr,bins=[0,cuts[i],1],right=True,include_lowest=True,labels=FLOOD_QUANTILES)
    #%%filter records for specific outcome
    df=sp#[sp.SVI_Cat==SVI_filter]
    if Dis_cat=="DEATH":df.loc[:,'Outcome']=filter_mortality(sp)
    if Dis_cat=="ALL":df.loc[:,'Outcome']=1
    if Dis_cat in outcome_cats.category.to_list():df.loc[:,'Outcome']=get_sp_outcomes(sp, Dis_cat)
    
    #%%for filtering flooded or non flooded alone
    #df=df[df.floodr_cat=="FLood_1"].copy()

    #%% bringing in intervention
    df.loc[:,'Time']=pd.cut(df.STMT_PERIOD_FROM,\
                                        bins=[0]+interv_dates+[20190101],\
                                        labels=['control']+[str(i) for i in interv_dates_cats]).cat.as_unordered()
    #set after 2018 as control
    df.loc[df.STMT_PERIOD_FROM>20180100,'Time']="control" if Dis_cat!="Psychiatric" else np.nan
    df=df.loc[~pd.isna(df.Time),]
    
    #take only control period
    #df=df[df.Time=='control']
    #%%controling for year month and week of the day
    df['year']=(df.STMT_PERIOD_FROM.astype('int32')//1e4).astype('category')
    df['month']=(df.STMT_PERIOD_FROM.astype('int32')//1e2%100).astype('category')
    df['weekday']=pd.to_datetime(df.STMT_PERIOD_FROM.astype('str'),format='%Y%m%d').dt.dayofweek.astype('category')
    
    #%%stratified model steps
    #df=df.loc[df.Time.isin(['control', '20171014']),]
    #df.Time.cat.remove_unused_categories(inplace=True)
    
    #%% save cross tab
     #counts_outcome=pd.DataFrame(df.Outcome.value_counts())
    outcomes_recs=df.loc[(df.Outcome>0)&(~pd.isna(df.loc[:,['floodr_cat','Time','year','month','weekday' ,'PAT_AGE_YEARS', 
                                                          'SEX_CODE','RACE','ETHNICITY',SVI_COL]]).any(axis=1)),]
    counts_outcome=pd.crosstab(outcomes_recs[SVI_COL] ,[outcomes_recs.Time,outcomes_recs.floodr_cat])
    counts_outcome.to_csv(Dis_cat+"_aux"+".csv")
    print(counts_outcome)
    del outcomes_recs
    
    #%%for total ED visits using grouped / coutns
    if Dis_cat=="ALL":
        grouped_tracts=df.loc[:,['STMT_PERIOD_FROM','PAT_AGE_YEARS','PAT_ADDR_CENSUS_TRACT','Outcome']]
        grouped_tracts=pd.concat([grouped_tracts]+[pd.get_dummies(df[i],prefix=i) for i in ['SEX_CODE','RACE','ETHNICITY','op','AGE_cat']],axis=1)
        
        grouped_tracts=grouped_tracts.groupby(['STMT_PERIOD_FROM', 'PAT_ADDR_CENSUS_TRACT']).agg({'Outcome':'sum',
                                                                                      'PAT_AGE_YEARS':'mean',
                                                                                      'SEX_CODE_M':'sum','SEX_CODE_F':'sum', 
                                                                                      'RACE_white':'sum','RACE_black':'sum','RACE_other':'sum',
                                                                                      'ETHNICITY_Non_Hispanic':'sum','ETHNICITY_Hispanic':'sum', 
                                                                                      'op_False':'sum','op_True':'sum',
                                                                                      'AGE_cat_18-64':'sum', 'AGE_cat_0-17':'sum', 'AGE_cat_>64':'sum'
                                                                                      }).reset_index()
                         
        grouped_tracts=grouped_tracts.merge(df.drop_duplicates(['STMT_PERIOD_FROM','PAT_ADDR_CENSUS_TRACT']).loc[:,['STMT_PERIOD_FROM','PAT_ADDR_CENSUS_TRACT','floodr_cat','Population','Time','year','month','weekday',SVI_COL,'floodr']],how='left',on=["PAT_ADDR_CENSUS_TRACT",'STMT_PERIOD_FROM'])
        dummy_cols=['SEX_CODE_M', 'SEX_CODE_F', 'RACE_white', 'RACE_black', 'RACE_other','ETHNICITY_Non_Hispanic', 'ETHNICITY_Hispanic', 'op_False', 'op_True','AGE_cat_18-64', 'AGE_cat_0-17', 'AGE_cat_>64']
        grouped_tracts.loc[:,dummy_cols]=grouped_tracts.loc[:,dummy_cols].divide(grouped_tracts.Outcome,axis=0)
        del df
        df=grouped_tracts
    
    
    #%%running the model
    if Dis_cat!="ALL":offset=np.log(df.TotalVisits)
    #offset=None
    if Dis_cat=="ALL":offset=np.log(df.Population)
    
    #change floodr into 0-100
    df.floodr=df.floodr*100
    formula='Outcome'+' ~ '+' Time * '+SVI_COL+' + year + month + weekday' + '  + op + SEX_CODE + RACE + ETHNICITY'#' + PAT_AGE_YEARS '
    if Dis_cat=='ALL': formula='Outcome'+' ~ '+' Time * '+SVI_COL+ '+ year + month + weekday + '+' + '.join(['SEX_CODE_M','op_True','RACE_white', 'RACE_black','ETHNICITY_Non_Hispanic'])#,'PAT_AGE_YEARS'])
    #formula=formula+' + Median_H_Income'
    
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
                              | reg_table['index'].str.contains('weekday')
                              #| reg_table['index'].str.contains('year')
                              #| reg_table['index'].str.contains('PAT_AGE_YEARS'))
                              
                              ),]
    reg_table['index']=reg_table['index'].str.replace("\[T.",'_').str.replace('\]','')
    reg_table_dev=pd.read_html(results.summary().tables[0].as_html())[0]
    
   
    
    # counts_outcome.loc["flood_bins",'Outcome']=str(flood_bins)
    #return reg_table
    #%%write the output
    reg_table.to_csv(Dis_cat+"_reg"+".csv")
    reg_table_dev.to_csv(Dis_cat+"_dev"+".csv")
    
