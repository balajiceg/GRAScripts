library(readr)
library(geepack)
library(dplyr)
library(sandwich)
library(lme4)
library(sf)
library(tidyr)
library(forcats)
library(fastDummies)
library(broom)
library(openxlsx)
library(corrplot)
library(lmtest)

outputDir = '//vetmed2/Blitzer/NASA project/Balaji/AnaysisIPOPdrSamarth/23122021/'

select = dplyr::select
#----read Ed visites from cleaned file----
EdData=read_csv('//vetmed2/Blitzer/NASA project/Balaji/R session_home_dir (PII)//spOutputToR.csv',col_types = 'dddddffifdldddfdifffffllllllll')

#rename insect bite and remove the row ID column
EdData= EdData %>% dplyr::rename(InsetBite='Bite-Insect') %>% dplyr::select(-X1) %>% as_tibble

#----Read flood scan data and merge based on date----
AerMFED = st_read("Z:/Balaji/indundation_harvey/censusTractsFloodScan_MFED/censusTractsFloodScan_MFED.gpkg")
#replace na with 0 for flood ratio
AerMFED = AerMFED %>% st_drop_geometry %>% select(GEOID,ends_with('Ratio')) %>% as_tibble() %>% replace(is.na(.), 0)
#reformat data
AerMFED = AerMFED %>% select(-WmaxFloodRatio) %>% pivot_longer(cols = ends_with('ratio'),values_to ='AERfRatio') %>% 
            separate(name,c(NA,'Date',NA),sep=c(1,9,15)) %>% 
            merge(AerMFED %>% select(GEOID,WmaxFloodRatio),by='GEOID',all.x=T) %>%
            mutate(Date=as.double(Date),GEOID=as.double(as.character(GEOID))) %>%
            dplyr::rename(AERMaxfRatio=WmaxFloodRatio)

#----read evacuation data----
evacDf_raw=read_csv('//vetmed2/Blitzer/NASA project/Balaji//EvacuationDataDrSamarth//all_feature_values.csv')
print(colnames(evacDf_raw))
evacDf=evacDf_raw %>% dplyr::rename(floodDur=flooding_duration_hr,
                             triProxDur=tri_close_proximity_duration_hr, triDist=tri_distance_mi,
                             hvyRainDur=heavy_rainfall_duration_hr, totRain=rainfall_total_mm,
                             evacRate=evacuation_rate,
                             distFlood=dist_in_flooding_mi, #distance travelled through flooding
                             evacFloodDur=evacuate_flooding_duration_hr,shelFloodDur=shelter_flooding_duration_hr,
                             evacDistFlood=evacuate_dist_in_flooding_mi,shelDistFlood=shelter_dist_in_flooding_mi,
                             evacHvyRainDur=evacuate_heavy_rainfall_duration_hr,shelHvyRainDur=shelter_heavy_rainfall_duration_hr,
                             evacTotRain=evacuate_rainfall_total_mm,shelTotRain=shelter_rainfall_total_mm,
                             evacTriProxDur=evacuate_tri_close_proximity_duration_hr,shelTriProxDur=shelter_tri_close_proximity_duration_hr,
                             evacTriDist=evacuate_tri_distance_mi,shelTriDist=shelter_tri_distance_mi,
                             evacCount=evacuate_count,shelCount=shelter_count)

evacDfCols = evacDf %>% select(-c(FIPS,date)) %>% colnames
  
#create max/sum columns for the three variables
evacDfMax = evacDf %>% dplyr::select(-date) %>% group_by(FIPS) %>% dplyr::summarise_all(sum) %>% 
                rename_at(vars(-FIPS),function(x) paste0(x,"Sum"))

#----subset df for census tracts in evac df----
EdEvac= EdData[EdData$PAT_ADDR_CENSUS_TRACT %in% evacDf$FIPS ,]

#remove some unwanted columns from EDevac
EdEvac = EdEvac %>% select(-c(PAT_ADDR_CENSUS_BLOCK_GROUP,RECORD_ID,PAT_STATUS,PAT_ZIP,floodr,floodr_cat))

#relevel categories
#EdEvac = EdEvac %>% mutate(floodr_cat=factor(floodr_cat,levels=c('NO','FLood_1')))

#reformat date in the evacDf
evacDf$date<- as.double(paste0(2017,gsub('_','',evacDf$date)))

