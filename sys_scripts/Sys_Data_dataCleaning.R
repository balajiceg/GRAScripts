## ----Load packages, message=FALSE-----------------------------------
library(GISTools)
library(rgdal)
library(dplyr)
library(plotly)
library(zoo)
#library(zipcodeR)
library(ggplot2)
library(sf)
library(readxl)
library(plyr)
library(knitr)
library(hrbrthemes)


## ----echo=FALSE-----------------------------------------------------
#data("zip_code_db")
#zipcode and state
#zip_st<-zip_code_db[,c('zipcode','state')]

#tropical strom imelda http://floodobservatory.colorado.edu/Events/4797/2019USA4797.html


## -------------------------------------------------------------------
sys_raw<-read.csv("Z:\\Balaji\\SyS data\\merged_with_rowid.csv")
#remove the text diagnosits fields
sys_raw<-subset(sys_raw,select=-c(ChiefComplaintOrig,Discharge.Diagnosis,ProviderDiagnosis))
recs_raw<-dim(sys_raw)[1]


## -------------------------------------------------------------------
zip_zcta_crosswalk<-read_excel('Z:\\Balaji\\Census_data_texas\\Crosswalk\\Zip_to_zcta_crosswalk_2020.xlsx')
sys_raw$zip_5c<-substr(sys_raw$Zipcode,1,5)
sys_raw<-merge(sys_raw, zip_zcta_crosswalk[,c('ZIP_CODE','ZCTA')],by.x='zip_5c',by.y='ZIP_CODE',all.y=F,all.x=T)
colnames(sys_raw)[colnames(sys_raw)=='ZCTA']<-'crossed_zcta'


## ----echo=FALSE-----------------------------------------------------
####  Find the how many records in how many states
# sys_raw<-merge(sys_raw,zip_st,by.x='zip_5c',by.y='zipcode',all.y=FALSE,all.x=TRUE)
# a<-data.frame(table(sys_raw$state))
#98.86% records from TX, 0.3% from LA


## ----echo=False-----------------------------------------------------
####  Map of tracts and ed counts using both direct and crosswalk ----
# zctas_all<-readOGR(dsn='Z:\\Balaji\\Census_data_texas\\tl_2019_us_zcta510',layer = 'tl_2019_us_zcta510')
# #counts as per mapped zctas
# counts_df_zcta<-sys_raw %>% group_by(crossed_zcta) %>% summarise(count_zcta=n())
# #counts as per directs zips
# counts_df_zips<-sys_raw %>% group_by(zip_5c) %>% summarise(count_zips=n())
#
# #merge counts to zctas shp
# zctas_all_merg<-merge(zctas_all,counts_df_zcta,by.x='ZCTA5CE10', by.y='crossed_zcta',all.x=T )
# zctas_all_merg<-merge(zctas_all_merg,counts_df_zips,by.x='ZCTA5CE10', by.y='zip_5c',all.x=T)
#
# #drop the unused boundries
# zctas_all_merg<-zctas_all_merg[((!is.na(zctas_all_merg$count_zcta)) | (!is.na(zctas_all_merg$count_zips))),]
#
# #extract texass alone
# texas_bound<-readOGR(dsn="Z:\\Balaji\\Census_data_texas\\texas_boundry_extrc_census",layer = 'texas_bound_census')
# intersections<-st_intersects(st_as_sf(zctas_all_merg),st_as_sf(texas_bound))
# zctas_txla<-zctas_all_merg[as.logical(unlist(lapply(intersections,length))),]
#
# #subset boundries with ed counts > 10
# zctas_txla<-subset(zctas_txla,count_zcta>10)
# #calcuate diff between direct zip code linking and through croww walk
# zctas_txla$DIFF<-zctas_txla$count_zcta - zctas_txla$count_zips
# mapView(zctas_txla,zcol='DIFF')
#


## -------------------------------------------------------------------
#zctas_all<-readOGR(dsn='Z:\\Balaji\\Census_data_texas\\tl_2019_us_zcta510',layer = 'tl_2019_us_zcta510')
#texas_bound<-readOGR(dsn="Z:\\Balaji\\Census_data_texas\\texas_boundry_extrc_census",layer = 'texas_bound_census')
#check intersection
#intersections<-st_intersects(st_as_sf(zctas_all),st_as_sf(texas_bound))
#zctas_txla<-zctas_all$ZCTA5CE10[as.logical(unlist(lapply(intersections,length)))]
#write this to file so as not to repeat
#write.csv(zctas_txla,"Z:\\Balaji\\Census_data_texas\\Zctas_in_texas_list\\zctzs_texas.csv",row.names = F)
zctas_txla<-as.list(read.csv("Z:\\Balaji\\Census_data_texas\\Zctas_in_texas_list\\zctzs_texas.csv"))[[1]]



