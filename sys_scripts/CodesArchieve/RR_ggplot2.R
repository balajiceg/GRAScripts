# Author guideline on artwork Health and place
# https://www.elsevier.com/authors/policies-and-guidelines/artwork-and-media-instructions/artwork-sizing
#install.packages('tidyverse')
#install.packages('readxl')
library(ggplot2)
library(readxl)
library(hablar)
library(dplyr)
library(stringr)
library(plyr)
library(scales)
library(egg)

AXIS_Y_SIZE<-14
LEGEND_SIZE<-14
Y_TITLE_SIZE<-14
LINE_WIDTH<-.5 #erro bar line width
GRID_WIDTH<-.9
POINT_WIDTH<-1.8 #error bar middle point width
DASH_WIDTH<-.2
DOT_SIZE<-.5
ERROR_BAR_TOP<-.2
LABEL_SIZE<-13
WORD_WRAP<-15
PLOT_MARGIN<-unit(c(.1,.2,-.2,.2), "cm")
LEGEND_MAR<-margin(-0.7,0,.4,0,"cm")
STRIP_LINES=0.2
DODGE_WIDTH=0.5
AXIS_X_SIZE<-12

#---- functions ----

make_chart<-function (df,column='flood',legend='none'){
  #wrap outcome names
  df$outcome = str_wrap(df$outcome,width = WORD_WRAP)
  #color column
  df['cate']<-df[,column]
  #period to roman
  periods<-unique(df$period)
  df$period<-mapvalues(df$period,from=periods,to=as.character(as.roman(seq(length(periods)))))
  caption<-paste(as.character(as.roman(seq(length(periods)))),periods,collapse = ' , ',sep=' - ')
  #draw plot
  p1<-ggplot(df, aes(y = RR, x = period ,shape=factor(cate),color=factor(cate))) +   facet_wrap(~outcome,nrow=1)+
    geom_errorbar(aes(ymax = conf25, ymin = conf95), size = LINE_WIDTH, width = 
                    ERROR_BAR_TOP,position = position_dodge(width = DODGE_WIDTH)) +
    geom_point(size = POINT_WIDTH,position = position_dodge(width = DODGE_WIDTH)) +
    scale_shape_manual(values=c(15,17,16,18,8,16,17,15,18,8,9))+
    scale_color_manual(values=c( "#009E73","#D55E00","#0072B2",  "#E69F00","#F0E442","#CC79A7","#E69F00","#999999","#000000","#009E73"))+
    geom_hline(aes(yintercept = 1), size = DASH_WIDTH, linetype = "dashed")+
    scale_y_log10(breaks = trans_breaks("log10", function(x) 10^x),
                  labels = trans_format("log10", function(x) round(10^x,1)))+ 
    theme_bw() +
    theme(panel.grid.minor = element_blank(),panel.grid.major.x = element_blank(),
          legend.title = element_blank(),
          panel.grid.major.y = element_line(size = GRID_WIDTH),
          legend.position =legend,legend.margin=LEGEND_MAR,
          legend.text=element_text(size=LEGEND_SIZE),
          axis.text.x= element_text(size = AXIS_X_SIZE),
          plot.caption=element_text(size=AXIS_X_SIZE,hjust = 0.5, margin=margin(-2,10,10,10)),
          axis.ticks.length.x=unit(0, "cm"),
          axis.text.y = element_text(size = AXIS_Y_SIZE,angle = 90),axis.title = element_text(size = Y_TITLE_SIZE),
          plot.margin = PLOT_MARGIN, strip.text = element_text(size=LABEL_SIZE), 
          panel.spacing.x = unit(0,'cm'),panel.border = element_rect(size=STRIP_LINES,linetype = 'solid'),
          axis.line = element_line(linetype = 'solid',size=LINE_WIDTH),strip.background = element_rect(colour="black", fill="gray95",size = LINE_WIDTH),)+
    ylab("Rate ratio") + xlab("")
  if(legend!='none'){p1=p1+labs(caption = caption)}
  return(p1)
}

merge_charts<-function (df,filename,column='flood',width=6,height=7,format='.pdf'){
  loutcomes<-list()
  loutcomes[[1]]<- c("Diarrhea","Pregnancy Complications","Respiratory Syndrome","Asthma")
  loutcomes[[2]]<-c("Insect Bite", "Dehydration",'Chest Pain','Heat Related Illness')
  
  outcomes<-loutcomes[[1]]
  sub_df<-subset(df,outcome %in% outcomes)
  p1<-make_chart(sub_df,legend='none',column=column)
  
  outcomes<-loutcomes[[2]]
  sub_df<-subset(df,outcome %in% outcomes)
  p2<-make_chart(sub_df,legend='bottom',column=column)
  
  #save the plot
  p<-ggarrange(p1,p2)
  ggsave(paste0(filename,format),plot=p,width = unit(width,'cm'),height=unit(height,'cm'))
  return(p)
}

#----- read data ----
all_df<-read_excel("Z:\\Balaji\\Analysis_SyS_data\\28032021\\merged_all.xlsx")
all_df$outcome<-mapvalues(all_df$outcome,from = c( "Bite_Insect", "Dehydration", "Diarrhea", "Pregnancy_complic","RespiratorySyndrome","Asthma",'Chest_pain','Heat_Related_But_Not_dehydration'),
                          to= c("Insect Bite", "Dehydration", "Diarrhea","Pregnancy Complications","Respiratory Syndrome","Asthma",'Chest Pain','Heat Related Illness'))


