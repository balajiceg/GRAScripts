#code to compare evacuation rate to tract's demographics

library(readr)
library(tidyr)
library(forcats)
library(openxlsx)
library(lmtest)
library(broom)

#----read evacuation data----
evacDf_raw=read_csv('//vetmed2/Blitzer/NASA project/Balaji//EvacuationDataDrSamarth//all_feature_values.csv')
evacDf=evacDf_raw %>% dplyr::rename(evacRate=evacuation_rate,evacCount=evacuate_count) %>%
  select(FIPS,date,evacCount,evacRate)
#create max/sum columns for the three variables
evacDfMax = evacDf %>% dplyr::select(-date) %>% group_by(FIPS) %>% dplyr::summarise_all(sum) %>% 
  rename_at(vars(-FIPS),function(x) paste0(x,"Sum"))

#----read population data ----
acsD05 = read_csv('//vetmed2/Blitzer/NASA project/Balaji/Census_data_texas/population/ACS_17_5YR_DP05_with_ann.csv')
acsD05 = acsD05 %>% select(GEO.id2,HC03_VC92,HC03_VC93,HC03_VC99,HC03_VC100,HC03_VC101,HC03_VC102,HC03_VC103,HC03_VC104)%>%
          filter(GEO.id2!='Id2') %>% mutate_all(as.numeric)
acsD05 = acsD05 %>% mutate(OtherRace=HC03_VC101+HC03_VC102+HC03_VC103+HC03_VC104) %>%
  rename(NH_White=HC03_VC99,NH_Black=HC03_VC100,Hispanic=HC03_VC93,population=HC03_VC92) %>% select(-c(HC03_VC101:HC03_VC104))
#----merge population data to evac ----
evacDfMax= evacDfMax %>% left_join(acsD05,by=c('FIPS'='GEO.id2'))

#run poisson regression to see how evaction varries by tracts 
model = glm(evacCountSum ~ NH_White +  Hispanic + NH_Black ,family = poisson, data = evacDfMax,
            offset=log(population))
summary(model)
resTab = tidy(model, exponentiate = T)
resTab = bind_cols(resTab , confint.default(model) %>% exp %>% as_tibble)
resTab<-resTab[,c("term", "estimate","2.5 %",  "97.5 %","p.value", "std.error")]
resTab
