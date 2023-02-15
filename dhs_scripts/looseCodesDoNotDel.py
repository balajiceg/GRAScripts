# -*- coding: utf-8 -*-
"""
Created on Thu Apr 16 20:31:43 2020

@author: balajiramesh
"""



icd_cols=['PRINC_DIAG_CODE', 'OTH_DIAG_CODE_1', 'OTH_DIAG_CODE_2',
       'OTH_DIAG_CODE_3', 'OTH_DIAG_CODE_4', 'OTH_DIAG_CODE_5',
       'OTH_DIAG_CODE_6', 'OTH_DIAG_CODE_7', 'OTH_DIAG_CODE_8',
       'OTH_DIAG_CODE_9', 'E_CODE_1', 'E_CODE_2', 'E_CODE_3', 'E_CODE_4',
       'E_CODE_5']
  
icd_codes=sp.loc[:,icd_cols]
icd_codes=icd_codes.values.flatten()

icd_codes = icd_codes[~pd.isnull(icd_codes)]
icd_codes=pd.Series(icd_codes)
unique_codes=pd.Series(icd_codes.unique())
#check for icd 10 format
unique_codes[~unique_codes.str.match("([A-TV-Z][0-9][A-Z0-9](\.?[A-Z0-9]{0,4})?)")]
unique_codes[unique_codes.str.match("[^A-Z\d.]")]

    #%%group by date and censustract
def groupAndCat(df):
    grouped_tracts=df.groupby(['STMT_PERIOD_FROM_GROUPED', 'PAT_ADDR_CENSUS_TRACT']).size().reset_index()
    grouped_tracts.columns = [*grouped_tracts.columns[:-1], 'Counts']
    #remove zero counts groups
    grouped_tracts=grouped_tracts.loc[grouped_tracts['Counts']>0,]
    
#%% merge aux files to see the counts
import pandas as pd
import glob
import os

files=glob.glob(r'Z:\Balaji\Analysis_out_IPOP\23122020\SVI_Cat_T4\*_aux.csv')
x=[]
for f in files:
    df=pd.read_csv(f)
    df["outcome"]=os.path.basename(f).replace("_aux.csv","")
    x.append(df)
concat_df=pd.concat(x)
concat_df['folder']='SVI_Cat_T4'
concat_df.to_clipboard(index=False)
#%%

result_df=pd.DataFrame({'outcome':concat_df.outcome.unique()})
flood_cats=['NO','FLood_1']
for cat in flood_cats:
    for period in concat_df.Time.unique():
        cols=concat_df.loc[concat_df.Time==period,['outcome',cat]].rename(columns={cat:cat+'_'+period})
        result_df=result_df.merge(cols,on='outcome',how='left')
        
result_df.to_clipboard(index=False)


#%%
#filtering zip codes
#using Zipcode
sp.loc[:,"ZIP5"]=sp.PAT_ZIP.str.slice(stop=5)
sp=sp.loc[~sp.ZIP5.isin(['0'*i for i in range(1,6)]),:]
one_var="ZIP5"

#%% read and merge sys

files=glob.glob('Z:\\SyS data\\*')
x=[pd.read_csv(f,encoding = "ISO-8859-1") for f in files]
result_df=pd.concat(x)
result_df.to_csv("Z:\\Balaji\\SyS data\\merged.csv",index=None)

