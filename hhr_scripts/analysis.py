#@author Balaji Ramesh

import pandas as pd
import numpy as np
#import jenkspy
import statsmodels.api as sm
import statsmodels.formula.api as smf
import geopandas
from recalculate_svi import recalculateSVI

def mGetValues(df,colname):
    snames=[s1 for s1 in df.columns if colname+'_' in s1 ]
    vec=[]
    for s in snames:
        val=s.split('_')[-1]
        if val!='t': vec.append(val)
    return vec

def zscore(d):
    return (d-np.nanmean(d))/np.nanstd(d)

def mGetDistri(data,cname):
    ret=[]
    values_s=mGetValues(data,cname)
    for i in values_s:
        sum_counts=np.nansum(data[cname+"_"+i])
        ret+=[int(float(i))]*int(sum_counts)
    return np.array(ret)


def recat(df,colname,cats):
    values_s=np.array(mGetValues(df,colname))
    temp_df=pd.DataFrame(columns=['cat_'+str(i) for i in cats[1:]])
    values=values_s.astype(np.int)
    for i in range(len(cats)-1):
        v=np.logical_and(values>cats[i] , values<=cats[i+1])
        if np.logical_not(np.any(v)): continue
        fil_col= df.loc[:,[colname+'_'+x for x in values_s[v]]]
        temp_df.iloc[:,i]=fil_col.sum(axis=1)
    return temp_df
    

#v1
data_copy=pd.read_csv(r"Z:/Balaji/HHR/HHR_20191001_CT/joined_table_nondemos.csv")

#v3
#data_copy=pd.read_csv(r"Z:/Balaji/HHR/HHR_20191001_CT_Summary_V03/joined_table_nondemos.csv")

#read svi file
svi_df_raw=geopandas.read_file(r'Z:/Balaji/SVI_Raw/TEXAS.shp').drop('geometry',axis=1)
svi_df_raw.FIPS=pd.to_numeric(svi_df_raw.FIPS)
svi_df=recalculateSVI(svi_df_raw[svi_df_raw.FIPS.isin(data_copy.tractId.unique())])

data_copy=data_copy.merge(svi_df,left_on='tractId',right_on="FIPS",how='left')
#data_copy=data_copy.merge(svi_df_raw.loc[:,['FIPS','RPL_THEMES']],on="FIPS",how='left')

data_copy=data_copy[~data_copy.FIPS.isna()]
data_copy.drop('FIPS',axis=1,inplace=True)


flood_ratio_data=geopandas.read_file(r'//vetmed2.vetmed.w2k.vt.edu/Blitzer/NASA project/Balaji/FloodRatioJoinedAll_v1/FloodInund_AllJoined_v1.gpkg')
flood_ratio_data.GEOID=flood_ratio_data.GEOID.astype('int64')
data_copy=data_copy.merge(flood_ratio_data.loc[:,['GEOID','DFO_R100','DFO_R200','DFO_R20','LIST_R20']],right_on="GEOID",left_on='tractId',how='left')

#%%
data=data_copy.copy()

#filtering less than n total responses
min_limit=5
for n in data.keys():
    if n[-2:]=="_t":
        data.loc[np.isnan(data[n]) | (data[n]<min_limit),n]=np.nan
        data.loc[np.isnan(data[n]) | (data[n]<min_limit),n[:-2]+'_1']=np.nan
        
#removing 3 tracts that doesn't cover 100m inundation
#data=data[~data.tractId.isin([48339694700,48339694201,48339694101])]

#rename if using v1 of the data
    
    
### data preparation poisson regression ---------------------
indes=("HomeFlooded","LosePower","OtherHomesFlooded","Contact_Water")
depnsB=('Illness','Injury',"Hospital","LeaveHome")

df=pd.DataFrame({'tractId':data.tractId,'floodRatio':data.DFO_R200,'SVI':data.SVI})#,'imperInd':data.imperInd})
df.floodRatio=df.floodRatio.fillna(0)

for field in indes:
    df.loc[:,field]=data[field+"_1"]/data[field+"_t"]
    
for field in depnsB:
    df.loc[:,field+'_1'],df[field+'_0']=data[field+'_1'],data[field+'_0']
    
# indes=indes+('SVI','floodRatio','imperInd')

# #recatagorizing required field independent variables-------------

