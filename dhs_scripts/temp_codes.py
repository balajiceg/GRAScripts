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
    
#%% population in 2881 tracts

x=pd.read_csv(r"Z:/Balaji/DSHS ED visit data/tractsInStudyArea.csv")

y=x.merge(demos,left_on='CensusTractFIPS',right_on='Id2',how='left')

y.loc[:,'Estimate; SEX AND AGE - Total population'].sum()
#%% chi square test
from scipy import stats
cols_to_check=["SEX_CODE","ETHNICITY","RACE","PAT_AGE_YEARS"]

#sex code
mfilt=["F","M"]
ch_var="SEX_CODE"
tractS=sp[ch_var][~pd.isnull(sp.PAT_ADDR_CENSUS_BLOCK_GROUP)]
zipS=sp[ch_var][~pd.isnull(sp.PAT_ZIP)]

zipS_counts=zipS.value_counts().to_frame()
tractS_counts=tractS.value_counts().to_frame()
table=zipS_counts.join(tractS_counts,rsuffix='_tract',lsuffix='_zip')
table=table.loc[mfilt,:].transpose()
res=stats.chi2_contingency(table)
print(res)
pd.DataFrame(res[3],index=table.index,columns=table.columns)

#race
mfilt=list(range(1,6))
tractS=pd.to_numeric(sp.RACE,errors="coerce")[~pd.isnull(sp.PAT_ADDR_CENSUS_BLOCK_GROUP)]
zipS=pd.to_numeric(sp.RACE,errors="coerce")[~pd.isnull(sp.PAT_ZIP)]

zipS_counts=zipS.value_counts().to_frame()
tractS_counts=tractS.value_counts().to_frame()
table=zipS_counts.join(tractS_counts,rsuffix='_tract',lsuffix='_zip')
table=table.loc[mfilt,:].transpose()
res=stats.chi2_contingency(table)
print(res)
pd.DataFrame(res[3],index=table.index,columns=table.columns)


#ethinicity
mfilt=[1,2]
tractS=pd.to_numeric(sp.ETHNICITY,errors="coerce")[~pd.isnull(sp.PAT_ADDR_CENSUS_BLOCK_GROUP)]
zipS=pd.to_numeric(sp.ETHNICITY,errors="coerce")[~pd.isnull(sp.PAT_ZIP)]

zipS_counts=zipS.value_counts().to_frame()
tractS_counts=tractS.value_counts().to_frame()
table=zipS_counts.join(tractS_counts,rsuffix='_tract',lsuffix='_zip')
table=table.loc[mfilt,:].transpose()
res=stats.chi2_contingency(table)
print(res)
pd.DataFrame(res[3],index=table.index,columns=table.columns)

#age
bins=sp.PAT_AGE_YEARS.quantile(np.arange(0,1.01,1/10))
tractS=pd.cut(sp.PAT_AGE_YEARS,bins=bins,include_lowest=True)[~pd.isnull(sp.PAT_ADDR_CENSUS_BLOCK_GROUP)]
zipS=pd.cut(sp.PAT_AGE_YEARS,bins=bins,include_lowest=True)[~pd.isnull(sp.PAT_ZIP)]

zipS_counts=zipS.value_counts().to_frame()
tractS_counts=tractS.value_counts().to_frame()
table=zipS_counts.join(tractS_counts,rsuffix='_tract',lsuffix='_zip')
table=table.transpose()
res=stats.chi2_contingency(table)
print(res)
pd.DataFrame(res[3],index=table.index,columns=table.columns)
#%% merge aux files to see the counts
import pandas as pd
import glob
import os

files=glob.glob(r'Z:\Balaji\Analysis_out_IPOP\13082020_final1\*_aux.csv')
x=[]
for f in files:
    df=pd.read_csv(f)
    df["outcome"]=os.path.basename(f).replace("_aux.csv","")
    x.append(df)
concat_df=pd.concat(x)

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
#%% generating summary table
#%%looping for automatic saving 


floodr_use="DFO_R200" #['DFO_R200','DFO_R100','LIST_R20','DFO_R20','DFOuLIST_R20']
nullAsZero="True" #null flood ratios are changed to 0
floodZeroSep="True" # zeros are considered as seperate class
#flood_data_zip=None

#Dis_cats=["DEATH","Dehydration","Bite-Insect","Dialysis","Asthma_like","Respiratory_All","Infectious_and_parasitic"]
Dis_cats=['ALL',
           'DEATH',
           #'Flood_Storms',
           'CO_Exposure',
           'Drowning',
           'Dehydration',
           'Heat_Related_But_Not_dehydration',
           'Hypothermia',
           'Bite-Insect',
           #'Dialysis',
           #'Medication_Refill',
           'Asthma',
           'Chest_pain',
           #'Psychiatric',
           'Intestinal_infectious_diseases',
            'ARI',
            'Pregnancy_complic'
         ]
