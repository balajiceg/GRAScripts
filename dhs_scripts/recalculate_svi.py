# -*- coding: utf-8 -*-
"""
Created on Thu May  7 23:52:37 2020

@author: balajiramesh
"""


import pandas as pd
import numpy as np
import geopandas
from scipy.stats import percentileofscore

df=geopandas.read_file(r"Z:/Balaji/SVI_Raw/TEXAS.shp").drop('geometry',axis=1)
df.FIPS=pd.to_numeric(df.FIPS)
df=df[df.FIPS//1000000==48201]

#%%function start
def recalculateSVI(df):
    def rerank(x):
        ranks=x.rank()
        return ((ranks - ranks.min())/(ranks.max() - ranks.min())).round(4)
    
    #remove no data as na
    df[df==-999]=np.nan
    
    #following directions starting on page 16 of CDC SVI documentation
    #theme 1
    
    EPL_POV = rerank(df.EP_POV)
    EPL_UNEMP = rerank(df.EP_UNEMP)
    EPL_PCI = (1-rerank(df.EP_PCI))
    EPL_NOHSDP = rerank(df.EP_NOHSDP)
    SP_THEME1_NEW = EPL_POV + EPL_UNEMP + EPL_PCI + EPL_NOHSDP
    RPL_THEMES_1_NEW = rerank(SP_THEME1_NEW)
    
    #theme 2
    EPL_AGE65 = rerank(df.EP_AGE65)
    EPL_AGE17 = rerank(df.EP_AGE17)
    EPL_DISABL = rerank(df.EP_DISABL)
    EPL_SNGPNT = rerank(df.EP_SNGPNT)
    SP_THEME2_NEW = EPL_AGE65 + EPL_AGE17 + EPL_DISABL + EPL_SNGPNT
    RPL_THEMES_2_NEW = rerank(SP_THEME2_NEW)
    
    #theme 3
    EPL_MINRTY = rerank(df.EP_MINRTY)
    EPL_LIMENG = rerank(df.EP_LIMENG)
    SP_THEME3_NEW = EPL_MINRTY + EPL_LIMENG
    RPL_THEMES_3_NEW = rerank(SP_THEME3_NEW)
    
    #theme 4
    EPL_MUNIT = rerank(df.EP_MUNIT)
    EPL_MOBILE = rerank(df.EP_MOBILE)
    EPL_CROWD = rerank(df.EP_CROWD)
    EPL_NOVEH = rerank(df.EP_NOVEH)
    EPL_GROUPQ = rerank(df.EP_GROUPQ)
    SP_THEME4_NEW = EPL_MUNIT + EPL_MOBILE + EPL_CROWD + EPL_NOVEH + EPL_GROUPQ
    RPL_THEMES_4_NEW = rerank(SP_THEME4_NEW)
    
    SPL_THEMES_NEW = SP_THEME1_NEW+SP_THEME2_NEW+SP_THEME3_NEW+SP_THEME4_NEW
    
    #adding newly calculated SVIs to HarrisCtyCent shapefile
    RPL_THEMES_NEW = rerank(SPL_THEMES_NEW)
    
    ret= pd.DataFrame({"FIPS":df.FIPS,"SVI":RPL_THEMES_NEW})
    return ret
   #%%
vis=ret.merge(validate_data,on="FIPS")
vis=ret.merge(subset_val,on="FIPS")
vis["diff"]=vis.SVI- vis.RPL_THEMES_HC

vis['rankSVI']=vis.SVI.rank()
vis['rankR']=vis.RPL_THEMES_HC.rank()