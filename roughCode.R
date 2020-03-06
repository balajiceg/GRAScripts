







#----------------------------------------------------------------------------
# junk code trials---------------


#check missinginsess of data
for (i in names(x)){
print(paste0(i,": ",sum(x[[i]]==0,na.rm=T )),quote=F)
}

for (i in names(x)){
  print(paste0(i,": ",sum(is.na(x[[i]]),na.rm=T)),quote=F)
}

for (i in names(x)){
  print(paste0(i,": ",sum(!is.na(x[[i]]) & x[[i]]!=0,na.rm=T)),quote=F)
}

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




