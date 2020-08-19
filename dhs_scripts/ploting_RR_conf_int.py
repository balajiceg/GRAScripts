# -*- coding: utf-8 -*-
"""
Created on Tue May 26 16:20:06 2020

@author: balajiramesh
"""

import pandas as pd

import glob,os
import plotly.express as px
import plotly.io as pio
import plotly.graph_objects as go
import numpy as np
pio.renderers.default='browser'


#%%read and merge required columns
first_dir=r"Z:\Balaji\Analysis_out_IPOP\13082020"
req_files=glob.glob(first_dir+"\\*_reg.csv")

op_dir=r"Z:\Balaji\Analysis_out_IPOP\20062020_1\RPL_THEMES_"
merge_df=pd.DataFrame()

for file in req_files:
    df=pd.read_csv(file)[['index','coef','P>|z|','[0.025','0.975]']]
    df=df.round(3)
    Dis_cat=os.path.basename(file).replace("_reg.csv","")
    df['outcome']=Dis_cat
    df['reference']=1
    
    # op_df=pd.read_csv(op_dir+"//"+os.path.basename(file))[['index','coef','P>|z|','[0.025','0.975]']]
    # op_df['outcome']=Dis_cat
    # op_df['reference']=0
    #merge_df=pd.concat([merge_df,df,op_df],axis=0)
    merge_df=pd.concat([merge_df,df],axis=0)
    
merge_df.columns=['covar', 'RR', 'P', 'conf25', 'conf95', 'outcome','reference']
merge_df['covar']=merge_df['covar'].str.replace("\[T.",'_').str.replace('\]','')


#%%pull required betas  for SVI vs dyn SVI
outcome_titls={1:"dyn RPL",0:"RPL"}
i="3"
#for i in ["1_2","1_3","1_4","2_2","2_3","2_4","3_2","3_3","3_4"]:
required=["RPL_THEMES_"+i,"dyn_RPL_THEMES_"+i]
req_df=merge_df.loc[merge_df['covar'].isin(required),:].copy()


#for SVI as scalar alone multipy by 10 percentile
#req_df.loc[:,["RR","conf25","conf95"]]=req_df.loc[:,["RR","conf25","conf95"]]**0.1

#prepare y distance
outcomes=req_df.outcome.unique()
n=len(required)
y_dis=req_df.outcome.astype('category').cat.rename_categories(range(1,len(req_files)*n+1,n)).astype('int')
req_df['text']=req_df.reference.astype('category').cat.rename_categories(outcome_titls).astype('str')
req_df['y_dis']=y_dis+req_df.reference/n
req_df.conf25,req_df.conf95=req_df.RR-req_df.conf25 , req_df.conf95-req_df.RR

#read Qic values and merge
qic=pd.read_csv(r'Z:\Balaji\Analysis_out_IPOP\20062020_1\qic_rpl_vs_dyn.csv')
req_df=req_df.merge(qic,left_on=['outcome','text'],right_on=['outcome','Model'],how='left')
req_df.QIC=np.round(req_df.QIC)
req_df=req_df.dropna()

req_df['text']=req_df.reference.astype('category').cat.rename_categories({1:"dyn RPL",0:"CDC RPL"}).astype('str')

#plot data
fig=px.scatter(req_df, x="RR", y="y_dis", color="outcome",
                 error_x="conf95", error_x_minus="conf25",text='text')
fig.update_traces(textposition='top center')
fig.add_shape(dict(type="line",x0=1,y0=0,x1=1,y1=req_df.y_dis.max()+1,
                   line=dict(color="Black",width=.5)#,dash='dot')
            ))

fig.add_trace(go.Scatter(
    x=req_df.RR+req_df.conf95,
    y=req_df.y_dis,
    name="Model Fitness : QIC",
    mode="text",
    text= "  "+req_df.QIC.astype(str),
    textposition="middle right",
    textfont=dict(
        family="sans serif",
        size=10,
        color="red"
    )
))

# Set title
fig.update_layout(title_text=required[0],xaxis_type='log')
fig.write_html(required[0]+'.html')
fig.show()

#%%for  op ip flood outcome

sp_file='op'
outcome_titls={"op":1,"ip":0}
required=['floodr_FLood_1:Time_flood', 'floodr_FLood_1:Time_PostFlood1','floodr_FLood_1:Time_PostFlood2']

req_df=merge_df.loc[merge_df['covar'].isin(required) & (merge_df.reference==outcome_titls[sp_file]),: ].copy()
outcomes_req=['Bite-Insect', 'CO_Exposure',
       'Dehydration', 'Dialysis', 'Drowning','Hypothermia',
       'Intestinal_infectious_diseases', 'Medication_Refill',
       'Pregnancy_complic', 'Psychiatric']
req_df=req_df[req_df.outcome.isin(outcomes_req)]

#prepare y distance
outcomes=req_df.outcome.unique()
n=len(required)
y_dis=req_df.outcome.astype('category').cat.rename_categories(np.arange(1,len(outcomes)*n*1+1,n*1)).astype('int')
req_df['reference']=req_df.covar.astype('category').cat \
                    .reorder_categories(required[::-1]).cat \
                    .rename_categories(range(len(required))).astype('int')
req_df['y_dis']=y_dis+req_df.reference
req_df.conf25,req_df.conf95=req_df.RR-req_df.conf25 , req_df.conf95-req_df.RR
req_df['text']=req_df.covar.str.split('_').str[3]

#plot data
fig=px.scatter(req_df, x="RR", y="y_dis", color="outcome",
                 error_x="conf95", error_x_minus="conf25",text='text')
fig.update_traces(textposition='top center')
fig.add_shape(dict(type="line",x0=1,y0=0,x1=1,y1=req_df.y_dis.max()+1,
                   line=dict(color="Red",width=1,dash='dot')
            ))

# Set title
fig.update_layout(title_text=sp_file,xaxis_type='log',plot_bgcolor='white')
fig.update_xaxes( gridcolor='rgb(210,210,210)',gridwidth=.5)
fig.update_yaxes( showgrid=False)
fig.write_html(sp_file+'.html')
fig.show()
    
#%% comparing zip code with census tract

outcome_titls={1:"zip_code",0:"census_tracts"}
i=2
flood_times= ['floodr_FLood_1:Time_flood','floodr_FLood_1:Time_PostFlood1','floodr_FLood_1:Time_PostFlood2']
required=[flood_times[i]]
req_df=merge_df.loc[merge_df['covar'].isin(required),:].copy()

#prepare y distance
outcomes=req_df.outcome.unique()
n=2
y_dis=req_df.outcome.astype('category').cat.rename_categories(range(1,len(req_files)*n+1,n)).astype('int')
req_df['text']=req_df.reference.astype('category').cat.rename_categories(outcome_titls).astype('str')
req_df['y_dis']=y_dis+req_df.reference/n
req_df.conf25,req_df.conf95=req_df.RR-req_df.conf25 , req_df.conf95-req_df.RR

#plot data
fig=px.scatter(req_df, x="RR", y="y_dis", color="outcome",
                 error_x="conf95", error_x_minus="conf25",text='text')
fig.update_traces(textposition='top center')
fig.add_shape(dict(type="line",x0=1,y0=0,x1=1,y1=req_df.y_dis.max()+1,
                   line=dict(color="Black",width=.5)#,dash='dot')
            ))
# Set title
fig.update_layout(title_text=required[0],xaxis_type='log')
fig.write_html(required[0].replace(':',' ')+'.html')
fig.show()











