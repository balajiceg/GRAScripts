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
    
    