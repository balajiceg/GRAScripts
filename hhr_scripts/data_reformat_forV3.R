#loading required packages
library(raster)
library(rgdal)
library(GISTools)
library(plotly)

# library(mapview)


#harricane harvey data
hhd_data<-read.csv('Z:\\Balaji\\HHR\\HHR_20191001_CT_Summary_V03\\HHR_20191001_CT_NonDemoVars_v03.csv')


#rename columns
colnames(hhd_data)<-c('tractId','variables','description','values','value_desc','no_of_reponses')
hhd_data<-hhd_data[hhd_data$no_of_reponses!=-1,]

#unique questions
questions<-unique(hhd_data$variables)
questions_short<-unique(hhd_data$description)
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
    
    df[j,paste0(questions_short[i],'_t')]<-sum(sub_tract$no_of_reponses)
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

#write the joined table to save the work
write.csv(joined,'Z:\\Balaji\\HHR\\HHR_20191001_CT_Summary_V03\\joined_table_nondemos.csv',row.names = F)