#----merge evacDF----
EdEvac= EdEvac %>% merge(evacDf,all.x = T,by.x = c('PAT_ADDR_CENSUS_TRACT','STMT_PERIOD_FROM'),by.y=c('FIPS','date'))
#merge evacMaxDf
EdEvac= EdEvac %>% merge(evacDfMax,all.x = T,by.x = c('PAT_ADDR_CENSUS_TRACT'),by.y=c('FIPS'))

#merge AER Flood scan  ------ 
EdEvac= EdEvac %>% merge(AerMFED %>% select(-AERMaxfRatio)
                         ,all.x = T,by.x = c('PAT_ADDR_CENSUS_TRACT','STMT_PERIOD_FROM'),by.y=c('GEOID','Date'))
#----merge AER Flood scan----
EdEvac= EdEvac %>% merge(AerMFED %>% select(GEOID,AERMaxfRatio) %>% filter(!duplicated(GEOID))
                         ,all.x = T,by.x = c('PAT_ADDR_CENSUS_TRACT'),by.y=c('GEOID'))

#----remove the some df to save memeory----
remove(EdData)
remove(evacDf_raw)
#remove(evacDfMax)
remove(AerMFED)

#remove records with nas
EdEvac =  EdEvac[complete.cases(EdEvac[,c("RACE","SEX_CODE", "PAT_AGE_YEARS" , "ETHNICITY")]),]

#----tweak the control period as per AER flood scan dates----
EdEvac[EdEvac$STMT_PERIOD_FROM==20170826,'Time'] = 'washout'
EdEvac[EdEvac$STMT_PERIOD_FROM>=20170910 & EdEvac$STMT_PERIOD_FROM<=20180000,'Time'] = 'PostFlood1'

#remove the Washout period records if wanted
#EdEvac = EdEvac %>% filter(Time!='washout') %>% droplevels()

#----tweak periods as per the evacutation dataset----
EdEvac = EdEvac %>% mutate(EvacPeriod=fct_recode(Time,evacuation="washout")) 
EdEvac[EdEvac$STMT_PERIOD_FROM>=20170818 & EdEvac$STMT_PERIOD_FROM<=20170828,'EvacPeriod'] = 'evacuation'

#fix days from start variable
DayFromStart = EdEvac %>% select(STMT_PERIOD_FROM) %>% unique() %>% arrange(STMT_PERIOD_FROM) %>% mutate(DayFromStart=row_number())
#DayFromStart$DayFromStart[DayFromStart$STMT_PERIOD_FROM>20170817 & DayFromStart$STMT_PERIOD_FROM<20170910] = seq(length(DayFromStart$DayFromStart[DayFromStart$STMT_PERIOD_FROM>20170817 & DayFromStart$STMT_PERIOD_FROM<20170910]))
#DayFromStart$DayFromStart[DayFromStart$STMT_PERIOD_FROM>20170909 & DayFromStart$STMT_PERIOD_FROM<20180000] = seq(24,136)
EdEvac = EdEvac %>% select(-DayFromStart) %>% merge(DayFromStart,by='STMT_PERIOD_FROM',all.x = T)

#----change fooding and other exposures before control to 0----
EdEvac[EdEvac$Time=='control',c("AERfRatio",evacDfCols)]=0
EdEvac[EdEvac$Time=='washout',c("AERfRatio")]=0
#----change flooding and other exposures for post flood period to max or sum ----
i=(EdEvac$Time=='PostFlood1')
EdEvac$AERfRatio[i] = EdEvac$AERMaxfRatio[i]
for(colum in evacDfCols){
  EdEvac[i,colum] = EdEvac[i,paste0(colum,'Sum')]
}


#change flood period as well to max in case of evacuation variables
i=(EdEvac$EvacPeriod=='flood')
for(colum in evacDfCols){
  EdEvac[i,colum] = EdEvac[i,paste0(colum,'Sum')]
}

#drop max columns
#EdEvac = EdEvac %>% select(-c(floodDurSum:evacRateSum))


#remove unused factor levels
EdEvac = EdEvac %>% droplevels()

#create list of evac variables to be used
evacVars = evacDfCols[!(evacDfCols %in% c("evacCount","shelCount","count","shelDistFlood"))]
# ___________ Data cleaning ends here ____________________ ----

 # All ED visits analysis by groupoing ----
