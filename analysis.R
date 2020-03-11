#http://environmentalcomputing.net/interpreting-coefficients-in-glms/
#https://stats.idre.ucla.edu/r/dae/probit-regression/
library(raster)
library(rgdal)
library(GISTools)
library(plotly)
library(BAMMtools)
library(stringi)
#function make quantiles


#function for z score
zscore<-function(data){
  return ((data-mean(data))/sd(data))
}
#function for forming distritubion from counts
mGetDistri<-function(data,cname){
  ret<-c()
  values_s<-mGetValues(data,cname)
  for (i in values_s){
    sum_counts<-sum(data[,paste0(cname,"_",i)],na.rm=T)
    ret<-c(ret,rep(as.integer(i),sum_counts)) 
  }
  return(ret)
}


#function to get the unique values for a variable
mGetValues <- function(df,colname) {
  cnames<-colnames(df)
  snames<-grep(paste0(colname,"_"), cnames, value=TRUE)
  vec<-c()
  for(s in snames){
    val<-unlist(strsplit(s,'_'))[2]
    if(val!='t') vec<-c(vec,val)
  }
  return(vec)
}

#function to recategorize data
recat<-function(df,colname,cats){
  values_s<-mGetValues(df,colname)
  temp_df<-data.frame(matrix(nrow=nrow(df),ncol=length(cats)-1))
  colnames(temp_df)<- paste0('cat',seq(length(cats)-1))
  values<-as.numeric(values_s)
  for (i in 1:(length(cats)-1)){
    v<- (values>cats[i] & values<=cats[i+1])
    if(!any(v)) next
    fil_col<-df[,paste0(colname,"_",values_s[v])]
    temp_df[,i]<-rowSums(data.frame(fil_col),na.rm=T)
  }
  return (temp_df)
}
  
  
  
questions_short<-c('waterLevel',
                   'homeDamaged',
                   'flooded',
                   'floodedDays',
                   'floodedHours',
                   'hospitalized',
                   'illness',
                   'injury',
                   'leftHome',
                   'electricity',
                   'electricityLostDays',
                   'otherHomesFlood',
                   'skinContact',
                   'whereLived',
                   'hospitalDays')


#read from the joined table
#data_copy<-read.csv('\\\\vetmed2.vetmed.w2k.vt.edu\\Blitzer\\NASA project\\Balaji\\HHR_20191001_CT\\joined_table_nondemos.csv')

data<-data_copy

min_limit=5
for(n in names(data))
  if(stri_sub(n,-2,-1)=="_t")
  {
    data[is.na(data[[n]]) | data[[n]]<min_limit ,n]<-NA
    data[is.na(data[[n]]) | data[[n]]<min_limit ,paste0(stri_sub(n,1,-3),'_1')]<-NA
    print(paste0(stri_sub(n,1,-3),'_1'))
    
  }


#removeing the 3 tracts - 
data<-data[!(data$tractId %in% c(48339694700,48339694201,48339694101)),]

### data preparation for logis regression ---------------------
indes<- c("flooded","electricity","otherHomesFlood","skinContact")
depnsB<-c('illness','injury',"hospitalized","leftHome")
#percentage responses for yes or no questions
df<-data.frame(tractId=data$tractId,floodRatio=data$floodR100,SVI=data$SVI,imperInd=data$imperInd)
for( field in c(indes) ){
  df[[field]] <- data[[paste0(field,"_1")]]/data[[paste0(field,"_t")]]
}

for( field in c(depnsB) ){
  df[[paste0(field,"_1")]] <- data[[paste0(field,"_1")]]
  df[[paste0(field,"_0")]] <- data[[paste0(field,"_0")]]
}

indes<-c(indes,'SVI','floodRatio','imperInd')
## recatagorizing required fields independent variables ------

#wherelived
tdf<-data[,grep('whereLived',colnames(data))]
tdf$whereLived_someHome<-tdf$whereLived_apartment+tdf$whereLived_hotel+tdf$whereLived_liveFamily+tdf$whereLived_singleFamily
tdf$whereLived_NoNMobileHome<-tdf$whereLived_mobileHome+tdf$whereLived_homeless
tdf<- sweep(tdf, 1, tdf$whereLived_t, "/")
tdf<-subset(tdf, select =c(whereLived_someHome,whereLived_NoNMobileHome,whereLived_temporaryShelter))
indes<-c(indes,names(tdf))
df<-cbind(df,tdf)


#waterLevel
cname<-"waterLevel"
cats<-c(0,3,6) #c(0,2,4,6,8) 4 removed because is always singlular
tdf<-recat(data,cname,cats)
colnames(tdf)<-paste0(cname,"C_",cats[-1])
tdf<-sweep(tdf, 1, data[[paste0(cname,'_t')]], "/")
indes<-c(indes,names(tdf))
df<-cbind(df,tdf)

