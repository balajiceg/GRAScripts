# -*- coding: utf-8 -*-
"""
Created on Fri May 15 08:05:08 2020

@author: balajiramesh
"""


import pandas as pd
import glob,os

req_files=glob.glob("*_reg.csv")

merge_df=pd.read_csv(req_files[0])[['index']]

for file in req_files:
    df=pd.read_csv(file)[['coef','P>|z|']]
    df=df.round(3)
    Dis_cat=os.path.basename(file).replace("_reg.csv","")
    df2=pd.read_csv(Dis_cat+"_aux.csv")
    df2.columns=['coef','P>|z|']
    df=pd.concat([df,df2],axis=0,ignore_index=True)
    
    df.columns=['B_'+Dis_cat,'P']
    merge_df=pd.concat([merge_df,df],axis=1)
    
merge_df.to_csv("merged_result.csv",index=False)
    