#---- for base model ---
df<-subset(all_df,model=='base')
#subset requried estimaes
df<-df[grep('flooded_.*:period_.*',df$covar),]
#assign flooding column
df$flood<-gsub('flooded_',"",gsub(":period_.*",'',df$covar))
#assign period coulumn
df$period<-gsub('flooded_.*:period_','',df$covar)

df$flood<-factor(df$flood,levels = c("moderately flooded", "highly flooded" ))
merge_charts(df,'base',column = 'flood',width = 8,height = 6) # try to keep it <=9cm for single column

#---- for ethnicity model ----
df<-subset(all_df,model=='ethnicity')
#subset requried estimaes
df<-df[grep('flood_binary_True:period_.*:Ethnicity_.*',df$covar),]
#assign period coulumn
df$period<-gsub(':Ethnicity_.*','',gsub('flood_.*:period_','',df$covar))
merge_charts(df,'ethnicity',column = 'modifier_cat',width = 8,height = 6)

#---- for race model ----
df<-subset(all_df,model=='Race')
#subset requried estimaes
df<-df[grep('flood_binary_True:period_.*:Race_.*',df$covar),]
#assign period coulumn
df$period<-gsub(':Race_.*','',gsub('flood_.*:period_','',df$covar))
merge_charts(df,'race',column = 'modifier_cat',width = 8,height = 6)

#---- for sex model ----
df<-subset(all_df,model=='sex')
#subset requried estimaes
df<-df[grep('flood_binary_True:period_.*:Sex_.*',df$covar),]
#assign period coulumn
df$period<-gsub(':Sex_.*','',gsub('flood_.*:period_','',df$covar))
merge_charts(df,'sex',column = 'modifier_cat',width = 8,height = 6)

##---- for stratified models ----

#---- for ethnicity model ----
df<-subset(all_df,model=='ethnicity_strata')
#subset requried estimaes
df<-df[grep('flood_binary_True:period_.*',df$covar),]
#assign period coulumn
df$period<-gsub('flood_.*:period_','',df$covar)
merge_charts(df,'ethnicity_strata',column = 'modifier_cat',width = 9,height = 6)

#---- for race model ----
df<-subset(all_df,model=='Race_strata')
#subset requried estimaes
df<-df[grep('flood_binary_True:period_.*',df$covar),]
#assign period coulumn
df$period<-gsub('flood_.*:period_','',df$covar)
merge_charts(df,'race_strata',column = 'modifier_cat',width = 11,height = 6)

#---- for sex model ----
df<-subset(all_df,model=='sex_strata')
#subset requried estimaes
df<-df[grep('flood_binary_True:period_.*',df$covar),]
#assign period coulumn
df$period<-gsub('flood_.*:period_','',df$covar)
merge_charts(df,'sex_strata',column = 'modifier_cat',width = 8,height = 6)

#---- for age model ----
df<-subset(all_df,model=='Age_strata')
#subset requried estimaes
df<-df[grep('flood_binary_True:period_.*',df$covar),]
#assign period coulumn
df$period<-gsub('flood_.*:period_','',df$covar)
df$modifier_cat<-gsub('gt','>',df$modifier_cat)
merge_charts(df,'age_strata',column = 'modifier_cat',width = 10,height = 8)


#---- sensitivity base model ------

#----- read data ----
all_df<-read_excel("Z:\\Balaji\\Analysis_SyS_data\\28032021\\sensitivity_remove_june\\merged_All_sens.xlsx")
all_df$outcome<-mapvalues(all_df$outcome,from = c( "Bite_Insect", "Dehydration", "Diarrhea", "Pregnancy_complic","RespiratorySyndrome","Asthma",'Chest_pain','Heat_Related_But_Not_dehydration'),
                          to= c("Insect Bite", "Dehydration", "Diarrhea","Pregnancy Complications","Respiratory Syndrome","Asthma",'Chest Pain','Heat Related Illness'))


#---- for base model ---
df<-all_df
#subset requried estimaes
df<-df[grep('flooded_.*:period_.*',df$covar),]
#assign flooding column
df$flood<-gsub('flooded_',"",gsub(":period_.*",'',df$covar))
#assign period coulumn
df$period<-gsub('flooded_.*:period_','',df$covar)

df$flood<-factor(df$flood,levels = c("moderately flooded", "highly flooded" ))
merge_charts(df,'base_sensitivity',column = 'flood',width = 8,height = 6)

#------ binaray model
all_df<-read_excel("Z:\\Balaji\\Analysis_SyS_data\\28032021\\sensitivity_binary\\merged_All.xlsx")
all_df$outcome<-mapvalues(all_df$outcome,from = c( "Bite_Insect", "Dehydration", "Diarrhea", "Pregnancy_complic","RespiratorySyndrome","Asthma",'Chest_pain','Heat_Related_But_Not_dehydration'),
                          to= c("Insect Bite", "Dehydration", "Diarrhea","Pregnancy Complications","Respiratory Syndrome","Asthma",'Chest Pain','Heat Related Illness'))


#---- for base model ---
df<-all_df
#subset requried estimaes
df<-df[grep('flood_binary_True:period_.*',df$covar),]
#assign flooding column
df$flood<-'flooded'
#assign period coulumn
df$period<-gsub('flood_binary_True:period_','',df$covar)

merge_charts(df,'base_binary',column = 'flood',width = 8,height = 6)

