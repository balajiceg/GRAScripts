# -*- coding: utf-8 -*-
"""
Created on Thu Jun 11 16:34:26 2020

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
import sys
sys.path.insert(1, r'Z:\GRAScripts\dhs_scripts')
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

def filter_from_icds_1(sp,outcome_cats,Dis_cat):
    icd_cols=['PRINC_DIAG_CODE', 'OTH_DIAG_CODE_1', 'OTH_DIAG_CODE_2',
       'OTH_DIAG_CODE_3', 'OTH_DIAG_CODE_4', 'OTH_DIAG_CODE_5',
       'OTH_DIAG_CODE_6', 'OTH_DIAG_CODE_7', 'OTH_DIAG_CODE_8',
       'OTH_DIAG_CODE_9', 'E_CODE_1', 'E_CODE_2', 'E_CODE_3', 'E_CODE_4',
       'E_CODE_5']
    incl=outcome_cats.loc[outcome_cats.category==Dis_cat,'incl']
    excl=outcome_cats.loc[outcome_cats.category==Dis_cat,'excl']
    
    incl=pd.Series(incl.to_list()[0].split(';'))
    excl=pd.Series(excl.to_list()[0].split(';'))
    
    #form the searh string
    search_text=sp[icd_cols[0]].astype('str')
    for i in icd_cols[1:]:
        search_text=search_text.str.cat(sp[i].astype('str'),sep=';')
    search_text=(';'+search_text+';').str.replace('nan;','')
    
    #apply regex for inclu code
    incl_bool=incl.apply(lambda x:search_text.str.match(r'.*;'+x+'[^;]*;',case=False)).any()
    result=incl_bool
    
    if excl.to_list()!=['']:
        excl_bool=excl.apply(lambda x:search_text.str.match(r'.*;'+x+'[^;]*;',case=False)).any()
        result= incl_bool & (~excl_bool)
        
    return result
    
    

#%%read ip op data
INPUT_IPOP_DIR=r'Z:\Balaji\DSHS ED visit data\CleanedMergedJoined'
sp_file='ip'
sp=pd.read_pickle(INPUT_IPOP_DIR+'\\'+sp_file)
#sp=pd.read_pickle(INPUT_IPOP_DIR+r'\op')
flood_data=geopandas.read_file(r'Z:/Balaji/FloodRatioJoinedAll_v1/FloodInund_AllJoined_v1.gpkg')


#read population
demos=pd.read_csv(r'Z:/Balaji/Census_data_texas/ACS_17_5YR_DP05_with_ann.csv',low_memory=False,skiprows=1)
demos.Id2=demos.Id2.astype("Int64")

flood_products=['DFO_R200','DFO_R100','LIST_R20','DFO_R20','DFOuLIST_R20']

#read counties that are innundated
county_to_filter=pd.read_csv('Z:/Balaji/counties_inun.csv').GEOID.to_list()
#%%predefine variable if got getting from gui
interven_date1,interven_date2=str(datetime(2017,8,25)),str(datetime(2017,9,13))
date_div=[{'props':{'date':i}} for i in [interven_date1,interven_date2]]
avg_window=3
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

#%%create tract id from block group id
sp.loc[:,'PAT_ADDR_CENSUS_TRACT']=(sp.PAT_ADDR_CENSUS_BLOCK_GROUP//10)
    
#%%filter counties
if county_to_filter != -1:
    sp=sp[(sp.PAT_ADDR_CENSUS_TRACT//1000000).isin(county_to_filter)].copy()

#%%keep only the required fields and dates
sp=sp.loc[(~pd.isna(sp.STMT_PERIOD_FROM))&(~pd.isna(sp.PAT_ADDR_CENSUS_BLOCK_GROUP))] 

sp=sp[((sp.STMT_PERIOD_FROM > 20160700) & (sp.STMT_PERIOD_FROM< 20161232))\
    | ((sp.STMT_PERIOD_FROM > 20170400) & (sp.STMT_PERIOD_FROM< 20171232))\
        | ((sp.STMT_PERIOD_FROM > 20180700) & (sp.STMT_PERIOD_FROM< 20181232))]
#%%define app GUI

first_load=True
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash('Rate Graph',external_stylesheets=external_stylesheets)

app.layout = html.Div([
    dcc.Slider(min=0, max=3, marks={i: item for i,item in enumerate(["NO","FLood_1","FLOOD_2","FLOOD_3"])},
        value=flood_cats_in,id='my-slider'),
    dcc.RadioItems(id='ip-op',options=[{'label':i, 'value': i} for i in ['ip','op']],value=sp_file,labelStyle={'display': 'inline-block'},style={'display': 'inline'}),
    dcc.Loading(children=html.Div(id='hidden-div', style={'display':'none'})),
    dcc.Input(id="avg_window",type="number",placeholder="avg window",value=avg_window,style={'display':'inline'}),
    dcc.Dropdown(id='floodr_use',options=[{'label':i, 'value': i} for i in flood_products],value=floodr_use),
    html.Div(id="flood_bins"),
    dcc.Dropdown(id="group_date",options=[{'label':i, 'value': i} for i in ["DAILY","WEEKLY","MONTHLY"]],value=DATE_GROUP),
    dcc.Dropdown(id="Dis_cat",options=[{'label':i, 'value': i} for i in Dis_cats+outcome_cats.category.to_list()],value=Dis_cat),
    dcc.RadioItems(id='nullAsZero',options=[{'label':i, 'value': i} for i in ['True','False']],value=nullAsZero,style={'display':'inline'},labelStyle={'display': 'inline-block'}),html.I(children=" nullAsZero"),html.Br(),
    dcc.RadioItems(id='floodZeroSep',options=[{'label':i, 'value': i} for i in ['True','False']],value=floodZeroSep ,style={'display':'inline'},labelStyle={'display': 'inline-block'}),html.I(children=" floodZeroSep"),html.Br(),
    
    dcc.Input(id="n_interv",type="number",value=2,style={'display':'inline','width':'50px'}),
    html.Div(id="dates",style={'display':'inline'},children=[dcc.DatePickerSingle(date=interven_date1,id='date0'),dcc.DatePickerSingle(date=interven_date2,id='date1')]),
    
    html.Button('Run', id='button'),
    dcc.Loading(children=[dcc.Graph(id='my-graph'),dash_table.DataTable(id='reg_table',columns='',data=''),html.Hr(),
                          dash_table.DataTable(id='reg_table_dev',columns='',data='')])
    
], style={'width': '500'})


# app.run_server()
#%%
@app.callback(Output("dates", "children"),[Input("n_interv", "value")])
def update_dates(value):
    return [dcc.DatePickerSingle(id='date'+str(i),date=interven_date1) for i in range(value)]

@app.callback(
    [Output('reg_table', 'data'),Output('reg_table','columns'),
      Output('reg_table_dev', 'data'),Output('reg_table_dev','columns'),
      Output('my-graph', 'figure'),Output('flood_bins','children')],
    [dash.dependencies.Input('button', 'n_clicks')],
    [dash.dependencies.State('my-slider', 'value'),dash.dependencies.State('avg_window', 'value'),
      dash.dependencies.State('nullAsZero','value'),dash.dependencies.State('floodZeroSep','value'),
      dash.dependencies.State('floodr_use','value'),
      dash.dependencies.State('Dis_cat','value'),
      dash.dependencies.State('dates','children'),dash.dependencies.State('group_date','value')])

def update_output(n_clicks, flood_cats_in,avg_window,nullAsZero,floodZeroSep,floodr_use,Dis_cat,date_div,DATE_GROUP):
    global sp,flood_data,demos,first_load,outcome_cats,county_to_filter
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
   
    #%%splitting into all and specific
    #df_all=sp_filtered.loc[:,['STMT_PERIOD_FROM_GROUPED','PAT_ADDR_CENSUS_TRACT','PAT_AGE_YEARS','SEX_CODE','RACE']].copy()
    
    df=sp.loc[:,['STMT_PERIOD_FROM_GROUPED','PAT_ADDR_CENSUS_TRACT']]
    
    if Dis_cat=="DEATH":df.loc[:,'Outcome']=filter_mortality(sp)
    if Dis_cat=="ALL":df.loc[:,'Outcome']=1
    if Dis_cat in outcome_cats.category.to_list():df.loc[:,'Outcome']=filter_from_icds(sp,outcome_cats,Dis_cat)
   
    #%% run grouping for dinominator and join them
    grouped_tracts_all=df.groupby(['STMT_PERIOD_FROM_GROUPED', 'PAT_ADDR_CENSUS_TRACT']).size().reset_index()
    grouped_tracts_all.columns=[*grouped_tracts_all.columns[:-1], 'TotalVisits']
    
    grouped_tracts=df.groupby(['STMT_PERIOD_FROM_GROUPED', 'PAT_ADDR_CENSUS_TRACT']).sum().reset_index()
    
    grouped_tracts=grouped_tracts.merge(grouped_tracts_all,on=['STMT_PERIOD_FROM_GROUPED', 'PAT_ADDR_CENSUS_TRACT'],how='left')
    
    #filter only >0 tracts
    grouped_tracts=grouped_tracts.loc[grouped_tracts.TotalVisits>0,:]
    del df
    
     #%% merege flood data
    grouped_tracts=grouped_tracts.merge(floodr,left_on="PAT_ADDR_CENSUS_TRACT",right_on='GEOID',how='left')
    #make tracts with null as zero flooding
    if nullAsZero == "True": grouped_tracts.loc[pd.isna(grouped_tracts.floodr),'floodr']=0.0

    
    tractsfloodr=grouped_tracts.loc[~grouped_tracts.duplicated("PAT_ADDR_CENSUS_TRACT"),['PAT_ADDR_CENSUS_TRACT','floodr']]
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
    grouped_tracts.loc[:,'floodr']=pd.cut(grouped_tracts.floodr,bins=flood_bins,right=True,include_lowest=True,labels=FLOOD_QUANTILES)
    grouped_tracts=grouped_tracts.drop("GEOID",axis=1)
    
    
    
    #%%plot the rate graph
    plot_data={}
    Dis_cat='ALL'
    for item in FLOOD_QUANTILES:
        plot_data[item]=grouped_tracts.loc[grouped_tracts.floodr==item,["STMT_PERIOD_FROM_GROUPED","Outcome","TotalVisits"]]
        plot_data[item]=plot_data[item].groupby(['STMT_PERIOD_FROM_GROUPED']).agg({'Outcome':'sum','TotalVisits':'sum'}).reset_index()
        
        if Dis_cat!="ALL":plot_data[item]["Outcome"]=plot_data[item]["Outcome"]/plot_data[item]["TotalVisits"]
        
        plot_data[item]=plot_data[item].loc[:,['STMT_PERIOD_FROM_GROUPED', 'Outcome']]
        plot_data[item].loc[:,"STMT_PERIOD_FROM_GROUPED"]=pd.to_datetime(plot_data[item].loc[:,"STMT_PERIOD_FROM_GROUPED"].astype(str))
    

    floodedCats=plot_data[FLOOD_QUANTILES[0]]
    for i in range(1,len(FLOOD_QUANTILES)):
        floodedCats=floodedCats.merge(plot_data[FLOOD_QUANTILES[i]],on='STMT_PERIOD_FROM_GROUPED',suffixes=FLOOD_QUANTILES[i-1:i+1])
    floodedCats.columns=["Date"]+FLOOD_QUANTILES
    
    #find dinominator population for computing rate
    if Dis_cat=="ALL":
         #merge population
        demos_subset=demos.iloc[:,[1,3]]
        demos_subset.columns=["PAT_ADDR_CENSUS_TRACT","Population"]
        grouped_tracts=grouped_tracts.merge(demos_subset,on="PAT_ADDR_CENSUS_TRACT",how='left')
        grouped_tracts=grouped_tracts.loc[grouped_tracts.Population>0,]
        
        population=grouped_tracts.loc[~grouped_tracts.duplicated("PAT_ADDR_CENSUS_TRACT"),:]
        population=population.groupby(["floodr"])[['Population']].sum()
        #per million
        tmp=(floodedCats.loc[:,FLOOD_QUANTILES]/population.T.iloc[0,:].to_numpy())*1e6
        floodedCats=pd.concat([floodedCats.Date,tmp],axis=1).reset_index().iloc[:,1:]
    
    rate=floodedCats.sort_values(by='Date',ignore_index=True)
    rate_avg=rate.copy()
    rate_avg.iloc[:,1:]=rate_avg.iloc[:,1:].rolling(window=avg_window).mean()
    
#%% return for listner    
   
    # inter_bars=pd.to_datetime( pd.Series(interv_dates,dtype='str'))
    # inter_bars=inter_bars.to_frame().merge(rate_avg,left_on=0,right_on='Date')
    # inter_bars.loc[:,'maxi']=inter_bars.loc[:,FLOOD_QUANTILES].max(axis=1).copy()
    
    # # return reg_table.to_dict('r ecords'),[{"name": i, "id": i} for i in reg_table.columns],\
    # #     reg_table_dev.to_dict('records'),[{"name": i, "id": i} for i in reg_table_dev.columns],\
    # #     {'data': [{'x': rate_avg.Date,'y': rate_avg[cat],'name':cat} for cat in FLOOD_QUANTILES]+
    # #     [{'x':inter_bars.Date,'y':inter_bars.maxi,'name':'intervention','type':'scatter','mode':'markers','marker':{'size':12}}],
    # #     'layout': {'margin': {'l': 40, 'r': 0, 't': 20, 'b': 30}}},\
    # #     'bin intervals:'+str(flood_bins)
        
    # return None,None,None,None,\
    #     {'data': [{'x': rate_avg.Date,'y': rate_avg[cat],'name':cat} for cat in FLOOD_QUANTILES]+
    #     [{'x':inter_bars.Date,'y':inter_bars.maxi,'name':'intervention','type':'scatter','mode':'markers','marker':{'size':12}}],
    #     'layout': {'margin': {'l': 40, 'r': 0, 't': 20, 'b': 30}}},\
    #     'bin intervals:'+str(flood_bins)
    
    #%%
    inter_bars=pd.to_datetime( pd.Series(interv_dates,dtype='str'))
    inter_bars=inter_bars.to_frame().merge(rate_avg,left_on=0,right_on='Date')
    inter_bars.loc[:,'maxi']=inter_bars.loc[:,FLOOD_QUANTILES].max(axis=1).copy()
    
    # return reg_table.to_dict('r ecords'),[{"name": i, "id": i} for i in reg_table.columns],\
    #     reg_table_dev.to_dict('records'),[{"name": i, "id": i} for i in reg_table_dev.columns],\
    #     {'data': [{'x': rate_avg.Date,'y': rate_avg[cat],'name':cat} for cat in FLOOD_QUANTILES]+
    #     [{'x':inter_bars.Date,'y':inter_bars.maxi,'name':'intervention','type':'scatter','mode':'markers','marker':{'size':12}}],
    #     'layout': {'margin': {'l': 40, 'r': 0, 't': 20, 'b': 30}}},\
    #     'bin intervals:'+str(flood_bins)
        
    return None,None,None,None,\
        {'data': [{'x': rate_avg.Date,'y': rate_avg[cat],'name':cat} for cat in FLOOD_QUANTILES]+
        [{'x':inter_bars.Date,'y':inter_bars.maxi,'name':'intervention','type':'scatter','mode':'markers','marker':{'size':12}}],
        'layout': {'margin': {'l': 40, 'r': 0, 't': 20, 'b': 30},'yaxis':{'title':'Outcome per 1Million'}}},\
        'bin intervals:'+str(flood_bins)
        
# %% ip op dropdown
@app.callback(Output('hidden-div', 'title'),[dash.dependencies.Input('ip-op','value')])
def update_data(value):
    global sp,sp_file
    if sp_file!=value:
        sp=pd.read_pickle(INPUT_IPOP_DIR+'\\'+value) 
        sp.loc[:,'PAT_ADDR_CENSUS_TRACT']=(sp.PAT_ADDR_CENSUS_BLOCK_GROUP//10)
        sp=sp[(sp.PAT_ADDR_CENSUS_TRACT//1000000).isin(county_to_filter)].copy()
    sp_file=value
    return None
    
     

# #%%run the server
app.run_server(debug=False)