cuts=[0.00183,0.01133,0.02668,0.05128,0.08075,0.12103,0.19259]
for i in range(len(cuts)):
    os.mkdir('cuts_'+str(i))
    os.chdir('cuts_'+str(i))
    for Dis_cat in Dis_cats:
        try:
            print(Dis_cat)
            print("-"*50)
            run()
        except Exception as e: print(e)
    os.chdir('..')
   
    
    
#%%poission regression for 
df.TotalVisits=1
grouped_tracts=df.groupby(['STMT_PERIOD_FROM', 'PAT_ADDR_CENSUS_TRACT']).agg({'Outcome':'sum','TotalVisits':'sum','PAT_AGE_YEARS':'mean'}).reset_index()
                 #.unstack(fill_value=0).stack()
                 
grouped_tracts=grouped_tracts.merge(df.loc[~df.PAT_ADDR_CENSUS_TRACT.duplicated(),['PAT_ADDR_CENSUS_TRACT','floodr_cat']],how='left',on="PAT_ADDR_CENSUS_TRACT")
grouped_tracts=grouped_tracts.merge(df.loc[~df.PAT_ADDR_CENSUS_TRACT.duplicated(),['PAT_ADDR_CENSUS_TRACT','Population']],how='left',on="PAT_ADDR_CENSUS_TRACT")
grouped_tracts.loc[:,'Time']=pd.cut(grouped_tracts.STMT_PERIOD_FROM,\
                                        bins=[0]+interv_dates+[20190101],\
                                        labels=['control']+[str(i) for i in interv_dates_cats]).cat.as_unordered()   

#comment this line for ALL ed category
grouped_tracts=grouped_tracts[~(grouped_tracts.TotalVisits==0)]
    
if Dis_cat!="ALL":offset=np.log(grouped_tracts.TotalVisits)
    #offset=None
if Dis_cat=="ALL":offset=np.log(grouped_tracts.Population)
    
    
#run basic poission model
formula= 'Outcome ~  floodr_cat * Time'
model=smf.glm(formula=formula,offset=offset,data=grouped_tracts,family=sm.families.Poisson())
results=model.fit()


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
results.summary()
reg_table.to_clipboard(index=False)
    
    
#%% 
grouped_tracts=df.loc[:,['STMT_PERIOD_FROM','PAT_AGE_YEARS','PAT_ADDR_CENSUS_TRACT','Outcome']]


grouped_tracts=pd.concat([grouped_tracts]+[pd.get_dummies(df[i],prefix=i) for i in ['SEX_CODE','RACE','ETHNICITY','op']],axis=1)

grouped_tracts=grouped_tracts.groupby(['STMT_PERIOD_FROM', 'PAT_ADDR_CENSUS_TRACT']).agg({'Outcome':'sum',
                                                                              'PAT_AGE_YEARS':'mean',
                                                                              'SEX_CODE_M':'sum','SEX_CODE_F':'sum', 
                                                                              'RACE_white':'sum','RACE_black':'sum','RACE_other':'sum',
                                                                              'ETHNICITY_Non_Hispanic':'sum','ETHNICITY_Hispanic':'sum', 
                                                                              'op_False':'sum','op_True':'sum'}).reset_index()
                 
grouped_tracts=grouped_tracts.merge(df.drop_duplicates(['STMT_PERIOD_FROM','PAT_ADDR_CENSUS_TRACT']).loc[:,['STMT_PERIOD_FROM','PAT_ADDR_CENSUS_TRACT','floodr_cat','Population','Time','year','month','weekday']],how='left',on=["PAT_ADDR_CENSUS_TRACT",'STMT_PERIOD_FROM'])
dummy_cols=['SEX_CODE_M', 'SEX_CODE_F', 'RACE_white', 'RACE_black', 'RACE_other','ETHNICITY_Non_Hispanic', 'ETHNICITY_Hispanic', 'op_False', 'op_True']
grouped_tracts.loc[:,dummy_cols]=grouped_tracts.loc[:,dummy_cols].divide(grouped_tracts.Outcome,axis=0)

if Dis_cat=="ALL":offset=np.log(grouped_tracts.Population)
formula='Outcome'+' ~ '+' floodr_cat * Time'+'+ year'+'+month'+'+weekday + PAT_AGE_YEARS + '+' + '.join(dummy_cols)

model = smf.gee(formula=formula,groups=grouped_tracts[flood_join_field], data=grouped_tracts,offset=offset,missing='drop',family=sm.families.Poisson(link=sm.families.links.log()))
    #model = smf.logit(formula=formula, data=df,missing='drop')
    #model = smf.glm(formula=formula, data=df,missing='drop',family=sm.families.Binomial(sm.families.links.logit()))
    
results=model.fit()    


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
results.summary()
reg_table.to_clipboard(index=False)
    

