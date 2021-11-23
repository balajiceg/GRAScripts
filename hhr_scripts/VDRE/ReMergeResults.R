# for remerging the outputs

library(openxlsx)
library(dplyr)

files<-c(list.files('D:\\NASAProjectFiles\\Analysis_HHR\\working_files\\modelOutputs_ContactWater_withoutCrossTabs\\modelOutputs_ContactWater\\formatedModelSummary',full.names = T),
         list.files('D:\\NASAProjectFiles\\Analysis_HHR\\working_files\\modelOutputs_withoutCrossTabs\\modelOutputs\\formatedModelSummary',full.names = T))
dfs<-data.frame()

for(mfile in files){
  dfs<-bind_rows(dfs,read_excel(mfile))
}

dfs<-as_tibble(dfs)
dfs<-dfs %>% mutate(dfs,sNo=rownames(dfs)) %>%select(-...1) %>% select(sNo,term:model)

write.xlsx(dfs,file='D:\\NASAProjectFiles\\Analysis_HHR\\working_files\\mergedOutputs.xlsx')
