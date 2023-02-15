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
import geopandas
import statsmodels.api as sm
import statsmodels.formula.api as smf
from datetime import timedelta, date,datetime
from dateutil import parser
import glob
import sys
import gc
sys.path.insert(1, r'H:\Balaji\GRAScripts\dhs_scripts')
from recalculate_svi import recalculateSVI

#%%functions
def filter_mortality(df):
    pat_sta=df.PAT_STATUS.copy()
    pat_sta=pd.to_numeric(pat_sta,errors="coerce")
    return pat_sta.isin([20,40,41,42]).astype('int') #status code for died

def get_sp_outcomes(sp,Dis_cat):
    global sp_outcomes
    return sp.merge(sp_outcomes.loc[:,['RECORD_ID','op',Dis_cat]],on=['RECORD_ID','op'],how='left')[Dis_cat].values


#%%read from pickle - shortcut ===================================================================================
#=================================================================================================================
INPUT_IPOP_DIR=r'H:\Balaji\DSHS ED visit data(PII)\CleanedMergedJoined'
sp=pd.read_pickle(r'Z:\Balaji\R session_home_dir (PII)\sp_pyton_EdVisit.pkl')
#read the categories file
outcome_cats=pd.read_csv('H:/Balaji/GRAScripts/dhs_scripts/categories.csv')
outcome_cats.fillna('',inplace=True)
#read op/ip outcomes df
sp_outcomes=pd.read_csv(INPUT_IPOP_DIR+'\\ip_op_outcomes.csv')

flood_join_field='PAT_ADDR_CENSUS_TRACT'
Dis_cat='Pregnancy_complic'
#%%merege Dr Samarth's dtataset
evacDf_raw=pd.read_csv('Z:/Balaji/EvacuationDataDrSamarth/overall_sim_feature_values.csv')
evacDf=evacDf_raw.rename(columns={'flooding_close_proximity_duration_hr':'floodCloseProxDur',
       'tri_close_proximity_duration_hr':'triCloseProxDur', 'tri_distance_mi':'triDistMiles',
       'heavy_rainfall_duration_hr':'hvyRainDur', 'rainfall_total_mm':'totRainfall'
       })
#make quantile bins for each variable
# evacDfCat=evacDf.loc[:,evacDf.columns != 'FIPS'] \
#     .apply(axis=0,func=lambda x: \
#            pd.cut(x,np.round(np.insert(np.quantile(x,[.25,.5,.75,1]),0,-1),3),labels=np.round(np.quantile(x,[.25,.5,.75,1]),3)))
#convert everything to categorical
#evacDf=pd.concat([evacDf.loc[:,'FIPS'],evacDfCat],axis=1)

#subset df for census tracts in evac df
sp=sp.loc[sp.PAT_ADDR_CENSUS_TRACT.isin(evacDf.FIPS),:]
#merge evacDF
sp=sp.merge(evacDf,how='left',left_on='PAT_ADDR_CENSUS_TRACT',right_on='FIPS')

#subset sp_outcomes to save memory
sp_outcomes=sp_outcomes.loc[sp_outcomes.RECORD_ID.isin(sp.RECORD_ID),:]

