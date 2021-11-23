# R code for creating honey comb shape files to quantify responses of HHR per grid as well as 
# comparing the % of differnce between the reported home flooding and remote sensed flooding
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
all_df<-subset(all_df,!is.na(fScanInundDist))

#create discripancy table
#when Dis =0 the point lies withing the pixel not necessarlity in the center of the pixel
Dis<-0
all_df$hTrueRsTrue<-as.integer((all_df$HomeFlooded==1)&(all_df$fScanInundDist<=Dis))
all_df$hTrueRsFalse<-as.integer((all_df$HomeFlooded==1)&(all_df$fScanInundDist>Dis))
all_df$hFalseRsTrue<-as.integer((all_df$HomeFlooded==0)&(all_df$fScanInundDist<=Dis))
all_df$hFalseRsFalse<-as.integer((all_df$HomeFlooded==0)&(all_df$fScanInundDist>Dis))

#make spatila
all_df<-st_as_sf(all_df,coords = c("X","Y"),crs=CRS("+proj=longlat +datum=WGS84"))

#transform
all_df<-st_transform(all_df,CRS("+init=epsg:6579"))
plot(all_df$geometry,axes = TRUE)

#create grids
grid <- st_make_grid(st_as_sf(all_df),
                     8.75 * 1000, # Kms
                     crs = st_crs(all_df),
                     what = "polygons",
                     square = FALSE )
# Make sf
grid <- st_sf(grid_id = 1:length(lengths(grid)), grid) # Add index

#spatial join
all_df<-st_join(all_df,grid,join=st_intersects)

#make grid
groupedDf <- all_df %>% group_by(grid_id) %>% summarise(
  hTrueRsTrue = sum(hTrueRsTrue,na.rm = T),
  hTrueRsFalse = sum(hTrueRsFalse,na.rm = T),
  hFalseRsTrue = sum(hFalseRsTrue,na.rm = T),
  hFalseRsFalse = sum(hFalseRsFalse,na.rm = T),
  nHomeFlooded = sum(HomeFlooded,na.rm=T),
  hTotal=n()
) %>% st_drop_geometry

#merge data
grid<-merge(grid,groupedDf,by='grid_id')

#create proportions
for(i in c( "hTrueRsTrue",   "hTrueRsFalse" , "hFalseRsTrue" , "hFalseRsFalse","nHomeFlooded")){
 grid[,paste0(i,'_perct')] <- st_drop_geometry(grid[i])/grid$hTotal
}

#create differnce collumn
grid$hVsRsDisaggCount<-grid$hTrueRsFalse+grid$hFalseRsTrue

# remove columns other than total and disagreement and remove the rest
grid<-grid[,c("grid_id" ,"nHomeFlooded", "hTotal","hVsRsDisaggCount")]
grid_data<-st_drop_geometry(grid)
grid_data[,c("nHomeFlooded", "hTotal","hVsRsDisaggCount")]<-grid_data[,c("nHomeFlooded", "hTotal","hVsRsDisaggCount")] %>% 
                                                                        sapply(function(x){
                                                                          x[x>0 & x<5]<--999
                                                                          return(x)
                                                                        })
grid<-st_set_geometry(grid_data, grid$geometry)



#ggplot(grid) + geom_sf(aes(fill=hTrueRsTrue)) + geom_sf(data=all_df)

#read raster 
inundation<-raster('K:/Projects/FY2020-018_HHR_Outcomes/EoFloodHealth/Data/InputData/floodscan_hurricane_harvey_p00/MFED/aer_mfed_acc_3s_20170827-20170909_v05r01.tif')
inundation[inundation!=1]<-0
#project raster
inundation<-crop(inundation,st_transform(grid,4326))
#inundation<-projectRaster(inundation,crs=st_crs(grid)$proj4string,method = 'ngb')
mapview(inundation,col.regions=c('#ffffff','#ff0000')) +
  mapview(grid,zcol="hTrueRsFalse_perct",col.regions=blues9)+mapview(grid,zcol="hFalseRsTrue_perct",col.regions=blues9)
#output grid
st_write(grid,'discripancyHexagons_4_75km_suppressedLt5.shp')
st_write(grid,'discripancyHexagons_4_75km_suppressedLt5.gpkg')