## ----warning=FALSE--------------------------------------------------
# read and plot percentiles of flood ratio
inun_zcta<-readOGR(dsn='Z:\\Balaji\\FloodInun_zcta_imelda_v2',layer = 'FloodInun_zcta_imelda')
spplot(inun_zcta,zcol='ZCT_f_R')
#round off to 3 decimal points
#inun_zcta@data$ZCT_f_R<-round(inun_zcta@data$ZCT_f_R,3)
#plot
plot(seq(0,1,by=0.1),quantile(inun_zcta$ZCT_f_R,seq(0,1,by=0.1)),type='b',ylab='flood Ratio',xlab='percentile')
axis(side=1, at=seq(0,1,by=0.1))


## -------------------------------------------------------------------
sys_sa<-sys_raw[sys_raw$crossed_zcta %in% zctas_txla ,]
sys_sa$Date<-as.Date(sys_sa$Date, format= "%m/%d/%Y")
sys_sa<-sys_sa[sys_sa$Date > '2018-12-31',]
recs_tx<-dim(sys_sa)[1]


## -------------------------------------------------------------------
sys_sa<-merge(sys_sa, inun_zcta@data[,c('ZCTA5CE10','ZCT_f_R')], by.x='crossed_zcta', by.y='ZCTA5CE10', all.x=TRUE)
#filter records in study arean -
sys_sa<-sys_sa[!is.na(sys_sa$ZCT_f_R),]
recs_sa<-dim(sys_sa)[1]


## -------------------------------------------------------------------
#Age - merge O and U to unknownRa
sys_sa$Sex [!(sys_sa$Sex %in% c('M','F'))] <- 'Unknown'
sys_sa$Sex <- factor(sys_sa$Sex, levels = c("M","F",'Unknown'))

#Ethnicity
sys_sa$Ethnicity[sys_sa$Ethnicity %in% c("1", "2135-2","2161-8", "2178-2")]<- "HISPANIC"  #hispanic or latino code to hispanic
sys_sa$Ethnicity[sys_sa$Ethnicity %in% c("2","2186-5")]<- "NON HISPANIC"   #not hispanic or latino code to non hispanic
# Unknown -> 1, 2, 2161-8 (Salvadoran)(only 3recs), 2178-2 (Latin American)(only3 recs), 3, 4, 48039, 48201, ASKU, NR, Refused, UNK
sys_sa$Ethnicity[sys_sa$Ethnicity %in% c("3", "4","48039","48201","ASKU", "NR", "Refused", "UNK")]<- 'Unknown'
sys_sa$Ethnicity<-factor(sys_sa$Ethnicity,levels = c("NON HISPANIC", "HISPANIC", "Unknown"))

#Race
sys_sa$Race[sys_sa$Race %in% c( "1002-5", "American Indian or Alaska Native", "AMIN" )] <- "American Indian"
sys_sa$Race[sys_sa$Race %in% c( "Asian", "2028-9","A","AI" )] <- "Asian"
sys_sa$Race[sys_sa$Race %in% c( "2054-5", "B", "Black or African American" )] <- "Black"
sys_sa$Race[sys_sa$Race %in% c( "2106-3", "White", "W" )] <- "White"
sys_sa$Race[sys_sa$Race %in% c( "2076-8", "2079-2", "Native Hawaiian or Other Pacific Islander", "H", "Hawaiian", "T" )] <- "Hawaiian"
sys_sa$Race[sys_sa$Race %in% c( "2118-8", "2129-5", "2131-1", "Other", "Other Race" )] <- "Others"
sys_sa$Race[sys_sa$Race %in% c( "ASKU",  "DECLINED",  "M",  "NR", "O", "UNK",  "X" )] <- "Unknown"
sys_sa$Race<-factor(sys_sa$Race,levels = c("White","Black","Asian","American Indian","Hawaiian","Others","Unknown"))
summary(sys_sa[,c('Sex','Ethnicity','Race')])



## -------------------------------------------------------------------
sys_sa$weekday<-as.factor(weekdays(sys_sa$Date,abbreviate=T))
sys_sa$month<-as.factor(months(sys_sa$Date,abbreviate = T))
sys_sa$day<-as.factor(format(sys_sa$Date, "%d"))


## -------------------------------------------------------------------

ZCTAdaily_count<-sys_sa %>% group_by(crossed_zcta,Date) %>% dplyr::summarise(ZCTAdaily_count=n())
sys_sa<-merge(sys_sa,ZCTAdaily_count,by=c('crossed_zcta','Date'),all.x=T)


