# R code for creating honey comb shape files to quantify responses of HHR per grid as well as 
# comparing the % of differnce between the reported home flooding and remote sensed flooding
#load libararies
library(sf)
library(raster)
library(dplyr)
library(caret)
#read data
all_df<- st_read('../practis_layer.gpkg') %>% st_drop_geometry()

#make spatila
all_df<-st_as_sf(all_df,coords = c("x","y"),crs=CRS("+proj=longlat +datum=WGS84"))
#transform
all_df<-st_transform(all_df,CRS("+init=epsg:6579"))


#read raster
ras <- raster('./MFED/aer_mfed_acc_3s_20170827-20170909_v05r01.tif')
aer_flood = ras$aer_mfed_acc_3s_20170827.20170909_v05r01 ==1

aer_flood = projectRaster(aer_flood,crs = CRS("+init=epsg:6579"),method = 'ngb')

plot(aer_flood,axes = TRUE)
plot(all_df$geometry, add=T)


#extract the values
extracted <- extract(aer_flood, all_df, df=T, cellnumbers=T)
#reinsert true respondent flooding values
extracted$respFlooded <- all_df$id


groupVal <- extracted %>% group_by(cells) %>% summarise(respFlooded=mean(respFlooded),layer=mean(layer))
groupVal$respFloodedBool <- as.integer(groupVal$respFlooded >=0.5)


#caret library
with(groupVal,(confusionMatrix(data=factor(layer), reference=factor(respFloodedBool))))
