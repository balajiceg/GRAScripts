##################################
# input file-> 'K:\\Projects\\FY2020-018_HHR_Outcomes\\EoFloodHealth\\Data\\Draft\\ProcessedTFR\\TFRHarveyRecordsInclPaperSurWithInundNSVI.csv
# output files ->K:\\Projects\\FY2020-018_HHR_Outcomes\\EoFloodHealth\\Output\\Draft\\analysisOutput\\
# Purpose: R code for running GEE models using the HHR dataset and flood inundation product from flood scan product

#######################################

#libraries
library(ggpubr)
library(dplyr)
library(tidyr)
library(broom)
library(MuMIn)
library(moments)
library(geepack)
library(car)
library(openxlsx)
library(sf)

#output file location
outputDir<-"K:\\Projects\\FY2020-018_HHR_Outcomes\\EoFloodHealth\\Output\\Draft\\analysisOutput07012022\\"

#functions
mQIC<-function (x){as.numeric(QIC(x)['QIC'])}

# read the TRF(Harvey) and inundation (DfO & floodScan) ------------------- N=20395
all_df<-read.csv('K:\\Projects\\FY2020-018_HHR_Outcomes\\EoFloodHealth\\Data\\Draft\\ProcessedTFR\\TFRHarveyRecordsInclPaperSurWithInundNSVI.csv',stringsAsFactors = F)
#color blid pallette
cbbPalette <- c(   "#D55E00", "#0072B2","#009E73","#56B4E9", "#CC79A7", "#000000", "#E69F00","#F0E442")

#intersting columns
interstCols<-c("X","Y","SurveyResponseID","GeoID10","tractID10","DOB","Male","RaceGroup","Hispanic","EducGroup","SelfAssess",
               "Contact_Water","HomeDamaged","HomeFlooded","OtherHomesFlooded","LosePower","TrashOnBlock",
               "LeaveHome","LoseIncome","VehicleDamaged",
               "Hospital","Illness","Injury","NoSymptoms","Concentrate","Headaches","RunnyNose","ShortBreath","SkinRash",
               "DFO_R200","dfoInundDist","fScanInundDist","fScanDepth","fScanNdays","fScanMaxFloodRatio",
               "reRankSVI", "reRankSVI_T1", "reRankSVI_T2", "reRankSVI_T3", "reRankSVI_T4")
#subset data with geocoding-> removes -------------- N=19762
all_df<-subset(all_df,Geocoded==1)

#-----clean data-----
#filter columns which has lessthan 3000 NAs
na_cols<-sapply(all_df, function(y) sum(length(which(is.na(y)))))
nonNaCols<-row.names(data.frame(na_cols))[na_cols<3000]

#filter only interested columns
subDf<-all_df[,interstCols]

#remove records without tract id - removes 5 records ------------ N= 19757
subDf<-subDf[!is.na(subDf$GeoID10),]

#remove records out of floodscan census tracts extent - removes 7 records - N=19750
subDf<-subDf[!is.na(subDf$fScanMaxFloodRatio),]

#create age column - age during hurricane harvey (2017-08-26)
subDf$Age<-as.numeric(difftime( as.Date('2017-08-26'),as.Date(subDf$DOB,'%m/%d/%Y'), unit="weeks"))/52.25
subDf$Age<-round(subDf$Age)

#remove records without basic persnoal infor - n=19592
subDf<-subDf[complete.cases(subDf[,c("Male", "RaceGroup", "Age")]),] #HIspanic not used as it is integrated in race

#remove blank education group n=19472
subDf<-subDf[(subDf$EducGroup!='') & !is.na(subDf$EducGroup),]

#check age below 17
table(subDf[subDf$Age<18,'Age'],subDf[subDf$Age<18,'EducGroup'])

#remove age less than 17 - n=19402
subDf<-subDf[subDf$Age>17,]

#remove records without self assesment - n=18948
subDf<-subDf[!is.na(subDf$SelfAssess),]

#remove data without SVI - n=18922
subDf<-subDf[!is.na(subDf$reRankSVI),]

#df for map crateion
# tractGrouped<-subDf %>% group_by(tractID10)%>% summarise(count=n(),nHomeFlooded=sum(HomeFlooded,na.rm = T),perct=sum(HomeFlooded,na.rm = T)/n())
# countyGrouped<-subDf %>% group_by(tractID10%/%1e6)%>% summarise(count=n(),nHomeFlooded=sum(HomeFlooded,na.rm=T),perct=sum(HomeFlooded,na.rm = T)/n())
# colnames(countyGrouped)[1]<-'countyFIPS'
####-------- change variables to factors -----
subDf$Male<-factor(subDf$Male,levels=c(1,0))
levels(subDf$Male)<-c('Male','Female')

subDf$Hispanic<-factor(subDf$Hispanic,levels=c(0,1))
levels(subDf$Hispanic)<-c('Non_Hispanic','Hispanic')

subDf$RaceGroup<-factor(subDf$RaceGroup,levels=c(1,2,3,4,5))
levels(subDf$RaceGroup)<-c("Non_Hispanic_White","Non_Hispanic_Black", "Hispanic", "Non_Hispanic_Asian","Non_Hispanic_Other")


subDf$EducGroup<-factor(subDf$EducGroup,levels=c("eighth","high_school", "ged", "college", "associates",  "bachelors", "graduate" ))
subDf$EducGroup<-recode(subDf$EducGroup,"c('eighth', 'high_school', 'ged')='highSchoolOrLess';c('college', 'associates') = 'collegeOrAssociates';c('bachelors','graduate')='bachelorsOrHigher'")

subDf$SelfAssess<-factor(subDf$SelfAssess,labels =c('Poor','Fair','Good','Very Good','Excellent'))
#create age group column - quantile breaks -18   38   50   60  117 
subDf$AgeGrp<-cut(subDf$Age,c(0,35,50,60,200),labels = c('18-35','36-50','51-60','gt60'))

#create SVI cat columns and Scale SVI to 0-100
for(i in c("reRankSVI","reRankSVI_T1","reRankSVI_T2","reRankSVI_T3","reRankSVI_T4")){
  subDf[gsub('reRank',"cat_",i)]<-cut(subDf[,i],breaks=seq(0,1,.25),include.lowest=T,labels=c('lowest','midLow','midHigh','highest'))
  subDf[,i]<- subDf[,i]*100
}