# ## -------------------------------------------------------------------
outcome_match<-read.csv("Z:\\Balaji\\SyS data\\sys_merged_outcomes.csv")
outcomes_all<-c('Pregnancy_complic', 'Asthma', 'Bite.Insect',
                'Dehydration', 'Drowning', 'Hypothermia', 'Chest_pain',
                'Heat_Related_But_Not_dehydration',
                'CO_Exposure','Diarrhea','RespiratorySyndrome','CardiovascularDiseases')
sys_sa<-merge(sys_sa,outcome_match[,c('row_id',outcomes_all)],all.x=T,by='row_id')

#creat a collective column
sys_sa$outcomes_any<-sys_sa[,outcomes_all] %>% apply(1,FUN=any)

#remove duplicate dfs
remove(sys_raw)
remove(outcome_match)
remove(ZCTAdaily_count)
remove(zip_zcta_crosswalk)
#make a copy of sys_sa
sys_sa_bkp<-sys_sa
remove(sys_sa)


## ---- message=FALSE-------------------------------------------------
library(GISTools)
library(rgdal)
library(dplyr)
library(plotly)
library(zoo)
#library(zipcodeR)
library(ggplot2)
library(sf)
library(readxl)
library(plyr)
library(knitr)
library(hrbrthemes)
library(stringr)
#configure reticulate
library(reticulate)
reticulate::use_condaenv(conda='C:\\Users\\balajiramesh\\Anaconda3\\condabin\\conda.bat',required = T,condaenv = 'r-reticulate')


## -------------------------------------------------------------------
sys_sa<-subset(sys_sa_bkp,select=-c(zip_5c, Time, Zipcode, HospitalName, HospitalZipCode))

#reduce race categories [combine American Indian and Hawaiian into others]
sys_sa$Race<-recode(sys_sa$Race,`American Indian`='Others',Hawaiian='Others',Asian='Others')
#remove incomplete recs
sys_sa<-sys_sa[complete.cases(sys_sa),]
#check if all columns are cmplete
#colSums(is.na(sys_sa))
"incomplet records = 3751"; 
#remove unknown sex records
sys_sa<-sys_sa[sys_sa$Sex!='Unknown',]
sys_sa$Sex<-droplevels(sys_sa$Sex)
"unknown sex records 681"



## -------------------------------------------------------------------
sys_sa$flooded <- cut(sys_sa$ZCT_f_R,c(0,quantile(inun_zcta$ZCT_f_R[inun_zcta$ZCT_f_R>0],
                      probs = seq(0,1,1/2))),include.lowest = T,right = F)
labels <- c('Non flooded','Moderately flooded','Highly flooded')
"Categories and intervals and ZCTA counts :";labels;table(sys_sa$flooded[!duplicated(sys_sa$crossed_zcta)])
levels(sys_sa$flooded)<-labels

"Records in each category"
table(sys_sa$flooded)



## -------------------------------------------------------------------
sys_sa$period<-'controlPeriod'
sys_sa$period[sys_sa$Date>='2019-09-12' & sys_sa$Date<='2019-09-18'] <-'washoutPeriod'
sys_sa$period[sys_sa$Date>='2019-09-19' & sys_sa$Date<='2019-10-01'] <-'floodPeriod'
sys_sa$period[sys_sa$Date>='2019-10-02' & sys_sa$Date<='2019-11-01'] <-'monthAfterFlood'
sys_sa$period[sys_sa$Date>='2019-11-02' & sys_sa$Date<='2019-12-31'] <-'novAndDec'

table(sys_sa$period)
#remove washout period
sys_sa<-subset(sys_sa,period!='washoutPeriod')

#sys_sa$period[sys_sa$Date<='2019-07-11'] <-'x_july_flood'
sys_sa$period<-factor(sys_sa$period)
levels(sys_sa$period)

## ----write output for python code ----
save(sys_sa,file = "Z:/Balaji/R session_home_dir/sys_sa_df.RData")

## -------------------------------------------------------------------
#merge flooded categories
sys_sa$flooded[sys_sa$flooded=='highly flooded']<-'moderately flooded'
sys_sa$flooded<-droplevels(sys_sa$flooded)
levels(sys_sa$flooded)[2]<-'flooded'

