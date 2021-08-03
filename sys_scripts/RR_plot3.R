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
LINE_WIDTH<-.8 #erro bar line width
GRID_WIDTH<-.5
POINT_WIDTH<-1.8 #error bar middle point width
DASH_WIDTH<-.2
DOT_SIZE<-.5
ERROR_BAR_TOP<-0
LABEL_SIZE<-14
WORD_WRAP<-15
PLOT_MARGIN<-unit(c(.1,.2,.2,-.3), "cm")
LEGEND_MAR<-margin(-.2,0,0,0,"cm")
STRIP_LINES=0.2
DODGE_WIDTH=0.5
AXIS_X_SIZE<-14

#---- functions ----

make_chart<-function (df,nrow=2){
  #wrap outcome names
  #wrap outcome names
  df$outcome = str_wrap(df$outcome,width = WORD_WRAP)
  
  p<-ggplot(df, aes(y = modifier_cat, x = RR ,shape=factor(model),color=factor(model)))  + facet_wrap(.~outcome,nrow=nrow,scales = 'free_x',drop = T) +
    geom_errorbar(aes(xmax = conf25, xmin = conf95), size = LINE_WIDTH, width = 
                    ERROR_BAR_TOP,position = position_dodge(width = DODGE_WIDTH)) +
    geom_point(size = POINT_WIDTH,position = position_dodge(width = DODGE_WIDTH)) +
    scale_shape_manual(values=c(15,16,18,15,17,8,16))+
    scale_color_manual(values=c("#56B4E9",  "#009E73", 
                                "#0072B2","#D55E00", "#CC79A7","#000000","#F0E442",  "#E69F00","#0072B2"))+
    geom_vline(aes(xintercept = 1), size = DASH_WIDTH, linetype = "dashed")+
    scale_x_log10(breaks = trans_breaks("log10", function(x) 10^x),
                  labels = trans_format("log10", function(x) round(10^x,1)))+
    geom_text(aes(label=labels),hjust=-0.25, vjust=-0.4,show.legend = F)+
    theme_bw()+
    theme(panel.grid.minor = element_blank(),
          legend.title = element_blank(),
          panel.grid.major.x = element_line(size = GRID_WIDTH),
          legend.position ='bottom',legend.margin=LEGEND_MAR,
          legend.text=element_text(size=LEGEND_SIZE),legend.box = "horizontal",
          axis.text.x= element_text(size = AXIS_X_SIZE),
          #plot.caption=element_text(size=AXIS_X_SIZE,hjust = 0, margin=margin(10,10,10,10)),
          axis.ticks.length.y=unit(.1, "cm"),
          axis.text.y = element_text(size = AXIS_Y_SIZE),axis.title = element_text(size = Y_TITLE_SIZE),
          plot.margin = PLOT_MARGIN, strip.text = element_text(size=LABEL_SIZE), 
          panel.spacing.x = unit(0,'cm'),panel.border = element_rect(size=STRIP_LINES,linetype = 'solid'),
          axis.line = element_line(linetype = 'solid',size=LINE_WIDTH),strip.background = element_rect(colour="black", fill="gray95",size = LINE_WIDTH),)+
    xlab("Rate ratio") + ylab("")+ guides(shape = guide_legend(nrow = 1))
  return(p) 
}

#----- read data ----
all_df<-read_excel("Z:\\Balaji\\Analysis_SyS_data\\09072021\\merged_All_09072020.xlsx",sheet = 'new')

#subset only required outcomes
req_outcomes<-c("Cardiovascular Diseases", "Insect Bite", "Dehydration", "Diarrhea","Pregnancy Related","Asthma")
all_df<-subset(all_df, outcome %in% req_outcomes)

#subset only required modifiers
all_df<-subset(all_df, !(modifier_cat %in% c('Unknown','Asian','0')))


#make groups for age of each outcome
all_df$labels<-all_df$modifier_cat
all_df$labels<-mapvalues(all_df$labels,from = c("0_5", "18_50", "6_17", "0_17", "51_64", "gt17", "gt64", "gt50", "18_64", "1_19", "20_27", "28_35", "gt35"),
                         to= c("(<5)", "(18-50)", "(6-17)", "(<17)", "(51-64)", "(>17)", "(>64)", "(>50)", "(18-64)", "(<19)", "(20-27)", "(28-35)", "(>35)"))


