# -*- coding: utf-8 -*-
"""
Created on Fri May 15 01:55:22 2020

@author: balajiramesh
"""


# -*- coding: utf-8 -*-
"""
Created on Fri Apr 10 00:25:12 2020

@author: balajiramesh


Raw : 16,319230 2,641562
Within study timeline: 14393806 2247749
Within study area and timeline: 7892752 1246896
AFter removing washout period: 7816138 1233913
After removeing missing data: 7,813,866 and 1,233,600 OP and IP ED visit records
"""
import pandas as pd
import numpy as np

import statsmodels.api as sm
import statsmodels.formula.api as smf
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

#%%read ip op data  ---- constant ----
INPUT_IPOP_DIR=r'Z:\DSHS ED visit data(PII)\CleanedMergedJoined'
#read_op
op=pd.read_pickle(INPUT_IPOP_DIR+'\\op')
op=op.loc[:,['RECORD_ID','STMT_PERIOD_FROM','PAT_ADDR_CENSUS_BLOCK_GROUP','PAT_AGE_YEARS','SEX_CODE','RACE','PAT_STATUS','ETHNICITY','PAT_ZIP','LCODE']]
op['op']=True
#sp=pd.read_pickle(INPUT_IPOP_DIR+r'\op')
#read_ip
ip=pd.read_pickle(INPUT_IPOP_DIR+'\\ip')
ip=ip.loc[:,['RECORD_ID','STMT_PERIOD_FROM','PAT_ADDR_CENSUS_BLOCK_GROUP','PAT_AGE_YEARS','SEX_CODE','RACE','PAT_STATUS','ETHNICITY','PAT_ZIP','LCODE']]
ip['op']=False
#merge Ip and OP
op=pd.concat([op,ip])
sp=op
del op,ip

#read op/ip outcomes df
sp_outcomes=pd.read_csv(INPUT_IPOP_DIR+'\\ip_op_outcomes.csv')

#read svi data
SVI_df_raw=pd.read_csv(r'Z:/SVI_Raw/TEXAS.csv')
SVI_df_raw.FIPS=pd.to_numeric(SVI_df_raw.FIPS)

#read population data
demos_ct=pd.read_csv(r'Z:/Census_data_texas/population/ACS_17_5YR_DP05_with_ann.csv',low_memory=False,skiprows=1).iloc[:,[1,3]]
demos_ct.Id2=demos_ct.Id2.astype("Int64")
demos_ct.columns=["PAT_ADDR_CENSUS_TRACT","Population"]

demos_bg= pd.read_csv(r'Z:\Census_data_texas\population\block_grp_level\ACSDT5Y2017.B01003-Data.csv',low_memory=False,skiprows=1).iloc[:,[0,2]]
demos_bg.Geography=pd.to_numeric(demos_bg.Geography.str.replace("1500000US","")).astype("Int64")
demos_bg.columns=["PAT_ADDR_CENSUS_BLOCK_GROUP","Population"]

#read flood ratio data
flood_data_ct= pd.read_csv('Z:\indundation_harvey\censusTracts_AER_DFO_flood\censusTracts_AER_DFO_flood.csv')
flood_data_bg= pd.read_csv('Z:\indundation_harvey\censusBlkGrp_AER_DFO_flood\censusBlkGrp_AER_DFO_flood.csv')

#update flood data to fill aer measure with DFO in the extent where there is no aer data available
idx = flood_data_ct.within_dfo==1 & flood_data_ct.within_aer.isna()
flood_data_ct.loc[idx,'AERfRatio'] = flood_data_ct.loc[idx,'DFOfRatio']
flood_data_ct.loc[idx,'AERfldResRatio'] = flood_data_ct.loc[idx,'DFOfldResRatio']

idx = flood_data_bg.within_dfo==1 & flood_data_bg.within_aer.isna()
flood_data_bg.loc[idx,'AERfRatio'] = flood_data_bg.loc[idx,'DFOfRatio']
flood_data_bg.loc[idx,'AERfldResRatio'] = flood_data_bg.loc[idx,'DFOfldResRatio']