#inundatiaion variables reclassify: flooded, inundataion distance, number of days, depth
#flood scan boolean field
subDf$fScanFlooded<-subDf$fScanInundDist==0

#inundation distance quantile(subDf$fScanInundDist[!subDf$fScanFlooded],seq(0,1,1/3),na.rm=T) # => 80.8  404.0 1099.0 8795.3 
subDf$fScanInunDisCat<-cut(subDf$fScanInundDist,breaks=c(0,80,400,1100,9000),include.lowest=T,labels=c('Flooded','lte400','lte1100','gt1100'))
#reorder
subDf$fScanInunDisCat<- factor(subDf$fScanInunDisCat,levels=c('gt1100','lte1100','lte400','Flooded'))

#inundataion days 
#quantile(subDf$fScanNdays[subDf$fScanNdays!=0],seq(0,1,1/3),na.rm=T) # 0% 33.3% 66.7%  100% # 1     1     3    14 
subDf$fScanNdaysCat<-cut(subDf$fScanNdays,breaks=c(-1,0,1,3,15),include.lowest=T,labels=c('noFlood','1Day','2_3Days','4_14Days'))
subDf$fScanNdaysCat[!subDf$fScanFlooded]<-'noFlood'

#inundataion depth
#chage to feet
subDf$fScanDepthFt<-subDf$fScanDepth*3.28084
#quantile(subDf$fScanDepthFt[subDf$fScanFlooded],seq(0,1,1/3),na.rm=T) #0.00  1.62  3.27 31.97
subDf$fScanDepthCat<-cut(subDf$fScanDepthFt,breaks=c(-1,0,1.5,3,33),labels=c('noFlood','lte1Dot5ft','lte3ft','gt3ft'))
subDf$fScanDepthCat[!subDf$fScanFlooded]<-'noFlood'


#exposure variables
for (i in c("HomeFlooded","Contact_Water", "HomeDamaged", "OtherHomesFlooded", "LosePower", "TrashOnBlock", 
            "LeaveHome","LoseIncome", "VehicleDamaged")){
  subDf[,i]<-subDf[,i]==1
}

#outcome variable
#create any symptom from no symptom variable
subDf$AnySymptoms<-as.integer(subDf$NoSymptoms==0)

#create variable OnlyOtherHomesFlooded
subDf <- subDf %>% mutate(OnlyOtherHomesFlooded=case_when(
  HomeFlooded==F ~ OtherHomesFlooded,
  TRUE ~ NA
))

#remove duplicate responses from the same point  -  removes 1333 records
#subDf<-subDf[!duplicated(paste0(subDf$X,subDf$Y,sep='')),]

#change xy to projected coordinates 
sfPoints<-st_transform(st_as_sf(subDf[,c('SurveyResponseID','X','Y')], coords = c("X", "Y"), crs = 4326),crs=6579)
subDf[,c('X','Y')]<-st_coordinates(sfPoints)


#summary(subDf)
remove(all_df)
#---------------------  data cleaning ends here N=18922 without removing responses from same point---------
#xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

##-------------write demographic table using base mode ------
df<-subDf[,c('fScanFlooded','cat_SVI', 
  "HomeFlooded",'OnlyOtherHomesFlooded',"Contact_Water", "OtherHomesFlooded",
  'AgeGrp',"Male", "RaceGroup", "Hispanic", "EducGroup","SelfAssess",
  "Illness", "Injury","Hospital",  "Concentrate", "Headaches", "RunnyNose", "ShortBreath", "SkinRash","AnySymptoms")]
#df<-df[complete.cases(df),] #n= 19217

#demograhic tables or cross table
library(pubh)
demoCT<-cross_tab(df,fScanFlooded~., label='fscanFlooded') 
print(demoCT)
write.table(demoCT, "clipboard", sep="\t")


summary(df)
remove(df)
#missing data summary
library(mice)
miss=md.pattern(df)


#check a few things
#check factor references
subDf %>% select(where(is.factor)) %>% head %>% str

table(df$HomeFlooded,df$OnlyOtherHomesFlooded)

##--------------- intial analysis --- comparission between home flooded and other x variables withbar ,----
# graphDF<-data.frame(percent=NA,conf25=NA,conf95=NA,p_val=NA,major_cat=NA,bar_cat=NA,comp_var=NA)
# 
# outcomes<-c("Contact_Water","HomeDamaged","HomeFlooded","OtherHomesFlooded","LosePower",
#           "TrashOnBlock","LeaveHome","LoseIncome","VehicleDamaged","Hospital","Illness","Injury",
#           "NoSymptoms","Concentrate","Headaches","RunnyNose","ShortBreath","SkinRash")
# 
# for(comp_var in c('HomeFloodedBool','fScanFlooded'))#,'dfoFlooded'))
#   for(y_var in outcomes){
#     #make table
#     mTab<-table(subDf[,comp_var],subDf[,y_var])
#     
#     
#     mProp<-prop.test(mTab['FALSE','1'],sum(mTab['FALSE',]))
#     graphDF<-rbind(graphDF,c(mProp$estimate ,mProp$conf.int,NA,y_var,paste0(comp_var,' ','FALSE'),comp_var))
#     
#     mProp<-prop.test(mTab['TRUE','1'],sum(mTab['TRUE',]))
#     mtest<-prop.test(c(mTab['TRUE','1'],mTab['FALSE','1']),c(sum(mTab['TRUE',]),sum(mTab['FALSE',])),alternative = 'greater')
#     graphDF<-rbind(graphDF,c(mProp$estimate ,mProp$conf.int,mtest$p.value,y_var,paste0(comp_var,' ','TRUE'),comp_var))
#     
#     graphDF<-graphDF[complete.cases(graphDF[,c(1,2,3)]),]
#     graphDF<-graphDF[order(graphDF$bar_cat),]
#     graphDF[,c(1,2,3,4)]<-lapply(graphDF[,c(1,2,3,4)],as.numeric)
#   }
# graphDF$text<-' '
# graphDF$text[graphDF$p_val<0.05]<- '*'
# 
# graphDF$major_cat<-factor(graphDF$major_cat,levels=outcomes)
# ggplot(graphDF, aes(x = major_cat, y = percent, fill = bar_cat )) + facet_grid(comp_var ~ .)+
#   geom_bar(stat = "identity", position = "dodge") +
#   geom_text(aes(x=major_cat,y=conf95,label=text),vjust=-0.1,nudge_x =0,size=6,colour='red')+
#   ggtitle(comp_var) + ylab("Percentage of respondents") + xlab(element_blank())+
#   geom_errorbar(aes(ymin = conf25, ymax = conf95), width = 0.1,
#                 position = position_dodge(0.9)) + scale_y_continuous(labels = scales::percent)+
#   theme(text = element_text(size=22),
#         axis.text.x = element_text(angle = 90, vjust = 0.5, hjust=1),
#         panel.background = element_rect(fill = "white", colour = "grey40",size = 0.5, linetype = "solid"),
#         panel.grid.major = element_line(size = 0.25, linetype = 'solid',colour = "grey70"),
#         panel.grid.minor = element_line(size = 0.1, linetype = 'solid',colour = "grey90")) +   
#   scale_fill_manual(values=rep( c("#D55E00", "#0072B2"),10))
# 
# 


