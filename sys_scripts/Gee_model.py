# -*- coding: utf-8 -*-
"""
Created on Thu Mar 18 22:47:04 2021

@author: balajiramesh
"""


import pandas as pd
import numpy as np
import statsmodels.api as sm
import statsmodels.formula.api as smf
import pyreadr
import os
os.chdir(r'Z:\Balaji\Analysis_SyS_data\28032021\stratified')
#%%function to reformat reg table
def reformat_reg_results(results,model=None,outcome=None,modifier_cat=None):
    results_as_html = results.summary().tables[1].as_html()
    reg_table=pd.read_html(results_as_html, header=0, index_col=0)[0].reset_index()
    reg_table.loc[:,'coef']=np.exp(reg_table.coef)
    reg_table.loc[:,['[0.025', '0.975]']]=np.exp(reg_table.loc[:,['[0.025', '0.975]']])
    reg_table=reg_table.loc[~(reg_table['index'].str.contains('weekday')),]
    reg_table['index']=reg_table['index'].str.replace("\[T.",'_').str.replace('\]','')
    reg_table_dev=pd.read_html(results.summary().tables[0].as_html())[0]
    reg_table['outcome']=outcome
    reg_table['model']=model
    reg_table['modifier_cat']=modifier_cat
    
    return reg_table,reg_table_dev
#%% read df
sys_sa= pyreadr.read_r(r"Z:\Balaji\R session_home_dir\sys_sa_df.RData")['sys_sa']
#change insect bite colname
sys_sa=sys_sa.rename(columns = {'Bite.Insect':'Bite_Insect'})
#change comparision group for each categories
sys_sa.Sex=sys_sa.Sex.cat.reorder_categories(['M','F','Unknown'])
sys_sa.Race=sys_sa.Race.cat.reorder_categories(['White','Black','Asian','Others','Unknown'])
sys_sa.Ethnicity=sys_sa.Ethnicity.cat.reorder_categories(['NON HISPANIC','HISPANIC', 'Unknown'])

#remove unknow sex categories:  ( removes 681 records )
sys_sa=sys_sa[sys_sa.Sex!='Unknown']
sys_sa.loc[:,'Sex']=sys_sa.Sex.cat.remove_unused_categories()

outcomes= ['Diarrhea','RespiratorySyndrome','outcomes_any','Asthma', 
           'Bite_Insect', 'Dehydration', 'Chest_pain','Heat_Related_But_Not_dehydration',
           'Hypothermia','Pregnancy_complic']

outcome='Heat_Related_But_Not_dehydration'
#make folder if not exists
#if not os.path.exists(outcome):os.makedirs(outcome)
#os.chdir(outcome)
#%%base model
# df=sys_sa.copy()

# #wite cross table
# outcomes_recs=df.loc[(df[outcome]),]
# counts_outcome=pd.crosstab(outcomes_recs.flooded,outcomes_recs.period, dropna=False)
# counts_outcome.to_csv(outcome+"_base_aux"+".csv")
# del outcomes_recs

# #run model
# #run geeglm and write the results
# formula=outcome+'.astype(float) ~ '+'flooded * period + Ethnicity + Race + Sex + weekday + Age'  
# model = smf.gee(formula=formula,groups=df.crossed_zcta, data=df,offset=np.log(df.ZCTAdaily_count),missing='drop',family=sm.families.Poisson(link=sm.families.links.log()))
# results=model.fit()

# # creating result dataframe tables
# reg_table,reg_table_dev= reformat_reg_results(results,model='base',outcome=outcome,modifier_cat=None)

# #write the results
# reg_table.to_csv(outcome+"_base_reg"+".csv")
# reg_table_dev.to_csv(outcome+"_base_dev"+".csv")
# print(outcome)

