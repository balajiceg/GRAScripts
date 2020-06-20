# -*- coding: utf-8 -*-
"""
Created on Tue May 26 16:20:06 2020

@author: balajiramesh
"""

import pandas as pd

import glob,os
import plotly.express as px
import plotly.io as pio

pio.renderers.default='browser'


#%%read and merge required columns
first_dir=r"Z:\Balaji\Analysis_out_IPOP\19062020\dyn_RPL_THEMES_"
req_files=glob.glob(first_dir+"\\*_reg.csv")

op_dir=r"Z:\Balaji\Analysis_out_IPOP\19062020\RPL_THEMES_"
merge_df=pd.DataFrame()

for file in req_files:
    df=pd.read_csv(file)[['index','coef','P>|z|','[0.025','0.975]']]
    df=df.round(3)
    Dis_cat=os.path.basename(file).replace("_reg.csv","")
    df['outcome']=Dis_cat
    df['reference']=1
    df['text']='Dyn theme'
    
    op_df=pd.read_csv(op_dir+"//"+os.path.basename(file))[['index','coef','P>|z|','[0.025','0.975]']]
    op_df['outcome']=Dis_cat
    op_df['reference']=0
    op_df['text']='theme'
    merge_df=pd.concat([merge_df,df,op_df],axis=0)
    
merge_df.columns=['covar', 'RR', 'P', 'conf25', 'conf95', 'outcome','reference','text']
merge_df['covar']=merge_df['covar'].str.replace("\[T.",'_').str.replace('\]','')


#%%pull required betas 

required=["RPL_THEMES_1_4","dyn_RPL_THEMES_1_4"]
req_df=merge_df.loc[merge_df['covar'].isin(required),:].copy()

#for SVI as scalar alone
req_df.loc[:,["RR","conf25","conf95"]]=req_df.loc[:,["RR","conf25","conf95"]]**0.10

#req_df.covar.replace(required,["FloodPeriod","PostFlood"],inplace=True)

outcomes=req_df.outcome.unique()
y_dis=req_df.outcome.astype('category').cat.rename_categories(range(1,len(req_files)*2+1,2)).astype('int')
req_df['y_dis']=y_dis+req_df.reference/2
req_df.conf25,req_df.conf95=req_df.RR-req_df.conf25 , req_df.conf95-req_df.RR

fig=px.scatter(req_df, x="RR", y="y_dis", color="outcome",
                 error_x="conf95", error_x_minus="conf25",text='text')
fig.update_traces(textposition='top center')
fig.add_shape(dict(type="line",x0=1,y0=0,x1=1,y1=req_df.y_dis.max()+1,
                   line=dict(color="Black",width=.5)#,dash='dot')
            ))

fig.show()

    
#%% tables
    
flood_df= req_df.dropna().copy()
flood_df=flood_df.loc[(flood_df.covar=="FloodPeriod")&(flood_df.P<=0.05),:]

post_flood= req_df.dropna().copy()
post_flood=post_flood.loc[(post_flood.covar=="PostFlood")&(post_flood.P<=0.05),:]

















