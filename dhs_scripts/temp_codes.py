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
       
icd_codes=sp.loc[:,ip_icd_cols]
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

#using Zipcode
sp.loc[:,"ZIP5"]=sp.PAT_ZIP.str.slice(stop=5)
sp=sp.loc[~sp.ZIP5.isin(['0'*i for i in range(1,6)]),:]
one_var="ZIP5"

#using census tract
sp.loc[:,"TRACT"]=(sp.PAT_ADDR_CENSUS_BLOCK_GROUP//10)
one_var="TRACT"

#for sex code
mfilt=["F","M"]
cros_tab=pd.crosstab(sp[one_var],sp.SEX_CODE)
cros_tab=cros_tab.loc[:,mfilt]
stats.chi2_contingency(cros_tab)

#for Race
df=sp.loc[:,[one_var,"RACE"]]
df.RACE=pd.to_numeric(df.RACE,errors="coerce")
df=df.loc[df.RACE.isin(range(1,6)),:]
cros_tab=pd.crosstab(df[one_var],df.RACE)
stats.chi2_contingency(cros_tab)


#for Ethinicity
df=sp.loc[:,[one_var,"ETHNICITY"]]
df.ETHNICITY=pd.to_numeric(df.ETHNICITY,errors="coerce")
df=df.loc[df.ETHNICITY.isin([1,2]),:]
cros_tab=pd.crosstab(df[one_var],df.ETHNICITY)
stats.chi2_contingency(cros_tab)

#for Age
df=sp.loc[:,[one_var,"PAT_AGE_YEARS"]]
bins=df.PAT_AGE_YEARS.quantile(np.arange(0,1.01,1/10))
df.PAT_AGE_YEARS=pd.cut(df.PAT_AGE_YEARS,bins=bins,include_lowest=True,labels=bins.iloc[:-1])
cros_tab=pd.crosstab(df[one_var],df.PAT_AGE_YEARS)
stats.chi2_contingency(cros_tab)
