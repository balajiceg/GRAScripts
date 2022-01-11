#rought trial codes used during the code createion
xx<-lapply(tfr_data,function(x)(unique(x)))

library(spdep)
library(DHARMa)
simRes<-simulateResiduals(model)
recalRes<-recalculateResiduals(simRes,group = paste0(mcoords[,1],mcoords[,2],sep=''))
mcoords1<-mcoords[!duplicated(mcoords),]
testSpatialAutocorrelation(recalRes, mcoords1[,1] ,  mcoords1[,2], plot = T)

library(spind)
GEE(formula=as.formula(mformula),data=df,corstr = 'fixed',family=poisson(),coord = mcoords)
#mark duplicates
latLonTxt<-paste0(df$X,df$Y,sep='')
mtab<-table(latLonTxt)
df[(mtab>1),'dup']<-rownames(mtab)[mtab>1]
df[latLonTxt %in% rownames(mtab)[mtab>1],'dup']<-'xx'
df$dup[!is.na(df$dup)]<-latLonTxt[!is.na(df$dup)]
df$dup<-as.factor(df$dup)
levels(df$dup)<-seq(length(levels(df$dup)))
View(table(df$dup,df$HomeFlooded))

#----- gee using spind -----
library(spind)
mcoords<-as.data.frame(lapply(df[,c('X','Y')],as.integer))
mcoords$X<-(mcoords$X-min(mcoords$X))%/%1000
mcoords$Y<-(mcoords$X-min(mcoords$Y))%/%1000
GEE(formula=as.formula(mformula),data=df,corstr = 'fixed',family='poisson',coord =mcoords)

#forming neighbour hood weights
plot(sfPoints$geometry,axes=T)
coords<-df[,c('X','Y')]
coords$X<-as.integer(coords$X)
coords$Y<-as.integer(coords$Y)
coords<-as.matrix(coords)


coords<-st_coordinates(sfPoints)
library(spdep)
dnbrs <- dnearneigh(coords, 0, 1000)
nbrs<-tri2nb(coords)

nbrsinter<-intersect.nb(dnbrs,nbrs)
weights<-nb2listw(nbrsinter,zero.policy = TRUE)


#plot neighbors, 
plot(sfPoints$geometry, border="grey60",axes=T,xlim=c(19e5,19.1e5),ylim=c(73e5,73.1e5))
plot(nbrsinter,coords, add=TRUE, pch=".")

#nbrsAsSf<-nb2lines(nbrsinter,coords = sfPoints$geometry,as_sf=T)
moran.test(mRes,listw = weights,zero.policy=T)

#=================================================================#
##------- check which results doesn't have sufficeint counts -----

library(dplyr)
library(tidyverse)
files<-c(list.files('D:\\NASAProjectFiles\\Analysis_HHR\\working_files\\modelOutputs_crossTabsOnly\\modelOutputs\\CrossTabModelRecords',full.names = T),
         list.files('D:\\NASAProjectFiles\\Analysis_HHR\\working_files\\modelOutputs_ContactWater_crossTabsOnly\\modelOutputs_ContactWater\\CrossTabModelRecords',full.names = T))
dfs<-data.frame()

for(mfile in files){
  dfs<-bind_rows(dfs,read.csv(mfile))
}
#filter interaction models seperately
inter_counts<-filter(dfs,!is.na(X5)) %>% rename(outcome=X1,exposure=X2,inter=X3,freq=X4,formula=X5)
main_counts<-filter(dfs,is.na(X5)) %>% select(-X5) %>% rename(outcome=X1,exposure=X2,freq=X3,formula=X4)

#remove headings and check
main_counts<-mutate(main_counts,freq=parse_number(freq)) %>% filter(!is.na(freq))
inter_counts<-mutate(inter_counts,freq=parse_number(freq)) %>% filter(!is.na(freq))


main_counts%>% filter(freq<15) %>% select(formula) %>% unique# %>% write.table('clipboard')
inter_counts%>% filter(freq<5) %>% select(formula,freq) %>% 
      separate(formula,c('formula'),sep='\\+') %>% separate(formula,c('outcome','interaction'),sep='~') %>% filter(!duplicated(interaction))  %>% arrange(interaction) %>% write.table('clipboard',sep = '\t')
