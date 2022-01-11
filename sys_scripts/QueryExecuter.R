library(stringr)
library(dplyr)

#for subsyndrome type qureries
get_points_subsyn<-function(query,chief_c){
  #trim the query and remove double spaces
  query<-str_trim(query)
  query<-gsub("\\s+",' ',query)
  #trim double spaces and front and back spaces of chief_c
  chief_c<-str_trim(chief_c)
  chief_c<-gsub("\\s+",' ',chief_c)
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
  # return total match points for each record
  return(total_points)
}


#for ccdd queries
get_match_ccdd<-function(query,ccdd){
  #trim double spaces and front and back spaces of ccdd
  ccdd<-str_trim(ccdd)
  ccdd<-gsub("\\s+",' ',ccdd)
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
    expr1<-paste0('\\b',expr1,'\\b')
    res_m<-regexpr(expr1,ccdd,ignore.case = T)>0
    query2<-paste0(query2,res_m)
    query1<-str_sub(subs,j)
    list_subq<-c(list_subq,expr1)
  }
  j<-regexpr('[|&)(]',subs)
  if (j!=-1) query2<-paste0(query2,str_sub(subs,j))
  
  query2<-as.matrix(query2)
  result<-apply(query2,1,function(x) {return(eval(parse(text=x)))})
  #return the math (true or false) for each record pased and also a subquery string list
  return(list(match=result,subqueries=list_subq))
}


#Examples for executting the above function

# #read data
# sys_data<-read.csv("Z:/Balaji/SyS data/merged.csv")
# #read queries
# queries<-read.csv("Z:/GRAScripts/sys_scripts/queries.csv")
# 
# 
# #excel read 
# sys_data<-read_xlsx("Z:/Balaji/Sys/Demo_page_data_MJ/Pregancy CCDD/Pregnancy CCDD DataDetails.xlsx")
# 
# #testing subsyndrome query
# query<-as.character(queries[queries$Name=="Pregnancy and Pregnancy Loss and Delivery v1 - CDC",]$Query[1])
# #get points for the chief complaints
# points<-get_points_subsyn(query,sys_data$ChiefComplaintParsed)
# #filter records with points >=6
# filtered<-sys_data$ChiefComplaintOrig[points>=6]
# #join points to form a dataframe
# filtered=data.frame(cc=filtered,points=points[points>=6])
# filtered_all<-sys_data[points>=6,]
# filtered_all$points<-points[points>=6]
# View(filtered)
# #write the filtered output to file
# write.csv(filtered,"subsyn_filtered_output.csv")
# write.csv(filtered_all,"subsyn_filtered_output_all_cols.csv")
# 
# 
# 
# 
# 
# #test ccdd "Disaster-related Mental Health v1 - Syndrome Definition Committee"	
# query<-as.character(queries[queries$Name=="Pregnancy and Pregnancy Loss and Delivery v1 - CDC",]$Query[1])
# 
# #join the CC and DD from data
# ccdd<-paste0(sys_data$ChiefComplaintParsed,' ',sys_data$`Discharge Diagnosis`)
# res<-get_match_ccdd(query,ccdd)
# View(res$subqueries)
# #view the filtered records
# length(ccdd[res$match])
# length(ccdd[!res$match])
# #write the filtered output to file
# write.csv(ccdd[res$match],"ccdd_filtered_output.csv")
# write.csv(sys_data[res$match,],"ccdd_filtered_output_all_cols.csv")
# 
# 
# #use only CC for ccdd query
# ccdd<-paste0(sys_data$ChiefComplaintOrig)
# res<-get_match_ccdd(query,ccdd)
# View(res$subqueries)
# #view the filtered records
# View(ccdd[!res$match])
# #write the filtered output to file
# write.csv(ccdd[res$match],"cc_filtered_output.csv")
# write.csv(sys_data[res$match,],"cc_filtered_output_all_cols.csv")
# 
# 
# #use only DD queries for ccdd query
# ccdd<-paste0(sys_data$Discharge.Diagnosis)
# res<-get_match_ccdd(query,ccdd)
# View(res$subqueries)
# #view the filtered records
# View(ccdd[res$match])
# #write the filtered output to file
# write.csv(ccdd[res$match],"dd_filtered_output.csv")
# write.csv(sys_data[res$match,],"dd_filtered_output_all_cols.csv")
