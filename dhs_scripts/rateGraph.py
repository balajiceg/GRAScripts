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

def get_sp_outcomes(sp,Dis_cat):
    global sp_outcomes
    return sp.merge(sp_outcomes.loc[:,['RECORD_ID','op',Dis_cat]],on=['RECORD_ID','op'],how='left')[Dis_cat].values

#%%read ip op data
INPUT_IPOP_DIR=r'Z:\Balaji\DSHS ED visit data\CleanedMergedJoined'
sp_file='ip_op'
sp=pd.read_pickle(INPUT_IPOP_DIR+'\\'+sp_file)
sp=sp.loc[:,['RECORD_ID','STMT_PERIOD_FROM','PAT_ADDR_CENSUS_BLOCK_GROUP','PAT_STATUS','op']]

#read flood data
flood_data=geopandas.read_file(r'Z:/Balaji/FloodRatioJoinedAll_v1/FloodInund_AllJoined_v1.gpkg')

#read op/ip outcomes df
sp_outcomes=pd.read_csv(INPUT_IPOP_DIR+'\\'+sp_file+'_outcomes.csv')

#read population
demos=pd.read_csv(r'Z:/Balaji/Census_data_texas/ACS_17_5YR_DP05_with_ann.csv',low_memory=False,skiprows=1)
demos.Id2=demos.Id2.astype("Int64")

flood_products=['DFO_R200','DFO_R100','LIST_R20','DFO_R20','DFOuLIST_R20']

#read counties that are innundated
county_to_filter=pd.read_csv('Z:/Balaji/counties_inun.csv').GEOID.to_list()
#%%predefine variable if got getting from gui
interven_date1,interven_date2=str(datetime(2017,8,25)),str(datetime(2017,9,13))
date_div=[{'props':{'date':i}} for i in [interven_date1,interven_date2]]
avg_window=7
flood_cats_in=1
floodr_use="DFO_R200"
nullAsZero="True"
floodZeroSep="True"
DATE_GROUP="DAILY"
Dis_cats=["ALL","DEATH"]
Dis_cat="ALL"
interv_dates=[20170825, 20170913, 20171014] #lower bound excluded
washout_period=[20170819,20170825] #including the dates specified
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

#remove washout period
sp= sp[~((sp.STMT_PERIOD_FROM >= washout_period[0]) & (sp.STMT_PERIOD_FROM <= washout_period[1]))]

#%%define app GUI

first_load=True
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash('Rate Graph',external_stylesheets=external_stylesheets)