#%% reduce flood category 
sys_sa['flood_binary']=pd.Categorical(~(sys_sa.flooded=='Non flooded'))
sys_sa=sys_sa[sys_sa['period']!='novAndDec']
sys_sa.loc[:,'period']=sys_sa.period.cat.remove_unused_categories()
#%%Sex as modifer
df=sys_sa.copy()

#wite cross table
outcomes_recs=df.loc[(df[outcome]),]
counts_outcome=pd.crosstab(outcomes_recs.flood_binary,[outcomes_recs.period,outcomes_recs.Sex], dropna=False)
#counts_outcome.to_csv(outcome+"_sex_aux"+".csv")
counts_outcome.T
del outcomes_recs

for c in ['M', 'F']:
    df=sys_sa.copy()
    df=df[df.Sex.isin([c])]
    df.loc[:,'Sex']=df.Sex.cat.remove_unused_categories()
    #run model
    #run geeglm and write the results
    formula=outcome+'.astype(float) ~ '+'flood_binary * period + Ethnicity + Race + weekday + Age'  
    model = smf.gee(formula=formula,groups=df.crossed_zcta, data=df,offset=np.log(df.ZCTAdaily_count),missing='drop',family=sm.families.Poisson(link=sm.families.links.log()))
    results=model.fit()

    # creating result dataframe tables
    reg_table,reg_table_dev= reformat_reg_results(results,model='sex_strata',outcome=outcome,modifier_cat=c)
    
    #write the results
    reg_table.to_csv(outcome+"_"+c+"_sex_reg"+".csv")
    reg_table_dev.to_csv(outcome+"_"+c+"_sex_dev"+".csv")
    print(c)
#%% Ethnicity as modifier
df=sys_sa.copy()
df.Ethnicity.cat.categories

#wite cross table
outcomes_recs=df.loc[(df[outcome]),]
counts_outcome=pd.crosstab(outcomes_recs.flood_binary,[outcomes_recs.period,outcomes_recs.Ethnicity], dropna=False)
#counts_outcome.to_csv(outcome+"_Ethnictiy_aux"+".csv")
counts_outcome.T
del outcomes_recs

#['NON HISPANIC', 'Unknown']
for c in ['NON HISPANIC','HISPANIC']:
    df=sys_sa.copy()
    df=df[df.Ethnicity.isin([c])]
    df.loc[:,'Ethnicity']=df.Ethnicity.cat.remove_unused_categories()
    #run model
    #run geeglm and write the results
    formula=outcome+'.astype(float) ~ '+'flood_binary * period + Sex + Race + weekday + Age'  
    model = smf.gee(formula=formula,groups=df.crossed_zcta, data=df,offset=np.log(df.ZCTAdaily_count),missing='drop',family=sm.families.Poisson(link=sm.families.links.log()))
    results=model.fit()
    
    # creating result dataframe tables
    reg_table,reg_table_dev= reformat_reg_results(results,model='ethnicity_strata',modifier_cat=c,outcome=outcome)
    
    #write the results
    reg_table.to_csv(outcome+"_"+c+"_Ethnictiy_reg"+".csv")
    reg_table_dev.to_csv(outcome+"_"+c+"_Ethnictiy_dev"+".csv")
    print(c)

#%%Race as modifier

df=sys_sa.copy()
df.Race.cat.categories

#wite cross table
outcomes_recs=df.loc[(df[outcome]),]
counts_outcome=pd.crosstab(outcomes_recs.flood_binary,[outcomes_recs.period,outcomes_recs.Race], dropna=False)
#counts_outcome.to_csv(outcome+"_Race_aux"+".csv")
counts_outcome.T
del outcomes_recs

