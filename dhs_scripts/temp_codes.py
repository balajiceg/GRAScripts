# -*- coding: utf-8 -*-
"""
Created on Thu Apr 16 20:31:43 2020

@author: balajiramesh
"""



op_icd_cols=['PAT_REASON_FOR_VISIT','PRINC_DIAG_CODE', 'OTH_DIAG_CODE_1', 'OTH_DIAG_CODE_2',
       'OTH_DIAG_CODE_3', 'OTH_DIAG_CODE_4', 'OTH_DIAG_CODE_5',
       'OTH_DIAG_CODE_6', 'OTH_DIAG_CODE_7', 'OTH_DIAG_CODE_8',
       'OTH_DIAG_CODE_9', 'E_CODE_1', 'E_CODE_2', 'E_CODE_3', 'E_CODE_4',
       'E_CODE_5']

ip_icd_cols=['ADMITTING_DIAGNOSIS',
       'PRINC_DIAG_CODE', 'OTH_DIAG_CODE_1', 'OTH_DIAG_CODE_2',
       'OTH_DIAG_CODE_3', 'OTH_DIAG_CODE_4', 'OTH_DIAG_CODE_5',
       'OTH_DIAG_CODE_6', 'OTH_DIAG_CODE_7', 'OTH_DIAG_CODE_8',
       'OTH_DIAG_CODE_9', 'E_CODE_1', 'E_CODE_2', 'E_CODE_3', 'E_CODE_4',
       'E_CODE_5' ]
       
icd_codes=sp.loc[:,op_icd_cols]
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


#%%
#filtering zip codes
#using Zipcode
sp.loc[:,"ZIP5"]=sp.PAT_ZIP.str.slice(stop=5)
sp=sp.loc[~sp.ZIP5.isin(['0'*i for i in range(1,6)]),:]
one_var="ZIP5"
#%%looping for automatic saving 


flood_cats_in=1
floodr_use="DFO_R200" #['DFO_R200','DFO_R100','LIST_R20','DFO_R20','DFOuLIST_R20']
nullAsZero="True" #null flood ratios are changed to 0
floodZeroSep="True" # zeros are considered as seperate class
interv_dates=[20170825, 20170913]
#Dis_cats=["DEATH","Dehydration","Bite-Insect","Dialysis","Asthma_like","Respiratory_All","Infectious_and_parasitic"]
Dis_cats=['ALL','DEATH',
         #'Flood_Storms',
         'CO_Exposure',
         #'Drowning',
         'Dehydration',
         'Heat_Related-No_dehydration',
         'Hypothermia',
         'Bite-Insect',
         'Dialysis',
         'Medication_Refill',
         'Asthma_like',
         'Chest_pain',
         'Psychiatric',
         'Intestinal_infectious',
         'Influenza_and_pneumonia',
         'Arthropod-borne_viral_fevers']

for Dis_cat in Dis_cats:
    try:
       run()
    except Exception as e: print(e)
   
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    

