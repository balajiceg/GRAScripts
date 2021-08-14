# @author Balaji Ramesh

#to merge the 3 different year ED visit files to single file
import pandas as pd
import os
import glob
import numpy as np

def seriesToTypes(series):
    try:
        series=series.astype("Int64")
    except (TypeError,ValueError):
        try:
            series=pd.to_numeric(series,downcast='unsigned')
        except (TypeError,ValueError): pass
            #series.loc[pd.isna(series)]=pd.NA
            # try:
            #     series=series.apply(lambda x: pd.NA if pd.isna(x) else str(x)).astype('string')
            #     series=series.astype('str')
            # except:
            #     pass
    return series

folder=r'\\vetmed2.vetmed.w2k.vt.edu\Blitzer\NASA project\Balaji\DSHS ED visit data\Dataset 3_13_2020'


IP_files = glob.glob(folder+'\\IP_*.{}'.format('txt'))
ip_df=pd.DataFrame()
for f in IP_files:
    df=pd.read_csv(f,sep='\t')
    df.loc[:,'file']=os.path.basename(f).split('.')[0]
    ip_df=pd.concat([ip_df,df])

ip_base_df=pd.read_csv(r"\\vetmed2.vetmed.w2pk.vt.edu\Blitzer\NASA project\Balaji\DSHS ED visit data\IP_2016_2018\IP_merged.txt",sep='\t')


OP_files = glob.glob(folder+'\\OP_*.{}'.format('txt'))
op_df=pd.DataFrame()
for f in OP_files:
    df=pd.read_csv(f,sep='\t')
    df.loc[:,'file']=os.path.basename(f).split('.')[0]
    op_df=pd.concat([op_df,df])
    
op_base_df=pd.read_csv(r"\\vetmed2.vetmed.w2k.vt.edu\Blitzer\NASA project\Balaji\DSHS ED visit data\OP_2016_2018\OP_merged.txt",sep='\t')


# count matchings
ip_df.RECORD_ID.isin(ip_base_df.RECORD_ID).value_counts()
op_df.RECORD_ID.isin(op_base_df.RECORD_ID).value_counts()

#count number of records with tract lvl lcode


#plot date
base_date=ip_base_df.loc[ip_base_df.ADMIT_START_OF_CARE>20160100,"ADMIT_START_OF_CARE"]
base_date=base_date.dropna().astype(int).astype(str)
base_date=pd.to_datetime(base_date)
bins=pd.to_datetime(['2016-01-01', '2016-03-31', '2016-06-30', '2016-09-30',
       '2016-12-31', '2017-03-31', '2017-06-30', '2017-09-30', '2017-12-31', 
       '2018-03-31', '2018-06-30', '2018-09-30', '2018-12-31'])
old=pd.cut(base_date,bins=bins).value_counts()


new_date=ip_df.loc[ip_df.STMT_PERIOD_FROM>20160100,"STMT_PERIOD_FROM"]
new_date=new_date.dropna().astype(int).astype(str)
new_date=pd.to_datetime(new_date)
bins=pd.to_datetime(['2016-01-01', '2016-03-31', '2016-06-30', '2016-09-30',
       '2016-12-31', '2017-03-31', '2017-06-30', '2017-09-30', '2017-12-31', 
       '2018-03-31', '2018-06-30', '2018-09-30', '2018-12-31'])
new=pd.cut(new_date,bins=bins).value_counts()

#merge the dataframes
#remove duplicates
ip_base_df_r=ip_base_df[~ip_base_df.duplicated()]
op_base_df_r=op_base_df[~op_base_df.duplicated()]


merged_ip=ip_base_df_r.merge(ip_df,on="RECORD_ID",how='left')
merged_op=op_base_df_r.merge(op_df,on="RECORD_ID",how='left')

#remove the filename column
merged_ip=merged_ip.drop(columns=['file',"FILE"])
merged_op=merged_op.drop(columns=['file',"FILE"])

#save the dataframes
merged_ip.to_csv(r"\\vetmed2.vetmed.w2k.vt.edu\Blitzer\NASA project\Balaji\DSHS ED visit data\CleanedMergedJoined\IP_JOINED.txt",sep="\t")
merged_op.to_csv(r"\\vetmed2.vetmed.w2k.vt.edu\Blitzer\NASA project\Balaji\DSHS ED visit data\CleanedMergedJoined\OP_JOINED.txt",sep="\t")


#turning it into binary
merged_ip=merged_ip.apply(seriesToTypes)
merged_op=merged_op.apply(seriesToTypes)


merged_ip.to_pickle(r"\\vetmed2.vetmed.w2k.vt.edu\Blitzer\NASA project\Balaji\DSHS ED visit data\CleanedMergedJoined\IP_JOINED.zip",compression='zip')
merged_op.to_pickle(r"\\vetmed2.vetmed.w2k.vt.edu\Blitzer\NASA project\Balaji\DSHS ED visit data\CleanedMergedJoined\OP_JOINED.zip",compression='zip')
