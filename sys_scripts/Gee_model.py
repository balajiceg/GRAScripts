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
import datetime
import winsound
#os.chdir(r'Z:\Balaji\Analysis_SyS_data\28032021\stratified')
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
sys_sa.Sex=sys_sa.Sex.cat.reorder_categories(['M','F'])
sys_sa.Race=sys_sa.Race.cat.reorder_categories(['White','Black','Others','Unknown'])
sys_sa.Ethnicity=sys_sa.Ethnicity.cat.reorder_categories(['NON HISPANIC','HISPANIC', 'Unknown'])
sys_sa.flooded=sys_sa.flooded.cat.reorder_categories(["Non flooded", "Moderately flooded", "Highly flooded"])

#remove the records with ages > 119
sys_sa=sys_sa[sys_sa.Age<120]

# reduce flood category 
sys_sa['flood_binary']=pd.Categorical(~(sys_sa.flooded=='Non flooded'))
#remove pregnancy complication match for  male entries for age other than 0 (remvoe 186)
sys_sa.loc[((sys_sa.Pregnancy_complic==True) & (sys_sa.Age>0) & (sys_sa.Sex=='M')),'Pregnancy_complic']=False
#make sys_sa bkp
sys_sa_bkp=sys_sa.copy()

#%%
for outcome in ['Asthma','Bite_Insect','CardiovascularDiseases','Dehydration','Diarrhea','Heat_Related_But_Not_dehydration','Pregnancy_complic']:
    sys_sa=sys_sa_bkp.copy()
    print(outcome+'--------------')
    #if not os.path.exists(outcome):os.makedirs(outcome)
    #os.chdir(outcome)
    #prepare sys_sa for outcome
    if outcome=='Heat_Related_But_Not_dehydration':
        #remove second post flood period
        sys_sa=sys_sa[sys_sa['period']!='novAndDec']
        sys_sa.loc[:,'period']=sys_sa.period.cat.remove_unused_categories()
    
    #%%base model
    #for outcome in ['Diarrhea','RespiratorySyndrome','Asthma','Bite_Insect', 'Dehydration', 'Chest_pain','Pregnancy_complic','Heat_Related_But_Not_dehydration']:
    df=sys_sa.copy()
    #wite cross table
    outcomes_recs=df.loc[(df[outcome]),]
    counts_outcome=pd.crosstab(outcomes_recs.flooded,outcomes_recs.period, dropna=False)
    print(counts_outcome)
    del outcomes_recs
    
    #run model
    #run geeglm and write the results
    formula=outcome+'.astype(float) ~ '+'flooded * period + Ethnicity + Race + weekday + Age'
    formula= formula+' + Sex' if outcome!='Pregnancy_complic' else formula
    model = smf.gee(formula=formula,groups=df.crossed_zcta, data=df,offset=np.log(df.ZCTAdaily_count),missing='drop',family=sm.families.Poisson(link=sm.families.links.log()))
    results=model.fit()
    
    # creating result dataframe tables
    reg_table,reg_table_dev= reformat_reg_results(results,model='base',outcome=outcome,modifier_cat=None)
    
    #write the results
    reg_table.to_csv(outcome+"_base_reg"+".csv")
    reg_table_dev.to_csv(outcome+"_base_dev"+".csv")
    print(results.params)

    #%%base binary model
    df=sys_sa.copy()
    #wite cross table
    outcomes_recs=df.loc[(df[outcome]),]
    counts_outcome=pd.crosstab(outcomes_recs.flood_binary,outcomes_recs.period, dropna=False)
    print(counts_outcome)
    del outcomes_recs
    
    #run model
    #run geeglm and write the results
    formula=outcome+'.astype(float) ~ '+'flood_binary * period + Ethnicity + Race + weekday + Age'  
    formula= formula+' + Sex' if outcome!='Pregnancy_complic' else formula
    
    model = smf.gee(formula=formula,groups=df.crossed_zcta, data=df,offset=np.log(df.ZCTAdaily_count),missing='drop',family=sm.families.Poisson(link=sm.families.links.log()))
    results=model.fit()
    
    # creating result dataframe tables
    reg_table,reg_table_dev= reformat_reg_results(results,model='base_binary',outcome=outcome,modifier_cat=None)
    
    #write the results
    reg_table.to_csv(outcome+"_base_binary_reg"+".csv")
    reg_table_dev.to_csv(outcome+"_base_binary_dev"+".csv")
    print(results.params)
    
    #%%base binary sensitivity model
    df=sys_sa.copy()
    #remove records falling into june AER observed flood [June 7-8] and one month after that - for sensitivity analysis
    df=df[(df.Date<datetime.date(2019, 6, 7)) | (df.Date>datetime.date(2019, 7, 9))]
    
    #wite cross table
    outcomes_recs=df.loc[(df[outcome]),]
    counts_outcome=pd.crosstab(outcomes_recs.flood_binary,outcomes_recs.period, dropna=False)
    print(counts_outcome)
    del outcomes_recs
    
    #run model
    #run geeglm and write the results
    formula=outcome+'.astype(float) ~ '+'flood_binary * period + Ethnicity + Race + weekday + Age'  
    formula= formula+' + Sex' if outcome!='Pregnancy_complic' else formula
    
    model = smf.gee(formula=formula,groups=df.crossed_zcta, data=df,offset=np.log(df.ZCTAdaily_count),missing='drop',family=sm.families.Poisson(link=sm.families.links.log()))
    results=model.fit()
    
    # creating result dataframe tables
    reg_table,reg_table_dev= reformat_reg_results(results,model='binary_june_remove_sensitivity',outcome=outcome,modifier_cat=None)
    
    #write the results
    reg_table.to_csv(outcome+"_binary_jun_rmv_reg"+".csv")
    reg_table_dev.to_csv(outcome+"_binary_jun_rmv_dev"+".csv")
    print(results.params)
    
    #%% if ouctome is heat related illness dont' run stratified models
    if outcome=='Heat_Related_But_Not_dehydration': continue
    #%%Sex stratified - run if outcome is not pregnancy complication
    if outcome!='Pregnancy_complic':
        df=sys_sa.copy()
        
        #wite cross table
        outcomes_recs=df.loc[(df[outcome]),]
        counts_outcome=pd.crosstab(outcomes_recs.flood_binary,[outcomes_recs.period,outcomes_recs.Sex], dropna=False)
        print(counts_outcome.T)
        del outcomes_recs
        
        formula=outcome+'.astype(float) ~ '+'flood_binary * period + Ethnicity + Race + weekday + Age'  
        for c in ['M', 'F']:
            df=sys_sa.copy()
            df=df[df.Sex.isin([c])]
            df.loc[:,'Sex']=df.Sex.cat.remove_unused_categories()
            #run model
            #run geeglm and write the results
        
            model = smf.gee(formula=formula,groups=df.crossed_zcta, data=df,offset=np.log(df.ZCTAdaily_count),missing='drop',family=sm.families.Poisson(link=sm.families.links.log()))
            results=model.fit()
        
            # creating result dataframe tables
            reg_table,reg_table_dev= reformat_reg_results(results,model='sex_strata',outcome=outcome,modifier_cat=c)
            
            #write the results
            reg_table.to_csv(outcome+"_"+c+"_sex_reg"+".csv")
            reg_table_dev.to_csv(outcome+"_"+c+"_sex_dev"+".csv")
            print(c)
            print(results.params)
            
        #%%Sex modifier
        df=sys_sa.copy()
        
        formula=outcome+'.astype(float) ~ '+'flood_binary * period * Sex + Ethnicity + Race + weekday + Age' 
        for c in ['F']:
            df=sys_sa.copy()
            df=df[df.Sex.isin([c,'M'])]
            df.loc[:,'Sex']=df.Sex.cat.remove_unused_categories()
            #run model
            #run geeglm and write the results
            model = smf.gee(formula=formula,groups=df.crossed_zcta, data=df,offset=np.log(df.ZCTAdaily_count),missing='drop',family=sm.families.Poisson(link=sm.families.links.log()))
            results=model.fit()
        
            # creating result dataframe tables
            reg_table,reg_table_dev= reformat_reg_results(results,model='sex',outcome=outcome,modifier_cat=c)
            
            #write the results
            reg_table.to_csv(outcome+"_"+c+"_sex_inter_reg"+".csv")
            reg_table_dev.to_csv(outcome+"_"+c+"_sex_inter_dev"+".csv")
            print(results.params)
            print(c)
    #%% Ethnicity strata
    df=sys_sa.copy()
    df.Ethnicity.cat.categories
    
    #wite cross table
    outcomes_recs=df.loc[(df[outcome]),]
    counts_outcome=pd.crosstab(outcomes_recs.flood_binary,[outcomes_recs.period,outcomes_recs.Ethnicity], dropna=False)
    print(counts_outcome.T)
    del outcomes_recs
    
    formula=outcome+'.astype(float) ~ '+'flood_binary * period + Race + weekday + Age'
    formula= formula+' + Sex' if outcome!='Pregnancy_complic' else formula
    
    #['NON HISPANIC', 'Unknown']
    for c in ['NON HISPANIC','HISPANIC','Unknown']:
        df=sys_sa.copy()
        df=df[df.Ethnicity.isin([c])]
        df.loc[:,'Ethnicity']=df.Ethnicity.cat.remove_unused_categories()
        #run model
        #run geeglm and write the results
      
        model = smf.gee(formula=formula,groups=df.crossed_zcta, data=df,offset=np.log(df.ZCTAdaily_count),missing='drop',family=sm.families.Poisson(link=sm.families.links.log()))
        results=model.fit()
        
        # creating result dataframe tables
        reg_table,reg_table_dev= reformat_reg_results(results,model='ethnicity_strata',modifier_cat=c,outcome=outcome)
        
        #write the results
        reg_table.to_csv(outcome+"_"+c+"_Ethnictiy_reg"+".csv")
        reg_table_dev.to_csv(outcome+"_"+c+"_Ethnictiy_dev"+".csv")
        print(results.params)
        print(c)
    #%% Ethnicity as modifier
    df=sys_sa.copy()
    df.Ethnicity.cat.categories
    
    formula=outcome+'.astype(float) ~ '+'flood_binary * period * Ethnicity + Race + weekday + Age'  
    formula= formula+' + Sex' if outcome!='Pregnancy_complic' else formula
        
    #['NON HISPANIC', 'Unknown']
    for c in ['HISPANIC','Unknown']:
        df=sys_sa.copy()
        df=df[df.Ethnicity.isin([c,'NON HISPANIC'])]
        df.loc[:,'Ethnicity']=df.Ethnicity.cat.remove_unused_categories()
        #run model
        #run geeglm and write the results
        model = smf.gee(formula=formula,groups=df.crossed_zcta, data=df,offset=np.log(df.ZCTAdaily_count),missing='drop',family=sm.families.Poisson(link=sm.families.links.log()))
        results=model.fit()
        
        # creating result dataframe tables
        reg_table,reg_table_dev= reformat_reg_results(results,model='ethnicity',modifier_cat=c,outcome=outcome)
        
        #write the results
        reg_table.to_csv(outcome+"_"+c+"_Ethnictiy_inter_reg"+".csv")
        reg_table_dev.to_csv(outcome+"_"+c+"_Ethnictiy_inter_dev"+".csv")
        print(results.params)
        print(c)
    
    #%%Race strata
    #for outcome in ['Diarrhea','RespiratorySyndrome','Asthma','Bite_Insect', 'Dehydration', 'Chest_pain']:
            
    df=sys_sa.copy()
    df.Race.cat.categories
    
    #wite cross table
    outcomes_recs=df.loc[(df[outcome]),]
    counts_outcome=pd.crosstab(outcomes_recs.flood_binary,[outcomes_recs.period,outcomes_recs.Race], dropna=False)
    print(counts_outcome.T)
    del outcomes_recs
    
    formula=outcome+'.astype(float) ~ '+'flood_binary * period + Ethnicity + weekday + Age'  
    formula= formula+' + Sex' if outcome!='Pregnancy_complic' else formula
        
    #['White', 'Black', 'Asian', 'Others', 'Unknown','Others']
    for c in ['Others','Black','Unknown','White']:
        df=sys_sa.copy()
        df=df[df.Race.isin([c])]
        df.loc[:,'Race']=df.Race.cat.remove_unused_categories()
        #run model
        #run geeglm and write the results
        model = smf.gee(formula=formula,groups=df.crossed_zcta, data=df,offset=np.log(df.ZCTAdaily_count),missing='drop',family=sm.families.Poisson(link=sm.families.links.log()))
        results=model.fit()
        
        # creating result dataframe tables
        reg_table,reg_table_dev= reformat_reg_results(results,model='Race_strata',modifier_cat=c,outcome=outcome)
        
        #write the results
        reg_table.to_csv(outcome+"_"+c+"_Race_reg"+".csv")
        reg_table_dev.to_csv(outcome+"_"+c+"_Race_dev"+".csv")
        print(results.params)
        print(c)
    #%%Race modifer
    #for outcome in ['Diarrhea','RespiratorySyndrome','Asthma','Bite_Insect', 'Dehydration', 'Chest_pain']:
            
    df=sys_sa.copy()
    df.Race.cat.categories
    
    formula=outcome+'.astype(float) ~ '+'flood_binary * period * Race + Ethnicity + weekday + Age'  
    formula= formula+' + Sex' if outcome!='Pregnancy_complic' else formula
        
    #['White', 'Black', 'Asian', 'Others', 'Unknown','Others']
    for c in ['Others','Black','Unknown']:
        df=sys_sa.copy()
        df=df[df.Race.isin([c,'White'])]
        df.loc[:,'Race']=df.Race.cat.remove_unused_categories()
        #run model
        #run geeglm and write the results
        model = smf.gee(formula=formula,groups=df.crossed_zcta, data=df,offset=np.log(df.ZCTAdaily_count),missing='drop',family=sm.families.Poisson(link=sm.families.links.log()))
        results=model.fit()
        
        # creating result dataframe tables
        reg_table,reg_table_dev= reformat_reg_results(results,model='Race',modifier_cat=c,outcome=outcome)
        
        #write the results
        reg_table.to_csv(outcome+"_"+c+"_Race_inter_reg"+".csv")
        reg_table_dev.to_csv(outcome+"_"+c+"_Race_inter_dev"+".csv")
        print(results.params)
        print(c)
    
    #%% format age grp as per discat
    age_dict={
        'Asthma':{'age_bins':[-1,5,17,50,200],'labels':["0_5","6_17","18_50","gt50"],'order':["18_50","0_5","6_17","gt50"]},
        'Bite_Insect':{'age_bins':[-1,5,17,200],'labels':["0_5","6_17","gt17"],'order':["gt17","0_5","6_17"]},
        'CardiovascularDiseases':{'age_bins':[-1,17,50,64,200],'labels':['0_17','18_50','51_64','gt64'],'order':['18_50','0_17','51_64','gt64']},
        'Dehydration':{'age_bins':[-1,5,17,50,64,200],'labels':["0_5","6_17","18_50","51_64","gt64"],'order':["18_50","0_5","6_17","51_64","gt64"]},
        'Diarrhea':{'age_bins':[-1,5,17,64,200],'labels':["0_5","6_17","18_64","gt64"],'order':["18_64","0_5","6_17","gt64"]},
    #    'Heat_Related_But_Not_dehydration':{'age_bins':[-1,21,200],'labels':['0_21','gt21'],'order':['0_21']},
        'Pregnancy_complic':{'age_bins':[-1,0,19,27,35,200],'labels':['0','1_19','20_27','28_35','gt35'],'order':['20_27','0','1_19','28_35','gt35']},    
        }    
    age_bins,age_lab,age_order=age_dict[outcome].values()
    
    sys_sa['AgeGrp']=pd.cut(sys_sa.Age,age_bins,labels=age_lab).cat.reorder_categories(age_order)
    ############################
    #%% Age as strata
    df=sys_sa.copy()
    df.AgeGrp.cat.categories
    
    #wite cross table
    outcomes_recs=df.loc[(df[outcome]),]
    counts_outcome=pd.crosstab(outcomes_recs.flood_binary,[outcomes_recs.period,outcomes_recs.AgeGrp], dropna=False)
    print(counts_outcome.T)
    del outcomes_recs
    
    formula=outcome+'.astype(float) ~ '+'flood_binary * period + Race + Ethnicity  + weekday'  
    formula= formula+' + Sex' if outcome!='Pregnancy_complic' else formula
    
    for c in age_order:#sys_sa.AgeGrp.cat.categories:
        df=sys_sa.copy()
        df=df[df.AgeGrp.isin([c])]
        df.loc[:,'AgeGrp']=df.AgeGrp.cat.remove_unused_categories()
        #run model
        #run geeglm and write the results
        model = smf.gee(formula=formula,groups=df.crossed_zcta, data=df,offset=np.log(df.ZCTAdaily_count),missing='drop',family=sm.families.Poisson(link=sm.families.links.log()))
        results=model.fit()
        
        # creating result dataframe tables
        reg_table,reg_table_dev= reformat_reg_results(results,model='Age_strata',modifier_cat=c,outcome=outcome)
        
        #write the results
        reg_table.to_csv(outcome+"_"+c+"_Age_reg"+".csv")
        reg_table_dev.to_csv(outcome+"_"+c+"_Age_dev"+".csv")
        print(c)
        print(results.params)

    #%% Age as modifier
    df=sys_sa.copy()
    df.AgeGrp.cat.categories
    
    formula=outcome+'.astype(float) ~ '+'flood_binary * period * AgeGrp + Race + Ethnicity  + weekday'
    formula= formula+' + Sex' if outcome!='Pregnancy_complic' else formula
    
    for c in age_order[1:]:#sys_sa.AgeGrp.cat.categories:
        df=sys_sa.copy()
        df=df[df.AgeGrp.isin([c,age_order[0]])]
        df.loc[:,'AgeGrp']=df.AgeGrp.cat.remove_unused_categories()
        #run model
        #run geeglm and write the results
        
        model = smf.gee(formula=formula,groups=df.crossed_zcta, data=df,offset=np.log(df.ZCTAdaily_count),missing='drop',family=sm.families.Poisson(link=sm.families.links.log()))
        results=model.fit()
        
        # creating result dataframe tables
        reg_table,reg_table_dev= reformat_reg_results(results,model='Age',modifier_cat=c,outcome=outcome)
        
        #write the results
        reg_table.to_csv(outcome+"_"+c+"_Age_inter_reg"+".csv")
        reg_table_dev.to_csv(outcome+"_"+c+"_Age_inter_dev"+".csv")
        print(c)
        print(results.params)


    winsound.Beep(1000,1000)