#redifine floodcat
#%%merge flood ratio ctegories
tractsfloodr=sp.loc[~sp.duplicated(flood_join_field),[flood_join_field,'floodr']]
s=tractsfloodr.loc[tractsfloodr.floodr>0,'floodr']
flood_bins=[0,0.00000001,s.quantile(0.5),1]
sp['floodr_cat']=pd.cut(sp.floodr,bins=flood_bins,right=True,include_lowest=True,labels=['NO','FloodCat1','FloodCat2'])
#%%function for looping
exposure='evacuation_pct'
def run():   
    #%%filter records for specific outcome
    df=sp#.sample(500000)#[sp.SVI_Cat=='SVI_filter']  #--------------Edit here for stratified model
    if Dis_cat=="DEATH":df.loc[:,'Outcome']=filter_mortality(sp)
    if Dis_cat=="ALL":df.loc[:,'Outcome']=1
    if Dis_cat in outcome_cats.category.to_list():df.loc[:,'Outcome']=get_sp_outcomes(df, Dis_cat)
    
    #%%for filtering flooded or non flooded alone
    #df=df[df.floodr_cat=="FLood_1"].copy()
    #df=df[df.SEX_CODE==FIL_COL].copy()
    #df=df[df.AGE_cat==FIL_COL].copy()
    #df=df[df[SVI_COL]==FIL_COL].copy()
    #df=df[df.RACE==FIL_COL].copy()
    
    #%%stratified model for each period
    #df=df.loc[df.Time.isin(['control', 'flood']),]
    #df.Time.cat.remove_unused_categories(inplace=True)
    
    #%% save cross tab
     #counts_outcome=pd.DataFrame(df.Outcome.value_counts())
    # outcomes_recs=df.loc[(df.Outcome>0)&(~pd.isna(df.loc[:,[exposure,'Time','year','month','weekday' ,'PAT_AGE_YEARS', 
    #                                                       'SEX_CODE','RACE','ETHNICITY','SVI_Cat']]).any(axis=1)),]
    # counts_outcome=pd.crosstab(outcomes_recs[exposure],outcomes_recs.Time)
    # counts_outcome.to_csv(Dis_cat+"_"+exposure+"_aux"+".csv")
    # print(counts_outcome)
    # del outcomes_recs
    
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
                                                                                      'AGE_cat_lte1':'sum', 'AGE_cat_2-5':'sum', 'AGE_cat_6-12':'sum', 'AGE_cat_13-17':'sum','AGE_cat_18-45':'sum', 'AGE_cat_46-64':'sum', 'AGE_cat_gt64':'sum'
                                                                                      }).reset_index()
                         
        grouped_tracts=grouped_tracts.merge(df.drop_duplicates(['STMT_PERIOD_FROM','PAT_ADDR_CENSUS_TRACT']).loc[:,['STMT_PERIOD_FROM','PAT_ADDR_CENSUS_TRACT','floodr_cat','Population','Time','year','month','weekday','SVI_Cat','RPL_THEMES_1','RPL_THEMES_2','RPL_THEMES_3','RPL_THEMES_4','floodr', 'triCloseProxDur','evacuation_pct', 'hvyRainDur']],how='left',on=["PAT_ADDR_CENSUS_TRACT",'STMT_PERIOD_FROM'])
        dummy_cols=['SEX_CODE_M', 'SEX_CODE_F', 'RACE_white', 'RACE_black', 'RACE_other','ETHNICITY_Non_Hispanic', 'ETHNICITY_Hispanic', 'op_False', 'op_True','AGE_cat_lte1', 'AGE_cat_2-5', 'AGE_cat_6-12', 'AGE_cat_13-17','AGE_cat_18-45', 'AGE_cat_46-64', 'AGE_cat_gt64']
        grouped_tracts.loc[:,dummy_cols]=grouped_tracts.loc[:,dummy_cols].divide(grouped_tracts.Outcome,axis=0)
        del df
        df=grouped_tracts
    
    
    #%%running the model
    if Dis_cat!="ALL":offset=np.log(df.TotalVisits)
    #offset=None
    if Dis_cat=="ALL":offset=np.log(df.Population)
    
    #change floodr into 0-100
    df.floodr=df.floodr*100
    formula='Outcome'+' ~ floodr_cat * '+exposure+' * Time '+' + year + month + weekday '+'+ op  + RACE + SEX_CODE + PAT_AGE_YEARS + ETHNICITY + triCloseProxDur + hvyRainDur'
    if Dis_cat=='ALL': formula='Outcome'+' ~ floodr_cat * '+exposure + ' * Time'+' + year + month + weekday + '+' + '.join(['SEX_CODE_M','op_True','PAT_AGE_YEARS','RACE_white', 'RACE_black','ETHNICITY_Non_Hispanic','triCloseProxDur', 'hvyRainDur'])
    #if Dis_cat=='ALL': formula='Outcome'+' ~ '+' floodr_cat * Time'+' + year + month + weekday + '+' + '.join(['SEX_CODE_M','op_True','RACE_white', 'RACE_black','ETHNICITY_Non_Hispanic','PAT_AGE_YEARS'])
    #formula=formula+' + Median_H_Income'
    formula=formula.replace('SEX_CODE_M +','').replace('SEX_CODE +','') if Dis_cat=='Pregnancy_complic' else formula
    model = smf.gee(formula=formula,groups=df[flood_join_field],offset=offset, data=df,missing='drop',family=sm.families.Poisson(link=sm.families.links.log()))
    #model = smf.logit(formula=formula, data=df,missing='drop')
    #model = smf.glm(formula=formula, data=df,missing='drop',offset=offset,family=sm.families.Binomial(sm.families.links.logit()))
    
    results=model.fit()
    # print(results.summary())
    print(np.exp(results.params))
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
    reg_table['model']=exposure
    
    reg_table_dev=pd.read_html(results.summary().tables[0].as_html())[0]
    del model,results
    gc.collect()
    # counts_outcome.loc["flood_bins",'Outcome']=str(flood_bins)
    #return reg_table
    #%%write the output
    reg_table.to_csv(Dis_cat+"_"+exposure+"_reg"+".csv")
    #reg_table_dev.to_csv(Dis_cat+"_dev"+".csv")
    
Dis_cats=[ 'ALL',
           #'Psychiatric',
            'Intestinal_infectious_diseases',
              'ARI',
             'Bite-Insect',
            #'DEATH',
           # #'Flood_Storms',
             #'CO_Exposure',
             #'Drowning',
            #'Heat_Related_But_Not_dehydration',
            # 'Hypothermia',
           # #'Dialysis',
           # #'Medication_Refill',
            # 'Asthma',
              'Pregnancy_complic',
              'Chest_pain',
             'Dehydration',
         ]

for exposure in ['evacuation_pct']:
    print(exposure)
    for Dis_cat in Dis_cats:
                try:
                    print(Dis_cat)
                    print("-"*50)
                    run()
                except Exception as e: print(e)
    
#%%combined merge
import glob, os
req_files=glob.glob("*_reg.csv")

merge_df=pd.DataFrame()

for file in req_files:
    df=pd.read_csv(file)[['index','coef','P>|z|','[0.025','0.975]','model']]
    df=df.round(5)
    Dis_cat=os.path.basename(file).replace("_reg.csv","")
    Dis_cat=Dis_cat.split('_')[0]
    df['outcome']=Dis_cat
    merge_df=pd.concat([merge_df,df],axis=0)
    
merge_df.columns=['covar', 'RR', 'P', 'conf25', 'conf95','model', 'outcome']
merge_df['covar']=merge_df['covar'].str.replace("\[T.",'_').str.replace('\]','')
#merge_df['folder']='SVI_Cat_T4'

#% outupt
merge_df.to_excel('merged_flood_cat8.xlsx',index=False)  