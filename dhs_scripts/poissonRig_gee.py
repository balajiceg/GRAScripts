# -*- coding: utf-8 -*-
"""
Created on Fri May 15 01:55:22 2020

@author: balajiramesh
"""


# -*- coding: utf-8 -*-
"""
Created on Fri Apr 10 00:25:12 2020

@author: balajiramesh
"""
import pandas as pd
import numpy as np
import geopandas
import plotly.express as px
import plotly.io as pio
import statsmodels.api as sm
import statsmodels.formula.api as smf
from datetime import timedelta, date,datetime
from dateutil import parser
from recalculate_svi import recalculateSVI

import dash
import dash_table
from dash.dependencies import Input, Output
import dash_core_components as dcc
import dash_html_components as html

pio.renderers.default = "browser"

#%%functions
def filter_mortality(df):
    pat_sta=df.PAT_STATUS.copy()
    pat_sta=pd.to_numeric(pat_sta,errors="coerce")
    return pat_sta.isin([20,40,41,42]).astype('int')

def filter_all(df):
    return (~pd.isna(df.index)).astype('int')

def filter_from_icds(sp,outcome_cats,Dis_cat):
    icd_cols=['PRINC_DIAG_CODE', 'OTH_DIAG_CODE_1', 'OTH_DIAG_CODE_2',
       'OTH_DIAG_CODE_3', 'OTH_DIAG_CODE_4', 'OTH_DIAG_CODE_5',
       'OTH_DIAG_CODE_6', 'OTH_DIAG_CODE_7', 'OTH_DIAG_CODE_8',
       'OTH_DIAG_CODE_9', 'E_CODE_1', 'E_CODE_2', 'E_CODE_3', 'E_CODE_4',
       'E_CODE_5']
    incl=outcome_cats.loc[outcome_cats.category==Dis_cat,'incl']
    excl=outcome_cats.loc[outcome_cats.category==Dis_cat,'excl']
    
    def find_cats(x,incl,excl):
        x=x.values.squeeze()
        x=x[~pd.isna(x)]
        incl=incl.to_list()[0].split(';')
        excl=excl.to_list()[0].split(';')
        ret=False
        for i in range(len(x)):
            for j in incl:
                j=j.strip()
                if j==x[i][:len(j)]:
                    ret=True
                    break
                
        if excl != ['']:
            for i in range(len(x)):
                for j in excl:
                    j=j.strip()
                    if j==x[i][:len(j)]:
                        ret=False
                        break
        return ret

    icd_data=sp.loc[:,icd_cols]
    result=icd_data.apply(find_cats,axis=1,incl=incl,excl=excl)
        
    return result.astype('int')
    

#%%read ip op data
INPUT_IPOP_DIR=r'Z:\Balaji\DSHS ED visit data\CleanedMergedJoined'
sp_file='ip'
sp=pd.read_pickle(INPUT_IPOP_DIR+'\\'+sp_file)
#sp=pd.read_pickle(INPUT_IPOP_DIR+r'\op')
flood_data=geopandas.read_file(r'Z:/Balaji/FloodRatioJoinedAll_v1/FloodInund_AllJoined_v1.gpkg')

#read svi data
SVI_df_raw=geopandas.read_file(r'Z:/Balaji/SVI_Raw/TEXAS.shp').drop('geometry',axis=1)
SVI_df_raw.FIPS=pd.to_numeric(SVI_df_raw.FIPS)

demos=pd.read_csv(r'Z:/Balaji/Census_data_texas/ACS_17_5YR_DP05_with_ann.csv',low_memory=False,skiprows=1)
flood_products=['DFO_R200','DFO_R100','LIST_R20','DFO_R20','DFOuLIST_R20']


#read counties that are innundated
county_to_filter=pd.read_csv('Z:/Balaji/counties_inun.csv').GEOID.to_list()
#%%predefine variable if got getting from gui
interven_date1,interven_date2=str(datetime(2017,8,24)),str(datetime(2017,10,2))
date_div=[{'props':{'date':i}} for i in [interven_date1,interven_date2]]
avg_window=5
flood_cats_in=1
floodr_use="DFO_R200"
nullAsZero="True"
floodZeroSep="True"
DATE_GROUP="DAILY"
Dis_cats=["ALL","DEATH"]
Dis_cat="ALL"

