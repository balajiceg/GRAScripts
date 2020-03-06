#http://environmentalcomputing.net/interpreting-coefficients-in-glms/
#https://stats.idre.ucla.edu/r/dae/probit-regression/
library(raster)
library(rgdal)
library(GISTools)
library(plotly)
library(BAMMtools)

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
#data<-read.csv('\\\\vetmed2.vetmed.w2k.vt.edu\\Blitzer\\NASA project\\Balaji\\HHR_20191001_CT\\joined_table_nondemos.csv')




### data preparation for logis regression ---------------------
indes<- c("flooded","electricity","otherHomesFlood","skinContact",'leftHome')
depnsB<-c('illness','injury',"hospitalized")
#percentage responses for yes or no questions
df<-data.frame(tractId=data$tractId,floodRatio=data$floodRatio,SVI=data$SVI,imperInd=data$imperInd)
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
cats<-c(0,2,4,8) #c(0,2,4,6,8)
tdf<-recat(data,cname,cats)
colnames(tdf)<-paste0(cname,"C_",cats[-1])
tdf<-sweep(tdf, 1, data[[paste0(cname,'_t')]], "/")
indes<-c(indes,names(tdf))
df<-cbind(df,tdf)

#electricityLostDays
cname<-"electricityLostDays"
d<-sort(mGetDistri(data,cname))
zs<-zscore(d)
ds<-d[abs(zs)<3.1 & d<=30]
#h<-hist(ds,breaks=c(min(d)-1,unique(ds)),right=T)
#View(data.frame(h$breaks[-1],h$counts))
#print(getJenksBreaks(ds,5))
cats<-c(0,18,30,90) # 3 9 removed after corr matrix c(0,18,30,60,90)
tdf<-recat(data,cname,cats) 
colnames(tdf)<-paste0(cname,"C_",cats[-1])
tdf<-sweep(tdf, 1, data$electricityLostDays_t, "/")
indes<-c(indes,names(tdf))
df<-cbind(df,tdf)


#floodedDays
cname<-"floodedDays"
d<-sort(mGetDistri(data,cname))
zs<-zscore(d)
ds<-d[d<=30]
#h<-hist(ds,breaks=c(min(d)-1,unique(ds)),right=T)
#View(data.frame(h$breaks[-1],h$counts))
#print(getJenksBreaks(ds,6))
cats<-c(0,2,5,90) # 60 remove after cor -c(0,2,5,10,18,30,90)
tdf<-recat(data,cname,cats)
colnames(tdf)<-paste0(cname,"C_",cats[-1])
tdf<-sweep(tdf, 1, data$floodedDays_t, "/")
indes<-c(indes,names(tdf))
df<-cbind(df,tdf)
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
#df$floodRatio<-cut(df$floodRatio,breaks=c(0,0.01,0.05,0.1,0.25,0.8),right=F,labels=c('<1%','<5%','<10%','<25%','<80%'))
df$SVI<-cut(df$SVI,breaks=c(0.00,1e-1,0.25,0.5,0.75,1.0),include.lowest=T,labels=c('==0','<=25%','<=50%','<=75%','<=100%'))
df$imperInd<-df$imperInd/5.0

print(indes)
indes <- c(
            'flooded','electricity','otherHomesFlood','skinContact',
            'leftHome'
            #'SVI','floodRatio','imperInd'
            # 'waterLevelC_2','waterLevelC_4','waterLevelC_8',
            # 'electricityLostDaysC_18','electricityLostDaysC_30','electricityLostDaysC_90',
            # 'floodedDaysC_2','floodedDaysC_5','floodedDaysC_90',
            # "whereLived_someHome" ,"whereLived_NoNMobileHome","whereLived_temporaryShelter"
            )




#depnsB<-c('illness','injury',"hospitalized")
#corellation analysis
#cor_mat<-cor(df[,indes],use="complete.obs")
cat("\014")
for (dependent in depnsB){
  print(strrep('_',200),quote=F)
  print(dependent)
  #glm binomial with probit link
  
  frmla=as.formula(paste0("cbind(",dependent,"_1,",dependent,"_0)", " ~ ",paste(indes,collapse = ' + '))) #incase of using fractions
  #print(frmla)
  #model <- glm (frmla, data = df,family=binomial(link="probit"))
  #summary(model)
  
  #glm binomial with logit
  print(strrep('BINOMIAL----------- ',5))
  model <- glm (frmla, data = df,family=binomial(link="logit"))
  print(summary(model))
  
  print(strrep('POISSON----------- ',5))
  #glm poisson
  frmla_poi=paste0(dependent,"_1 ~ ",
               paste(indes,collapse = ' + ')) #incase of using fractions
  w=data[[paste0(dependent,"_0")]]+data[[paste0(dependent,"_1")]]
  model <- glm (frmla_poi, data = df,family=poisson,offset  = log(w))
  print(summary(model))
}