#electricityLostDays
# cname<-"electricityLostDays"
# d<-sort(mGetDistri(data,cname))
# zs<-zscore(d)
# ds<-d[abs(zs)<3.1 & d<=30]
# #h<-hist(ds,breaks=c(min(d)-1,unique(ds)),right=T)
# #View(data.frame(h$breaks[-1],h$counts))
# #print(getJenksBreaks(ds,5))
# cats<-c(0,15,30) # 3 9 removed after corr matrix c(0,18,30,60,90)
# tdf<-recat(data,cname,cats) 
# colnames(tdf)<-paste0(cname,"C_",cats[-1])
# tdf<-sweep(tdf, 1, data$electricityLostDays_t, "/")
# indes<-c(indes,names(tdf))
# df<-cbind(df,tdf)


#floodedDays
# cname<-"floodedDays"
# d<-sort(mGetDistri(data,cname))
# zs<-zscore(d)
# ds<-d[d<=30]
# #h<-hist(ds,breaks=c(min(d)-1,unique(ds)),right=T)
# #View(data.frame(h$breaks[-1],h$counts))
# #print(getJenksBreaks(ds,6))
# cats<-c(0,10,90) # 60 remove after cor -c(0,2,5,10,18,30,90)
# tdf<-recat(data,cname,cats)
# colnames(tdf)<-paste0(cname,"C_",cats[-1])
# tdf<-sweep(tdf, 1, data$floodedDays_t, "/")
# indes<-c(indes,names(tdf))
# df<-cbind(df,tdf)
#qplot(sample=mGetDistri(data,cname))



## logistic regression



# indes <- c( 
#   'flooded','electricity','otherHomesFlood','skinContact',
#   'leftHome',
#   'SVI','floodRatio','imperInd',
#   'whereLived_liveFamily','whereLived_apartment','whereLived_other','whereLived_singleFamily','whereLived_hotel','whereLived_homeless','whereLived_mobileHome','whereLived_temporaryShelter',
#   'waterLevelC_2','waterLevelC_8',
#   'electricityLostDaysC_18','electricityLostDaysC_30','electricityLostDaysC_90',
#   'floodedDaysC_2','floodedDaysC_5','floodedDaysC_90'
# )

#recoding values
#df$floodRatio<-cut(df$floodRatio,e,right=F,labels=c("0"," <6.5%"," <50%"))
s<-df$floodRatio[df$floodRatio>0]
df$floodRatio<-cut(df$floodRatio,breaks=c(quantile(df$floodRatio,prob=seq(0,1,1/2))),right=F)
df$SVI<-cut(df$SVI,breaks=c(0.00,0.25,.5,.75,1.0),include.lowest=T)#,labels=c('<=25%','<=100%'))
#df$SVI<-cut(df$SVI,breaks=c(quantile(df$SVI,na.rm=T,probs=seq(0,1,1/4))),include.lowest=T,labels=c('<=25%','<=50%','<=75%','<=100%'))

# inds<-df$SVI>0.25 & df$SVI<1
# df<-df[inds,]
# data<-data[inds,]

df$imperInd<-df$imperInd


print(indes)
indes <- c(
            # 'flooded',
            # 'electricity','otherHomesFlood','skinContact',
            #'  #'leftHome',
             'floodRatio','SVI'#,'imperInd',
            # 'waterLevelC_3','waterLevelC_6',
            # 'electricityLostDaysC_15','electricityLostDaysC_30',
            # 'floodedDaysC_10','floodedDaysC_90',
            # "whereLived_someHome" ,"whereLived_NoNMobileHome","whereLived_temporaryShelter"
            )


#depnsB<-c('illness','injury',"hospitalized")
#corellation analysis
#cor_mat<-cor(df[,indes],use="complete.obs")
#cat("\014")
for (dependent in depnsB[1:1]){
  print(strrep('_',200),quote=F)
  #print(dependent)
  #glm binomial with probit link
  
  #frmla=as.formula(paste0("cbind(",dependent,"_1,",dependent,"_0)", " ~ ",paste(indes,collapse = ' * '))) #incase of using fractions
  
  # model <- glm (frmla, data = df,family=binomial(link="probit"))
  # summary(model)
  #glm binomial with logit
  # print(strrep('BINOMIAL----------- ',5))
  # df1=df[,c("illness_0","illness_1",indes)]
  # df1=na.omit(df1, cols = names(df1))
  # frmla=paste0('c(',dependent,"_1, ",dependent,"_0 )"," ~ ",
  #                        paste(indes,collapse = ' + '))
  #model <- glm (frmla, data = df1,family=binomial(link="logit"))
  #print(summary(model))
  # 
  print(strrep('POISSON----------- ',5))
  #glm poisson
  frmla_poi=paste0(dependent,"_1 ~ ",
               paste(indes,collapse = ' + ')) #incase of using fractions
  frmla_poi=paste0(frmla_poi)
  
  #dependent='leftHome';  frmla_poi=paste0("leftHome","_1 ~ ","floodRatio")
  print(frmla_poi)
  w=data[[paste0(dependent,"_0")]]+data[[paste0(dependent,"_1")]]
  model <- glm (frmla_poi, data = df,family=poisson,offset  = log(w))
  print(summary(model))
  #print(confint(model,level=0.95))
}

