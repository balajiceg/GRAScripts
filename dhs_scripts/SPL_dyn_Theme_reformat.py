# -*- coding: utf-8 -*-
"""
Created on Thu Jun 11 21:24:29 2020

@author: balajiramesh
"""

import pandas as pd


def rerank(x):
        ranks=x.rank().copy()
        return ((ranks - ranks.min())/(ranks.max() - ranks.min())).round(6)

for j in ['1','2','3']:
    dyn_svi_raw=pd.read_csv('Z:/Balaji/Dynamic_SVI/spl'+j+'_theme_raw.csv')
    
    tracts_to_filter=pd.read_csv('Z:/Balaji/DSHS ED visit data/CensusTractsInData.csv').GEOID.to_list()
    dyn_svi=dyn_svi_raw[(dyn_svi_raw.FIPS).isin(tracts_to_filter)].copy()
    dyn_svi.iloc[:,1:]=dyn_svi.iloc[:,1:].apply(rerank)
    
    indes=[[11,12,13,14],[35,36,37,38],[59,60,61,62],[83,84,85,86],[107,108,109,110],[131,132,133,134],[155,156,157,158]]
    
    outdf=pd.DataFrame()
    for i in range(7):
        avg=dyn_svi.iloc[:,indes[i]].mean(axis=1).round(4)
        df=pd.DataFrame({'FIPS':dyn_svi.FIPS,'Day_of_week':i,'Theme_'+j:avg})
        outdf=pd.concat([outdf,df])
        
    outdf.to_csv('Z:/Balaji/Dynamic_SVI/SPL_Theme'+j+'.csv')


#%% Joining the themes file into single one
df=pd.read_csv('Z:/Balaji/Dynamic_SVI/SPL_Theme'+str(1)+'.csv').iloc[:,1:]
for i in range(2,4):
    ndf=pd.read_csv('Z:/Balaji/Dynamic_SVI/SPL_Theme'+str(i)+'.csv').iloc[:,1:]
    df=df.merge(ndf,on=['FIPS','Day_of_week'])

df.to_csv('Z:/Balaji/Dynamic_SVI/SPL_Themes_1_2_3.csv')
