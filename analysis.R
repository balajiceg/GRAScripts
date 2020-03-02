library(raster)
library(rgdal)
library(GISTools)
library(plotly)
library(BAMMtools)

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
data<-read.csv('\\\\vetmed2.vetmed.w2k.vt.edu\\Blitzer\\NASA project\\Balaji\\HHR_20191001_CT\\joined_table_nondemos.csv')



### data preparation for logis regression ---------------------
indes<- c("flooded","electricity","otherHomesFlood","skinContact")
depnsB<-c('illness','injury','leftHome',"hospitalized")
#percentage responses for yes or no questions
df<-data.frame(tractId=data$tractId,floodRatio=data$floodRatio,SVI=data$SVI)
for( field in c(indes) ){
  df[[field]] <- data[[paste0(field,"_1")]]/data[[paste0(field,"_t")]]
}

for( field in c(depnsB) ){
  df[[paste0(field,"_1")]] <- data[[paste0(field,"_1")]]
  df[[paste0(field,"_0")]] <- data[[paste0(field,"_0")]]
}

indes<-c(indes,'SVI','floodRatio')
## recatagorizing required fields independent variables ------

#wherelived
tdf<-data[,grep('whereLived',colnames(data))]
tdf<- sweep(tdf, 1, tdf$whereLived_t, "/")
tdf<-subset(tdf, select = -c(whereLived_t))
indes<-c(indes,names(tdf))
df<-cbind(df,tdf)


#waterLevel
cname<-"waterLevel"
cats<-c(0,2,4,6,8)
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
h<-hist(ds,breaks=c(min(d)-1,unique(ds)),right=T)
View(data.frame(h$breaks[-1],h$counts))
print(getJenksBreaks(ds,5))
cats<-c(0,3,9,18,30,60,90)
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
h<-hist(ds,breaks=c(min(d)-1,unique(ds)),right=T)
#View(data.frame(h$breaks[-1],h$counts))
print(getJenksBreaks(ds,6))
cats<-c(0,2,5,10,18,30,60,90)
tdf<-recat(data,cname,cats)
colnames(tdf)<-paste0(cname,"C_",cats[-1])
tdf<-sweep(tdf, 1, data$floodedDays_t, "/")
indes<-c(indes,names(tdf))
df<-cbind(df,tdf)
#qplot(sample=mGetDistri(data,cname))



## logistic regression

#indesB<- c("flooded","electricity","otherHomesFlood","skinContact")
#depnsB<-c('illness','injury','leftHome',"hospitalized")

dependent<-depnsB[1]
print(dependent)
#glm binomial with probit link
frmla=paste0("cbind(",dependent,"_1,",dependent,"_0)", " ~ ",paste(indes,collapse = ' + ')) #incase of using fractions
print(frmla)
model <- glm (frmla, data = df,family=binomial(link="logit"))
summary(model)


#glm
frmla=paste0("as.integer(",dependent,"*100) ~ ",paste(indes,collapse = ' + ')) #incase of using fractions
model <- glm (frmla, data = df,family="poisson")
summary(model)


















































#----------------------------------------------------------------------------
# junk code trials---------------




# finding min max responses in each category
c<-"electricityLostDays"
x<- paste0(c,'_', sprintf("%#.1f", as.numeric(mGetValues(data,c)) %>% sort))
x<-data[,x]
View(colSums(x))


df$percent_postive=df[,paste0(questionss_short[selected_ques],'_',1)]/df[,paste0(questionss_short[selected_ques],'_t')]
merged<-merge(df, inun_data,by = "tract_id",all.x=T)
# png(paste0(questionss_short[selected_ques],'_c.png'))
# print(ggplot(merged,aes(x=flooded_percent_c,y=percent_postive))+geom_point()+ggtitle(questionss[selected_ques]))
# dev.off()
print(questions[selected_ques])
print(summary(lm(flooded_percent_c~percent_postive,data=merged)))

#max repondents
tot_cols<-data[,grep("_t",names(data))]
tot_cols$max<-apply(tot_cols,1,max,na.rm=T)

#plot histograms
ggplot(data, aes(x=floodRatio)) + 
  geom_histogram(bins=100)
ggplot(data, aes(x=max_t_counts)) + 
  geom_histogram(bins=50)

#flood ratio vs total res
ggplot(data, aes(x=floodRatio,y=log(max_t_counts))) + 
  geom_point()

ggplot(data, aes(x=floodRatio,y=(max_t_counts))) + 
  geom_qq_line()

#calcualting quantile
quantile(data$floodRatio,probs=seq(0,1,0.1))



#jenks break
#install.packages("BAMMtools")
library(BAMMtools)
getJenksBreaks(mGetDistri(data,cname),5)

#unique histogram
hist(data$max_t_counts,nclass=length(unique(data$max_t_counts)))


cname<-"waterLevel"
cname<-"floodedDays"
cname<-"electricityLostDays"
d<-sort(mGetDistri(data,cname))
h<-hist(d,breaks=c(min(d)-1,unique(d)),right=T)
View(data.frame(h$breaks[-1],h$counts))
plot_ly(x=d,type='histogram')
ggplot(data.frame(d),aes(x=d))+geom_histogram(bins=length(unique(d)))+geom_density()
ggplot(data.frame(d),aes(x=d))+geom_density()
qplot(sample=d) #quantile range
zs<-zscore(d)
View(data.frame(unique(zs),unique(d)))
ds<-d[abs(zs)<3.1]

plot_ly(x=ds,type='histogram')
h<-hist(ds,breaks=c(min(d)-1,unique(ds)),right=T)
View(data.frame(h$breaks[-1],h$counts))

quan<-quantile(d)
iqr<-quan[4]-quan[2]

library(dbscan)
dbscan(as.matrix(d))


l=5
a<-kmeans(ds,l)
for (i in 1:l) unique(ds[a$cluster==i]) %>% print