library(dlnm)
sys_sa_bkp<-sys_sa
## -------------------------------------------------------------------
for (nk in c(1,2,3,4,5,6)){
    
sys_sa<-sys_sa_bkp
#library(dlnm)
#order the df by date
sys_sa<-sys_sa[order(sys_sa$Date),]
#create date and expoure
lag_df<-sys_sa[!duplicated(sys_sa$Date),c('Date','period')]
lag_df<-lag_df[order(lag_df$Date),]
row.names(lag_df) <- NULL
#define the peiod of exposure
lag_df$period[lag_df$Date>'2019-10-01']<-'monthAfterFlood'
lag_df$period<-droplevels(lag_df$period)
levels(lag_df$period)<-c(0,1,0)
#run cross basis
cb<-crossbasis(lag_df$period,lag=13,argvar=list(fun="strata",breaks=c(1)),
    #arglag=list(fun='integer'))
  arglag=list(knots=logknots(13,nk=nk)))
  #arglag=list(fun='strata',breaks=breaks))

#fill na with 0
cb[is.na(cb)]<-0


#bind date to the lag df and drop the binary exposure and keep lag
lag_df<-cbind(lag_df,cb)

#take only need lag columns
# req_cols<-paste0('l',seq(1,91,by = 7))
# #take only need lag columns
# lag_df<-lag_df[,c(T,matrix(unlist(strsplit(colnames(lag_df),'\\.')),nrow=2)[2,] %in% req_cols)]
# #reset cb's attributes
# attr(cb,"arglag")$values<-as.integer(gsub('l','',req_cols))-1


lag_df<-subset(lag_df,select=-period)
#merge this back to df
sys_sa<-merge(sys_sa,lag_df,by='Date',all.x=T)

#exptract the lag _df seperately
lag_df_all<-sys_sa[,colnames(lag_df)[colnames(lag_df)!='Date']]
#set expsoure variable to 0 for non flooded tracts? 
#lag_df_all[sys_sa$flooded=='Non flooded',]<-0
#make the lag df into cross basis object
lag_df_all<-as.matrix(lag_df_all)
class(lag_df_all) <- c("crossbasis","matrix")
for(i in c('arglag','df',"range","lag","argvar")){
attr(lag_df_all,i)<-attr(cb,i)
}

lag_cols<-colnames(lag_df)[colnames(lag_df)!='Date']


## -------------------------------------------------------------------

for (outcome in c('Asthma','Diarrhea','Pregnancy_complic','RespiratorySyndrome','Bite_Insect','Dehydration','Chest_pain')){
## import pandas as pd
pd<-import('pandas')
np<-import('numpy')
smf<-import('statsmodels.formula.api')
sm<-import('statsmodels.api')
winsound<-import('winsound')

#change column names
old_names=colnames(sys_sa)[grep('\\.',colnames(sys_sa))]
new_names=gsub('\\.','_',old_names)
colnames(sys_sa)[colnames(sys_sa) %in% old_names]<-new_names


#define outcome
outcome=outcome
#run gee glm
formula=paste0(outcome,'.astype(float) ~ ',paste0(gsub('\\.','_',lag_cols),collapse = ' * flooded + '),' * flooded + Ethnicity + Race + Sex + Age + weekday')
sys_sa$offset=log(sys_sa$ZCTAdaily_count)
model = smf$gee(formula=formula,groups=sys_sa$crossed_zcta, data = sys_sa,offset=np$array(sys_sa$offset),missing='drop',family=sm$families$Poisson(link=sm$families$links$log()))
results=model$fit()
#print(results.summary())
print('completed')
# winsound$Beep(as.integer(800),as.integer(500))


## -------------------------------------------------------------------
gee_coeff<-data.frame(results$params)
gee_cov<-results$cov_params_default


lag_cols<-gsub('\\.','_',lag_cols)
#rownames(gee_coeff)[grep(paste0(lag_cols,':.*flooded',collapse = '|'),rownames(gee_coeff))]

to_filter<-'flooded'
indxs<-grep(paste0(lag_cols,':.*',to_filter,collapse = '|'),rownames(gee_coeff))
#gee_cov[indxs,indxs]

pred7 <- crosspred(lag_df_all,coef =  gee_coeff[indxs,],vcov =gee_cov[indxs,indxs],model.link = 'log',at=1,cumul = T)

tablag2 <- with(pred7,t(rbind(matRRfit,matRRlow,matRRhigh)))
colnames(tablag2) <- c("RR","ci.low","ci.hi")
#tablag2
#tablag2[c(1,2,10),]

knots=logknots(13,nk)

pdf(paste0('graphs//',outcome,'_nk_',nk,'_cons_contrlPrePost.pdf'),width =6 ,height=4.5)
plot(pred7,var=1,type="p",ci="bars",col=1,pch=19,#ylim=c(0.7,1.4),
  main=paste0(outcome,' knots: ',paste0(round(knots,3),collapse=', ')),xlab="Lag (days)",cumul=F,
  ylab="RR")
dev.off()

#plo
pdf(paste0('graphs//',outcome,'_nk_',nk,'_cons_contrlPrePost_Cuml.pdf'),width =6 ,height=4.5)
plot(pred7,var=1,type="p",ci="bars",col=1,pch=19,#ylim=c(0.7,1.4),
     main=paste0(outcome,' knots: ',paste0(round(knots,3),collapse=', '),' Cumulative'),xlab="Lag (days)",cumul=T,
     ylab="RR")
dev.off()

print(paste0(outcome,' ',nk))
print(results$qic(scale=1000))
winsound$Beep(as.integer(800),as.integer(500))


save(pred7,knots,file=paste0(outcome,'_nk_',nk,'_cons_contrlPrePost.RData'))
  }
}
# 
# ## -------------------------------------------------------------------
# outcome<-'Pregnancy_complic'
# sys_sa$outcome<-as.numeric(sys_sa[,outcome])
# 
# 
# ## -------------------------------------------------------------------
# start.time <- Sys.time()
# model <-glm(formula = outcome ~ flooded * period + Age + Sex + Ethnicity + Race + weekday,
#                     data = sys_sa,#id=crossed_zcta,
#                     family = poisson(link='log'),
#                     #corstr = "ar1", 
#                     offset=log(ZCTAdaily_count))
# summary(model)
# "\n Time taken:"; Sys.time()-start.time
# 
# 
# ## -------------------------------------------------------------------
# sam_data<-sys_sa#sample_n(sys_sa,100000)
# sam_data$ids<-as.numeric(as.factor(sam_data$crossed_zcta),levels=seq(1,length(unique(sam_data$crossed_zcta))))
# sam_data<-sam_data[order(sam_data$ids),c("outcome" ,"flooded", "period", "Age", "Sex","Ethnicity","Race","weekday", "crossed_zcta","ZCTAdaily_count","Date","ids")]
# summary(sam_data)
# 
# 
# ## -------------------------------------------------------------------
# library(gee)
# start.time <- Sys.time()
# model <-gee(formula = outcome ~ flooded * period + Age + Sex + Ethnicity + weekday + Race + offset(log(ZCTAdaily_count)),
#                     data = sam_data,
#                     id=ids,
#                     family = poisson(link = 'log'), corstr = "exchangeable", 
#                     silent=F, maxiter = 30,
#                     #corstr = "ar1", 
#                     #offset=log(ZCTAdaily_count)
#             )
# model
# "\n Time taken:"; Sys.time()-start.time
# 
# 
# ## -------------------------------------------------------------------
# library(geepack)
# start.time <- Sys.time()
# model <-geeglm(formula = outcome ~ flooded * period + Age + Sex + Ethnicity + weekday, # + Race,
#                     data = sam_data,
#                     id=ids,
#                     family = poisson(link = 'log'), corstr = "exchangeable", 
#                     offset=log(ZCTAdaily_count)
#                )
# summary(model)
# "\n Time taken:"; Sys.time()-start.time
# 
# 
# ## -------------------------------------------------------------------
# ##update correlation structure
# usmodelnew2 <- update(usmodelnew, corstr = "exch")
# usmodelnew3 <- update(usmodelnew, corstr = "independence")
# 
# ##select correlation structure based on smallest QIC
# model.sel(usmodelnew, usmodelnew2, usmodelnew3, rank=QIC)
# usmodel.select<- usmodelnew
# 
# ##get summary from the selected model
# QIC(usmodelnew)
# summary(usmodelnew)
# 
# # 'tidy' function to clean results from 'broom' package. 
# tidy(usmodelnew, conf.int = TRUE)
# 
# 
# 
# sys_sa_subset<-sys_sa[,c("outcome","flooded","period","Age","Sex","Race","Ethnicity","ZCTAdaily_count",'crossed_zcta')]
# #remove incomplete rows
# sys_sa_subset<-na.omit(sys_sa_subset)
# 
# #run model
# model <-geeglm(formula = outcome ~ flooded * period + Age + Sex + Race + Ethnicity,
#             data = sys_sa_subset,id=crossed_zcta,
#             family = poisson(link='log'),
#             #corstr = "ar1", 
#             offset=log(ZCTAdaily_count))
# print(summary(model))
# results<-data.frame(exp((summary(model)[["coefficients"]])[,'Estimate']))
# results<-cbind(results,data.frame(exp(confint.default(model))))
# colnames(results)<-c('estimate','conf_int2_5','conf_int_97_5')
# View(results)
# write.table(results, "clipboard", sep="\t", row.names=T,col.names = F)
# print(outcome)
# 
# 
# 
# ## -------------------------------------------------------------------
# sam_data<-sam_data[(sam_data$Date<'2019-10-05') & (sam_data$Date>'2019-08-30'),]
# sam_data$period<-droplevels(sam_data$period)
# #bulild lag variable
# library(dlnm)
# sam_data<-sam_data[order(sam_data$Date),]
# #create date and expoure
# lag_df<-sam_data[!duplicated(sam_data$Date),c('Date','period')]
# lag_df<-lag_df[order(lag_df$Date),]
# row.names(lag_df) <- NULL
# lag_df$period[lag_df$Date>'2019-09-22']<-'controlPeriod'
# lag_df$period<-droplevels(lag_df$period)
# levels(lag_df$period)<-c(0,1)
# #run cross basis
# cb<-crossbasis(lag_df$period,lag=10,argvar=list(fun="strata",breaks=1),
#   arglag=list(fun="strata",breaks=c(4,8)))
# #bind date to the lag df and drop the binary exposure and keep lag
# lag_df<-cbind(lag_df,cb)
# lag_df<-subset(lag_df,select=-period)
# #merge this back to df
# sam_data<-merge(sam_data,lag_df,by='Date',all.x=T)
# 
# #run glm 
# lag_df_all<-sam_data[,colnames(cb)]
# #lag_df_all[sam_data$flooded=='Non flooded',]<-0
# lag_df_all<-as.matrix(lag_df_all)
# 
# class(lag_df_all) <- c("crossbasis","matrix")
# for(i in c('arglag','df',"range","lag","argvar")){
# attr(lag_df_all,i)<-attr(cb,i)
# }
# 
# 
# start.time <- Sys.time() 
# model1 <-glm(formula = outcome ~ v1.l1 * flooded + v1.l2 * flooded + v1.l3 * flooded + Age + Sex + Ethnicity + Race + weekday,
#                     data = sam_data,#id=crossed_zcta,
#                     family = poisson(link='log'),
#                     offset=log(ZCTAdaily_count))
# summary(model2)
# "\n Time taken:"; Sys.time()-start.time
# 
# pred7 <- crosspred(lag_df_all,coef = coef(model)[2:4],vcov = vcov(model)[2:4,2:4],model.link = 'log',at=1)
# 
# tablag2 <- with(pred7,t(rbind(matRRfit,matRRlow,matRRhigh)))
# colnames(tablag2) <- c("RR","ci.low","ci.hi")
# tablag2
# 
# sub_sam_data<-sample_n(sys_sa,10000)
# 
# 
# 
# 
# ## -------------------------------------------------------------------
# library(fastDummies)
# grouped_sys<- subset(sam_data,select=-c(Race))
# grouped_sys<-dummy_cols(grouped_sys,select_columns = c('Sex','Ethnicity'),remove_selected_columns = T)
# #colnames(grouped_sys)
# # group by date and zctas
# grouped_sys<-grouped_sys %>% group_by(Date,crossed_zcta) %>% 
#                                 dplyr::summarise(outcome=sum(outcome),
#                                 flooded=first(flooded),
#                                 period=first(period),
#                                 Age=mean(Age),
#                                 weekday=first(weekday),
#                                 ZCTAdaily_count=first(ZCTAdaily_count),
#                                 Sex_F=sum(Sex_F),
#                                 Sex_M=sum(Sex_M),
#                                 Ethnicity_NON_HISPANIC=sum(`Ethnicity_NON HISPANIC`),
#                                 Sex_Unknown=sum(Sex_Unknown),
#                                 Ethnicity_HISPANIC=sum(Ethnicity_HISPANIC),
#                                 Ethnicity_Unknown=sum(Ethnicity_Unknown))
# 
# grouped_sys[,c('Sex_F','Sex_M','Sex_Unknown', 'Ethnicity_HISPANIC','Ethnicity_Unknown','Ethnicity_NON_HISPANIC')]<-apply(grouped_sys[,c('Sex_F','Sex_M','Sex_Unknown', 'Ethnicity_HISPANIC','Ethnicity_Unknown','Ethnicity_NON_HISPANIC')],2,as.numeric)
# grouped_sys[,c('Sex_F','Sex_M','Sex_Unknown', 'Ethnicity_HISPANIC','Ethnicity_Unknown','Ethnicity_NON_HISPANIC')]<-grouped_sys[,c('Sex_F','Sex_M','Sex_Unknown', 'Ethnicity_HISPANIC','Ethnicity_Unknown','Ethnicity_NON_HISPANIC')]/grouped_sys$ZCTAdaily_count
# #grouped_sys
# 
# #run model
# library(geepack)
# start.time <- Sys.time()
# group_model <-geeglm(formula = outcome ~ flooded * period + Age + Sex_F + Sex_Unknown + Ethnicity_HISPANIC + Ethnicity_Unknown  + weekday, # + Race,
#                     data = grouped_sys,
#                     id=crossed_zcta,
#                     family = poisson(link = 'log'), corstr = "independence", 
#                     offset=log(ZCTAdaily_count)
#                )
# summary(group_model)
# "\n Time taken:"; Sys.time()-start.time
# 
# 
# ## -------------------------------------------------------------------
# 