all_df$labels[all_df$model!='Age_strata']<-NA
fil<-(all_df$model=='Age_strata' & all_df$outcome=="Insect Bite")
all_df$modifier_cat[fil]<-mapvalues(all_df$modifier_cat[fil],from = c("0_5" ,"6_17", "gt17"),
                                    to= c("I", "II", "III"))

fil<-(all_df$model=='Age_strata' & all_df$outcome=="Cardiovascular Diseases")
all_df$modifier_cat[fil]<-mapvalues(all_df$modifier_cat[fil],from = c("0_17", "18_50" , "51_64", "gt64" ),
                                    to= c("I", "II", "III","IV"))

fil<-(all_df$model=='Age_strata' & all_df$outcome=="Dehydration")
all_df$modifier_cat[fil]<-mapvalues(all_df$modifier_cat[fil],from = c("0_5","6_17","18_50" ,"51_64", "gt64" ),
                                    to= c("I", "II", "III","IV",'V'))

fil<-(all_df$model=='Age_strata' & all_df$outcome=="Diarrhea")
all_df$modifier_cat[fil]<-mapvalues(all_df$modifier_cat[fil],from = c("0_5", "6_17", "18_64", "gt64"),
                                    to= c("I", "II", "III","IV"))

fil<-(all_df$model=='Age_strata' & all_df$outcome=="Pregnancy Related")
all_df$modifier_cat[fil]<-mapvalues(all_df$modifier_cat[fil],from = c("1_19", "20_27", "28_35", "gt35" ),
                                    to= c("I", "II", "III","IV"))

fil<-(all_df$model=='Age_strata' & all_df$outcome=="Asthma")
all_df$modifier_cat[fil]<-mapvalues(all_df$modifier_cat[fil],from = c( "0_5", "6_17","18_50", "gt50") ,
                                    to= c("I", "II", "III","IV"))

#subset only models required
req_models<-c("Age_strata","Ethnicity_strata","Race_strata","Sex_strata",'base','base_binary')
all_df<-subset(all_df,model %in% req_models)

#rename models
all_df$model<-mapvalues(all_df$model,from =req_models ,
          to= c("Age","Ethnicity","Race","Sex",'Flood subcategory','Overall'))

#order modifer categories
all_df$modifier_cat[all_df$model=='Overall']<-'Overall'
all_df$modifier_cat<-factor(all_df$modifier_cat,
                            levels=rev(c("Overall","Moderately flooded", "Highly flooded", "M","F","Non-Hispanic", "Hispanic",   "White", "Black","Others", "I","II","III","IV", "V")))
levels(all_df$modifier_cat)<-rev(c("Overall","Moderate", "High", "Male","Female","Non-Hispanic", "Hispanic",   "White", "Black","Others", "Age Group I","Age Group II","Age Group III","Age Group IV", "Age Group V"))

#--- for flood period
df<-subset(all_df,period=='floodPeriod')
make_chart(df)
ggsave('floodPeriod.pdf',plot = make_chart(df),width = unit(8.8,'cm'),height=unit(9,'cm'))

df<-subset(all_df,period=='monthAfterFlood')
ggsave('monthAfterFlood.pdf',plot = make_chart(df),width = unit(8.8,'cm'),height=unit(10,'cm'))

df<-subset(all_df,period=='novAndDec')
ggsave('novAndDec.pdf',plot = make_chart(df),width = unit(8.8,'cm'),height=unit(10,'cm'))



#-- for sensitivity analysis alone
df<-read_excel("Z:\\Balaji\\Analysis_SyS_data\\09072021\\merged_All_09072020.xlsx",sheet = 'new')
df<-subset(df,model=='binary_june_remove_sensitivity' & !is.na(period) )
df$period<-mapvalues(df$period,from = c("floodPeriod", "monthAfterFlood", "novAndDec"),
                     to= c("Flood period", "Acute phase", "Protracted Phase"))
df$period<-factor(df$period,levels = c("Flood period", "Acute phase", "Protracted Phase"))
df['labels']<-''
df$modifier_cat<-df$outcome
df$model<-df$period
df$outcome<-'Sensitivity Analysis'
make_chart(df,nrow=1)
ggsave('sensitivity.pdf',plot = make_chart(df,nrow=1),height=unit(5.5,'cm'),width = unit(7.1,'cm'))