# #where lived
# tdf=data[[s1 for s1 in data.keys() if 'whereLived' in s1 ]]
# tdf.loc[:,"whereLived_someHome"]=tdf.whereLived_apartment+tdf.whereLived_hotel+tdf.whereLived_liveFamily+tdf.whereLived_singleFamily
# tdf.loc[:,"whereLived_NoNMobileHome"]=tdf.whereLived_mobileHome+tdf.whereLived_homeless
# tdf=tdf.div(tdf.whereLived_t,axis=0)
# tdf=tdf.loc[:,['whereLived_someHome','whereLived_NoNMobileHome','whereLived_temporaryShelter']]
# indes+=tuple(tdf.columns.tolist())
# df=pd.concat([df,tdf],axis=1)


# #water Level
# cname="waterLevel"
# cats=(0,3,6) #c(0,2,4,6,8) 4 removed because is always singlular
# tdf=recat(data,cname,cats)
# tdf.columns=[cname+"C_"+str(c) for c in cats[1:]]
# tdf=tdf.div(data[cname+"_t"],axis=0)
# indes+=tuple(tdf.columns.tolist())
# df=pd.concat([df,tdf],axis=1)

# #electricity Lost Days
# cname="electricityLostDays"
# d=np.sort(mGetDistri(data,cname))
# zs=zscore(d)
# ds=d[np.logical_and(np.abs(zs)<3.1,d<=30)]
# h=np.array(np.unique(ds,return_counts=True)).T
# print(jenkspy.jenks_breaks(ds, nb_class=5))
# cats=(0,15,30) # 3 9 removed after corr matrix c(0,18,30,60,90)
# tdf=recat(data,cname,cats)
# tdf.columns=[cname+"C_"+str(c) for c in cats[1:]]
# tdf=tdf.div(data[cname+"_t"],axis=0)
# indes+=tuple(tdf.columns.tolist())
# df=pd.concat([df,tdf],axis=1)



# #floodedDays
# cname="floodedDays"
# d=np.sort(mGetDistri(data,cname))
# zs=zscore(d)
# ds=d[d<=30]
# h=np.array(np.unique(ds,return_counts=True)).T
# print(jenkspy.jenks_breaks(ds, nb_class=6))
# cats=(0,15,30) # 3 9 removed after corr matrix c(0,18,30,60,90)
# tdf=recat(data,cname,cats)
# tdf.columns=[cname+"C_"+str(c) for c in cats[1:]]
# tdf=tdf.div(data[cname+"_t"],axis=0)
# indes+=tuple(tdf.columns.tolist())
# df=pd.concat([df,tdf],axis=1)

#recoding values
s=df.loc[df.floodRatio>0,'floodRatio']

#df.loc[:,'floodRatioCat']=pd.cut(df.floodRatio,bins=df.floodRatio.quantile(np.arange(0,1.1,1/2)),right=False)
df.loc[:,'floodRatioCat']=pd.cut(df.floodRatio,bins=[0]+s.quantile([0]+np.arange(0,1.1,1/1)).to_list(),right=False)

df.loc[:,'SVI']=pd.cut(df.SVI,bins=np.arange(0,1.1,1/4),include_lowest=True) #,labels=['<=25%','<=100%'])

##%%run model
indes = [
            #'flooded',
             #'electricity',

             #'otherHomesFlood',#'skinContact',
            #'  #'leftHome',
             'floodRatioCat','SVI',#,'imperInd',
            # 'waterLevelC_3','waterLevelC_6',
            # 'electricityLostDaysC_15','electricityLostDaysC_30',
            # 'floodedDaysC_10','floodedDaysC_90',
            # "whereLived_someHome" ,"whereLived_NoNMobileHome","whereLived_temporaryShelter"
            ]

depnsB=['Illness','Injury',"Hospital"]
#corellation analysis
#cor_mat=df.loc[:,indes].corr()

for dependent in depnsB[1:2]:
    print("_"*200)
    #print(dependent)
     
    print('POISSON----------- '*5)
    #glm poisson
    formula=dependent+'_1 ~ '+' * '.join(indes)
    
    offset=np.log(df[dependent+'_1']+df[dependent+'_0'])
    
    model = smf.glm(formula=formula,data=df,offset=offset,missing='drop',family=sm.families.Poisson(link=sm.families.links.log()))
    results=model.fit()
    print(results.summary())
    results_as_html = results.summary().tables[1].as_html()
    reg_table=pd.read_html(results_as_html, header=0, index_col=0)[0].reset_index()
    reg_table.loc[:,'coef']=np.exp(reg_table.coef)
    reg_table.loc[:,['[0.025', '0.975]']]=np.exp(reg_table.loc[:,['[0.025', '0.975]']])
    print(reg_table)
    reg_table.drop(['z', 'std err'],axis=1).to_clipboard()
    
    