##--------------- comparing similar columns  ------------
# compCols<-c("Contact_Water", "HomeDamaged", "HomeFlooded", "OtherHomesFlooded", "LosePower", "TrashOnBlock", "LeaveHome",  "VehicleDamaged" )
# compDf<-data.frame()
# for(i in compCols)
#   for(j in compCols){
#     if (i==j) next
#     tbl<-table(subDf[,i],subDf[,j])
#     compDf<-rbind(compDf,c(i,j,round(as.vector(tbl)/sum(tbl)*100,2)))
#   }
# colnames(compDf)<-c('col1','col2','FF','FT','TF','TT')
# compDf[,c(3,4,5,6)]<-sapply(compDf[,c(3,4,5,6)],as.numeric)
# compDf['FF_TT']<-compDf$FF+compDf$TT
# compDf['FT_TF']<-compDf$TF+compDf$FT


##------ =========== RUN GEE MODELS ================================= ------------
##------ 1.base model without SVI interaction and controlling for self assess ------

covariates<- c('Male','AgeGrp', 'RaceGroup', 'EducGroup',"SelfAssess") #,'Hispanic'
outcomes<- c("Illness", "Injury","Hospital",  "Concentrate", "Headaches", "RunnyNose", "ShortBreath", "SkinRash","AnySymptoms")
exposures<-c("OnlyOtherHomesFlooded")#,"Contact_Water","OtherHomesFlooded","HomeFlooded","fScanFlooded","fScanInunDisCat","fScanNdaysCat" ,"fScanDepthCat","fScanDepthFt","fScanInundDist","fScanNdays")
print(paste0(c('outcomes-> ',outcomes),collapse = ', '))
print(paste0(c('exposures-> ',exposures),collapse = ', '))
print(paste0(c('covariates-> ',covariates),collapse = ', '))
summary(subDf[,c(covariates,exposures,outcomes)])

outcome<-outcomes[1]
exposure<- exposures[2]
allRes<-NA
allSumm<-''
allCrosTabs<-data.frame()

for(exposure in exposures)
  for(outcome in outcomes){
  mformula<-paste0(outcome,' ~ ', exposure, ' + ' , paste0(covariates,collapse = ' + '))
  df<-subDf[complete.cases(subDf[,c(outcome,exposure,covariates,'tractID10')]),]
  df['id']<-seq(dim(df)[1])
  model<-geeglm(as.formula(mformula),
                      id=tractID10,
                      data = df,
                      family =poisson(link='log'),
                      corstr = "independence")

  #update correlation structure
  model2 <- update(model, corstr = "exch")
  model3 <- update(model, corstr = "ar1")

  ##select correlation structure based on smallest QIC
  modelSel<-list(model,model2,model3)[which.min(unlist(lapply(list(model,model2,model3),mQIC)))][[1]]
  remove(model,model2,model3)

  ##get summary from the selected model
  qic<- QIC(modelSel)
  #summary(modelSel)

  #broom results
  resTab<-tidy(modelSel, conf.int = TRUE,exponentiate = T)
  resTab[,c('estimate','p.value','conf.low','conf.high')]<-round(resTab[,c('estimate','p.value','conf.low','conf.high')],3)
  resTab<-resTab[,c("term", "estimate","conf.low",  "conf.high","p.value", "std.error", "statistic")]

  #insert exposure,outcome and formula and Qic
  resTab$qic<-qic['QIC']
  resTab$outcome<-outcome
  resTab$exposure<-exposure
  resTab$formula<-mformula
  #correlation struture
  resTab$corstr<-modelSel$corstr
  resTab$Nrow<-nrow(modelSel$data)
  resTab$id<-as.character(modelSel$call$id)
  resTab$otherCom<-""
  #print(resTab)

  #prepare raw summary file
  sumTxt<-paste0(c(capture.output(summary(modelSel)),
                   '\n QIC:',capture.output(qic),
                   'Time:',as.character(Sys.time()),'\n'),collapse = '\n')
  #replace formula with orginal formula
  sumTxt<-gsub('mformula',mformula,sumTxt)


  #add to all output stored df and str
  if(is.na(allRes)) allRes<-resTab else allRes<-rbind(allRes,resTab)
  allSumm<-paste0(allSumm,sumTxt,sep=paste0(rep('=',100),collapse=''))

  print(mformula)

  #create cross table if intersection columns are factor
  if(is.factor(df[,exposure]) | is.logical(df[,exposure])){
    ftab<-data.frame(ftable(df[,outcome],df[,exposure],dnn=c(outcome,exposure)),stringsAsFactors = F)
    ftab$formula<-mformula
    ftab<-rbind(colnames(ftab),sapply(ftab,as.character))
    colnames(ftab) <- as.character(seq(dim(ftab)[2]))
    allCrosTabs<-rbind(allCrosTabs,ftab)
  }
}

#write output files
allRes$model<-'baseModel'
write.xlsx(allRes, file=paste0(outputDir,'baseModel.xlsx'), sheetName = "Sheet1",col.names = TRUE, row.names = TRUE, append = FALSE)
write.csv(allCrosTabs,file = paste0(outputDir,'baseModel.csv'))
cat(allSumm,file = paste0(outputDir,'baseModel.txt'))


##------ 1.2. reruning base model controlling for self assess to compare homeflooded, other homes flooded, fcsn flooded with same number of records ------

