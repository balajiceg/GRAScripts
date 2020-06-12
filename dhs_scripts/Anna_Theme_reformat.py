# -*- coding: utf-8 -*-
"""
Created on Thu Jun 11 21:24:29 2020

@author: balajiramesh
"""

import pandas as pd


def rerank(x):
        ranks=x.rank().copy()
        return ((ranks - ranks.min())/(ranks.max() - ranks.min())).round(6)




dyn_svi_raw=pd.read_csv('Z:/Balaji/Dynamic_SVI/spl1_theme_raw.csv')

county_to_filter=pd.read_csv('Z:/Balaji/counties_inun.csv').GEOID.to_list()
dyn_svi=dyn_svi_raw[(dyn_svi_raw.Tract_Id//1000000).isin(county_to_filter)].copy()
dyn_svi.iloc[:,1:]=dyn_svi.iloc[:,1:].apply(rerank)

indes=[[11,12,13,14],[35,36,37,38],[59,60,61,62],[83,84,85,86],[107,108,109,110],[131,132,133,134],[155,156,157,158]]

outdf=pd.DataFrame()
for i in range(7):
    avg=dyn_svi.iloc[:,indes[i]].mean(axis=1).round(4)
    df=pd.DataFrame({'FIPS':dyn_svi.Tract_Id,'Day_of_week':i,'Theme_1':avg})
    outdf=pd.concat([outdf,df])
    
outdf.to_csv('Z:/Balaji/Dynamic_SVI/SPL_Theme1.csv')
