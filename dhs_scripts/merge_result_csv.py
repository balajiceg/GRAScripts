# -*- coding: utf-8 -*-
"""
Created on Fri May 15 08:05:08 2020

For merging the results csv that was created using glm/gee models

@author: balajiramesh
"""


import pandas as pd
import os
import glob

#%%read and merge required columns
first_dir=r"Z:\Balaji\Analysis_out_IPOP\19072020"
req_files=glob.glob(first_dir+"\\op\\*_reg.csv")

merge_df=pd.DataFrame()

for file in req_files:
    df=pd.read_csv(file)[['index','coef','P>|z|','[0.025','0.975]']]
    df=df.round(3)
    Dis_cat=os.path.basename(file).replace("_reg.csv","")
    df['outcome']=Dis_cat
    df['reference']=1
    
    op_df=pd.read_csv(first_dir+"\\ip\\"+os.path.basename(file))[['index','coef','P>|z|','[0.025','0.975]']]
    op_df['outcome']=Dis_cat
    op_df['reference']=0
    merge_df=pd.concat([merge_df,df,op_df],axis=0)
    
merge_df.columns=['covar', 'RR', 'P', 'conf25', 'conf95', 'outcome','reference']
merge_df['covar']=merge_df['covar'].str.replace("\[T.",'_').str.replace('\]','')

#%% outupt
outcome_files={1:"op",0:"ip"}
merge_df['file']=merge_df.reference.astype('category').cat.rename_categories(outcome_files)
merge_df=merge_df.drop('reference',axis=1)
merge_df.to_excel(first_dir+r'\merged.xlsx',index=False)  