covariates<- c('Male','AgeGrp', 'RaceGroup', 'EducGroup',"SelfAssess") #,'Hispanic'
outcomes<- c("Illness", "Injury","Hospital",  "Concentrate", "Headaches", "RunnyNose", "ShortBreath", "SkinRash","AnySymptoms")
exposures<-c("OtherHomesFlooded","HomeFlooded","fScanFlooded")
print(paste0(c('outcomes-> ',outcomes),collapse = ', '))
print(paste0(c('exposures-> ',exposures),collapse = ', '))
print(paste0(c('covariates-> ',covariates),collapse = ', '))
summary(subDf[,c(covariates,exposures,outcomes)])

allRes<-NA
allSumm<-''
allCrosTabs<-data.frame()

for(exposure in exposures)
  for(outcome in outcomes){
    mformula<-paste0(outcome,' ~ ', exposure, ' + ' , paste0(covariates,collapse = ' + '))
    df<-subDf[complete.cases(subDf[,c(outcome,exposures,covariates,'tractID10')]),]
    df['id']<-seq(dim(df)[1])
    model<-geeglm(as.formula(mformula),
                  id=tractID10,
                  data = df,
                  family =poisson(link='log'),
                  corstr = "independence")

    #update correlation structure
    model2 <- update(model, corstr = "exch")
    model3 <- update(model, corstr = "ar1")

    ##select correlation structure based on smallest QIC
    modelSel<-list(model,model2,model3)[which.min(unlist(lapply(list(model,model2,model3),mQIC)))][[1]]
    remove(model,model2,model3)

    ##get summary from the selected model
    qic<- QIC(modelSel)
    #summary(modelSel)

    #broom results
    resTab<-tidy(modelSel, conf.int = TRUE,exponentiate = T)
    resTab[,c('estimate','p.value','conf.low','conf.high')]<-round(resTab[,c('estimate','p.value','conf.low','conf.high')],3)
    resTab<-resTab[,c("term", "estimate","conf.low",  "conf.high","p.value", "std.error", "statistic")]

    #insert exposure,outcome and formula and Qic
    resTab$qic<-qic['QIC']
    resTab$outcome<-outcome
    resTab$exposure<-exposure
    resTab$formula<-mformula
    #correlation struture
    resTab$corstr<-modelSel$corstr
    resTab$Nrow<-nrow(modelSel$data)
    resTab$id<-as.character(modelSel$call$id)
    resTab$otherCom<-""
    #print(resTab)

    #prepare raw summary file
    sumTxt<-paste0(c(capture.output(summary(modelSel)),
                     '\n QIC:',capture.output(qic),
                     'Time:',as.character(Sys.time()),'\n'),collapse = '\n')
    #replace formula with orginal formula
    sumTxt<-gsub('mformula',mformula,sumTxt)


    #add to all output stored df and str
    if(is.na(allRes)) allRes<-resTab else allRes<-rbind(allRes,resTab)
    allSumm<-paste0(allSumm,sumTxt,sep=paste0(rep('=',100),collapse=''))

    print(mformula)

    #create cross table if intersection columns are not factor
    if(is.factor(df[,exposure]) | is.logical(df[,exposure])){
      ftab<-data.frame(ftable(df[,outcome],df[,exposure],dnn=c(outcome,exposure)),stringsAsFactors = F)
      ftab$formula<-mformula
      ftab<-rbind(colnames(ftab),sapply(ftab,as.character))
      colnames(ftab) <- as.character(seq(dim(ftab)[2]))
      allCrosTabs<-rbind(allCrosTabs,ftab)
    }
  }

#write output files
allRes$model<-'baseModelCompRSvsReported'
write.xlsx(allRes, file=paste0(outputDir,'baseModelCompRSvsReported.xlsx'), sheetName = "Sheet1",col.names = TRUE, row.names = TRUE, append = FALSE)
write.csv(allCrosTabs,file = paste0(outputDir,'baseModelCompRSvsReported.csv'))
cat(allSumm,file = paste0(outputDir,'baseModelCompRSvsReported.txt'))

##----- 1.3. base model controlling for self assess as well as the four themes of SVI  ----
covariates<- c('Male','AgeGrp', 'RaceGroup', 'EducGroup',"SelfAssess","reRankSVI_T1","reRankSVI_T2",  "reRankSVI_T3", "reRankSVI_T4") #,'Hispanic'
outcomes<- c("Illness", "Injury","Hospital",  "Concentrate", "Headaches", "RunnyNose", "ShortBreath", "SkinRash","AnySymptoms")
exposures<-c("OtherHomesFlooded","HomeFlooded","fScanFlooded","fScanInunDisCat","fScanNdaysCat" ,"fScanDepthCat","fScanDepthFt","fScanInundDist","fScanNdays")
print(paste0(c('outcomes-> ',outcomes),collapse = ', '))
print(paste0(c('exposures-> ',exposures),collapse = ', '))
print(paste0(c('covariates-> ',covariates),collapse = ', '))
summary(subDf[,c(covariates,exposures,outcomes)])

outcome<-outcomes[2]
exposure<- exposures[1]
allRes<-NA
allSumm<-''
allCrosTabs<-data.frame()

for(exposure in exposures)
  for(outcome in outcomes){
    mformula<-paste0(outcome,' ~ ', exposure, ' + ' , paste0(covariates,collapse = ' + '))
    df<-subDf[complete.cases(subDf[,c(outcome,exposure,covariates,'tractID10')]),]
    df['id']<-seq(dim(df)[1])
    model<-geeglm(as.formula(mformula),
                  id=tractID10,
                  data = df,
                  family =poisson(link='log'),
                  corstr = "independence")

    #update correlation structure
    model2 <- update(model, corstr = "exch")
    model3 <- update(model, corstr = "ar1")

    ##select correlation structure based on smallest QIC
    modelSel<-list(model,model2,model3)[which.min(unlist(lapply(list(model,model2,model3),mQIC)))][[1]]
    remove(model,model2,model3)

    ##get summary from the selected model
    qic<- QIC(modelSel)
    #summary(modelSel)

    #broom results
    resTab<-tidy(modelSel, conf.int = TRUE,exponentiate = T)
    resTab[,c('estimate','p.value','conf.low','conf.high')]<-round(resTab[,c('estimate','p.value','conf.low','conf.high')],3)
    resTab<-resTab[,c("term", "estimate","conf.low",  "conf.high","p.value", "std.error", "statistic")]

    #insert exposure,outcome and formula and Qic
    resTab$qic<-qic['QIC']
    resTab$outcome<-outcome
    resTab$exposure<-exposure
    resTab$formula<-mformula
    #correlation struture
    resTab$corstr<-modelSel$corstr
    resTab$Nrow<-nrow(modelSel$data)
    resTab$id<-as.character(modelSel$call$id)
    resTab$otherCom<-""
    #print(resTab)

    #prepare raw summary file
    sumTxt<-paste0(c(capture.output(summary(modelSel)),
                     '\n QIC:',capture.output(qic),
                     'Time:',as.character(Sys.time()),'\n'),collapse = '\n')
    #replace formula with orginal formula
    sumTxt<-gsub('mformula',mformula,sumTxt)


    #add to all output stored df and str
    if(is.na(allRes)) allRes<-resTab else allRes<-rbind(allRes,resTab)
    allSumm<-paste0(allSumm,sumTxt,sep=paste0(rep('=',100),collapse=''))

    print(mformula)

    #create cross table if intersection columns are not factor
    if(is.factor(df[,exposure]) | is.logical(df[,exposure])){
      ftab<-data.frame(ftable(df[,outcome],df[,exposure],dnn=c(outcome,exposure)),stringsAsFactors = F)
      ftab$formula<-mformula
      ftab<-rbind(colnames(ftab),sapply(ftab,as.character))
      colnames(ftab) <- as.character(seq(dim(ftab)[2]))
      allCrosTabs<-rbind(allCrosTabs,ftab)
    }
  }