grouped<-sys_sa %>% group_by(Date,flooded) %>% dplyr::summarise(count=sum(Diarrhea),total_visits=n(),period=first(period))
grouped<-grouped[order(grouped$flooded, grouped$Date),]
grouped$count<-as.numeric(grouped$count)
# 
# #min max scale
# normalize <- function(x){return((x- min(x)) /(max(x)-min(x)))}
# for(i in levels(grouped$flooded)){
# grouped[grouped$flooded==i,'count']=normalize(grouped[grouped$flooded==i,'count'])}
# 
grouped$count<-grouped$count/grouped$total_visits
#rolling window of 7
grouped$rolled_count<-rollmean(grouped$count,7,fill=NA)
grouped$rolled_count[grouped$Date %in% grouped$Date[is.na(grouped$rolled_count)]]<-NA
# 
# 
# ## ----warning=FALSE--------------------------------------------------
#merge flood category to population data
population<-read.csv("Z:\\Balaji\\Census_data_texas\\ZCTA population\\ACSDT5Y2019.B01003_data_with_overlays_2021-05-31T125325.csv")
population$zcta<-str_sub(population$GEO_ID,10)
population<-merge(population,sys_sa[!duplicated(sys_sa$crossed_zcta),],by.x='zcta',by.y="crossed_zcta",all.x=F,all.y=F)
population$B01003_001E<-as.integer(population$B01003_001E)
flood_pop<-population %>% group_by(flooded) %>% dplyr::summarise(pop=sum(B01003_001E))