#['White', 'Black', 'Asian', 'Others', 'Unknown']
for c in ['White','Black']:
    df=sys_sa.copy()
    df=df[df.Race.isin([c])]
    df.loc[:,'Race']=df.Race.cat.remove_unused_categories()
    #run model
    #run geeglm and write the results
    formula=outcome+'.astype(float) ~ '+'flood_binary * period + Ethnicity + Sex  + weekday + Age'  
    model = smf.gee(formula=formula,groups=df.crossed_zcta, data=df,offset=np.log(df.ZCTAdaily_count),missing='drop',family=sm.families.Poisson(link=sm.families.links.log()))
    results=model.fit()
    
    # creating result dataframe tables
    reg_table,reg_table_dev= reformat_reg_results(results,model='Race_strata',modifier_cat=c,outcome=outcome)
    
    #write the results
    reg_table.to_csv(outcome+"_"+c+"_Race_reg"+".csv")
    reg_table_dev.to_csv(outcome+"_"+c+"_Race_dev"+".csv")
    print(c)
    
#%% Age as modifier
#sys_sa['AgeGrp']=pd.cut(sys_sa.Age,[0,5,17,50,64,200],labels=['0_5','6_17','18_50','51_64','gt64']).cat.reorder_categories(['18_50','0_5','6_17','51_64','gt64'])
sys_sa['AgeGrp']=pd.cut(sys_sa.Age,[0,21,200],labels=['0_21','gt21'])#.cat.reorder_categories(['18_50','0_5','6_17','51_64','gt64'])

df=sys_sa.copy()
df.AgeGrp.cat.categories

#wite cross table
outcomes_recs=df.loc[(df[outcome]),]
counts_outcome=pd.crosstab(outcomes_recs.flood_binary,[outcomes_recs.period,outcomes_recs.AgeGrp], dropna=False)
#counts_outcome.to_csv(outcome+"_Age_aux"+".csv")
counts_outcome.T
del outcomes_recs

#['White', 'Black', 'Asian', 'Others', 'Unknown']
for c in sys_sa.AgeGrp.cat.categories:
    df=sys_sa.copy()
    df=df[df.AgeGrp.isin([c])]
    df.loc[:,'AgeGrp']=df.AgeGrp.cat.remove_unused_categories()
    #run model
    #run geeglm and write the results
    formula=outcome+'.astype(float) ~ '+'flood_binary * period + Race + Ethnicity + Sex  + weekday'  
    model = smf.gee(formula=formula,groups=df.crossed_zcta, data=df,offset=np.log(df.ZCTAdaily_count),missing='drop',family=sm.families.Poisson(link=sm.families.links.log()))
    results=model.fit()
    
    # creating result dataframe tables
    reg_table,reg_table_dev= reformat_reg_results(results,model='Age_strata',modifier_cat=c,outcome=outcome)
    
    #write the results
    reg_table.to_csv(outcome+"_"+c+"_Age_reg"+".csv")
    reg_table_dev.to_csv(outcome+"_"+c+"_Age_dev"+".csv")
    print(c)


#%% combine the results into a single file
import glob2, os
req_files=glob2.glob("./**/*_reg.csv")
merge_df=pd.DataFrame()

for file in req_files:
    df=pd.read_csv(file)[['index','coef','P>|z|','[0.025','0.975]','outcome', 'model', 'modifier_cat']]
    df=df.round(3)
    merge_df=pd.concat([merge_df,df],axis=0)
    
merge_df.columns=['covar', 'RR', 'P', 'conf25', 'conf95','outcome', 'model', 'modifier_cat']
merge_df.to_excel('merged_All.xlsx',index=False)  
#%% combine aux files into single file
import glob2, os
import pandas as pd
req_files=glob2.glob("*_aux.csv")

merge_df=pd.DataFrame()

for file in req_files:
    df=pd.read_csv(file)
    df=df.iloc[2:,]
    Dis_cat=os.path.basename(file).replace("_aux.csv","")
    df['outcome']=Dis_cat
    merge_df=pd.concat([merge_df,df],axis=0)
merge_df.loc[-1] = pd.read_csv(file).iloc[0,:] # adding a row
merge_df.index = merge_df.index + 1  # shifting index
merge_df.sort_index(inplace=True) 
merge_df.to_excel('merged_eth_aux.xlsx',index=False) 