#write output files
allRes$model<-'baseModelCntrlSVI'
write.xlsx(allRes, file=paste0(outputDir,'baseModelCntrlSVI.xlsx'), sheetName = "Sheet1",col.names = TRUE, row.names = TRUE, append = FALSE)
write.csv(allCrosTabs,file = paste0(outputDir,'baseModelCntrlSVI.csv'))
cat(allSumm,file = paste0(outputDir,'baseModelCntrlSVI.txt'))

##----- 1.4. base model with overall svi cat as a covariate  ----
covariates<- c("cat_SVI",'Male','AgeGrp', 'RaceGroup', 'EducGroup',"SelfAssess") #,'Hispanic'
outcomes<- c("Illness", "Injury","Hospital",  "Concentrate", "Headaches", "RunnyNose", "ShortBreath", "SkinRash","AnySymptoms")
exposures<-c("OtherHomesFlooded","HomeFlooded","fScanFlooded","fScanInunDisCat","fScanNdaysCat" ,"fScanDepthCat","fScanDepthFt","fScanInundDist","fScanNdays")
print(paste0(c('outcomes-> ',outcomes),collapse = ', '))
print(paste0(c('exposures-> ',exposures),collapse = ', '))
print(paste0(c('covariates-> ',covariates),collapse = ', '))
summary(subDf[,c(covariates,exposures,outcomes)])

outcome<-outcomes[2]
exposure<- exposures[1]
allRes<-NA
allSumm<-''
allCrosTabs<-data.frame()

for(exposure in exposures)
  for(outcome in outcomes){
    mformula<-paste0(outcome,' ~ ', exposure, ' + ' , paste0(covariates,collapse = ' + '))
    df<-subDf[complete.cases(subDf[,c(outcome,exposure,covariates,'tractID10')]),]
    df['id']<-seq(dim(df)[1])
    model<-geeglm(as.formula(mformula),
                  id=tractID10,
                  data = df,
                  family =poisson(link='log'),
                  corstr = "independence")

    #update correlation structure
    model2 <- update(model, corstr = "exch")
    model3 <- update(model, corstr = "ar1")

    ##select correlation structure based on smallest QIC
    modelSel<-list(model,model2,model3)[which.min(unlist(lapply(list(model,model2,model3),mQIC)))][[1]]
    remove(model,model2,model3)

    ##get summary from the selected model
    qic<- QIC(modelSel)
    #summary(modelSel)

    #broom results
    resTab<-tidy(modelSel, conf.int = TRUE,exponentiate = T)
    resTab[,c('estimate','p.value','conf.low','conf.high')]<-round(resTab[,c('estimate','p.value','conf.low','conf.high')],3)
    resTab<-resTab[,c("term", "estimate","conf.low",  "conf.high","p.value", "std.error", "statistic")]

    #insert exposure,outcome and formula and Qic
    resTab$qic<-qic['QIC']
    resTab$outcome<-outcome
    resTab$exposure<-exposure
    resTab$formula<-mformula
    #correlation struture
    resTab$corstr<-modelSel$corstr
    resTab$Nrow<-nrow(modelSel$data)
    resTab$id<-as.character(modelSel$call$id)
    resTab$otherCom<-""
    #print(resTab)

    #prepare raw summary file
    sumTxt<-paste0(c(capture.output(summary(modelSel)),
                     '\n QIC:',capture.output(qic),
                     'Time:',as.character(Sys.time()),'\n'),collapse = '\n')
    #replace formula with orginal formula
    sumTxt<-gsub('mformula',mformula,sumTxt)


    #add to all output stored df and str
    if(is.na(allRes)) allRes<-resTab else allRes<-rbind(allRes,resTab)
    allSumm<-paste0(allSumm,sumTxt,sep=paste0(rep('=',100),collapse=''))

    print(mformula)

    #create cross table if intersection columns are not factor
    if(is.factor(df[,exposure]) | is.logical(df[,exposure])){
      ftab<-data.frame(ftable(df[,outcome],df[,exposure],dnn=c(outcome,exposure)),stringsAsFactors = F)
      ftab$formula<-mformula
      ftab<-rbind(colnames(ftab),sapply(ftab,as.character))
      colnames(ftab) <- as.character(seq(dim(ftab)[2]))
      allCrosTabs<-rbind(allCrosTabs,ftab)
    }
  }

#write output files
allRes$model<-'baseModelWithSVIcat'
write.xlsx(allRes, file=paste0(outputDir,'baseModelWithSVIcat.xlsx'), sheetName = "Sheet1",col.names = TRUE, row.names = TRUE, append = FALSE)
write.csv(allCrosTabs,file = paste0(outputDir,'baseModelWithSVIcat.csv'))
cat(allSumm,file = paste0(outputDir,'baseModelWithSVIcat.txt'))

##----- 2.base model not controlling for self assess  ----