#%%find unique tracts and counts in OP data
rm_df=df.loc[:,['Outcome','floodr','Time','year','month','weekday', 'PAT_AGE_YEARS','SEX_CODE','RACE','ETHNICITY','PAT_ADDR_CENSUS_TRACT']]
rm_df=rm_df.dropna()
rm_df.PAT_ADDR_CENSUS_TRACT.unique()
(rm_df.PAT_ADDR_CENSUS_TRACT//1000000).unique()
#%% checking how glm and gee poisson models works with offset
###############################
import random
df=pd.DataFrame(np.random.randint(0,2,size=(1000, 2)),columns=['x','y'])
df.y[df.x==1]=random.choices([0,1], [.2,.8],k= df.y[df.x==1].shape[0])
ct=pd.crosstab(df.y,df.x).values
#(390/(104+390))/(263/(263+243))
print(pd.crosstab(df.x,df.y))

orr= (ct[1,1]/(ct[1,1]+ct[0,1]))/(ct[1,0]/(ct[1,0]+ct[0,0]))



choices=[1000,4000]
offset=np.log(random.choices(choices, [.5,.5],k= 1000))
#%%
print('overall rr')
print(orr)
sub_df=df[offset==np.log(choices[0])]
ct=pd.crosstab(sub_df.y,sub_df.x).values
print('subdf 1 rr')
rr= (ct[1,1]/(ct[1,1]+ct[0,1]))/(ct[1,0]/(ct[1,0]+ct[0,0]))
print(rr)

sub_df=df[offset==np.log(choices[1])]
ct=pd.crosstab(sub_df.y,sub_df.x).values
print('subdf 2 rr')
rr= (ct[1,1]/(ct[1,1]+ct[0,1]))/(ct[1,0]/(ct[1,0]+ct[0,0]))
print(rr)


model = smf.gee(formula='y~x',groups=df.index, data=df,offset=None,family=sm.families.Poisson(link=sm.families.links.log()))
results=model.fit()
results_as_html = results.summary().tables[1].as_html()
reg_table=pd.read_html(results_as_html, header=0, index_col=0)[0].reset_index()
reg_table.loc[:,'coef']=np.exp(reg_table.coef)
reg_table.loc[:,['[0.025', '0.975]']]=np.exp(reg_table.loc[:,['[0.025', '0.975]']])
print('gee---------------')
print(reg_table)


model = smf.glm(formula='y~x',data=df,offset=None,family=sm.families.Poisson(link=sm.families.links.log()))
results=model.fit()
results_as_html = results.summary().tables[1].as_html()
reg_table=pd.read_html(results_as_html, header=0, index_col=0)[0].reset_index()
reg_table.loc[:,'coef']=np.exp(reg_table.coef)
reg_table.loc[:,['[0.025', '0.975]']]=np.exp(reg_table.loc[:,['[0.025', '0.975]']])
print('glm---------------')
print(reg_table)

print('with offset glm-------------')
model = smf.glm(formula='y~x',data=df,offset=offset,family=sm.families.Poisson(link=sm.families.links.log()))
results=model.fit()
results_as_html = results.summary().tables[1].as_html()
reg_table=pd.read_html(results_as_html, header=0, index_col=0)[0].reset_index()
reg_table.loc[:,'coef']=np.exp(reg_table.coef)
reg_table.loc[:,['[0.025', '0.975]']]=np.exp(reg_table.loc[:,['[0.025', '0.975]']])
print(reg_table)


 #model = smf.logit(formula=formula, data=df,missing='drop')
    #model = smf.glm(formula=formula, data=df,missing='drop',family=sm.families.Binomial(sm.families.links.logit()))
    


#%%looping for automatic saving 


#floodr_use="DFO_R200" #['DFO_R200','DFO_R100','LIST_R20','DFO_R20','DFOuLIST_R20']
#nullAsZero="True" #null flood ratios are changed to 0
#floodZeroSep="True" # zeros are considered as seperate class
#flood_data_zip=None

#Dis_cats=["DEATH","Dehydration","Bite-Insect","Dialysis","Asthma_like","Respiratory_All","Infectious_and_parasitic"]
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

for exposure in ['triCloseProxDur',
       'triDistMiles', 'hvyRainDur', 'totRainfall']:
    print(exposure)
    for Dis_cat in Dis_cats:
                try:
                    print(Dis_cat)
                    print("-"*50)
                    run()
                except Exception as e: print(e)
            
#%%
SVI_COLS=['SVI_Cat','SVI_Cat_T1', 'SVI_Cat_T2', 'SVI_Cat_T3', 'SVI_Cat_T4']
import os
for SVI_COL in SVI_COLS:
    for FIL_COL in [1,2,3,4]:
        #os.mkdir(SVI_COL)
        #os.chdir(SVI_COL)
        for Dis_cat in Dis_cats:
            try:
                print(Dis_cat)
                print("-"*50)
                run()
            except Exception as e: print(e)
        #os.chdir('..')
       
        
#%% pivot table for counts  and mergingt the pivot tables
outcomes=['Asthma','Bite_Insect','CardiovascularDiseases','Dehydration','Diarrhea','Pregnancy_complic','Heat_Related_But_Not_dehydration']
sex=pd.pivot_table(data=df,index=['period','flood_binary'],values=outcomes,aggfunc='sum',columns=['Sex']).T.rename(columns=str).reset_index().rename(columns={'Sex':'cats'})

Ethnicity=pd.pivot_table(data=df,index=['period','flood_binary'],values=outcomes,aggfunc='sum',columns=['Ethnicity']).T.rename(columns=str).reset_index().rename(columns={'Ethnicity':'cats'})

Race=pd.pivot_table(data=df,index=['period','flood_binary'],values=outcomes,aggfunc='sum',columns=['Race']).T.rename(columns=str).reset_index().rename(columns={'Race':'cats'})

start=-1
df['AgeGrp']=pd.cut(df.Age,[start,5,17,50,64,200],labels=['0_5','6_17','18_50','51_64','gt64'])
age1=pd.pivot_table(data=df,index=['period','flood_binary'],values=['Dehydration'],aggfunc='sum',columns=['AgeGrp']).T.rename(columns=str).reset_index().rename(columns={'AgeGrp':'cats'})

df['AgeGrp']=pd.cut(df.Age,[start,5,17,50,200],labels=['0_5','6_17','18_50','gt50'])
age2=pd.pivot_table(data=df,index=['period','flood_binary'],values=['Asthma'],aggfunc='sum',columns=['AgeGrp']).T.rename(columns=str).reset_index().rename(columns={'AgeGrp':'cats'})

df['AgeGrp']=pd.cut(df.Age,[start,5,17,200],labels=['0_5','6_17','gt17'])
age3=pd.pivot_table(data=df,index=['period','flood_binary'],values=['Bite_Insect'],aggfunc='sum',columns=['AgeGrp']).T.rename(columns=str).reset_index().rename(columns={'AgeGrp':'cats'})

#df['AgeGrp']=pd.cut(df.Age,[start,17,50,64,200],labels=['0_17','18_50','51_64','gt64'])
#age4=pd.pivot_table(data=df,index=['period','flood_binary'],values=['Chest_pain'],aggfunc='sum',columns=['AgeGrp']).T.rename(columns=str).reset_index().rename(columns={'AgeGrp':'cats'})

df['AgeGrp']=pd.cut(df.Age,[start,5,17,64,200],labels=['0_5','6_17','18_64','gt64'])
age5=pd.pivot_table(data=df,index=['period','flood_binary'],values=['Diarrhea'],aggfunc='sum',columns=['AgeGrp']).T.rename(columns=str).reset_index().rename(columns={'AgeGrp':'cats'})

df['AgeGrp']=pd.cut(df.Age,[start,21,200],labels=['0_21','gt21'])
age6=pd.pivot_table(data=df,index=['period','flood_binary'],values=['Heat_Related_But_Not_dehydration'],aggfunc='sum',columns=['AgeGrp']).T.rename(columns=str).reset_index().rename(columns={'AgeGrp':'cats'})

df['AgeGrp']=pd.cut(df.Age,[-1,0,19,27,35,200],labels=['0','1_19','20_27','28_35','gt35'])
age7=pd.pivot_table(data=df,index=['period','flood_binary'],values=['Pregnancy_complic'],aggfunc='sum',columns=['AgeGrp']).T.rename(columns=str).reset_index().rename(columns={'AgeGrp':'cats'})

df['AgeGrp']=pd.cut(df.Age,[-1,17,50,64,200],labels=['0_17','18_50','51_64','gt64'])
age8=pd.pivot_table(data=df,index=['period','flood_binary'],values=['CardiovascularDiseases'],aggfunc='sum',columns=['AgeGrp']).T.rename(columns=str).reset_index().rename(columns={'AgeGrp':'cats'})


merg=pd.concat([sex,Ethnicity,Race,age1,age2,age3,age7,age5,age6,age8]).reset_index()
merg['ind']=merg.index
merg=merg.sort_values(['level_0','ind'])