#####################
################
##############
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
#%% insert period column
#read excel file 
df=pd.read_excel('merged_All.xlsx',index=False)
df['period']=""

cond=df.model.isin(['base', 'base_sensi_remove_june']) & (df.covar.str.contains('flooded:period_'))
df.loc[cond,'period']=df.loc[cond,'covar'].str.split(':period_',expand=True)[1]

cond=df.model.isin(['base_binary', 'binary_june_remove_sensitivity', 'Age_strata', 'Race_strata', 'sex_strata', 'ethnicity_strata']) & (df.covar.str.contains('flood_binary_True:period_'))
df.loc[cond,'period']=df.loc[cond,'covar'].str.split('_binary_True:period_',expand=True)[1]


cond=df.model.isin(['Age', 'Race',  'ethnicity', 'sex']) & (df.covar.str.contains('flood_binary_True:period_.*:'))
df.loc[cond,'period']=df.loc[cond,'covar'].str.split('_binary_True:period_',expand=True)[1].str.split(':',expand=True)[0] 

cond=df.model.isin(['base']) & (df.covar.str.contains(':'))
df.loc[cond,'modifier_cat']=df.loc[cond,'covar'].str.split('_',expand=True)[1].str.split(':',expand=True)[0] 


df['outcome']=df.outcome.map({"CardiovascularDiseases":"Cardiovascular Diseases", 
                "Bite_Insect":"Insect Bites" , 
                "Pregnancy_complic":'Pregnancy Related',
                'Heat_Related_But_Not_dehydration':'Heat Related Illness',
                "Dehydration":"Dehydration",
                "Diarrhea":"Diarrhea",
                "Asthma":"Asthma"})
#reorder
df=df.loc[:,['covar', 'RR', 'conf25', 'conf95', 'P', 'outcome', 'model','modifier_cat', 'period']]
df.to_excel('merged_All.xlsx',index=False)       
      
#%% interston between records
outcomes=[ 'Asthma', 'Bite_Insect','CardiovascularDiseases',
                'Dehydration', 'Diarrhea',
                'Heat_Related_But_Not_dehydration',
                'Pregnancy_complic']



in_df=pd.DataFrame()
for o1 in outcomes:
    for o2 in outcomes:
        in_df.loc[o1,o2]=(df[o1] & df[o2]).value_counts()[True]