#group df 
grpEdEvac = EdEvac %>% dummy_cols(select_columns = c("RACE", "SEX_CODE","ETHNICITY"), remove_first_dummy = T, remove_selected_columns = T) %>% 
                  group_by(PAT_ADDR_CENSUS_TRACT, STMT_PERIOD_FROM) %>% 
                  summarise(DailyED=n(),PAT_AGE_YEARS=mean(PAT_AGE_YEARS),
                            RACE_black=sum(RACE_black)/n(),RACE_other=sum(RACE_other)/n(),
                            SEX_CODE_F=sum(SEX_CODE_F)/n(),
                            ETHNICITY_Hispanic=sum(ETHNICITY_Hispanic)/n(),
                            op=mean(op)) 
#merge needed columns
grpEdEvac = EdEvac %>% select(c("STMT_PERIOD_FROM","PAT_ADDR_CENSUS_TRACT",
                    "Population","Time","month","year","weekday",
                    "AERfRatio", "AERMaxfRatio",
                    "EvacPeriod","DayFromStart",
                    evacDfCols,paste0(evacDfCols,"Sum"))) %>% filter(!duplicated(.)) %>%
                    inner_join(grpEdEvac,by = c("STMT_PERIOD_FROM","PAT_ADDR_CENSUS_TRACT"))

#categorize AER max variable
#only 88 non flooded tracts
# grpEdEvac %>% select(PAT_ADDR_CENSUS_TRACT,AERMaxfRatio) %>% filter(!duplicated(.)) %>% 
#               mutate(AERMaxfRatio=AERMaxfRatio==0) %>% select(AERMaxfRatio) %>% summary()
grpEdEvac=grpEdEvac %>% mutate(AERFlooded=AERMaxfRatio>0)

# _run models for grouped df based ----
# ___interupted time series on grouped ----
# allRes<- NA
# allSum=''
# grpEdEvacOnlyControlEvac = grpEdEvac %>% select(-c(colnames(grpEdEvac)[grep('Sum',colnames(grpEdEvac))])) %>%
#                                          filter(EvacPeriod %in% c('control','evacuation')) %>% droplevels()
# for(evacVar in evacVars){
#   
#   mformula= paste0('DailyED ~ ',evacVar,' * DayFromStart + year + month + weekday +  RACE_other + RACE_black + SEX_CODE_F + PAT_AGE_YEARS + ETHNICITY_Hispanic + op') # + hvyRainDur'
#   model=glm(data=grpEdEvacOnlyControlEvac, formula=as.formula(mformula),family = poisson(),
#             offset = log(grpEdEvacOnlyControlEvac$Population))
#   summary(model)
#   aic = AIC(model)
#   
#   #broom results
#   resTab = tidy(model, exponentiate = T)
#   resTab = bind_cols(resTab , confint.default(model) %>% exp %>% as_tibble)
#   resTab<-resTab[,c("term", "estimate","2.5 %",  "97.5 %","p.value", "std.error")]
#     #insert exposure,outcome and formula and Aic
#   resTab$aic<-aic
#   
#   resTab$evacVar<-evacVar
#   resTab$formula<-mformula
#   
#   #prepare raw summary file
#   sumTxt<-paste0(c(capture.output(summary(model)),
#                    'Time:',as.character(Sys.time()),'\n'),collapse = '\n')
#   #replace formula with orginal formula
#   sumTxt<-gsub('mformula',mformula,sumTxt)
#   
#   #add to all output stored df and str
#   if(is.na(allRes)) allRes<-resTab else allRes<-rbind(allRes,resTab)
#   allSum<-paste0(allSum,sumTxt,sep=paste0(rep('=',100),collapse=''))
#   
#   print(mformula)
# }
# allRes$outcome<-'TotalED'
# allRes$model<-"ITS"
# allRes$evacVarQuantilesUsed <- "NA"
# write.xlsx(allRes, file=paste0(outputDir,'ITSmodel.xlsx'), sheetName = "Sheet1",col.names = TRUE, row.names = TRUE, append = FALSE)
# cat(allSum,file = paste0(outputDir,'ITSmodel.txt'))


# ___interupted time series on grouped  for evacuation period alone----
allRes<- NA
allSum=''
grpEdEvacOnlyEvac = grpEdEvac %>% select(-c(colnames(grpEdEvac)[grep('Sum',colnames(grpEdEvac))])) %>%
                                         filter(EvacPeriod %in% c('evacuation')) %>% droplevels()
