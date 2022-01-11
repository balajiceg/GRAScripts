#example -- converting statewide TX SVIs to new values for just Harris County, TX
#@author - Lauren - modified by Balaij

recalcSVI<-function(HarrisCtyCent){
  HarrisCtyCent@data[HarrisCtyCent@data == -999] <- NA
  
  #following directions starting on page 16 of CDC SVI documentation
  #theme 1
  EPL_POV <- signif(dplyr::percent_rank(HarrisCtyCent@data$EP_POV),4)
  EPL_UNEMP <- signif(dplyr::percent_rank(HarrisCtyCent@data$EP_UNEMP),4)
  EPL_PCI <- (1-signif(dplyr::percent_rank(HarrisCtyCent@data$EP_PCI),4))
  EPL_NOHSDP <- signif(dplyr::percent_rank(HarrisCtyCent@data$EP_NOHSDP),4)
  SP_THEME1_HC <- EPL_POV + EPL_UNEMP + EPL_PCI + EPL_NOHSDP #HC = Harris County
  RPL_THEMES_1_HC <- signif(dplyr::percent_rank(SP_THEME1_HC),4)
  
  #theme 2
  EPL_AGE65 <- signif(dplyr::percent_rank(HarrisCtyCent@data$EP_AGE65),4)
  EPL_AGE17 <- signif(dplyr::percent_rank(HarrisCtyCent@data$EP_AGE17),4)
  EPL_DISABL <- signif(dplyr::percent_rank(HarrisCtyCent@data$EP_DISABL),4)
  EPL_SNGPNT <- signif(dplyr::percent_rank(HarrisCtyCent@data$EP_SNGPNT),4)
  SP_THEME2_HC <- EPL_AGE65 + EPL_AGE17 + EPL_DISABL + EPL_SNGPNT
  RPL_THEMES_2_HC <- signif(dplyr::percent_rank(SP_THEME2_HC),4)
  
  #theme 3
  EPL_MINRTY <- signif(dplyr::percent_rank(HarrisCtyCent@data$EP_MINRTY),4)
  EPL_LIMENG <- signif(dplyr::percent_rank(HarrisCtyCent@data$EP_LIMENG),4)
  SP_THEME3_HC <- EPL_MINRTY + EPL_LIMENG
  RPL_THEMES_3_HC <- signif(dplyr::percent_rank(SP_THEME3_HC),4)
  
  #theme 4
  EPL_MUNIT <- signif(dplyr::percent_rank(HarrisCtyCent@data$EP_MUNIT),4)
  EPL_MOBILE <- signif(dplyr::percent_rank(HarrisCtyCent@data$EP_MOBILE),4)
  EPL_CROWD <- signif(dplyr::percent_rank(HarrisCtyCent@data$EP_CROWD),4)
  EPL_NOVEH <- signif(dplyr::percent_rank(HarrisCtyCent@data$EP_NOVEH),4)
  EPL_GROUPQ <- signif(dplyr::percent_rank(HarrisCtyCent@data$EP_GROUPQ),4)
  SP_THEME4_HC <- EPL_MUNIT + EPL_MOBILE + EPL_CROWD + EPL_NOVEH + EPL_GROUPQ
  RPL_THEMES_4_HC <- 
  
  SPL_THEMES_HC <- SP_THEME1_HC+SP_THEME2_HC+SP_THEME3_HC+SP_THEME4_HC
  
  #adding newly calculated SVIs to HarrisCtyCent shapefile
  HarrisCtyCent@data$reRankSVI <- signif(dplyr::percent_rank(SPL_THEMES_HC),4)
  HarrisCtyCent@data$reRankSVI_T1 <- signif(dplyr::percent_rank(SP_THEME1_HC),4)
  HarrisCtyCent@data$reRankSVI_T2 <- signif(dplyr::percent_rank(SP_THEME2_HC),4)
  HarrisCtyCent@data$reRankSVI_T3 <- signif(dplyr::percent_rank(SP_THEME3_HC),4)
  HarrisCtyCent@data$reRankSVI_T4 <- signif(dplyr::percent_rank(SP_THEME4_HC),4)
  
  return(HarrisCtyCent@data)
}