#%%read the categories file
outcome_cats=pd.read_csv('Z:/GRAScripts/dhs_scripts/categories.csv')
outcome_cats.fillna('',inplace=True)

#%%cleaing for age, gender and race
    #age
sp.loc[:,'PAT_AGE_YEARS']=pd.to_numeric(sp.PAT_AGE_YEARS,errors="coerce")
sp.loc[:,'PAT_AGE_YEARS']=sp.loc[:,'PAT_AGE_YEARS'].astype('float')

#sp.loc[:,'PAT_AGE_YEARS']=pd.cut(sp.PAT_AGE_YEARS,bins=[0,1,4,11,16,25,64,150],include_lowest=True,labels=(0,1,4,11,16,25,64)) 

#gender
sp.loc[~sp.SEX_CODE.isin(["M","F"]),'SEX_CODE']=np.nan
sp.SEX_CODE=sp.SEX_CODE.astype('category')

#ethinicity
# sp.loc[:,'RACE']=pd.to_numeric(sp.RACE,errors="coerce")
# sp.loc[~sp.RACE.isin([1,2]),'RACE']=np.nan
# sp.RACE=sp.RACE.astype('category')

#race
sp.loc[:,'RACE']=pd.to_numeric(sp.RACE,errors="coerce")
sp.loc[(sp.RACE<=0) | (sp.RACE>5),'RACE']=np.nan
sp.loc[sp.RACE<=2,'RACE']=5
sp.RACE=sp.RACE.astype('category')
sp.RACE.cat.rename_categories({3:'black',4:'white',5:'other'},inplace=True)


#%%define app GUI

# first_load=True
# external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
# app = dash.Dash('Rate Graph',external_stylesheets=external_stylesheets)

# app.layout = html.Div([
#     dcc.Slider(min=0, max=3, marks={i: item for i,item in enumerate(["NO","FLood_1","FLOOD_2","FLOOD_3"])},
#         value=flood_cats_in,id='my-slider'),
#     dcc.RadioItems(id='ip-op',options=[{'label':i, 'value': i} for i in ['ip','op']],value=sp_file,labelStyle={'display': 'inline-block'},style={'display': 'inline'}),
#     dcc.Loading(children=html.Div(id='hidden-div', style={'display':'none'})),
#     dcc.Input(id="avg_window",type="number",placeholder="avg window",value=avg_window,style={'display':'inline'}),
#     dcc.Dropdown(id='floodr_use',options=[{'label':i, 'value': i} for i in flood_products],value=floodr_use),
#     html.Div(id="flood_bins"),
#     dcc.Dropdown(id="group_date",options=[{'label':i, 'value': i} for i in ["DAILY","WEEKLY","MONTHLY"]],value=DATE_GROUP),
#     dcc.Dropdown(id="Dis_cat",options=[{'label':i, 'value': i} for i in Dis_cats+outcome_cats.category.to_list()],value=Dis_cat),
#     dcc.RadioItems(id='nullAsZero',options=[{'label':i, 'value': i} for i in ['True','False']],value=nullAsZero,style={'display':'inline'},labelStyle={'display': 'inline-block'}),html.I(children=" nullAsZero"),html.Br(),
#     dcc.RadioItems(id='floodZeroSep',options=[{'label':i, 'value': i} for i in ['True','False']],value=floodZeroSep ,style={'display':'inline'},labelStyle={'display': 'inline-block'}),html.I(children=" floodZeroSep"),html.Br(),
    
#     dcc.Input(id="n_interv",type="number",value=2,style={'display':'inline','width':'50px'}),
#     html.Div(id="dates",style={'display':'inline'},children=[dcc.DatePickerSingle(date=interven_date1,id='date0'),dcc.DatePickerSingle(date=interven_date2,id='date1')]),
    
#     html.Button('Run', id='button'),
#     dcc.Loading(children=[dcc.Graph(id='my-graph'),dash_table.DataTable(id='reg_table',columns='',data=''),html.Hr(),
#                           dash_table.DataTable(id='reg_table_dev',columns='',data='')])
    