library(scales)
# data<-read.csv("Z:\\Balaji\\stram_flow\\imelda\\data_gagues_ZCTA_study_area.csv")
# data$datetime<-data$datetime_Converted
# grouped_fg<-data %>%
#   group_by(datetime) %>%
#   dplyr::summarise(above_floo = sum(na.omit(exceed_flood_stage)))
# grouped_fg$date<-as.Date(grouped_fg$datetime,format='%Y-%m-%d')
# grouped_fg<-grouped_fg[order(grouped_fg$datetime),]
# 
# #merge sys_groupd counts and flood population
# grouped_fg=merge(grouped,grouped_fg,by.x='Date',by.y='date', all.x=T)


grouped_fg<-merge(grouped,flood_pop,by='flooded',all.x=T)


#standardise by population
#grouped_fg$rolled_count<-(grouped_fg$rolled_count/grouped_fg$pop)*1e6
#compute percentage
#grouped_fg<-grouped_fg[order(grouped_fg$Date),]
#plot
fig<-plot_ly(x = grouped_fg$Date, y = grouped_fg$rolled_count, mode='lines',color=factor(grouped_fg$flooded))
fig

#plot
#blind frinedly pallete
cbbPalette <- c( "#009E73","#0072B2", "#D55E00", "#CC79A7", "#000000", "#E69F00", "#56B4E9", "#F0E442")
# To use for fills, add
h=max(grouped_fg$rolled_count,na.rm = T)-0.001
scale_fill_manual(values=cbbPalette)
vj=0.5
lwd= unit(0.1,'lines')
myarrow=arrow(length=unit(0.01,'npc'),ends = 'both')