for(evacVar in evacVars){

  mformula= paste0('DailyED ~ ',evacVar,' * DayFromStart +  RACE_other + RACE_black + SEX_CODE_F + PAT_AGE_YEARS + ETHNICITY_Hispanic + op') # + hvyRainDur'
  model=glm(data=grpEdEvacOnlyEvac, formula=as.formula(mformula),family = poisson(),
            offset = log(grpEdEvacOnlyEvac$Population))
  summary(model)
  aic = AIC(model)

  #broom results
  resTab = tidy(model, exponentiate = T)
  resTab = bind_cols(resTab , confint.default(model) %>% exp %>% as_tibble)
  resTab<-resTab[,c("term", "estimate","2.5 %",  "97.5 %","p.value", "std.error")]
    #insert exposure,outcome and formula and Aic
  resTab$aic<-aic

  resTab$evacVar<-evacVar
  resTab$formula<-mformula

  #prepare raw summary file
  sumTxt<-paste0(c(capture.output(summary(model)),
                   'Time:',as.character(Sys.time()),'\n'),collapse = '\n')
  #replace formula with orginal formula
  sumTxt<-gsub('mformula',mformula,sumTxt)

  #add to all output stored df and str
  if(is.na(allRes)) allRes<-resTab else allRes<-rbind(allRes,resTab)
  allSum<-paste0(allSum,sumTxt,sep=paste0(rep('=',100),collapse=''))

  print(mformula)
}
allRes$outcome<-'TotalED'
allRes$model<-"ITS_evacuationDaysOnly"
allRes$evacVarQuantilesUsed <- "NA"
write.xlsx(allRes, file=paste0(outputDir,'ITSmodel_evacPeriod.xlsx'), sheetName = "Sheet1",col.names = TRUE, row.names = TRUE, append = FALSE)
cat(allSum,file = paste0(outputDir,'ITSmodel_evacPeriod.txt'))




# ___using max values from the evacuation models ----

#function to form tertiles ignoring zeros----
form_tertile<-function(x)
  unname(`if`(quantile(x,1/3)==0,c(0,1e-8,quantile(x[x!=0],c(0.5,1))),quantile(x,seq(0,1,1/3))))

#model.matrix(~EvacPeriod* totRainSum,data=grpEdEvac) %>% as_tibble%>% select(-`(Intercept)`)  %>% cor %>% corrplot(method='pie')
allRes<- NA
allSum=''
allCrosTabs<-data.frame()
for(evacVarType in c('linear','tertile'))
for(formula_add in c(" * AERFlooded",""))
for(evacVar in paste0(evacVars,'Sum')){
  #categorise if needed
  if(evacVarType=='tertile'){
    tertile = form_tertile(unlist(evacDfMax[,evacVar]))
    grpEdEvac[paste0(evacVar,'_cat')]=cut(unlist(grpEdEvac[evacVar]),breaks = tertile,include.lowest = T,labels = c(1,2,3))
    evacVar= paste0(evacVar,'_cat')
  }
  
  mformula= paste0('DailyED ~ ',evacVar,' * EvacPeriod',formula_add," + year + month + weekday +  RACE_other + RACE_black + SEX_CODE_F + PAT_AGE_YEARS + ETHNICITY_Hispanic + op") # + hvyRainDur'
  model=glm(data=grpEdEvac, formula=as.formula(mformula),family = poisson(),
            offset = log(grpEdEvac$Population))
  summary(model)
  aic = AIC(model)
  
  
  
  #broom results
  resTab = tidy(model, exponentiate = T)
  resTab = bind_cols(resTab , confint.default(model) %>% exp %>% as_tibble)
  resTab<-resTab[,c("term", "estimate","2.5 %",  "97.5 %","p.value", "std.error")]
  #insert exposure,outcome and formula and Aic
  resTab$aic<-aic
  
  resTab$evacVar<-evacVar
  resTab$formula<-mformula
  resTab$model<-paste0("MaxEvacVariable",ifelse(formula_add=="","",'_InterWithFlood'))
  resTab$evacVarQuantiles <- ifelse(evacVarType=="tertile",paste0(signif(tertile,3),collapse = ','),"NA")
  
  #prepare raw summary file
  sumTxt<-paste0(c(capture.output(summary(model)),
                   'Time:',as.character(Sys.time()),'\n'),collapse = '\n')
  #replace formula with orginal formula
  sumTxt<-gsub('mformula',mformula,sumTxt)
  
  
  lrtest_pval=NA
  #lrt test if AER flood 
  if(formula_add!=''){
    mformula_reduced= "DailyED ~ AERFlooded * EvacPeriod + year + month + weekday +  RACE_other + RACE_black + SEX_CODE_F + PAT_AGE_YEARS + ETHNICITY_Hispanic + op" # + hvyRainDur'
    model_reduced=glm(data=grpEdEvac, formula=as.formula(mformula_reduced),family = poisson(),
                      offset = log(grpEdEvac$Population))
    res=lrtest(model,model_reduced)
    lrtest_pval=res$`Pr(>Chisq)`[2]
    sumTxt<-paste0(sumTxt,paste0(capture.output(res),collapse='\n'),'\n')
  }
  resTab$lrtest_pval<-lrtest_pval
  
  #add to all output stored df and str
  if(all(is.na(allRes))) allRes<-resTab else allRes<-rbind(allRes,resTab)
  allSum<-paste0(allSum,sumTxt,sep=paste0(rep('=',100),collapse=''))
  
  print(mformula)
  
  #create cross table if intersection columns are factor
  if(is.factor(grpEdEvac[,evacVar])){
    if(formula_add=="") {
      ftab=grpEdEvac %>% group_by(get(evacVar),EvacPeriod) %>% summarise(nrow=n(),edCounts=sum(DailyED)) %>% rename_with(~evacVar,`get(evacVar)`)
    }else ftab=ftab=grpEdEvac %>% group_by(get(evacVar),EvacPeriod,AERFlooded) %>% summarise(nrow=n(),edCounts=sum(DailyED)) %>% rename_with(~evacVar,`get(evacVar)`)
    allCrosTabs<-bind_rows(allCrosTabs,ftab)
  }
  
  #remove the categorical variable if added
  grpEdEvac = grpEdEvac %>% select(-ends_with('_cat'))
}
resTab$outcome<-'TotalED'
write.xlsx(allRes, file=paste0(outputDir,'GroupedMax.xlsx'), sheetName = "Sheet1",col.names = TRUE, row.names = TRUE, append = FALSE)
cat(allSum,file = paste0(outputDir,'GroupedMax.txt'))
write.csv(allCrosTabs,file = paste0(outputDir,'GroupedMax.csv'))

