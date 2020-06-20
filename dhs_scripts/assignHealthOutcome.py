# -*- coding: utf-8 -*-
"""
Created on Fri Jun 19 13:02:13 2020

For assigning health outcome to op and ip records

@author: balajiramesh
"""

import pandas as pd


def filter_from_icds(sp,outcome_cats,Dis_cat):
    icd_cols=['PRINC_DIAG_CODE', 'OTH_DIAG_CODE_1', 'OTH_DIAG_CODE_2',
       'OTH_DIAG_CODE_3', 'OTH_DIAG_CODE_4', 'OTH_DIAG_CODE_5',
       'OTH_DIAG_CODE_6', 'OTH_DIAG_CODE_7', 'OTH_DIAG_CODE_8',
       'OTH_DIAG_CODE_9', 'E_CODE_1', 'E_CODE_2', 'E_CODE_3', 'E_CODE_4',
       'E_CODE_5']
    incl=outcome_cats.loc[outcome_cats.category==Dis_cat,'incl']
    excl=outcome_cats.loc[outcome_cats.category==Dis_cat,'excl']
    
    def find_cats(x,incl,excl):
        x=x.values.squeeze()
        x=x[~pd.isna(x)]
        incl=incl.to_list()[0].split(';')
        excl=excl.to_list()[0].split(';')
        ret=False
        for i in range(len(x)):
            for j in incl:
                j=j.strip()
                if j==x[i][:len(j)]:
                    ret=True
                    break
                
        if excl != ['']:
            for i in range(len(x)):
                for j in excl:
                    j=j.strip()
                    if j==x[i][:len(j)]:
                        ret=False
                        break
        return ret

    icd_data=sp.loc[:,icd_cols]
    result=icd_data.apply(find_cats,axis=1,incl=incl,excl=excl)
        
    return result.astype('int')


def filter_from_icds_1(sp,outcome_cats,Dis_cat):
    icd_cols=['PRINC_DIAG_CODE', 'OTH_DIAG_CODE_1', 'OTH_DIAG_CODE_2',
       'OTH_DIAG_CODE_3', 'OTH_DIAG_CODE_4', 'OTH_DIAG_CODE_5',
       'OTH_DIAG_CODE_6', 'OTH_DIAG_CODE_7', 'OTH_DIAG_CODE_8',
       'OTH_DIAG_CODE_9', 'E_CODE_1', 'E_CODE_2', 'E_CODE_3', 'E_CODE_4',
       'E_CODE_5']
    incl=outcome_cats.loc[outcome_cats.category==Dis_cat,'incl']
    excl=outcome_cats.loc[outcome_cats.category==Dis_cat,'excl']
    
    incl=pd.Series(incl.to_list()[0].split(';'))
    excl=pd.Series(excl.to_list()[0].split(';'))
    
    #form the searh string
    search_text=sp[icd_cols[0]].astype('str')
    for i in icd_cols[1:]:
        search_text=search_text.str.cat(sp[i].astype('str'),sep=';')
    search_text=(';'+search_text+';').str.replace('nan;','')
    
    #apply regex for inclu code
    incl_bool=incl.apply(lambda x:search_text.str.match(r'.*;'+x+'[^;]*;',case=False)).any()
    result=incl_bool
    
    if excl.to_list()!=['']:
        excl_bool=excl.apply(lambda x:search_text.str.match(r'.*;'+x+'[^;]*;',case=False)).any()
        result= incl_bool & (~excl_bool)
        
    return result
    
#%%read op or ip as sp
INPUT_IPOP_DIR=r'Z:\Balaji\DSHS ED visit data\CleanedMergedJoined'
sp_file='ip'
sp=pd.read_pickle(INPUT_IPOP_DIR+'\\'+sp_file) 

#read categories
outcome_cats=pd.read_csv('Z:/GRAScripts/dhs_scripts/categories.csv')
outcome_cats.fillna('',inplace=True)
print(outcome_cats.category.to_list())

cats=outcome_cats.category.to_list()

df=pd.DataFrame(sp.RECORD_ID)
for Dis_cat in cats:
    df[Dis_cat]=filter_from_icds(sp, outcome_cats, Dis_cat)
    print(Dis_cat)

df.to_csv(INPUT_IPOP_DIR+'\\'+sp_file+'_outcomes.csv',index=False)