#scale_fac=30
ggplot(grouped_fg, aes(x=Date)) +

  #geom_bar( aes(y=above_floo*scale_fac), stat="sum",size=.1, fill='#56B4E9',alpha=.6) +
  geom_line( aes(y=rolled_count,colour=flooded), size=0.6) +
  
  geom_segment(aes(x=as.Date('2019-06-02'),xend=as.Date('2019-09-11'),y=h,yend=h),size=lwd,arrow=myarrow) +
  geom_label(aes(as.Date('2019-08-01'),h,label = 'Control period', vjust = -vj),label.size =NA,label.padding = unit(0, "cm"))+
  
  geom_segment(aes(x=as.Date('2019-09-19'),xend=as.Date('2019-10-01'),y=h,yend=h),size=lwd,colour='blue',arrow=myarrow) +
  geom_label(aes(as.Date('2019-09-22'),h,label = 'Flood period', vjust = 1+vj),colour='blue',label.size =NA,label.padding = unit(0, "cm"))+
  
  geom_segment(aes(x=as.Date('2019-10-02'),xend=as.Date('2019-11-01'),y=h,yend=h),size=lwd,arrow=myarrow) +
  geom_label(aes(as.Date('2019-10-17'),h,label = 'Acute phase', vjust = -vj),label.size =NA,label.padding = unit(0, "cm"))+
  
  geom_segment(aes(x=as.Date('2019-11-02'),xend=as.Date('2019-12-31'),y=h,yend=h),size=lwd,arrow=myarrow) +
  geom_label(aes(as.Date('2019-12-01'),h,label = 'Protracted phase', vjust = -vj),label.size =NA,label.padding = unit(0, "cm"))+
  
  xlab(element_blank()) +
  scale_y_continuous(
    # Features of the first axis
    name = "% of Total ED visits",
    labels = scales::percent_format(accuracy =0.1)
    # Add a second axis and specify its features
    #sec.axis = sec_axis(~./scale_fac, name="Number of stream guages \nindicating flooding")
  ) +
  scale_x_date(date_breaks = "15 day", expand = c(0,0),
                 labels=date_format("%d-%b-%Y"),
                 limits = as.Date(c('2019-06-01','2019-12-31'))) +
  theme(
    text = element_text(size=12),
    axis.text.x = element_text(angle = 45, hjust = 1,size=10),
    axis.title.y = element_text(size=13),
    axis.title.y.right = element_text(color = '#3e89b3', size=13),
    legend.position="bottom",
    legend.title =element_blank(),
    panel.background = element_rect(fill = "white", colour = "grey40",
                                    size = 0.5, linetype = "solid"),
    panel.grid.major = element_line(size = 0.25, linetype = 'solid',
                                    colour = "grey70"),
    panel.grid.minor = element_line(size = 0.1, linetype = 'solid',
                                    colour = "grey90")
  )+ scale_color_manual(values=cbbPalette) #+ ggtitle('ED visits related to diarrhea')