# ____using max values from the evacuation models controlling for summed evac rate----

#model.matrix(~EvacPeriod* totRainSum,data=grpEdEvac) %>% as_tibble%>% select(-`(Intercept)`)  %>% cor %>% corrplot(method='pie')
evacVarsWithOutEvacRate <- evacVars[evacVars!='evacRate']
allRes<- NA
allSum=''
allCrosTabs<-data.frame()
for(evacVarType in c('linear'))#,'tertile'))
  for(formula_add in c(" * AERFlooded",""))
    for(evacVar in paste0(evacVarsWithOutEvacRate,'Sum')){
      #categorise if needed
      if(evacVarType=='tertile'){
        tertile = form_tertile(unlist(evacDfMax[,evacVar]))
        grpEdEvac[paste0(evacVar,'_cat')]=cut(unlist(grpEdEvac[evacVar]),breaks = tertile,include.lowest = T,labels = c(1,2,3))
        evacVar= paste0(evacVar,'_cat')
      }
      
      mformula= paste0('DailyED ~ ',evacVar,' * EvacPeriod',formula_add," + evacRateSum  + year + month + weekday +  RACE_other + RACE_black + SEX_CODE_F + PAT_AGE_YEARS + ETHNICITY_Hispanic + op") # + hvyRainDur'
      model=glm(data=grpEdEvac, formula=as.formula(mformula),family = poisson(),
                offset = log(grpEdEvac$Population))
      summary(model)
      aic = AIC(model)
      
      #broom results
      resTab = tidy(model, exponentiate = T)
      resTab = bind_cols(resTab , confint.default(model) %>% exp %>% as_tibble)
      resTab<-resTab[,c("term", "estimate","2.5 %",  "97.5 %","p.value", "std.error")]
      #insert exposure,outcome and formula and Aic
      resTab$aic<-aic
      
      resTab$evacVar<-evacVar
      resTab$formula<-mformula
      resTab$model<-paste0("MaxEvacVariable",ifelse(formula_add=="","",'_InterWithFlood'))
      resTab$evacVarQuantiles <- ifelse(evacVarType=="tertile",paste0(signif(tertile,3),collapse = ','),"NA")
      
      #prepare raw summary file
      sumTxt<-paste0(c(capture.output(summary(model)),
                       'Time:',as.character(Sys.time()),'\n'),collapse = '\n')
      #replace formula with orginal formula
      sumTxt<-gsub('mformula',mformula,sumTxt)
      
      
      lrtest_pval=NA
      #lrt test if AER flood 
      if(formula_add!=''){
        mformula_reduced= "DailyED ~ AERFlooded * EvacPeriod + year + month + weekday +  RACE_other + RACE_black + SEX_CODE_F + PAT_AGE_YEARS + ETHNICITY_Hispanic + op" # + hvyRainDur'
        model_reduced=glm(data=grpEdEvac, formula=as.formula(mformula_reduced),family = poisson(),
                          offset = log(grpEdEvac$Population))
        res=lrtest(model,model_reduced)
        lrtest_pval=res$`Pr(>Chisq)`[2]
        sumTxt<-paste0(sumTxt,paste0(capture.output(res),collapse='\n'),'\n')
      }
      resTab$lrtest_pval<-lrtest_pval
      
      #add to all output stored df and str
      if(all(is.na(allRes))) allRes<-resTab else allRes<-rbind(allRes,resTab)
      allSum<-paste0(allSum,sumTxt,sep=paste0(rep('=',100),collapse=''))
      
      print(mformula)
      
      #create cross table if intersection columns are factor
      if(is.factor(grpEdEvac[,evacVar])){
        if(formula_add=="") {
          ftab=grpEdEvac %>% group_by(get(evacVar),EvacPeriod) %>% summarise(nrow=n(),edCounts=sum(DailyED)) %>% rename_with(~evacVar,`get(evacVar)`)
        }else ftab=ftab=grpEdEvac %>% group_by(get(evacVar),EvacPeriod,AERFlooded) %>% summarise(nrow=n(),edCounts=sum(DailyED)) %>% rename_with(~evacVar,`get(evacVar)`)
        allCrosTabs<-bind_rows(allCrosTabs,ftab)
      }
      
      #remove the categorical variable if added
      grpEdEvac = grpEdEvac %>% select(-ends_with('_cat'))
    }
