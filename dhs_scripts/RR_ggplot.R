#install.packages('tidyverse')
#install.packages('readxl')
library(ggplot2)
library(readxl)
library(hablar)
library(dplyr)
library(stringr)

all_df<-read_excel("merged_flood_cat.xlsx",sheet='results_rr',range="A1:J15")
colnames(all_df)<-c('Outcome',rep(c('RR','conf25','conf95'),3))
flood_df<-all_df[-1,1:4]
flood_df<-rbind(flood_df,all_df[-1,c(1,5,6,7)])
flood_df<-rbind(flood_df,all_df[-1,c(1,8,9,10)])
flood_df$Period<-rep(c('Flood Period','Post Flood 1','Post Flood 2'),each=length(unique(flood_df$Outcome)))

outcomes<-c("CO Poisoning","Drowning","Hypothermia","Dehydration","Heat Related Illness","Intestinal infectious diseases","Insect Bite")
#outcomes<-c("All","Mortality","Pregnancy Complications")
outcomes<-c("ARI","Chest Pain/Palpitation","Asthma")

flood_df<-flood_df %>% retype()
flood_df<-flood_df[order(flood_df$Outcome),]
flood_df<-subset(flood_df,Outcome %in% outcomes)
flood_df$xindex<-1:length(flood_df$Outcome)

(p <- ggplot(flood_df, aes(y = RR, x = xindex ,color=factor(Period))) + 
    geom_errorbar(aes(ymax = conf25, ymin = conf95), size = .5, width = 
                     .2, color = "gray40") +
    geom_point(size = 6,shape="_") +
    geom_hline(aes(yintercept = 1), size = .25, linetype = "dashed")+
    geom_vline(data=flood_df[seq(3,length(flood_df$xindex)-1,3),],aes(xintercept=xindex+.5),color='gray60',size=.5,linetype = "dotted")+
    scale_x_continuous(breaks=flood_df$xindex[seq(2,length(flood_df$xindex),3)],
                       labels=flood_df$Outcome[seq(2,length(flood_df$Outcome),3)])+
    scale_y_log10()+
    theme_bw()+
    theme(panel.grid.minor = element_blank(),panel.grid.major.x = element_blank(),axis.ticks.length.x=unit(-0.1, "cm"),
          axis.text.x = element_text(vjust = 7),legend.title = element_blank(),
          legend.justification = c("right", "top"),legend.position = c(.99, .99),legend.text = element_text(size = 10),
          axis.text = element_text(size = 11),axis.title = element_text(size = 13),) +
    ylab("Rate ratio") +
    xlab("") 
  
) 
ggsave('RRPlot3.png',plot=p,width = unit(12,'cm'))

#---------------------------------For stratified SVI-------------------
#flood_period
#all_df<-read_excel("merged_all.xlsx",sheet='Results_formated',range="A16:M20")
#post flood 1
all_df<-read_excel("Docum_for_paper.xlsx",sheet='dicho_comparision_RR',range="A16:J30")
#post flood 2
#all_df<-read_excel("merged_all.xlsx",sheet='Results_formated',range="A36:J50")

colnames(all_df)<-c('Outcome',rep(c('RR','conf25','conf95'),7))
flood_df<-all_df[-1,1:4]
flood_df<-rbind(flood_df,all_df[-1,c(1,5,6,7)])
flood_df<-rbind(flood_df,all_df[-1,c(1,8,9,10)])
flood_df<-rbind(flood_df,all_df[-1,c(1,11,12,13)])
flood_df<-rbind(flood_df,all_df[-1,c(1,14,15,16)])
flood_df<-rbind(flood_df,all_df[-1,c(1,17,18,19)])
flood_df<-rbind(flood_df,all_df[-1,c(1,20,21,22)])
#flood_df$Period<-rep(c('0.2%','1.1%','2.7%','5.1%','8.1%','12.1%','19.3%'),each=length(unique(flood_df$Outcome)))
flood_df$Period<-rep(c('Flood Period','Post Flood 1', 'Post Flood 2'),each=length(unique(flood_df$Outcome)))
#flood_df$Period<-rep(c('Low flood','Moderate flood', 'High flood'),each=length(unique(flood_df$Outcome)))


n=length(unique(flood_df$Period))
loutcomes<-list()
# loutcomes[[1]]<-c("Bite-Insect","CO_Exposure","Dehydration","Drowning","Heat_Related_But_Not_dehydration","Hypothermia")
# loutcomes[[2]]<-c("ALL","DEATH","Pregnancy_complic","Medication_Refill","Dialysis")
# loutcomes[[3]]<-c("Intestinal_infectious_diseases","ARI","Chest_pain","Asthma")
loutcomes[[1]]<-c("CO Poisoning","Drowning","Hypothermia","Dehydration","Heat Related Illness","Intestinal infectious diseases","Insect Bite")
loutcomes[[2]]<-c("All","Mortality","Pregnancy Complications")
loutcomes[[3]]<-c("ARI","Chest Pain/Palpitation","Asthma")

flood_df<-flood_df %>% retype()
flood_df<-flood_df[order(flood_df$Outcome),]
i<-2


for(outcomes in loutcomes){
  
outcomes<-loutcomes[[i]]
flood_df_sub<-subset(flood_df,Outcome %in% outcomes)
flood_df_sub$xindex<-1:length(flood_df_sub$Outcome)
#flood_df_sub$Outcome = str_wrap(flood_df_sub$Outcome,width = 20)

(p <- ggplot(flood_df_sub, aes(y = RR, x = xindex ,color=factor(Period))) + 
    geom_errorbar(aes(ymax = conf25, ymin = conf95), size = .5, width = 
                    .2, color = "gray40") +
    geom_point(size = 6,shape="_") +
    geom_hline(aes(yintercept = 1), size = .25, linetype = "dashed")+
    geom_vline(data=flood_df_sub[seq(n,length(flood_df_sub$xindex)-1,n),],aes(xintercept=xindex+.5),color='gray50',size=.4,linetype = "dotted")+
    scale_x_continuous(breaks=flood_df_sub$xindex[seq(2,length(flood_df_sub$xindex),n)],
                       labels=flood_df_sub$Outcome[seq(2,length(flood_df_sub$Outcome),n)])+
                       
    scale_y_log10()+
    theme_bw()+
    theme(panel.grid.minor = element_blank(),panel.grid.major.x = element_blank(),axis.ticks.length.x=unit(-0.2, "cm"),
          axis.text.x = element_text(vjust = 6.5,size=15),legend.title = element_blank(),
          legend.justification = c("left", "top"),legend.position = c(0.01, .99),legend.text = element_text(size = 13),
          axis.text.y = element_text(size = 12,angle = 90),axis.title = element_text(size = 16),) +
    ylab("Rate ratio") +
    xlab("") #+  scale_color_discrete(breaks=mlevels)
)
#ggsave(paste0('plot_binalry_rr',i,'.png'),plot=p,width = unit(15.8,'cm'),height=unit(7,'cm'))
ggsave(paste0('plot_binalry_rr1',i,'.png'),plot=p,width = unit(8.1,'cm'),height=unit(6,'cm'))

i<-i+1
}