ggsave('SysWithGaugesDiarrhea_percent.pdf',path=getwd(),height=12,width = 20,units = "cm")

# 
# 
# ## -------------------------------------------------------------------
# #create grouped df
# grouped<-sys_sa %>% group_by(Date) %>% dplyr::summarise(count=n())
# grouped$rolled_count<-rollmean(grouped$count,7,fill=NA)
# #create daye variables
# grouped$weekday<-as.factor(weekdays(grouped$Date,abbreviate=T))
# grouped$month<-as.factor(months(grouped$Date,abbreviate = T))
# 
# plot(grouped$Date,grouped$count,col=grey(0.6),main="ED per day",ylab="ED visits", type='b',
#   xlab="Date")
# 
# plot(grouped$Date,grouped$rolled_count,col=grey(0.6),main="ED per day (7 day avg)",ylab="ED visits", type='b',
#   xlab="Date")
# 
# 
# ## ----message=FALSE--------------------------------------------------
# model1 <- glm(count ~ weekday  ,grouped,family=poisson)
# summary(model1)
# 
# # COMPUTE PREDICTED NUMBER OF DEATHS FROM THIS MODEL
# pred1 <- predict(model1,type="response")
# 
# plot(grouped$Date,grouped$count,col=grey(0.6), type='p',
#   main="Time-stratified model (month strata)",ylab="Daily number of deaths",
#   xlab="Date")
# lines(grouped$Date,pred1,lwd=1)
# 
# model2 <- glm(count ~ weekday + month,grouped,family=poisson)
# summary(model2)
# 
# # COMPUTE PREDICTED NUMBER OF DEATHS FROM THIS MODEL
# pred2 <- predict(model2,type="response")
# 
# plot(grouped$Date,grouped$count,col=grey(0.6), type='p',
#   main="Time-stratified model (inteaction)",ylab="Daily number of deaths",
#   xlab="Date")
# lines(grouped$Date,pred2,lwd=1)
# 
# 
# ## ----eval=FALSE, include=FALSE--------------------------------------
# ## #### See number of hospitals broadcasting data
# ## grouped_hosp<-sys_sa  %>% group_by(Date) %>% dplyr::summarise(count=n_distinct(HospitalName))
# ## grouped_hosp$rolled_count<-rollmean(grouped_hosp$count,7,fill=NA)
# ## plot_ly(x = grouped_hosp$Date, y = grouped_hosp$rolled_count, mode='lines')
# 
# 
# ## -------------------------------------------------------------------
# grouped_outcomes<-sys_sa %>% group_by(Date,flooded) %>% dplyr::summarise(
#                                      Pregnancy_complic=sum(Pregnancy_complic),
#                                      Asthma=sum(Asthma),
#                                      Bite.Insect=sum(Bite.Insect),
#                                      Dehydration=sum(Dehydration),
#                                      Drowning=sum(Drowning),
#                                      Hypothermia=sum(Hypothermia),
#                                      Chest_pain=sum(Chest_pain),
#                                      Heat_Related_But_Not_dehydration=sum(Heat_Related_But_Not_dehydration),
#                                      CO_Exposure=sum(CO_Exposure)
#                                      )
# grouped_outcomes<-grouped_outcomes[order(grouped$flooded, grouped$Date),]
# #create pivot
# library(tidyr)
# pivot<-grouped_outcomes %>% pivot_wider(names_from = flooded, values_from=outcomes_all)
# write.csv(pivot,'SysOutcomesDailyCounts.csv',row.names = F)
# 
