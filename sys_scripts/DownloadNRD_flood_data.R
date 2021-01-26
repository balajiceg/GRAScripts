##---- for download NRD global flood mapping data ----
library(RCurl)

#date range
dates<-as.character(seq(from=as.Date('2019-05-01'),to=as.Date('2019-10-31'),by="day"))

#type of data: 14 day composite/ 3day / 2day - A14x3D3OT_V /3D3OT_V / 2D2OT_V
type<- "2D2OT_V"

#required grid
grid<-"100W040N"

#file type .zip(shp) / .kmz
f_type<- ".zip"

#base url -- for ex 14 day product url https://floodmap.modaps.eosdis.nasa.gov/Products/100W040N/2019/MFW_2019272_100W040N_A14x3D3OT_V.zip
base_url<-"https://floodmap.modaps.eosdis.nasa.gov/Products/"
error_dates<-c()
for(date in dates){
  print(date)
  #frame the url
  day_of_year<- strftime(date, format = "%j")
  year<- substring(date,1,4)
  download_url<- paste0(base_url,grid,'/',year,'/','MFW_',year,day_of_year,'_',grid,'_',type,f_type)
  
  #download the file
  destfile = paste0('MFW_',year,day_of_year,'_',grid,'_',type,f_type)
  tryCatch(download.file(download_url,destfile = destfile),error=function(e){})
  
  if(f_type=='.zip'){
    #unzip the file
    msg<-tryCatch(unzip(destfile),error=function(e) e, warning=function(w) w)
    if(is(msg,"warning")) {
      print(paste0(destfile,' not zipping'))
      error_dates<-c(error_dates,date)
    }
    #delete the zip files
    file.remove(destfile)
  }
}

##----- REad assign dates to shpes and merge everthing together
library(GISTools)
library(rgdal)

#read all shp files
shp_files<-list.files(path = ".", pattern = '*.shp' )

merged_feature<-c()
for(shp_file in shp_files){
  features<-readOGR(dsn='.',layer = substr(shp_file,1,nchar(shp_file)-4),verbose = F )
  
  feature_data<-features@data
  #add date columun and grid column
  feature_data$GRID<- unlist(strsplit(shp_file,'_'))[3]
  file_date<-unlist(strsplit(shp_file,'_'))[2]
  file_date<-as.Date(file_date,format = '%Y%j')
  cat(paste0(as.character(file_date),'\n'))
  feature_data$to_date<- as.character(file_date)
  feature_data$from_date<- as.character(file_date - 1)
  features@data<-feature_data
  #put into the list
  merged_feature<-c(merged_feature,features)
}

#set proj for those not set
proj_taken<-proj4string(merged_feature[[1]])
for(i in 1:length(merged_feature)){
  if(is.na(proj4string(merged_feature[[i]]))){
    proj4string(merged_feature[[i]])<-proj_taken
  }
}

#merge everything together
merged_features<-do.call('rbind',merged_feature)

#write each month separately
# months<- unique(substr(unique(merged_features$to_date),6,7))
# for(month in months){
#   month_subset<-subset(merged_features,substr(merged_features$to_date,6,7)==month)
#   writeOGR(month_subset,dsn="merged",layer=paste0('merged_month_',month),driver = 'ESRI Shapefile')
# }
#write the entire thing if required
writeOGR(merged_features,dsn="merged",layer='merged_all_month',driver = 'ESRI Shapefile')