resTab$outcome<-'TotalED'
write.xlsx(allRes, file=paste0(outputDir,'GroupedMaxAdjEvacRate.xlsx'), sheetName = "Sheet1",col.names = TRUE, row.names = TRUE, append = FALSE)
cat(allSum,file = paste0(outputDir,'GroupedMaxAdjEvacRate.txt'))
write.csv(allCrosTabs,file = paste0(outputDir,'GroupedMaxAdjEvacRate.csv'))

# _____base model only  AER flood scan----

mformula= "DailyED ~ AERFlooded * EvacPeriod + year + month + weekday +  RACE_other + RACE_black + SEX_CODE_F + PAT_AGE_YEARS + ETHNICITY_Hispanic + op" # + hvyRainDur'
model=glm(data=grpEdEvac, formula=as.formula(mformula),family = poisson(),
                offset = log(grpEdEvac$Population))
summary(model)
aic = AIC(model)
#broom results
resTab = tidy(model, exponentiate = T)
resTab = bind_cols(resTab , confint.default(model) %>% exp %>% as_tibble)
resTab<-resTab[,c("term", "estimate","2.5 %",  "97.5 %","p.value", "std.error")]
#insert exposure,outcome and formula and Aic
resTab$aic<-aic
resTab$formula<-mformula
#prepare raw summary file
sumTxt<-paste0(c(capture.output(summary(model)),
                 'Time:',as.character(Sys.time()),'\n'),collapse = '\n')
#replace formula with orginal formula
sumTxt<-gsub('mformula',mformula,sumTxt)

#create cross table if intersection columns are factor
allCrosTabs=grpEdEvac %>% group_by(EvacPeriod,AERFlooded) %>% summarise(nrow=n(),edCounts=sum(DailyED)) 

write.xlsx(resTab, file=paste0(outputDir,'baseModelAER.xlsx'), sheetName = "Sheet1",col.names = TRUE, row.names = TRUE, append = FALSE)
cat(sumTxt,file = paste0(outputDir,'baseModelAER.txt'))
write.csv(allCrosTabs,file = paste0(outputDir,'baseModelAER.csv'))

#================================================== -
#==================EOF======================= ----
#================================================== -