# ], style={'width': '500'})


# app.run_server()
#%%
# @app.callback(Output("dates", "children"),[Input("n_interv", "value")])
# def update_dates(value):
#     return [dcc.DatePickerSingle(id='date'+str(i),date=interven_date1) for i in range(value)]

# @app.callback(
#     [Output('reg_table', 'data'),Output('reg_table','columns'),
#      Output('reg_table_dev', 'data'),Output('reg_table_dev','columns'),
#      Output('my-graph', 'figure'),Output('flood_bins','children')],
#     [dash.dependencies.Input('button', 'n_clicks')],
#     [dash.dependencies.State('my-slider', 'value'),dash.dependencies.State('avg_window', 'value'),
#      dash.dependencies.State('nullAsZero','value'),dash.dependencies.State('floodZeroSep','value'),
#      dash.dependencies.State('floodr_use','value'),
#      dash.dependencies.State('Dis_cat','value'),
#      dash.dependencies.State('dates','children'),dash.dependencies.State('group_date','value')])

def update_output(n_clicks, flood_cats_in,avg_window,nullAsZero,floodZeroSep,floodr_use,Dis_cat,date_div,DATE_GROUP):
    global sp,flood_data,demos,first_load,outcome_cats
    if first_load:
        first_load=False
        return
    #%%variables 
    interv_dates=[x['props']['date'] for x in date_div]
     
    interv_dates=[int(datetime.strftime(parser.parse(test),"%Y%m%d")) for test in interv_dates]
    #DATE_GROUPS={"DAILY","WEEKLY","MONTHLY"}
    #flood quantiles
    FLOOD_QUANTILES=["NO","FLood_1","FLOOD_2","FLOOD_3","FLOOD_4"]
    FLOOD_QUANTILES=FLOOD_QUANTILES[:int(flood_cats_in)+1]
    #%%spatial dataframe
    floodr=flood_data.copy()
    floodr.GEOID=pd.to_numeric(floodr.GEOID).astype("Int64")
    floodr=floodr.loc[:,['GEOID']+[floodr_use]]
    floodr.columns=['GEOID','floodr']
    #%%read population data
    demos.Id2=demos.Id2.astype("Int64")
    
    #%%keep only the required fields and dates
    
    #remove records before 2016
    sp=sp.loc[(~pd.isna(sp.STMT_PERIOD_FROM))&(~pd.isna(sp.PAT_ADDR_CENSUS_BLOCK_GROUP))] 
    
    sp=sp[((sp.STMT_PERIOD_FROM > 20160700) & (sp.STMT_PERIOD_FROM< 20161232))\
        | ((sp.STMT_PERIOD_FROM > 20170400) & (sp.STMT_PERIOD_FROM< 20171232))\
            | ((sp.STMT_PERIOD_FROM > 20180700) & (sp.STMT_PERIOD_FROM< 20181232))]
    #df_cp=df.copy(deep=True)
    
    #%% state ment period to months or week
    if DATE_GROUP=="DAILY":
        sp.loc[:,'STMT_PERIOD_FROM_GROUPED']=sp.STMT_PERIOD_FROM#(sp.STMT_PERIOD_FROM//10)*10+2
    elif DATE_GROUP=="MONTHLY":
        sp.loc[:,'STMT_PERIOD_FROM_GROUPED']=(sp.STMT_PERIOD_FROM//100)*100+1
    elif DATE_GROUP=="WEEKLY":
        date1,date2=datetime.strptime('20160702','%Y%m%d'),datetime.strptime('20170101','%Y%m%d')
        weekly_bins=np.arange(date1,date2,timedelta(7))
        date1,date2=datetime.strptime('20170401','%Y%m%d'),datetime.strptime('20180101','%Y%m%d')
        weekly_bins=np.concatenate([weekly_bins,np.arange(date1,date2,timedelta(7))])
        date1,date2=datetime.strptime('20180630','%Y%m%d'),datetime.strptime('20190101','%Y%m%d')
        weekly_bins=np.concatenate([weekly_bins,np.arange(date1,date2,timedelta(7))])
        weekly_bins=pd.to_numeric(pd.Series(weekly_bins).dt.strftime("%Y%m%d"))
        sp.loc[:,'STMT_PERIOD_FROM_GROUPED']=pd.cut(sp.STMT_PERIOD_FROM,bins=weekly_bins,include_lowest=True,labels=weekly_bins[1:],right=True)
        #remove intermediate year records
        sp.loc[(sp.STMT_PERIOD_FROM==20170401) | (sp.STMT_PERIOD_FROM==20180630),'STMT_PERIOD_FROM_GROUPED']=None
        sp=sp.loc[~pd.isna(sp.STMT_PERIOD_FROM_GROUPED),]
           
    #%%cnesus block group to census tract
    sp.loc[:,'PAT_ADDR_CENSUS_TRACT']=(sp.PAT_ADDR_CENSUS_BLOCK_GROUP//10)
    
    #%%filter counties
    if county_to_filter != -1:
        sp_filtered=sp[(sp.PAT_ADDR_CENSUS_TRACT//1000000).isin(county_to_filter)].copy()
    else:
        sp_filtered=sp
    #sp_filtered=sp_filtered.loc[~pd.isna(sp[['PAT_AGE_YEARS','SEX_CODE','RACE']]).any(axis=1),:]
        #%%splitting into all and specific
    df_all=sp_filtered.loc[:,['STMT_PERIOD_FROM_GROUPED','PAT_ADDR_CENSUS_TRACT','PAT_AGE_YEARS','SEX_CODE','RACE']].copy()
    
    df=sp_filtered.loc[:,['STMT_PERIOD_FROM_GROUPED','PAT_ADDR_CENSUS_TRACT','PAT_AGE_YEARS','SEX_CODE','RACE']]
    
    if Dis_cat=="DEATH":df.loc[:,'Counts']=filter_mortality(sp_filtered)
    if Dis_cat=="ALL":df.loc[:,'Counts']=filter_all(sp_filtered)
    if Dis_cat in outcome_cats.category.to_list():df.loc[:,'Counts']=filter_from_icds(sp_filtered,outcome_cats,Dis_cat)
    
    
    #%% merge population
    demos_subset=demos.iloc[:,[1,3]]
    demos_subset.columns=["PAT_ADDR_CENSUS_TRACT","Population"]
    df=df.merge(demos_subset,on="PAT_ADDR_CENSUS_TRACT",how='left')
    df=df.loc[df.Population>0,]
    
    #%%merge SVI and flood ratio
    df=df.merge(floodr,left_on="PAT_ADDR_CENSUS_TRACT",right_on='GEOID',how='left')
    #make tracts with null as zero flooding
    if nullAsZero == "True": df.loc[pd.isna(df.floodr),'floodr']=0.0
    
    #%% merge SVI after recategorization
    svi=recalculateSVI(SVI_df_raw[SVI_df_raw.FIPS.isin(df.PAT_ADDR_CENSUS_TRACT.unique())])
    #join svi
    df=df.merge(svi,left_on="PAT_ADDR_CENSUS_TRACT",right_on="FIPS",how='left').drop("FIPS",axis=1)
    df.loc[:,'SVI']=pd.cut(df.SVI,bins=np.arange(0,1.1,1/4),include_lowest=True,labels=[1,2,3,4])
    #%%categorize floods as per quantiles
    tractsfloodr=df.loc[~df.duplicated("PAT_ADDR_CENSUS_TRACT"),['PAT_ADDR_CENSUS_TRACT','floodr']]
    if floodZeroSep == "True":
        s=tractsfloodr.loc[tractsfloodr.floodr>0,'floodr']  
        flood_bins=s.quantile(np.arange(0,1.1,1/(len(FLOOD_QUANTILES)-1))).to_numpy()
        flood_bins=np.append([0],flood_bins)
    else:
        s=tractsfloodr.loc[tractsfloodr.floodr>-1,'floodr']
        flood_bins=s.quantile(np.arange(0,1.1,1/len(FLOOD_QUANTILES))).to_numpy()
        
    # adjust if some bincenters were zero    
    for i in range(1,len(FLOOD_QUANTILES)):
        flood_bins[i]=i*1e-6 if flood_bins[i]==0.0 else flood_bins[i]
    
    #flood_bins=np.insert(flood_bins,0,0)
    df.loc[:,'floodr']=pd.cut(df.floodr,bins=flood_bins,right=True,include_lowest=True,labels=FLOOD_QUANTILES)
    df=df.drop("GEOID",axis=1)
   
    #%% run grouping for dinominator and join them
    #grouped_tracts_all=df_all.groupby(['STMT_PERIOD_FROM_GROUPED', 'PAT_ADDR_CENSUS_TRACT']).size().reset_index()
    #grouped_tracts_all.columns=[*grouped_tracts_all.columns[:-1], 'TotalVisits']
    
    #df=df.merge(grouped_tracts_all,on=['STMT_PERIOD_FROM_GROUPED', 'PAT_ADDR_CENSUS_TRACT'],how='left')
    
    #filter only >0 tracts
    #df=df.loc[df.TotalVisits>0,:]
    
    #%% bringing in intervention
    df.loc[:,'Time']=pd.cut(df.STMT_PERIOD_FROM_GROUPED,\
                                        bins=[0]+interv_dates+[20190101],\
                                        labels=['control']+[str(i) for i in interv_dates]).cat.as_unordered()
    #set after 2018 as control
    df.loc[df.STMT_PERIOD_FROM_GROUPED>20180100,'Time']="control"
    #filter only after the impact
    #df=df.loc[df.Time==str(interv_dates[-1]),:]
    
    #%%controling for year
    df['year']=(df.STMT_PERIOD_FROM_GROUPED.astype('int32')//1e4).astype('category')
    df['month']=(df.STMT_PERIOD_FROM_GROUPED.astype('int32')//1e2%100).astype('category')
    df['weekday']=pd.to_datetime(df.STMT_PERIOD_FROM_GROUPED.astype('str'),format='%Y%m%d').dt.dayofweek.astype('category')
    
    
    #%%create the category columan
    # grouping_cols=["PAT_ADDR_CENSUS_TRACT", "STMT_PERIOD_FROM_GROUPED","SEX_CODE","RACE","PAT_AGE_YEARS"]
    
    # df['group']=df[grouping_cols[0]].astype('str').copy()
    # for col in grouping_cols[1:]:
    #     df['group']=df.loc[:,'group']+"_"+df[col].astype('str')
    # df['group']=df['group'].astype('category')
    # df['group']=df.group.cat.rename_categories(range(df.group.cat.categories.size))
    #%%running the model
    outcome='Counts'
    
    #if Dis_cat!="ALL":offset=np.log(df.TotalVisits)
    if Dis_cat=="ALL":offset=np.log(df.Population)
    
    
    formula='Counts'+' ~ '+' floodr * Time + SVI '+'+ year'+'+month'+'+weekday' + '+PAT_AGE_YEARS + SEX_CODE + RACE'
    model = smf.gee(formula=formula,groups=df.index, data=df,missing='drop',offset=offset,family=sm.families.Poisson(link=sm.families.links.log()))
    #model = smf.logit(formula=formula, data=df,missing='drop')
    #model = smf.glm(formula=formula, data=df,missing='drop',family=sm.families.Binomial(sm.families.links.logit()))
    
    results=model.fit()
    #print(results.summary())
    #print(np.exp(results.params))
    # print(np.exp(results.conf_int()))
    
    
    #%%plot the rate graph
    # plot_data={}
    # for item in FLOOD_QUANTILES:
    #     plot_data[item]=df.loc[df.floodr==item,["STMT_PERIOD_FROM_GROUPED","Counts","TotalVisits"]]
    #     plot_data[item]=plot_data[item].groupby(['STMT_PERIOD_FROM_GROUPED']).agg({'Counts':'sum','TotalVisits':'count'}).reset_index()
        
    #     if Dis_cat!="ALL":plot_data[item]["Counts"]=plot_data[item]["Counts"]/plot_data[item]["TotalVisits"]
        
    #     plot_data[item]=plot_data[item].loc[:,['STMT_PERIOD_FROM_GROUPED', 'Counts']]
    #     plot_data[item].loc[:,"STMT_PERIOD_FROM_GROUPED"]=pd.to_datetime(plot_data[item].loc[:,"STMT_PERIOD_FROM_GROUPED"].astype(str))
    
    # floodedCats=plot_data[FLOOD_QUANTILES[0]]
    # for i in range(1,len(FLOOD_QUANTILES)):
    #     floodedCats=floodedCats.merge(plot_data[FLOOD_QUANTILES[i]],on='STMT_PERIOD_FROM_GROUPED',suffixes=FLOOD_QUANTILES[i-1:i+1])
    # floodedCats.columns=["Date"]+FLOOD_QUANTILES
    
    # #find dinominator population for computing rate
    # if Dis_cat=="ALL":
    #     population=df.loc[~df.duplicated("PAT_ADDR_CENSUS_TRACT"),:]
    #     population=population.groupby(["floodr"])[['Population']].sum()
    #     tmp=floodedCats.loc[:,FLOOD_QUANTILES]/population.T.iloc[0,:].to_numpy()
    #     floodedCats=pd.concat([floodedCats.Date,tmp],axis=1).reset_index().iloc[:,1:]
    
    # rate=floodedCats.sort_values(by='Date',ignore_index=True)
    # rate_avg=rate.copy()
    # rate_avg.iloc[:,1:]=rate_avg.iloc[:,1:].rolling(window=avg_window).mean()
    
#%% return for listner
    results_as_html = results.summary().tables[1].as_html()
    reg_table=pd.read_html(results_as_html, header=0, index_col=0)[0].reset_index()
    reg_table.loc[:,'coef']=np.exp(reg_table.coef)
    reg_table.loc[:,['[0.025', '0.975]']]=np.exp(reg_table.loc[:,['[0.025', '0.975]']])
    reg_table=reg_table.loc[~(reg_table['index'].str.contains('month') 
                              | reg_table['index'].str.contains('month')
                              | reg_table['index'].str.contains('weekday')
                              #| reg_table['index'].str.contains('year')
                              #| reg_table['index'].str.contains('PAT_AGE_YEARS')
                              
                              ),]
    reg_table_dev=pd.read_html(results.summary().tables[0].as_html())[0]
    
    counts_outcome=pd.DataFrame(df.Counts.value_counts())
    counts_outcome.loc["flood_bins",'Counts']=str(flood_bins)
    
    reg_table.to_csv(Dis_cat+"_reg"+".csv")
    reg_table_dev.to_csv(Dis_cat+"_dev"+".csv")
    counts_outcome.to_csv(Dis_cat+"_aux"+".csv")
    
    print(Dis_cat)
    print(counts_outcome)
    
    # inter_bars=pd.to_datetime( pd.Series(interv_dates,dtype='str'))
    # inter_bars=inter_bars.to_frame().merge(rate_avg,left_on=0,right_on='Date')
    # inter_bars.loc[:,'maxi']=inter_bars.loc[:,FLOOD_QUANTILES].max(axis=1).copy()
    
    # return reg_table.to_dict('r ecords'),[{"name": i, "id": i} for i in reg_table.columns],\
    #     reg_table_dev.to_dict('records'),[{"name": i, "id": i} for i in reg_table_dev.columns],\
    #     {'data': [{'x': rate_avg.Date,'y': rate_avg[cat],'name':cat} for cat in FLOOD_QUANTILES]+
    #     [{'x':inter_bars.Date,'y':inter_bars.maxi,'name':'intervention','type':'scatter','mode':'markers','marker':{'size':12}}],
    #     'layout': {'margin': {'l': 40, 'r': 0, 't': 20, 'b': 30}}},\
    #     'bin intervals:'+str(flood_bins)

#%% ip op dropdown
# @app.callback(Output('hidden-div', 'title'),[dash.dependencies.Input('ip-op','value')])
# def update_data(value):
#     global sp,sp_file
#     if sp_file!=value:
#         sp=pd.read_pickle(INPUT_IPOP_DIR+'\\'+value) 
#     sp_file=value
#     return None
    
     

# #%%run the server
# app.run_server(debug=False)







