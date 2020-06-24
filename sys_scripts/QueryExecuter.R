
library(stringr)

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


#testing
#read data
sys_data<-read.csv("Z:/Balaji/SyS data/merged.csv")
#read queries
queries<-read.csv("Z:/GRAScripts/sys_scripts/queries.csv")


#get the subsyndromes alone
subsyn_queries<-queries[queries$Type=="Subsyndrome",]
subsyn_queries$Query<-droplevels(subsyn_queries$Query)

#get a query
query<-subsyn_queries$Query[1]

#get points for all diagnosis
chief_c<-sys_data$ChiefComplaintOrig
points<-get_points_subsyn(query,chief_c)

#get records with points >=10
filtered<-chief_c[points>=10]
View(filtered)
