# -*- coding: utf-8 -*-
"""
Created on Tue May 26 16:20:06 2020

@author: balajiramesh
"""

import pandas as pd

import glob,os
import matplotlib.pyplot as plt
import pylab as pl

#%%read and merge required columns
req_files=glob.glob("*_reg.csv")

op_dir=r"Z:\Balaji\Analysis_out_IPOP\25052020\op"
merge_df=pd.DataFrame()

for file in req_files:
    df=pd.read_csv(file)[['index','coef','P>|z|','[0.025','0.975]']]
    df=df.round(3)
    Dis_cat=os.path.basename(file).replace("_reg.csv","")
    df['outcome']=Dis_cat
    op_df=pd.read_csv(op_dir+"//"+os.path.basename(file))[['index','coef','P>|z|','[0.025','0.975]']]
    op_df['outcome']=Dis_cat+"_op_"
    merge_df=pd.concat([merge_df,df,op_df],axis=0)
    
merge_df.columns=['covar', 'coef', 'P', 'conf25', 'conf95', 'outcome']
#%%pull required betas 
required=["floodr[T.FLood_1]:Time[T.20170825]","floodr[T.FLood_1]:Time[T.20170913]"]#,"Time[T.20170825]","Time[T.20170913]"]
req_df=merge_df.loc[merge_df['covar'].isin(required),:].copy()
req_df.covar.replace(required,["FloodPeriod","PostFlood"],inplace=True)

outcomes=req_df.outcome.str.replace('_op_','').unique()
for i,outcome in enumerate(outcomes):
    df=req_df[(req_df.outcome==outcome) | (req_df.outcome==outcome+'_op_')].copy()
    df.P=(df.P<=0.05).replace([True,False],["*",""])
    df.conf25,df.conf95=df.coef-df.conf25 , df.conf95-df.coef
    
    #ax = plt.subplot(req_df.outcome.unique()[:5].size,1,i+1)
    fig,ax=plt.subplots()
    sub_df=df[df.outcome==outcome]
    pl.errorbar(sub_df.covar, sub_df.coef, yerr=[sub_df.conf25,sub_df.conf95], color='red', ls='--', marker='o', capsize=5, capthick=1, ecolor='black')
    for i in sub_df.index: ax.annotate(sub_df.loc[i,"P"], (sub_df.loc[i,"covar"],sub_df.loc[i,"coef"]+sub_df.loc[i,"conf95"]))
    
    
    sub_df=df[~(df.outcome==outcome)]
    ax.errorbar(sub_df.covar+" ", sub_df.coef, yerr=[sub_df.conf25,sub_df.conf95], color='red', ls='--', marker='o', capsize=5, capthick=1, ecolor='black')
    for i in sub_df.index: ax.annotate(sub_df.loc[i,"P"], (sub_df.loc[i,"covar"]+" ",sub_df.loc[i,"coef"]+sub_df.loc[i,"conf95"]),xytext=(0, 2),  # 3 points vertical offset
                    textcoords="offset pixels")
     
    #ax.get_xaxis().set_ticks([])
    
    ax.axhline(1, color='green', ls="--",lw=0.5)
    ax.set_ylabel(outcome)
    
    ax.spines['bottom'].set_color('none')
    ax.spines['top'].set_color('none')
# ax.set_xlim(xlims)
# ax.set_ylim(ylims)


