covariates<- c('Male','AgeGrp', 'RaceGroup', 'EducGroup') #,'Hispanic'
outcomes<- c("Illness", "Injury","Hospital",  "Concentrate", "Headaches", "RunnyNose", "ShortBreath", "SkinRash","AnySymptoms")
exposures<-c("OtherHomesFlooded","HomeFlooded","fScanFlooded","fScanInunDisCat","fScanNdaysCat" ,"fScanDepthCat","fScanDepthFt","fScanInundDist","fScanNdays")
print(paste0(c('outcomes-> ',outcomes),collapse = ', '))
print(paste0(c('exposures-> ',exposures),collapse = ', '))
print(paste0(c('covariates-> ',covariates),collapse = ', '))
summary(subDf[,c(covariates,exposures,outcomes)])

allRes<-NA
allSumm<-''
allCrosTabs<-data.frame()

for(exposure in exposures)
  for(outcome in outcomes){
    mformula<-paste0(outcome,' ~ ', exposure, ' + ' , paste0(covariates,collapse = ' + '))
    df<-subDf[complete.cases(subDf[,c(outcome,exposure,covariates,'tractID10')]),]
    df['id']<-seq(dim(df)[1])
    model<-geeglm(as.formula(mformula),
                  id=tractID10,
                  data = df,
                  family =poisson(link='log'),
                  corstr = "independence")

    #update correlation structure
    model2 <- update(model, corstr = "exch")
    model3 <- update(model, corstr = "ar1")



    ##select correlation structure based on smallest QIC
    modelSel<-list(model,model2,model3)[which.min(unlist(lapply(list(model,model2,model3),mQIC)))][[1]]
    remove(model,model2,model3)

    ##get summary from the selected model
    qic<- QIC(modelSel)
    #summary(modelSel)

    #broom results
    resTab<-tidy(modelSel, conf.int = TRUE,exponentiate = T)
    resTab[,c('estimate','p.value','conf.low','conf.high')]<-round(resTab[,c('estimate','p.value','conf.low','conf.high')],3)
    resTab<-resTab[,c("term", "estimate","conf.low",  "conf.high","p.value", "std.error", "statistic")]

    #insert exposure,outcome and formula and Qic
    resTab$qic<-qic['QIC']
    resTab$outcome<-outcome
    resTab$exposure<-exposure
    resTab$formula<-mformula
    #correlation struture
    resTab$corstr<-modelSel$corstr
    resTab$Nrow<-nrow(modelSel$data)
    resTab$id<-as.character(modelSel$call$id)
    resTab$otherCom<-""
    #print(resTab)

    #prepare raw summary file
    sumTxt<-paste0(c(capture.output(summary(modelSel)),
                     '\n QIC:',capture.output(qic),
                     'Time:',as.character(Sys.time()),'\n'),collapse = '\n')
    #replace formula with orginal formula
    sumTxt<-gsub('mformula',mformula,sumTxt)


    #add to all output stored df and str
    if(is.na(allRes)) allRes<-resTab else allRes<-rbind(allRes,resTab)
    allSumm<-paste0(allSumm,sumTxt,sep=paste0(rep('=',100),collapse=''))

    print(mformula)

    #create cross table if intersection columns are not factor
    if(is.factor(df[,exposure]) | is.logical(df[,exposure])){
      ftab<-data.frame(ftable(df[,outcome],df[,exposure],dnn=c(outcome,exposure)),stringsAsFactors = F)
      ftab$formula<-mformula
      ftab<-rbind(colnames(ftab),sapply(ftab,as.character))
      colnames(ftab) <- as.character(seq(dim(ftab)[2]))
      allCrosTabs<-rbind(allCrosTabs,ftab)
    }
  }

allRes$model<-'baseModelNotAdjSelfAssess'
#write output files
write.xlsx(allRes, file=paste0(outputDir,'baseModelNotCntrlSelfAsses.xlsx'), sheetName = "Sheet1",col.names = TRUE, row.names = TRUE, append = FALSE)
write.csv(allCrosTabs,file = paste0(outputDir,'baseModelNotCntrlSelfAsses.csv'))
cat(allSumm,file = paste0(outputDir,'baseModelNotCntrlSelfAsses.txt'))

##----- 3.model not controlling for any covariates  ----
covariates<- c('Male','AgeGrp', 'RaceGroup', 'EducGroup',"SelfAssess") #,'Hispanic'
outcomes<- c("Illness", "Injury","Hospital",  "Concentrate", "Headaches", "RunnyNose", "ShortBreath", "SkinRash","AnySymptoms")
exposures<-c("OtherHomesFlooded","HomeFlooded","fScanFlooded","fScanInunDisCat","fScanNdaysCat" ,"fScanDepthCat")
print(paste0(c('outcomes-> ',outcomes),collapse = ', '))
print(paste0(c('exposures-> ',exposures),collapse = ', '))
summary(subDf[,c(exposures,outcomes)])

allRes<-NA
allSumm<-''
allCrosTabs<-data.frame()

for(exposure in exposures)
  for(outcome in outcomes){
    mformula<-paste0(outcome,' ~ ', exposure)
    df<-subDf[complete.cases(subDf[,c(outcome,exposure,'tractID10')]),]
    df['id']<-seq(dim(df)[1])
    model<-geeglm(as.formula(mformula),
                  id=tractID10,
                  data = df,
                  family =poisson(link='log'),
                  corstr = "independence")

    #update correlation structure
    model2 <- update(model, corstr = "exch")
    model3 <- update(model, corstr = "ar1")



    ##select correlation structure based on smallest QIC
    modelSel<-list(model,model2,model3)[which.min(unlist(lapply(list(model,model2,model3),mQIC)))][[1]]
    remove(model,model2,model3)

    ##get summary from the selected model
    qic<- QIC(modelSel)
    #summary(modelSel)

    #broom results
    resTab<-tidy(modelSel, conf.int = TRUE,exponentiate = T)
    resTab[,c('estimate','p.value','conf.low','conf.high')]<-round(resTab[,c('estimate','p.value','conf.low','conf.high')],3)
    resTab<-resTab[,c("term", "estimate","conf.low",  "conf.high","p.value", "std.error", "statistic")]

    #insert exposure,outcome and formula and Qic
    resTab$qic<-qic['QIC']
    resTab$outcome<-outcome
    resTab$exposure<-exposure
    resTab$formula<-mformula
    #correlation struture
    resTab$corstr<-modelSel$corstr
    resTab$Nrow<-nrow(modelSel$data)
    resTab$id<-as.character(modelSel$call$id)
    resTab$otherCom<-""
    #print(resTab)

    #prepare raw summary file
    sumTxt<-paste0(c(capture.output(summary(modelSel)),
                     '\n QIC:',capture.output(qic),
                     'Time:',as.character(Sys.time()),'\n'),collapse = '\n')
    #replace formula with orginal formula
    sumTxt<-gsub('mformula',mformula,sumTxt)


    #add to all output stored df and str
    if(is.na(allRes)) allRes<-resTab else allRes<-rbind(allRes,resTab)
    allSumm<-paste0(allSumm,sumTxt,sep=paste0(rep('=',100),collapse=''))

    print(mformula)

    #create cross table if intersection columns are not factor
    if(is.factor(df[,exposure]) | is.logical(df[,exposure])){
      ftab<-data.frame(ftable(df[,outcome],df[,exposure],dnn=c(outcome,exposure)),stringsAsFactors = F)
      ftab$formula<-mformula
      ftab<-rbind(colnames(ftab),sapply(ftab,as.character))
      colnames(ftab) <- as.character(seq(dim(ftab)[2]))
      allCrosTabs<-rbind(allCrosTabs,ftab)
    }
  }