#### ----- temp codes for future ------
for(outcome in c("Dehydration","InsetBite", "Chest_pain", "Intestinal_infectious_diseases", "Pregnancy_complic")){
  formula= as.formula(paste0(outcome,' ~ evacRateSumCat * EvacPeriod + year + month + weekday + op  + RACE + SEX_CODE + PAT_AGE_YEARS + ETHNICITY')) # + hvyRainDur')
  
  #gee model
  #model1=geeglm(data=EdEvac, formula=formula,family = poisson(),offset = log(EdEvac$TotalVisits),id = EdEvac$PAT_ADDR_CENSUS_TRACT)
  
  #glm model
  model.glm=glm(data=EdEvac, formula=formula,family = poisson(),offset = log(EdEvac$TotalVisits))
  print(paste0(outcome, '======================================'))
  print(summary(model.glm))
  model.glm %>% confint.default %>% exp %>% print
}

#categorise evacRateSum into quantiles
EdEvac = EdEvac %>% mutate(evacRateSumCat=cut(evacRateSum, breaks=quantile(evacDfMax$evacRateSum,seq(0,1,1/3)),include.lowest = T,
                                              labels=c("low","mid","high")))
for(outcome in c("Dehydration","InsetBite", "Chest_pain", "Intestinal_infectious_diseases", "Pregnancy_complic")){
formula= as.formula(paste0(outcome,' ~ evacRateSumCat * EvacPeriod + year + month + weekday + op  + RACE + SEX_CODE + PAT_AGE_YEARS + ETHNICITY')) # + hvyRainDur')

#gee model
#model1=geeglm(data=EdEvac, formula=formula,family = poisson(),offset = log(EdEvac$TotalVisits),id = EdEvac$PAT_ADDR_CENSUS_TRACT)

#glm model
model.glm=glm(data=EdEvac, formula=formula,family = poisson(),offset = log(EdEvac$TotalVisits))
print(paste0(outcome, '======================================'))
print(summary(model.glm))
model.glm %>% confint.default %>% exp %>% print
}

#try lme4 model
formula.mixed=as.formula(paste0(paste0(format(formula),collapse = ''),'+ (1 | PAT_ADDR_CENSUS_TRACT)'))
model.mixed = glmer(data=EdEvac, formula=formula.mixed,family = poisson(),offset = log(EdEvac$TotalVisits),verbose=2,control = glmerControl(boundary.tol = 1e-1))
summary(model.mixed)

###
#OK the problem with ITCS is that when we try a three way interaction model the interaction between evacuation Post flood and evacuation variable (say total rain) is totally correlational to evaluation post flood period. This is because valuation post flood period Is 0 everywhere except during post flood and similarly the interaction term is also zero elsewhere and reaches maximum value during post flood. The other challenge with ITC S is that it's hard to separate the control and treatment then we consider the evacuation variable as a continuous.
#also discuss about control being beofre and after
# totRain EvacPeriod_evacuation EvacPeriod_flood EvacPeriod_PostFlood1 EvacPeriod_evacuation_t
# totRain                  1.00000000           -0.03827734      0.274771531            0.93821622             0.023635426
# EvacPeriod_evacuation   -0.03827734            1.00000000     -0.017236938           -0.05883692             0.459734481
# EvacPeriod_flood         0.27477153           -0.01723694      1.000000000           -0.06294225            -0.007924415
# EvacPeriod_PostFlood1    0.93821622           -0.05883692     -0.062942248            1.00000000            -0.027049361
# EvacPeriod_evacuation_t  0.02363543            0.45973448     -0.007924415           -0.02704936             1.000000000
# EvacPeriod_flood_t       0.27560764           -0.01720066      0.997895264           -0.06280977            -0.007907736
# EvacPeriod_PostFlood1_t  0.94069551           -0.05868893     -0.062783935            0.99748480            -0.026981327
# EvacPeriod_flood_t EvacPeriod_PostFlood1_t
# totRain                        0.275607643              0.94069551
# EvacPeriod_evacuation         -0.017200659             -0.05868893
# EvacPeriod_flood               0.997895264             -0.06278394
# EvacPeriod_PostFlood1         -0.062809771              0.99748480
# EvacPeriod_evacuation_t       -0.007907736             -0.02698133
# EvacPeriod_flood_t             1.000000000             -0.06265179
# EvacPeriod_PostFlood1_t       -0.062651791              1.00000000
###