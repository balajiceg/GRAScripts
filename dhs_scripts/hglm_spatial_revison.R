#import libraries
library(sf)
library(spdep)
library(dplyr)
library(readr)
library(zoom)
library(spatialreg)
library(hglm)

#import study area census tracts
tracts_all <- st_read('Z:/Balaji/indundation_harvey/FloodRatioJoinedAll_v1/FloodInund_AllJoined_v1.gpkg')

#read ED grouped data
ed_groupd <- read_csv('Z:/Balaji/DSHS ED visit data(PII)/groupdED visits_IJDRrevision/allEDgroupdByWeek.csv')
#reformat variables
ed_groupd <- ed_groupd %>% mutate( floodr_cat = relevel(as.factor(floodr_cat),ref = 'NO'),
                      Time = relevel(as.factor(Time),ref = 'control')) %>%
                      mutate(across(c(year,month,weekday,SVI_Cat),as.factor))
#remove na recs
ed_groupd <- ed_groupd %>% filter(complete.cases(.))
summary(ed_groupd)    
ed_groupd_bkp = ed_groupd
#####################################################################
######For Testing
####################################################################

#or sample by buffer
centerFeature <- tracts_all %>% filter(GEOID==48201543100)
res<-st_is_within_distance(centerFeature,tracts_all,dist=50000)[[1]]
req_tracts <- tracts_all[res,]
plot(req_tracts["AWATER"])
ed_groupd <- ed_groupd_bkp %>% filter(PAT_ADDR_CENSUS_TRACT %in% as.numeric(req_tracts$GEOID))
summary(ed_groupd)
##################################################################
#################################################################

#get only tracts in ed records
tracts_sa <- tracts_all%>% mutate(GEOID=as.double(as.character(GEOID))) %>% filter(GEOID %in% unique(ed_groupd$PAT_ADDR_CENSUS_TRACT))
tracts_sa <- tracts_sa %>% mutate(census_unique_id = row_number())
#create neighboruhood weights
nb_queen<-poly2nb(tracts_sa,queen = T,row.names = tracts_sa$census_unique_id)
#######for testing ####
#nb_queen <-knn2nb(knearneigh(st_centroid(tracts_sa$geom), k=5))
###############
summary(nb_queen)

#plot
#plot(tracts_sa$geom, border="grey60")
#plot(nb_queen,st_centroid(tracts_sa$geom),add=TRUE, pch=".")
#zm()

#neightbours to weights
nb_w <- nb2listw(nb_queen,style = 'W')
n_w<-as(nb_w, "CsparseMatrix")


#merge unique census id
ed_groupd <- ed_groupd %>% merge(st_drop_geometry(tracts_sa[,c("GEOID","census_unique_id")]),by.x="PAT_ADDR_CENSUS_TRACT",by.y="GEOID") %>% arrange(census_unique_id)

#normal gee model ----
formula='Outcome ~  floodr_cat * Time * SVI_Cat  + year + month + SEX_CODE_M + op_True + PAT_AGE_YEARS + RACE_white +  RACE_black + ETHNICITY_Non_Hispanic'
#formula='Outcome ~  floodr_cat * Time * SVI_Cat + year + month + weekday  + SEX_CODE_M + op_True + PAT_AGE_YEARS + RACE_white +  RACE_black + ETHNICITY_Non_Hispanic'

# library(geepack)
# gee_model <- geeglm(formula=as.formula(formula), id=census_unique_id, 
#                     offset=log(ed_groupd$Population),
#                     data=ed_groupd, family=poisson(link=log))
# summary(gee_model)
# gc()

#run hglm with spatial----

# HGLM_sar <- hglm(fixed=as.formula(formula), random= ~ 1|census_unique_id,
#                  offset=log(ed_groupd$Population), weights=NULL,
#                  data=ed_groupd, family=poisson(link=log),
#                  rand.family=SAR(D=n_w),verbose = T
#                  )
# summary(HGLM_sar)
# # z matrix created by (number of groups ie. census tracts) * (n row in dataframe)
# 
# 
# hglm wihout spatial ----
HGLM_gen <- hglm(fixed=as.formula(formula), random= ~ 1|census_unique_id,
                 offset=log(ed_groupd$Population), weights=NULL,
                 data=ed_groupd, family=poisson(link=log),
                 verbose = T
)
summary(HGLM_gen)


#clean results
library(broom)
resTab<-tidy(gee_model, exponentiate = T)
conf<-confint.default(gee_model)
resTab=cbind(resTab,exp(unname(conf)))
colnames(resTab)[c(6,7)] <- c('95p_lowConf','95p_upConf')
write.table(resTab,'clipboard',sep='\t',row.names = F)



resTab<-data.frame(summary(HGLM_sar)$FixCoefMat)
resTab$`95p_lowConf` <- exp(resTab$Estimate -  1.96 * resTab$Std..Error)
resTab$`95p_upConf`<- exp(resTab$Estimate +  1.96 * resTab$Std..Error)
resTab$Estimate <- exp(resTab$Estimate)
write.table(resTab,'clipboard',sep='\t',row.names = T)