#write output files
allRes$model<-'baseModelNotAdjAnyCovariates'
write.xlsx(allRes, file=paste0(outputDir,'baseModelNotCntrlAnything.xlsx'), sheetName = "Sheet1",col.names = TRUE, row.names = TRUE, append = FALSE)
write.csv(allCrosTabs,file = paste0(outputDir,'baseModelNotCntrlAnything.csv'))
cat(allSumm,file = paste0(outputDir,'baseModelNotCntrlAnything.txt'))

##------ 4.base model with interaction for individual level characteristic and controlling for self assess ------

covariates<- c('Male','AgeGrp', 'RaceGroup', 'EducGroup',"SelfAssess") #,'Hispanic'
outcomes<- c("Illness", "Injury","Hospital",  "Concentrate", "Headaches", "RunnyNose", "ShortBreath", "SkinRash","AnySymptoms")
exposures<-c("OnlyOtherHomesFlooded","OtherHomesFlooded","HomeFlooded","fScanFlooded","Contact_Water")#,"fScanInunDisCat","fScanNdaysCat" ,"fScanDepthCat")
inters<-c('RaceGroup','Male','AgeGrp',  'EducGroup')
print(paste0(c('outcomes-> ',outcomes),collapse = ', '))
print(paste0(c('exposures-> ',exposures),collapse = ', '))
print(paste0(c('covariates-> ',covariates),collapse = ', '))
summary(subDf[,c(covariates,exposures,outcomes,inters)])

allRes<-NA
allSumm<-''
allCrosTabs<-data.frame()

for(inter in inters){
  for(exposure in exposures)
    for(outcome in outcomes){
      mformula<-paste0(outcome,' ~ ', exposure,' * ',inter,' + ' , paste0(covariates,collapse = ' + '))
      df<-subDf[complete.cases(subDf[,c(outcome,exposure,covariates,inter,'tractID10')]),]
      #combine race - asian and others
      df$RaceGroup<-recode(df$RaceGroup,"c('Non_Hispanic_Asian', 'Non_Hispanic_Other')='Non_Hispanic_AsianNOthers'")
      df <- df %>% mutate(RaceGroup=relevel(RaceGroup,ref='Non_Hispanic_White'))
      #create cross table if intersection columns are not factor
      if (is.factor(df[,inter])){
        ftab<-data.frame(ftable(df[,outcome],df[,exposure],df[,inter],dnn=c(outcome,exposure,inter)),stringsAsFactors = F)
        ftab$formula<-mformula
        ftab1<-rbind(colnames(ftab),sapply(ftab,as.character))
        colnames(ftab1) <- as.character(seq(dim(ftab1)[2]))
        allCrosTabs<-rbind(allCrosTabs,ftab1)

        #if any of the counts is 0 skip this loop
        if(any(ftab$Freq==0)){
          allSumm<-paste0(allSumm,'\n',mformula,'\n skipped due to not enought records count in each category bin \n',sep=paste0(rep('=',100),collapse=''))
          next()}
      }

      df['id']<-seq(dim(df)[1])
      model<-geeglm(as.formula(mformula),
                    id=tractID10,
                    data = df,
                    family =poisson(link='log'),
                    corstr = "independence")

      #update correlation structure
      model2 <- update(model, corstr = "exch")
      model3 <- update(model, corstr = "ar1")

      ##select correlation structure based on smallest QIC
      modelSel<-list(model,model2,model3)[which.min(unlist(lapply(list(model,model2,model3),mQIC)))][[1]]
      remove(model,model2,model3)

      ##get summary from the selected model
      qic<- QIC(modelSel)
      #summary(modelSel)

      #broom results
      resTab<-tidy(modelSel, conf.int = TRUE,exponentiate = T)
      resTab[,c('estimate','p.value','conf.low','conf.high')]<-round(resTab[,c('estimate','p.value','conf.low','conf.high')],3)
      resTab<-resTab[,c("term", "estimate","conf.low",  "conf.high","p.value", "std.error", "statistic")]

      #insert exposure,outcome and formula and Qic
      resTab$qic<-qic['QIC']
      resTab$outcome<-outcome
      resTab$exposure<-exposure
      resTab$formula<-mformula
      #correlation struture
      resTab$corstr<-modelSel$corstr
      resTab$Nrow<-nrow(modelSel$data)
      resTab$id<-as.character(modelSel$call$id)
      resTab$otherCom<-paste0('interaction term ',inter)
      #print(resTab)

      #prepare raw summary file
      sumTxt<-paste0(c(capture.output(summary(modelSel)),
                       '\n QIC:',capture.output(qic),
                       'Time:',as.character(Sys.time()),'\n'),collapse = '\n')
      #replace formula with orginal formula
      sumTxt<-gsub('mformula',mformula,sumTxt)


      #add to all output stored df and str
      if(is.na(allRes)) allRes<-resTab else allRes<-rbind(allRes,resTab)
      allSumm<-paste0(allSumm,sumTxt,sep=paste0(rep('=',100),collapse=''))

      #print(ftab)
      print(mformula)

    }
  cat(allSumm,file = paste0(outputDir,'demogInteractionModel.txt'),append = T)
  allSumm<-''
}
allRes$model<-'demogInteractionModel'
#write output files
write.xlsx(allRes, file=paste0(outputDir,'demogInteractionModel.xlsx'), sheetName = "Sheet1",col.names = TRUE, row.names = TRUE, append = FALSE)
write.csv(allCrosTabs,file = paste0(outputDir,'demogInteractionModel.csv'))

