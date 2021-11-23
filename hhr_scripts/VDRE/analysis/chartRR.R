#----------R code for plotting graph from the base model outputs created by the analysis.R code
reqRes<-allRes[allRes$term %in% paste0(exposures,'TRUE'),]
#graph confintervals
library(egg)
library(scales)
library(hablar)
library(openxlsx)

AXIS_Y_SIZE<-12
LEGEND_SIZE<-12
Y_TITLE_SIZE<-14
LINE_WIDTH<-.5 #erro bar line width
GRID_WIDTH<-.9
POINT_WIDTH<-0.7 #error bar middle point width
DASH_WIDTH<-.2
DOT_SIZE<-.5
ERROR_BAR_TOP<-.2
LABEL_SIZE<-13
WORD_WRAP<-15
PLOT_MARGIN<-unit(c(.1,.2,-.2,.2), "cm")
LEGEND_MAR<-margin(-0.7,0,.4,0,"cm")
STRIP_LINES=0.2
DODGE_WIDTH=0.7
AXIS_X_SIZE<-12

#read excel
allDf<-read.xlsx("K:\\Projects\\FY2020-018_HHR_Outcomes\\EoFloodHealth\\Output\\Draft\\baseModel.xlsx")


#get required rows
req_terms<-c("OtherHomesFloodedTRUE", "HomeFloodedTRUE", 
"fScanFloodedTRUE", 
#"fScanInunDisCatlte1100", "fScanInunDisCatlte400", "fScanInunDisCatFlooded", 
"fScanDepthCatlte1Dot5ft", "fScanDepthCatlte3ft", "fScanDepthCatgt3ft",
"fScanNdaysCat1Day", "fScanNdaysCat2_3Days", "fScanNdaysCat4_14Days"
)
reqRes<-subset(allDf,term %in% req_terms)
reqRes<-subset(reqRes,outcome %in% c("Illness", "Injury", "Concentrate", "Headaches", "RunnyNose", "ShortBreath", "SkinRash"))

#renames a few thing\
reqRes$term<-gsub('Cat','',reqRes$term)
reqRes$exposure<-gsub('Cat','',reqRes$exposure)
reqRes$term<-gsub('TRUE','',reqRes$term)
reqRes$term<-gsub('lte','<=',reqRes$term)
reqRes$term<-gsub('fScanInunDis','Distance ',reqRes$term)
reqRes$term<-gsub('fScanNdays','Flooded upto ',reqRes$term)
reqRes$term<-gsub('fScanDepth','Depth ',reqRes$term)
reqRes$term<-gsub('fScanFlooded','y',reqRes$term)
reqRes$term<-gsub('HomeFlooded','x',reqRes$term)
reqRes$term<-gsub('OtherHomesFlooded','z',reqRes$term)
reqRes$term<-gsub('gt','>',reqRes$term)
reqRes$term<-gsub('Dot','.',reqRes$term)
reqRes$term<-gsub('_','-',reqRes$term)


reqRes$exposure<-gsub('fScanInunDis','Distance',reqRes$exposure)
reqRes$exposure<-gsub('fScanNdays','Days',reqRes$exposure)
reqRes$exposure<-gsub('fScanDepth','Depth',reqRes$exposure)
reqRes$exposure<-gsub('OtherHomesFlooded','Other homes in\nblock flooded',reqRes$exposure)
reqRes$exposure<-gsub('fScanFlooded','Flood map\nbased flooding',reqRes$exposure)
reqRes$exposure<-gsub('HomeFlooded','Reported\nhome flooding',reqRes$exposure)

reqRes$outcome<-gsub('ShortBreath','Shortness of breath',reqRes$outcome)
reqRes$outcome<-gsub('Concentrate','Concentration problems',reqRes$outcome)