app.layout = html.Div([
    dcc.Slider(min=0, max=3, marks={i: item for i,item in enumerate(["NO","FLood_1","FLOOD_2","FLOOD_3"])},
        value=flood_cats_in,id='my-slider'),
    dcc.RadioItems(id='ip-op',options=[{'label':i, 'value': i} for i in ['ip_op']],value=sp_file,labelStyle={'display': 'inline-block'},style={'display': 'inline'}),
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
    #interv_dates=[x['props']['date'] for x in date_div]
     
    #interv_dates=[int(datetime.strftime(parser.parse(test),"%Y%m%d")) for test in interv_dates]
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
    if Dis_cat in outcome_cats.category.to_list():df.loc[:,'Outcome']=get_sp_outcomes(sp,Dis_cat)
   
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
    

    #%% merge SVI after recategorization
        #read svi data
    SVI_df_raw=geopandas.read_file(r'Z:/Balaji/SVI_Raw/TEXAS.shp').drop('geometry',axis=1)
    SVI_df_raw.FIPS=pd.to_numeric(SVI_df_raw.FIPS)
    
    svi=recalculateSVI(SVI_df_raw[SVI_df_raw.FIPS.isin(grouped_tracts.PAT_ADDR_CENSUS_TRACT.unique())]).loc[:,["FIPS",'SVI']]
    grouped_tracts=grouped_tracts.merge(svi,left_on="PAT_ADDR_CENSUS_TRACT",right_on="FIPS",how='left').drop("FIPS",axis=1)
    grouped_tracts['SVI_Cat']=pd.cut(grouped_tracts.SVI,bins=np.arange(0,1.1,1/4),include_lowest=True,labels=['SVI_1','SVI_2','SVI_3','SVI_4'])
    #%%plot the rate graph
    param="SVI_Cat"
    QUANTILES=grouped_tracts[param].cat.categories.tolist()
    plot_data={}
    #Dis_cat='ALL'
    for item in QUANTILES:
        plot_data[item]=grouped_tracts.loc[grouped_tracts[param]==item,["STMT_PERIOD_FROM_GROUPED","Outcome","TotalVisits"]]
        plot_data[item]=plot_data[item].groupby(['STMT_PERIOD_FROM_GROUPED']).agg({'Outcome':'sum','TotalVisits':'sum'}).reset_index()
        
        if Dis_cat!="ALL":plot_data[item].loc[:,"Outcome"]=plot_data[item]["Outcome"]/plot_data[item]["TotalVisits"]
        
        plot_data[item]=plot_data[item].loc[:,['STMT_PERIOD_FROM_GROUPED', 'Outcome']]
        plot_data[item].loc[:,"STMT_PERIOD_FROM_GROUPED"]=pd.to_datetime(plot_data[item].loc[:,"STMT_PERIOD_FROM_GROUPED"].astype(str))
    

    floodedCats=plot_data[QUANTILES[0]]
    for i in range(1,len(QUANTILES)):
        floodedCats=floodedCats.merge(plot_data[QUANTILES[i]],on='STMT_PERIOD_FROM_GROUPED',suffixes=QUANTILES[i-1:i+1])
    floodedCats.columns=["Date"]+QUANTILES
    
    #find dinominator population for computing rate
    if Dis_cat=="ALL":
         #merge population
        demos_subset=demos.iloc[:,[1,3]]
        demos_subset.columns=["PAT_ADDR_CENSUS_TRACT","Population"]
        if 'Population' not in grouped_tracts.columns: grouped_tracts=grouped_tracts.merge(demos_subset,on="PAT_ADDR_CENSUS_TRACT",how='left')
        grouped_tracts=grouped_tracts.loc[grouped_tracts.Population>0,]
        
        population=grouped_tracts.loc[~grouped_tracts.duplicated("PAT_ADDR_CENSUS_TRACT"),:]
        population=population.groupby([param])[['Population']].sum()
        #per million
        tmp=(floodedCats.loc[:,QUANTILES]/population.T.iloc[0,:].to_numpy())*1e6
        floodedCats=pd.concat([floodedCats.Date,tmp],axis=1).reset_index().iloc[:,1:]
    
    rate=floodedCats.sort_values(by='Date',ignore_index=True)
    rate_avg=rate.copy()
    rate_avg.iloc[:,1:]=rate_avg.iloc[:,1:].rolling(window=avg_window).mean()

#%% stanalone plot
    rate_avg=rate_avg.dropna()
    
    interv_dates_cats=['control','flood','PostFlood1','PostFlood2']
    rate_avg.loc[:,'Time']=pd.cut(rate_avg.Date.dt.strftime('%Y%m%d').astype('int'),\
                                        bins=[0]+interv_dates+[20190101],\
                                        labels=[str(i) for i in interv_dates_cats]).cat.as_unordered()
    rate_avg.loc[rate_avg.Date.dt.strftime('%Y%m%d').astype('int')>20180100,'Time']="control"
        
    #create baseline variables
    for i in QUANTILES:
        rate_avg.loc[:,"base_"+str(i)]=rate_avg.loc[rate_avg.Time=='control',i].mean()
        for j in interv_dates_cats[1:]:
            rate_avg.loc[rate_avg.Time==j,"mean_"+str(i)]=rate_avg.loc[rate_avg.Time==j,i].mean()
            rate_avg.loc[rate_avg.Time==j,"diff_"+str(i)]=rate_avg.loc[rate_avg.Time==j,"mean_"+str(i)]-rate_avg.loc[rate_avg.Time==j,"base_"+str(i)]
    
    colors=['rgb(0,9,9)','rgb(8,48,107)', 'rgb(66,146,198)', 'rgb(158,202,225)'][:len(QUANTILES)]*3 # 3- mean,base,actual; 2-
    fig = px.line(rate_avg, x="Date", y=["mean_"+str(i) for i in QUANTILES], color_discrete_sequence=colors,line_dash_sequence=['dash'],template='plotly_white')
    fig=fig.add_traces(px.line(rate_avg, x="Date", y=["base_"+str(i) for i in QUANTILES], color_discrete_sequence=colors,line_dash_sequence=['dot']).data)
    fig=fig.add_traces(px.line(rate_avg, x="Date", y=[i for i in QUANTILES], color_discrete_sequence=colors,line_dash_sequence=['solid']).data)
    fig.update_layout(title_text=Dis_cat,title_font_size=16)
    fig.show()
    
    fig1= px.line(rate_avg, x="Date", y=["diff_"+str(i) for i in QUANTILES], color_discrete_sequence=colors,template='plotly_white')
    fig1.update_layout(title_text=Dis_cat,title_font_size=16)
    fig1.show()
    
#%% return for listner    
   
    # inter_bars=pd.to_datetime( pd.Series(interv_dates,dtype='str'))
    # inter_bars=inter_bars.to_frame().merge(rate_avg,left_on=0,right_on='Date')
    # inter_bars.loc[:,'maxi']=inter_bars.loc[:,QUANTILES].max(axis=1).copy()
    
    # # return reg_table.to_dict('r ecords'),[{"name": i, "id": i} for i in reg_table.columns],\
    # #     reg_table_dev.to_dict('records'),[{"name": i, "id": i} for i in reg_table_dev.columns],\
    # #     {'data': [{'x': rate_avg.Date,'y': rate_avg[cat],'name':cat} for cat in QUANTILES]+
    # #     [{'x':inter_bars.Date,'y':inter_bars.maxi,'name':'intervention','type':'scatter','mode':'markers','marker':{'size':12}}],
    # #     'layout': {'margin': {'l': 40, 'r': 0, 't': 20, 'b': 30}}},\
    # #     'bin intervals:'+str(flood_bins)
        
    # return None,None,None,None,\
    #     {'data': [{'x': rate_avg.Date,'y': rate_avg[cat],'name':cat} for cat in QUANTILES]+
    #     [{'x':inter_bars.Date,'y':inter_bars.maxi,'name':'intervention','type':'scatter','mode':'markers','marker':{'size':12}}],
    #     'layout': {'margin': {'l': 40, 'r': 0, 't': 20, 'b': 30}}},\
    #     'bin intervals:'+str(flood_bins)
    
    #%%
    inter_bars=pd.to_datetime( pd.Series(interv_dates,dtype='str'))
    inter_bars=inter_bars.to_frame().merge(rate_avg,left_on=0,right_on='Date')
    inter_bars.loc[:,'maxi']=inter_bars.loc[:,QUANTILES].max(axis=1).copy()
    
    # return reg_table.to_dict('r ecords'),[{"name": i, "id": i} for i in reg_table.columns],\
    #     reg_table_dev.to_dict('records'),[{"name": i, "id": i} for i in reg_table_dev.columns],\
    #     {'data': [{'x': rate_avg.Date,'y': rate_avg[cat],'name':cat} for cat in QUANTILES]+
    #     [{'x':inter_bars.Date,'y':inter_bars.maxi,'name':'intervention','type':'scatter','mode':'markers','marker':{'size':12}}],
    #     'layout': {'margin': {'l': 40, 'r': 0, 't': 20, 'b': 30}}},\
    #     'bin intervals:'+str(flood_bins)
        
    return None,None,None,None,\
        {'data': [{'x': rate_avg.Date,'y': rate_avg[cat],'name':cat} for cat in QUANTILES]+
        [{'x':inter_bars.Date,'y':inter_bars.maxi,'name':'intervention','type':'scatter','mode':'markers','marker':{'size':12}}],
        'layout': {'margin': {'l': 40, 'r': 0, 't': 20, 'b': 30},'title':Dis_cat,'yaxis':{'title':'Outcome per 1Million'}}},\
        'bin intervals:'+str(flood_bins)
        
# %% ip op dropdown
@app.callback(Output('hidden-div', 'title'),[dash.dependencies.Input('ip-op','value')])
def update_data(value):
    global sp,sp_file
    if sp_file!=value:
        sp=pd.read_pickle(INPUT_IPOP_DIR+'\\'+value) 
        sp=sp.loc[:,['RECORD_ID','STMT_PERIOD_FROM','PAT_ADDR_CENSUS_BLOCK_GROUP','PAT_STATUS']]
        sp.loc[:,'PAT_ADDR_CENSUS_TRACT']=(sp.PAT_ADDR_CENSUS_BLOCK_GROUP//10)
        sp=sp[(sp.PAT_ADDR_CENSUS_TRACT//1000000).isin(county_to_filter)].copy()
    sp_file=value
    return None
    
     

# #%%run the server
app.run_server(debug=False)