##------ 5.base model with SVI interaction and controlling for self assess ------

covariates<- c('Male','AgeGrp', 'RaceGroup', 'EducGroup',"SelfAssess") #,'Hispanic'
outcomes<- c("Illness", "Injury","Hospital",  "Concentrate", "Headaches", "RunnyNose", "ShortBreath", "SkinRash","AnySymptoms")
exposures<-c("OtherHomesFlooded","HomeFlooded","fScanFlooded","fScanInunDisCat","fScanNdaysCat" ,"fScanDepthCat")
inters<-c("reRankSVI", "reRankSVI_T1", "reRankSVI_T2", "reRankSVI_T3", "reRankSVI_T4",
          "cat_SVI", "cat_SVI_T1", "cat_SVI_T2", "cat_SVI_T3", "cat_SVI_T4")
print(paste0(c('outcomes-> ',outcomes),collapse = ', '))
print(paste0(c('exposures-> ',exposures),collapse = ', '))
print(paste0(c('covariates-> ',covariates),collapse = ', '))
summary(subDf[,c(covariates,exposures,outcomes,inters)])

outcome<-outcomes[2]
exposure<- exposures[1]
allRes<-NA
allSumm<-''
allCrosTabs<-data.frame()

for(inter in inters){
for(exposure in exposures)
  for(outcome in outcomes){
    mformula<-paste0(outcome,' ~ ', exposure,' * ',inter,' + ' , paste0(covariates,collapse = ' + '))
    df<-subDf[complete.cases(subDf[,c(outcome,exposure,covariates,inter,'tractID10')]),]

    #create cross table if intersection columns are not factor
    if (is.factor(df[,inter])){
      ftab<-data.frame(ftable(df[,outcome],df[,exposure],df[,inter],dnn=c(outcome,exposure,inter)),stringsAsFactors = F)
      ftab$formula<-mformula
      ftab1<-rbind(colnames(ftab),sapply(ftab,as.character))
      colnames(ftab1) <- as.character(seq(dim(ftab1)[2]))
      allCrosTabs<-rbind(allCrosTabs,ftab1)

      #if any of the counts is 0 skip this loop
      if(any(ftab$Freq==0)){
        allSumm<-paste0(allSumm,'\n',mformula,'\n skipped due to not enought records count in each category bin \n',sep=paste0(rep('=',100),collapse=''))
        next()}
    }


    df['id']<-seq(dim(df)[1])
    model<-geeglm(as.formula(mformula),
                  id=tractID10,
                  data = df,
                  family =poisson(link='log'),
                  corstr = "independence")

    #update correlation structure
    model2 <- update(model, corstr = "exch")
    model3 <- update(model, corstr = "ar1")

    ##select correlation structure based on smallest QIC
    modelSel<-list(model,model2,model3)[which.min(unlist(lapply(list(model,model2,model3),mQIC)))][[1]]
    remove(model,model2,model3)

    ##get summary from the selected model
    qic<- QIC(modelSel)
    #summary(modelSel)

    #broom results
    resTab<-tidy(modelSel, conf.int = TRUE,exponentiate = T)
    resTab[,c('estimate','p.value','conf.low','conf.high')]<-round(resTab[,c('estimate','p.value','conf.low','conf.high')],3)
    resTab<-resTab[,c("term", "estimate","conf.low",  "conf.high","p.value", "std.error", "statistic")]

    #insert exposure,outcome and formula and Qic
    resTab$qic<-qic['QIC']
    resTab$outcome<-outcome
    resTab$exposure<-exposure
    resTab$formula<-mformula
    #correlation struture
    resTab$corstr<-modelSel$corstr
    resTab$Nrow<-nrow(modelSel$data)
    resTab$id<-as.character(modelSel$call$id)
    resTab$otherCom<-paste0('interaction term ',inter)
    #print(resTab)

    #prepare raw summary file
    sumTxt<-paste0(c(capture.output(summary(modelSel)),
                     '\n QIC:',capture.output(qic),
                     'Time:',as.character(Sys.time()),'\n'),collapse = '\n')
    #replace formula with orginal formula
    sumTxt<-gsub('mformula',mformula,sumTxt)


    #add to all output stored df and str
    if(is.na(allRes)) allRes<-resTab else allRes<-rbind(allRes,resTab)
    allSumm<-paste0(allSumm,sumTxt,sep=paste0(rep('=',100),collapse=''))

    #print(ftab)
    print(mformula)
  }
  #write some outputs to clear memorty
  cat(allSumm,file = paste0(outputDir,'sviInteractionModel.txt'),append = T)
  allSumm<-''
  write.table(allCrosTabs, file = paste0(outputDir,'sviInteractionModel.csv'), sep = ",",
              col.names = !file.exists(paste0(outputDir,'sviInteractionModel.csv')), append = T)
  allCrosTabs<-data.frame()
}
allRes$model<-'sviInteractionModel'
#write output files
write.xlsx(allRes, file=paste0(outputDir,'sviInteractionModel.xlsx'), sheetName = "Sheet1",col.names = TRUE, row.names = TRUE, append = FALSE)


##----- End of model run
##XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX


#----------Comparision between home flooded and remote flooded----
#
#subset only those with flooding -> removes 8 recs
# subDf<-subDf[!is.na(subDf$dfoInundDist),]
# library(caret)
# confusionMatrix(factor(subDf$dfoInundDist==0),reference=factor(subDf$HomeFlooded==1))
# confusionMatrix(factor(subDf$fScanInundDist==0),reference=factor(subDf$HomeFlooded==1))
# #using raster distance
# confusionMatrix(factor(subDf$dfoInundDist<400),reference=factor(subDf$HomeFlooded==1))
# confusionMatrix(factor(subDf$fScanInundDist<100),reference=factor(subDf$HomeFlooded==1))
#
# #plot distance vs specificity and sensitivity
# disSenSpec<-data.frame()
# for(i in seq(0,8500,by = 50)){
# cm<-confusionMatrix(factor(subDf$fScanInundDist<i),reference=factor(subDf$HomeFlooded==1))
# disSenSpec<-rbind(disSenSpec,data.frame(distance=i,sensitivity=cm$byClass['Sensitivity'],specificity=cm$byClass['Specificity']))
# }
# plot(disSenSpec)
