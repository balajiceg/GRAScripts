source("Z:\\GRAScripts\\sys_scripts\\QueryExecuter.R")
library(dplyr)

#read raw sys data
sys_raw<-read.csv("Z:\\Balaji\\SyS data\\merged_with_rowid.csv")

#read already created outcomes file
sys_outcomes<-read.csv("Z:\\Balaji\\SyS data\\sys_merged_outcomes.csv")

#read queries file
queries<-read.csv("Z:/GRAScripts/sys_scripts/queries.csv")

#outcomes to be assigned , names same as in the queries file
outcomes<-c('Cardiovascular diseases')#"NVD - Diarrhea","Respiratory_Syndrome_RESP","CDC Asthma CCDD v1","Bite: Insect","Dehydration 2","DrowningOrSubmersion - Oregon","Hypothermia","Chest Pain","Heat-Related Illness, No Dehydration","CO Exposure (Non-fire, Unintentional)")
outcomes_cols<-c('CardiovascularDiseases')#"Diarrhea","RespiratorySyndrome",'Asthma','Bite-Insect','Dehydration','Drowning','Hypothermia','Chest_pain','Heat_Related_But_Not_dehydration','CO_Exposure')
for(i in 1:length(outcomes)){
  outcome<-outcomes[i]
  type<-queries$Type[queries$Name==outcome]
  query<-as.character(queries[queries$Name==outcome,]$Query[1])
  if(type=='CCDD'){
    #use ccdd query
    #join the CC and DD from data
    ccdd<-paste0(sys_raw$ChiefComplaintOrig,' ',sys_raw$`Discharge.Diagnosis`)
    res<-get_match_ccdd(query,ccdd)
    to_filter<-res$match
  }
  else{
    #subsyndrome query
    #get points for the chief complaints
    points<-get_points_subsyn(query,sys_raw$ChiefComplaintOrig)
    #see which records with points >=6
    to_filter<-points>=6
  }
  to_join<-data.frame(row_id=sys_raw$row_id,xyz=to_filter)
  colnames(to_join)[2]<-c(outcomes_cols[i])
  sys_outcomes<-merge(sys_outcomes,to_join,by='row_id', all.x=T )
  print(outcomes_cols[i])
  write.csv(sys_outcomes,"Z:\\Balaji\\SyS data\\sys_merged_outcomes.csv",row.names = F)
}