#read the categories file
outcome_cats=pd.read_csv('Z:/GRAScripts/dhs_scripts/categories.csv')
outcome_cats.fillna('',inplace=True)


county_to_filter=county_to_filter=pd.read_csv('Z:\DSHS ED visit data(PII)\contiesInStudyArea.csv').County_FIPS.to_list()
#%%cleaing for age, gender and race and create census tract ---- constant ----
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
#age
sp=sp[sp.PAT_AGE_YEARS<119]
#create tract id from block group id
sp.loc[:,'PAT_ADDR_CENSUS_TRACT']=(sp.PAT_ADDR_CENSUS_BLOCK_GROUP//10)
    

#%%keep only the dates we requested for ---- constant ----

washout_period=[20170819,20170825] #including the dates specified
#remove records before 2016
sp=sp.loc[(~pd.isna(sp.STMT_PERIOD_FROM))&(~pd.isna(sp.PAT_ADDR_CENSUS_BLOCK_GROUP))] 

sp=sp[((sp.STMT_PERIOD_FROM > 20160700) & (sp.STMT_PERIOD_FROM< 20161232))\
    | ((sp.STMT_PERIOD_FROM > 20170400) & (sp.STMT_PERIOD_FROM< 20171232))\
        | ((sp.STMT_PERIOD_FROM > 20180700) & (sp.STMT_PERIOD_FROM< 20181232))]

#remove data in washout period
sp= sp[~((sp.STMT_PERIOD_FROM >= washout_period[0]) & (sp.STMT_PERIOD_FROM <= washout_period[1]))]

#%% merge SVI after recategorization ---- constant ----
svi=recalculateSVI(SVI_df_raw[SVI_df_raw.FIPS.isin(sp.PAT_ADDR_CENSUS_TRACT.unique())]).loc[:,["FIPS",'SVI','RPL_THEMES_1',"RPL_THEMES_2","RPL_THEMES_3","RPL_THEMES_4"]]
sp=sp.merge(svi,left_on="PAT_ADDR_CENSUS_TRACT",right_on="FIPS",how='left').drop("FIPS",axis=1)
sp['SVI_Cat']=pd.cut(sp.SVI,bins=np.arange(0,1.1,1/4),include_lowest=True,labels=[1,2,3,4])

#do same for the for cats
for i in ['1','2','3','4']:
    sp['SVI_Cat_T'+i]=pd.cut(sp['RPL_THEMES_'+i],bins=np.arange(0,1.1,1/4),include_lowest=True,labels=[1,2,3,4])

#%%controling for year month and week of the day ---- constant ----
sp['year']=(sp.STMT_PERIOD_FROM.astype('int32')//1e4).astype('category')
sp['month']=(sp.STMT_PERIOD_FROM.astype('int32')//1e2%100).astype('category')
sp['weekday']=pd.to_datetime(sp.STMT_PERIOD_FROM.astype('str'),format='%Y%m%d').dt.dayofweek.astype('category')

#%%filter sp to greater boundary of counties which whill all cts and bgs will lie for dfo or are extent
sp=sp[(sp.PAT_ADDR_CENSUS_TRACT//1000000).isin(county_to_filter)]
                 
#%%calculating total visits for offset ---- constant ----
vists_per_ct=sp.groupby(['PAT_ADDR_CENSUS_TRACT','STMT_PERIOD_FROM'])\
                  .size().reset_index().rename(columns={0:'TotalVisits'})
                  
vists_per_bg = sp.groupby(['PAT_ADDR_CENSUS_BLOCK_GROUP','STMT_PERIOD_FROM'])\
                  .size().reset_index().rename(columns={0:'TotalVisits'})
                  

#%% backup the orig df after subsetting counties  --- WARRRRRNNNNINNNGGGG ----- constant ----------
sp_bkp = sp.copy()

#%%predefine variable 

#expsoure level ct or bg (ct-census tract; bg- blockgroup)
EXPOSURE_LEVEL = 'bg' 
#exposure product dfo or aer
EXPOSURE_PRODUCT = 'dfo'
#type of flooding fRatio or fldResRatio (fRatio - overall flood ratio; fldResRatio - residential flooding ratio) 
FLOOD_TYPE = 'fldResRatio'
#extent of cenus tracts defined using which flood product extent : dfo or aer
EXTENT_ANALYSIS = 'dfo'

tracts_to_filter= flood_data_ct.GEOID[~pd.isna(flood_data_ct['within_'+EXTENT_ANALYSIS])]
tract_bg_to_filter= flood_data_bg.GEOID[~pd.isna(flood_data_bg['within_'+EXTENT_ANALYSIS])]

floodr_use= EXPOSURE_PRODUCT.upper() + FLOOD_TYPE

nullAsZero="True" #null flood ratios are changed to 0
floodZeroSep="True" # zeros are considered as seperate class
flood_data_zip=None

interv_dates=[20170825, 20170913, 20171014,20180701,20181001] #lower bound excluded - for additional post flood in 2018
#interv_dates=[20170825, 20170913, 20171014] #lower bound excluded

#interv_dates_cats=['flood','PostFlood1','PostFlood2'] 
interv_dates_cats=['flood','PostFlood1','PostFlood2','JulToSep2018','OctToDec2018']# - for additional post flood in 2018

Dis_cat="ALL"



#%%pat age categoriy based on SVI theme  2  <=17,18-64,>=65
#sp['AGE_cat']=pd.cut(sp.PAT_AGE_YEARS,bins=[-1,5,12,17,45,64,200],labels=['lte5','6-12','13-17','18-45','46-64','gt64']).cat.reorder_categories(['lte5','6-12','13-17','18-45','46-64','gt64'])
sp = sp_bkp
#%%filter records for counties in study area or from zip codes
if EXPOSURE_LEVEL == 'ct' :
    sp=sp[sp.PAT_ADDR_CENSUS_TRACT.isin(tracts_to_filter)]
elif EXPOSURE_LEVEL == 'bg':
    sp=sp[sp.PAT_ADDR_CENSUS_BLOCK_GROUP.isin(tract_bg_to_filter)]
    
#%% merge population and total visits for offset

sp=sp.drop(columns='Population')  if 'Population' in sp.columns else sp  #drop before merging
if EXPOSURE_LEVEL=='ct':
    sp=sp.merge(demos_ct,on='PAT_ADDR_CENSUS_TRACT',how='left')
elif EXPOSURE_LEVEL=='bg':
    sp=sp.merge(demos_bg,on='PAT_ADDR_CENSUS_BLOCK_GROUP',how='left')
    

sp=sp.loc[sp.Population>0,]


#merges total visits per tract or per bg 
sp=sp.drop(columns='TotalVisits')  if 'TotalVisits' in sp.columns else sp  #drop before merging
if EXPOSURE_LEVEL=='ct':
    sp=sp.merge(vists_per_ct,on=['PAT_ADDR_CENSUS_TRACT','STMT_PERIOD_FROM'],how='left')
elif EXPOSURE_LEVEL=='bg':
    sp=sp.merge(vists_per_bg,on=['PAT_ADDR_CENSUS_BLOCK_GROUP','STMT_PERIOD_FROM'],how='left')

#%% bringing in intervention
sp.loc[:,'Time']=pd.cut(sp.STMT_PERIOD_FROM,\
                                    bins=[0]+interv_dates+[20190101],\
                                    labels=['control']+[str(i) for i in interv_dates_cats]).cat.as_unordered()
#set after 2018 as control
#sp.loc[sp.STMT_PERIOD_FROM>20180100,'Time']="control" #if Dis_cat!="Psychiatric" else np.nan
sp=sp.loc[~pd.isna(sp.Time),]

#take only control period
#sp=sp[sp.Time=='control']
#%%merge flood ratio

if EXPOSURE_LEVEL == 'ct' :
    flood_join_field='PAT_ADDR_CENSUS_TRACT'
    floodr=flood_data_ct.copy()
elif EXPOSURE_LEVEL == 'bg':
    flood_join_field='PAT_ADDR_CENSUS_BLOCK_GROUP'
    floodr=flood_data_bg.copy()

# if flood_data_zip is not None: 
#     flood_data=flood_data_zip
#     flood_join_field='PAT_ZIP'

FLOOD_QUANTILES=["NO","Flood_1"]

floodr.GEOID=pd.to_numeric(floodr.GEOID).astype("Int64")
floodr=floodr.loc[:,['GEOID']+[floodr_use]]
floodr.columns=['GEOID','floodr']

sp=sp.drop(columns='floodr')  if 'floodr' in sp.columns else sp  #drop before merging
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
    
print("flood bins:" , flood_bins)
#%%
Dis_cat="Dehydration"
#sp['AGE_cat']=pd.cut(sp.PAT_AGE_YEARS,bins=[-1,1,5,12,17,45,64,200],labels=['lte1','2-5','6-12','13-17','18-45','46-64','gt64']).cat.reorder_categories(['lte1','2-5','6-12','13-17','18-45','46-64','gt64'])
#%%function for looping
def run(Dis_cat):   
    #%%filter records for specific outcome
    print(Dis_cat)
    print('===========================')
    df=sp#[sp.SVI_Cat=='SVI_filter']  #--------------Edit here for stratified model
    if Dis_cat=="ALL":df.loc[:,'Outcome']=1
    df.loc[:,'Outcome']=get_sp_outcomes(sp, Dis_cat)
   
    #%% save cross tab
     #counts_outcome=pd.DataFrame(df.Outcome.value_counts())
    outcomes_recs=df.loc[(df.Outcome>0)&(~pd.isna(df.loc[:,['floodr_cat','Time','year','month','weekday' ,'PAT_AGE_YEARS', 
                                                          'SEX_CODE','RACE','ETHNICITY']]).any(axis=1)),]
    counts_outcome=pd.crosstab(outcomes_recs.Time,outcomes_recs.floodr_cat)
    #counts_outcome=pd.crosstab([outcomes_recs.Time,outcomes_recs.floodr_cat],outcomes_recs.SVI_Cat)
    print(counts_outcome)
    counts_outcome.to_csv(Dis_cat+"_aux"+".csv")
    del outcomes_recs
    
       
    #%%running the model
    if Dis_cat!="ALL":offset=np.log(df.TotalVisits)
    #offset=None
    if Dis_cat=="ALL":offset=np.log(df.Population)
    
    #offset=np.log(df.Population) #keeping offset as population for subsequent analysis
    
    #change floodr into 0-100
    df.floodr=df.floodr*100
    formula='Outcome'+' ~ '+' floodr_cat * Time'+' + year + month + weekday' + '  + RACE + SEX_CODE + PAT_AGE_YEARS + ETHNICITY  + op '
   
    model = smf.gee(formula=formula,groups=df[flood_join_field], data=df,offset=offset,missing='drop',family=sm.families.Poisson(link=sm.families.links.log()))
    
    results=model.fit()
    #print(results.summary())
    #print(np.exp(results.params))
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
    reg_table['model']='base'
    
    reg_table_dev=pd.read_html(results.summary().tables[0].as_html())[0]
    
   
    # counts_outcome.loc["flood_bins",'Outcome']=str(flood_bins)
    #return reg_table
    #%%write the output
    reg_table.to_csv(Dis_cat+"_reg"+".csv")
    reg_table_dev.to_csv(Dis_cat+"_dev"+".csv")
    
#%% looping 
#["Alcohol","Cannabis",'DrugOverdoseAbuse','Opi_Illicit','Opi_Synthetic','Opi_Natural_SemiSynth','Opi_Methadone', 'Opi_Other','Opi_Use_Abuse_Depend','Opi_psychosimul','Opi_Any']

Dis_cats = ['Intestinal_infectious_diseases', 'Pregnancy_complic', 'Bite-Insect','Opi_Illicit','Opi_Any_NonIllicit',"Alcohol","Cannabis",'Dehydration']
for x in Dis_cats:
    run(x)
    
    