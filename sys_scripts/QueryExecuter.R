
library(stringr)
library(dplyr)
#functions

get_points_subsyn<-function(query,chief_c){
  #trim the query and remove double spaces
  query<-str_trim(query)
  query<-gsub("\\s+",' ',query)
  #extract the points in brackets and make it number
  points<-str_extract_all(query,regex("\\(.*?\\)"))[[1]]
  points<-as.numeric(gsub("[()]","",points))
  #extract words before brackets and drop empty words
  words<-str_split(query,regex("\\(.*?\\)"))[[1]]
  words<-words[words!=""]
  #trim the words and replace space with \s
  words<-trimws(words)
  #replace the wildcard in query with regex wildcard
  words<-gsub("\\*",".*",words)
  #add regex word boundaries
  words<-paste0('\\b',words,'\\b')
  
  #create dataframe using points and words
  words_pts<-data.frame(words,points)
  
  # check each condition in each record and sum up the points
  total_points<-rowSums(apply(words_pts,1,function(x){
    return(as.integer(regexpr(x['words'],chief_c,ignore.case = T)>0) * as.integer(x['points']))
  }))
  
  return(total_points)
}


#for ccdd query
get_match_ccdd<-function(query,ccdd){
  #replace and or andnot using regex
  x<-gsub(",\\s*or\\s*,"," || ",query,ignore.case = T)
  x<-gsub(",\\s*and\\s*,"," && ",x,ignore.case = T)
  x<-gsub(",\\s*andnot\\s*,"," &&! ",x,ignore.case = T)
  
  #replace special symbols
  x<-gsub(",","",x,ignore.case = T)
  x<-gsub("\\.","\\\\.",x,ignore.case = T)
  
  #replace regex used
  x<-gsub("\\^",".*",x,ignore.case = T)
  x<-gsub("_",".",x,ignore.case = T)
  
  query1<-x
  query2<-""
  list_subq<-c()
  while(T){
    #get the subquery
    i<-regexpr('[^|&)(! ]',query1)
    query2<-paste0(query2,str_sub(query1,end=i-1))
    subs<-str_sub(query1,i)
    j<-regexpr('[|&)(]',subs)
    expr<- str_sub(subs,1,j-1)
    if(expr=='')break();
    
    #check for match
    expr1<-str_trim(expr)
    res_m<-regexpr(expr,ccdd,ignore.case = T)>0
    query2<-paste0(query2,res_m)
    query1<-str_sub(subs,j)
    list_subq<-c(list_subq,expr1)
  }
  j<-regexpr('[|&)(]',subs)
  if (j!=-1) query2<-paste0(query2,str_sub(subs,j))
  
  query2<-as.matrix(query2)
  result<-apply(query2,1,function(x) {return(eval(parse(text=x)))})
  return(list(match=result,subqueries=list_subq))
}



#read data
sys_data<-read.csv("H:/SyS data/merged.csv")
#read queries
queries<-read.csv("H:/Balaji/GRAScripts/sys_scripts/queries.csv")




#testing subsyndrome query
query<-as.character(queries[queries$Name=="ExcessiveHeat",]$Query[1])
#get points for the chief complaints
points<-get_points_subsyn(query,sys_data$ChiefComplaintOrig)
#filter records with points >=6
filtered<-sys_data$ChiefComplaintOrig[points>=10]
#join points to form a dataframe
filtered=data.frame(cc=filtered,points=points[points>=10])
View(filtered)
#write the filtered output to file
write.csv(filtered,"subsyn_filtered_output.csv")




#test ccdd "Disaster-related Mental Health v1 - Syndrome Definition Committee"	
query<-as.character(queries[queries$Name=="Disaster-related Mental Health v1 - Syndrome Definition Committee",]$Query[1])
#join the CC and DD from data
ccdd<-paste0(sys_data$ChiefComplaintOrig,' ',sys_data$Discharge.Diagnosis)
res<-get_match_ccdd(query,ccdd)
View(res$subqueries)
#view the filtered records
View(ccdd[res$match])
#write the filtered output to file
write.csv(ccdd[res$match],"ccdd_filtered_output.csv")

