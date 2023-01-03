# -*- coding: utf-8 -*-
"""
Created on Fri May 15 08:05:08 2020

For merging the results csv that was created using glm/gee models

@author: balajiramesh
"""

#%%combined merge
import pandas as pd
import glob, os
first_dir= ".\\"#r"Z:\Balaji\Analysis_out_IPOP\13082020_final1_manu\SVI_adjusted_res"
req_files=glob.glob(first_dir+"\\*_reg.csv")

merge_df=pd.DataFrame()

for file in req_files:
    df=pd.read_csv(file)[['index','coef','P>|z|','[0.025','0.975]','model']]
    df=df.round(3)
    Dis_cat=os.path.basename(file).replace("_reg.csv","")
    #Dis_cat=Dis_cat.split('_')[0]
    df['outcome']=Dis_cat
    
    merge_df=pd.concat([merge_df,df],axis=0)
    
merge_df.columns=['covar', 'RR', 'P', 'conf25', 'conf95','model', 'outcome']
merge_df['covar']=merge_df['covar'].str.replace("\[T.",'_').str.replace('\]','')
#merge_df['folder']='SVI_Cat_T4'

#% outupt
merge_df.to_excel(first_dir+r'\merged_flood_pop_aer_floodcats.xlsx',index=False)  
#%%writ pivot table
pmerge_df=merge_df.loc[merge_df.covar.isin(['floodr_cat_FLood_1:Time_flood',
       'floodr_cat_FLood_1:Time_PostFlood1',
       'floodr_cat_FLood_1:Time_PostFlood2']),:]
pivot_table=pd.pivot_table(pmerge_df, columns=['covar'], values=['RR','conf25','conf95'], index='outcome', aggfunc='first')
pivot_table=pivot_table.sort_index(axis='columns', level='covar')
pivot_table.to_excel(first_dir+r'\merged_flood_cat.xlsx',sheet_name='pivot') 
