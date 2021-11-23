# R code for creating count of responses from HHR dataset per census tract or per county

#load libararies
library(sf)
library(rgdal)
library(raster)
library(dplyr)
library(RColorBrewer)
library(mapview)
library(ggplot2)

#read data
all_df<-read.csv('K:\\Projects\\FY2020-018_HHR_Outcomes\\EoFloodHealth\\Data\\Draft\\ProcessedTFR\\TFRHarveyRecordsInclPaperSurWithInundNSVI.csv',stringsAsFactors = F)

#records filtered in main analysis
load('K:\\Projects\\FY2020-018_HHR_Outcomes\\EoFloodHealth\\Data\\Draft\\ProcessedTFR\\ResponseIdsFilterdForStudy.Rdata')

#subset data with geocoding and those filtered for analysis-> removes 633 records
all_df<-subset(all_df,SurveyResponseID %in% SurveyResponseIDs)

#create county id
all_df$countyID10<-all_df$tractID10%/%1e6
#groupby county
cnty_grouped<- all_df %>% group_by(countyID10) %>% summarise(
  nHomeFlooded = sum(HomeFlooded,na.rm=T),
  nTotal=n()
  #perct=sum(HomeFlooded,na.rm=T)/n()
)
#sensor values for total less than 5
cnty_grouped[,c("nHomeFlooded", "nTotal")]<-cnty_grouped[,c("nHomeFlooded", "nTotal")] %>% 
                                                                sapply(function(x){
                                                                  x[x>0 & x<5]<--999
                                                                  return(x)
                                                                })
#read county boundaries
cnty_bnd<-st_read(dsn='K:\\Projects\\FY2020-018_HHR_Outcomes\\EoFloodHealth\\Code\\Draft\\GIS\\TFR_analysis\\TFR_analysis.gdb',layer='CEN_2010_TX_CNTY_BOUNDARY')
#merege
cnty_bnd<-merge(cnty_bnd["GEOID_NUM"],cnty_grouped,by.x="GEOID_NUM",by.y="countyID10",all.x=F,all.y=T)
#st write
st_write(cnty_bnd,'countyGrouped.shp')
st_write(cnty_bnd,'countyGrouped.gpkg')


#groupby census tracts
ct_grouped<- all_df %>% group_by(tractID10) %>% summarise(
  nHomeFlooded = sum(HomeFlooded,na.rm=T),
  nTotal=n()
  #perct=sum(HomeFlooded,na.rm=T)/n()
)
#sensor values for total less than 5
ct_grouped[,c("nHomeFlooded", "nTotal")]<-ct_grouped[,c("nHomeFlooded", "nTotal")] %>% 
  sapply(function(x){
    x[x>0 & x<5]<--999
    return(x)
  })
#read county boundaries
ct_bnd<-st_read(dsn='K:\\Projects\\FY2020-018_HHR_Outcomes\\EoFloodHealth\\Code\\Draft\\GIS\\TFR_analysis\\TFR_analysis.gdb',layer='CEN_2010_TX_TRT_BOUNDARY')
#merege
ct_bnd<-merge(ct_bnd["GeoidNum"],ct_grouped,by.x="GeoidNum",by.y="tractID10",all.x=F,all.y=T)
ct_bnd$GeoidNum<-as.character(ct_bnd$GeoidNum)
#st write
st_write(ct_bnd,'tractGrouped.shp')
st_write(ct_bnd,'tractGrouped.gpkg')
