`#install.packages('tidyverse')
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

merge_charts<-function (df,filename,loutcomes=list(),column='flood',width=6,height=7,format='.pdf'){
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
merged_file <- list.files(pattern = 'merged_flood*')
print(merged_file)
all_df<-read_excel(merged_file[1])
all_df$outcome<-mapvalues(all_df$outcome,from = c( 'DrugOverdoseAbuse', 'Opi_Any', 'Opi_Illicit', 
                                                   'Opi_Natural_SemiSynth', 'Opi_Other', 'Opi_psychosimul', 
                                                   'Opi_Synthetic', 'Opi_Use_Abuse_Depend',"Opi_Any_NonIllicit" ),
                           to= c("Substance use", "All","Illicit",
                                 'Natural/Semi Synthetic','Other','Psychosimulants',
                                 'Synthetic','Use/Abuse/Dependence',"Other Non-Illicit" ))

df<-subset(all_df, !(outcome %in% c("Psychosimulants", "Synthetic", "Natural/Semi Synthetic","Use/Abuse/Dependence",
                                    "All",'Other',"Substance use")))

#df$outcome <- factor(df$outcome, levels = c("Other Non-Illicit", "Illicit", "Alcohol", "Cannabis") )             
#---- for main model ----
#subset requried estimaes
df<-df[grep('floodr_cat_FLood_1:Time_*',df$covar,ignore.case = T),]
#assign period coulumn
df$period<-gsub('floodr_cat_FLood_1:Time_','',df$covar,ignore.case = T)
df$period <- factor(df$period,levels=c("flood","PostFlood1", "PostFlood2","NextYear1", "NextYear2"  ))
make_chart(df ,"model", legend = 'bottom')

#---- for categorical model ----

#subset requried estimaes
df<-df[grep(':Time_*',df$covar),]
#assign period coulumn
df$period<-gsub('floodr_cat_FLood_.:Time_','',df$covar,ignore.case = T)
df$flood <- gsub('floodr_cat','',gsub(':Time_.*','',df$covar,ignore.case = T),ignore.case = T)

df$period <- factor(df$period,levels=c("flood","PostFlood1", "PostFlood2","NextYear1", "NextYear2"  ))
make_chart(df ,'flood', legend = 'bottom')




loutcomes<- list()
loutcomes[[2]]<- c('Intestinal Infectious Diseases',"Dehydration","Pregnancy Complications",'All',"Insect Bite")
loutcomes[[1]]<-c('Hypothermia')


merge_charts(df,'RACE',column = 'modifier_cat', loutcomes ,width = 8,height = 6)
