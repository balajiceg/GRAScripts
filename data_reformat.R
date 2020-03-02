#loading required packages
library(raster)
library(rgdal)
library(GISTools)
library(plotly)

# library(mapview)



#census tracts
tracts<-readOGR('./flood_aggregates',layer='flood_ratio_200')
inun_data<-tracts@data[,c("GEOID","floodRatio","geom_area")]
colnames(inun_data)[1]<-"tractId"

#histogram table for flood ratio
hist_table<-hist(inun_data$floodRatio*100,breaks=c(0,1,3,seq(5,100,5)))
hist_table<-data.frame(hist_table$breaks[-1],hist_table$counts,hist_table$density)


#harricane harvey data
hhd_data<-read.csv('\\\\vetmed2.vetmed.w2k.vt.edu\\Blitzer\\NASA project\\Balaji\\HHR_20191001_CT\\HHR_20191001_CT_NonDemoVars_v01.csv')

#rename columns
colnames(hhd_data)<-c('tractId','variables','values','no_of_reponses','total_responses')

#unique questions
questions<-unique(hhd_data$variables)
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
#tracts in dataset
unq_tracts<-unique(hhd_data$tractId)

#for each question
for(i in 1:length(questions)){
  #subest the rows with the question
  rows<-subset(hhd_data,variables==questions[i])
  unq_values<-unique(rows$values)
  
  #create df for this ques
  df<-data.frame(matrix(nrow=length(unq_tracts),ncol=length(unq_values)+1))
  
  #create one col per value
  colnames(df)<-c(paste0(questions_short[i],'_',unq_values),paste0(questions_short[i],'_t'))
  df$tractId<-unq_tracts

  # for each census tract
  for(j in 1:length(unq_tracts)){
    tract<-unq_tracts[j]
    #subset the count for tracts
    sub_tract<-subset(rows,tractId==tract)
    
    df[j,paste0(questions_short[i],'_t')]<-sub_tract$total_responses[1]
    #for each value in various answers in a tract
    k<-1
    for(value in unq_values){
      #subset for the particular value
      sub<-subset(sub_tract,values==value)
      if(nrow(sub)!=0){
        df[j,k]<-sub$no_of_reponses
        
      }
      else{df[j,k]<-0}
      k<-k+1
    }
    
  }
  
  #join the df of each question
  if(i==1) joined<-df
    else joined<-merge(x = joined, y = df, by = "tractId", all = TRUE)
}
#creating the max column
tot_cols<-joined[,grep("_t",names(joined))]
joined$max_t_counts<-apply(tot_cols,1,max,na.rm=T)

#joining SVI
svi_s<-readOGR('D:/texas/spatial/Texas_SVI_tracts',layer='TEXAS')
svi<-svi_s@data[,c("FIPS","RPL_THEMES")]
names(svi)<-c("tractId","SVI")
filterd_svi<-svi[svi$tractId %in% joined$tractId,]
joined<-merge(joined,filterd_svi,by="tractId",all.x=T)

#merge the inundation data
merged<-merge(joined,inun_data,by='tractId',all.x=T)

#create merged shape file
filtered_tract<-tracts[tracts$GEOID %in% merged$tractId,]
filtered_tract@data<-filtered_tract@data[,c("GEOID","floodRatio","geom_area")]
colnames(filtered_tract@data)[1]<-"tractId"

filtered_tract<-merge(filtered_tract,joined,by='tractId',all.x=T)
writeOGR(filtered_tract,dsn = '\\\\vetmed2.vetmed.w2k.vt.edu\\Blitzer\\NASA project\\Balaji\\HHR_20191001_CT\\joined_shp_nondemos.gpkg',layer='joined_nondemos',overwrite_layer = T,driver='GPKG')

#write the joined table to save the work
write.csv(merged,'\\\\vetmed2.vetmed.w2k.vt.edu\\Blitzer\\NASA project\\Balaji\\HHR_20191001_CT\\joined_table_nondemos.csv',row.names = F)