reqRes1<-subset(reqRes,!outcome %in% c("Headaches", "RunnyNose", "Shortness of breath"))
#draw plot
x<-ggplot(reqRes1, aes(y = estimate, x = exposure,color=factor(term))) + facet_wrap(~ outcome,nrow=1)+
  geom_errorbar(aes(ymax = conf.high, ymin = conf.low), size = LINE_WIDTH, width =
                  ERROR_BAR_TOP,position = position_dodge(width = DODGE_WIDTH)) +
  geom_point(size = POINT_WIDTH,position = position_dodge(width = DODGE_WIDTH)) +
  #scale_shape_manual(values=c(15,17,16,18,8,16,17,15,18,8,9))+
  scale_color_manual(values=c( "#009E73","#D55E00","#0072B2","#CC79A7","#E69F00","#999999","#000000","#E69F00","#009E73","#F0E442"))+
  geom_hline(aes(yintercept = 1), size = DASH_WIDTH, linetype = "dashed")+
  scale_y_log10(breaks = trans_breaks("log10", function(x) 10^x),
                labels = trans_format("log10", function(x) round(10^x,1)))+
  theme_bw() +   ylab("Rate ratio") + xlab("") +
  theme(panel.grid.minor = element_blank(),panel.grid.major.x = element_blank(),
        legend.title = element_blank(),
        panel.grid.major.y = element_line(size = GRID_WIDTH),
        legend.position ='none',#,legend.margin=LEGEND_MAR,
        legend.text=element_text(size=LEGEND_SIZE),
        axis.text.x= element_text(size = AXIS_X_SIZE,angle = 90, vjust = 0.5, hjust=1),
        plot.caption=element_text(size=AXIS_X_SIZE,hjust = 0.5, margin=margin(-2,10,10,10)),
        axis.ticks.length.x=unit(0, "cm"),
        axis.text.y = element_text(size = AXIS_Y_SIZE,angle = 90,hjust = 0.5),axis.title = element_text(size = Y_TITLE_SIZE),
        plot.margin = PLOT_MARGIN, strip.text = element_text(size=LABEL_SIZE),
        panel.spacing.x = unit(0,'cm'),panel.border = element_rect(size=STRIP_LINES,linetype = 'solid'),
        axis.line = element_line(linetype = 'solid',size=LINE_WIDTH),strip.background = element_rect(colour="black", fill="gray95",size = LINE_WIDTH),)

reqRes2<-subset(reqRes,(outcome %in% c("Headaches", "RunnyNose", "Shortness of breath")))
x1<-ggplot(reqRes2, aes(y = estimate, x = exposure,color=factor(term))) + facet_wrap(~ outcome,nrow=1)+
  geom_errorbar(aes(ymax = conf.high, ymin = conf.low), size = LINE_WIDTH, width =
                  ERROR_BAR_TOP,position = position_dodge(width = DODGE_WIDTH)) +
  geom_point(size = POINT_WIDTH,position = position_dodge(width = DODGE_WIDTH)) +
  #scale_shape_manual(values=c(15,17,16,18,8,16,17,15,18,8,9))+
  scale_color_manual(values=c( "#009E73","#D55E00","#0072B2","#CC79A7","#E69F00","#999999","#000000","#E69F00","#009E73","#F0E442"))+
  geom_hline(aes(yintercept = 1), size = DASH_WIDTH, linetype = "dashed")+
  scale_y_log10(breaks = trans_breaks("log10", function(x) 10^x),
                labels = trans_format("log10", function(x) round(10^x,1)))+
  theme_bw() +   ylab("Rate ratio") + xlab("") +
  theme(panel.grid.minor = element_blank(),panel.grid.major.x = element_blank(),
        legend.title = element_blank(),
        panel.grid.major.y = element_line(size = GRID_WIDTH),
        legend.position ='right',#,legend.margin=LEGEND_MAR,
        legend.text=element_text(size=LEGEND_SIZE),
        axis.text.x= element_text(size = AXIS_X_SIZE,angle = 90, vjust = 0.5, hjust=1),
        plot.caption=element_text(size=AXIS_X_SIZE,hjust = 0.5, margin=margin(-2,10,10,10)),
        axis.ticks.length.x=unit(0, "cm"),
        axis.text.y = element_text(size = AXIS_Y_SIZE,angle = 90,hjust = 0.5),axis.title = element_text(size = Y_TITLE_SIZE),
        plot.margin = PLOT_MARGIN, strip.text = element_text(size=LABEL_SIZE),
        panel.spacing.x = unit(0,'cm'),panel.border = element_rect(size=STRIP_LINES,linetype = 'solid'),
        axis.line = element_line(linetype = 'solid',size=LINE_WIDTH),strip.background = element_rect(colour="black", fill="gray95",size = LINE_WIDTH),)

ggarrange(x,x1,nrow = 2)
ggsave("confintGraph.pdf",width = unit(10,'cm'),height=unit(8,'cm'))
