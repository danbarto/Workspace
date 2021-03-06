import ROOT
import pickle
from array import array
import operator
from Workspace.HEPHYPythonTools.helpers import getChain, getPlotFromChain, getYieldFromChain
from Workspace.RA4Analysis.helpers import nameAndCut, nJetBinName, nBTagBinName, varBinName, varBin, UncertaintyDivision
#from Workspace.RA4Analysis.cmgTuples_Spring15_MiniAODv2_25ns_postProcessed import *
from Workspace.RA4Analysis.cmgTuples_Spring16_MiniAODv2_postProcessed import *
from Workspace.RA4Analysis.rCShelpers import *
from Workspace.RA4Analysis.signalRegions import *
from Workspace.HEPHYPythonTools.user import username
from cutFlow_helper import *
from Workspace.RA4Analysis.general_config import *


ROOT.TH1D().SetDefaultSumw2()


btagString = "nBJetMediumCSV30"
maxN = -1
lepSels = [
{'cut':'((!isData&&singleLeptonic)||(isData&&((eleDataSet&&singleElectronic)||(muonDataSet&&singleMuonic))))' , 'veto':'nLooseHardLeptons==1&&nTightHardLeptons==1&&nLooseSoftLeptons==0',\
 #'chain': getChain([single_ele_Run2015D,single_mu_Run2015D],maxN=maxN,histname="",treeName="Events") ,\
# 'trigWeight': "0.94" ,\
  'label':'_lep_', 'str':'1 $lep$' , 'trigger': '((HLT_EleHT350)||(HLT_MuHT350))'},\
]

lepSel = lepSels[0]
signalRegions = signalRegions2016
#lep_weight_Up_Err = "(lepton_eleSF_miniIso01_err*lepton_eleSF_cutbasedID_err*lepton_muSF_sip3d_err*lepton_muSF_miniIso02_err*lepton_muSF_mediumID_err)"
#lep_weight_Up = lepton_Scale+"+"+lep_weight_Up_Err
#### Here enter which sample do you wanna reweight and the variation
#tot_list = [TTJets_combined,DY_25ns,WJetsHTToLNu_25ns,singleTop_25ns,TTV_25ns]
tot_list = [TTV,singleTop_lep,DY_HT,WJetsHTToLNu,TTJets_Comb]
search_c = WJetsHTToLNu
#search_c = TTJets_combined
variation = 0.3
common_weight = '*'.join([reweight,topPt,trigger_scale,PU])

presel = "&&".join([lepSel['cut'],lepSel['veto'],"Jet_pt[1]>80"])
signalRegions = signalRegions2016

cTot = getChain(tot_list,histname='')
tot_list.remove(search_c)
cBkg = getChain(tot_list,histname='')
search_chain = getChain(search_c , histname='')
#weight_str =  '*'.join([trigger_scale,lepton_Scale,reweight,topPt,weight_0b])
weight_var = weight_str_plot 
weight_str = weight_var
print "base weight" , weight_var
nbtag = (0,0)
bin = {}
for srNJet in sorted(signalRegions):
  bin[srNJet]={} 
  for stb in sorted(signalRegions[srNJet]):
    bin[srNJet][stb]={}
    for htb in sorted(signalRegions[srNJet][stb]):
      bin[srNJet][stb][htb]={}
      deltaPhiCut = signalRegions[srNJet][stb][htb]['deltaPhi']
      cut_SR = "deltaPhi_Wl>"+str(deltaPhiCut)
      cut_CR = "deltaPhi_Wl<"+str(deltaPhiCut)
      name_bla, SB_cut    = nameAndCut(stb, htb, (3,4),  btb=nbtag, presel=presel, btagVar = btagString)
      name_bla, SB_cut_CR = nameAndCut(stb, htb, (3,4),  btb=nbtag, presel=presel+"&&"+cut_CR, btagVar = btagString)
      name_bla, SB_cut_SR = nameAndCut(stb, htb, (3,4),  btb=nbtag, presel=presel+"&&"+cut_SR, btagVar = btagString)
      name    , MB_cut    = nameAndCut(stb, htb, srNJet, btb=nbtag, presel=presel, btagVar = btagString)
      name_bla, MB_cut_CR = nameAndCut(stb, htb, srNJet, btb=nbtag, presel=presel+"&&"+cut_CR, btagVar = btagString)
      name_bla, MB_cut_SR = nameAndCut(stb, htb, srNJet, btb=nbtag, presel=presel+"&&"+cut_SR, btagVar = btagString)

      print name

      #calc nominal kappa
      rCS_tot_SB_nominal = max(0,getRCS(cTot, SB_cut ,  deltaPhiCut,weight = weight_str)['rCS']) 
      rCS_tot_MB_nominal = max(0,getRCS(cTot, MB_cut ,  deltaPhiCut,weight = weight_str)['rCS']) 
      bin[srNJet][stb][htb]['kappa_original'] = rCS_tot_MB_nominal/rCS_tot_SB_nominal
      print "kappa orig:" , bin[srNJet][stb][htb]['kappa_original']

      #calc ttv upi/down kappa
      yield_bkg_SB_SR        = getYieldFromChain(cBkg, SB_cut_SR, weight = weight_str) 
      yield_ttv_SB_SR_Up     = getYieldFromChain(search_chain, SB_cut_SR, weight =  "*".join(["(1)" , weight_var]))*(1+variation) 
      yield_ttv_SB_SR_Down   = getYieldFromChain(search_chain, SB_cut_SR, weight =  "*".join(["(1)" , weight_var]))*(1-variation) 
      yield_tot_SB_SR_Up     = yield_bkg_SB_SR + yield_ttv_SB_SR_Up 
      yield_tot_SB_SR_Down   = yield_bkg_SB_SR + yield_ttv_SB_SR_Down

      yield_bkg_SB_CR        = getYieldFromChain(cBkg, SB_cut_CR, weight = weight_str) 
      yield_ttv_SB_CR_Up     = getYieldFromChain(search_chain, SB_cut_CR, weight = "*".join(["(1)", weight_var]))*(1+variation) 
      yield_ttv_SB_CR_Down   = getYieldFromChain(search_chain, SB_cut_CR, weight = "*".join(["(1)", weight_var]))*(1-variation) 
      yield_tot_SB_CR_Up     = yield_bkg_SB_CR + yield_ttv_SB_CR_Up 
      yield_tot_SB_CR_Down   = yield_bkg_SB_CR + yield_ttv_SB_CR_Down 

      yield_bkg_MB_SR      = getYieldFromChain(cBkg, MB_cut_SR, weight = weight_str) 
      yield_ttv_MB_SR_Up   = getYieldFromChain(search_chain, MB_cut_SR, weight =  "*".join(["(1)" , weight_var]))*(1+variation) 
      yield_ttv_MB_SR_Down = getYieldFromChain(search_chain, MB_cut_SR, weight =  "*".join(["(1)" , weight_var]))*(1-variation) 
      yield_tot_MB_SR_Up   = yield_bkg_MB_SR + yield_ttv_MB_SR_Up 
      yield_tot_MB_SR_Down = yield_bkg_MB_SR + yield_ttv_MB_SR_Down

      yield_bkg_MB_CR      =  getYieldFromChain(cBkg, MB_cut_CR, weight = weight_str)    
      yield_ttv_MB_CR_Up   =  getYieldFromChain(search_chain, MB_cut_CR, weight = "*".join(["(1)", weight_var]))*(1+variation) 
      yield_ttv_MB_CR_Down =  getYieldFromChain(search_chain, MB_cut_CR, weight = "*".join(["(1)", weight_var]))*(1-variation) 
      yield_tot_MB_CR_Up   = yield_bkg_MB_CR + yield_ttv_MB_CR_Up 
      yield_tot_MB_CR_Down = yield_bkg_MB_CR + yield_ttv_MB_CR_Down

      rCS_tot_SB_Up  = max(0, yield_tot_SB_SR_Up  / yield_tot_SB_CR_Up)
      rCS_tot_MB_Up  = max(0, yield_tot_MB_SR_Up  / yield_tot_MB_CR_Up)

      rCS_tot_SB_Down= max(0,yield_tot_SB_SR_Down  / yield_tot_SB_CR_Down)
      rCS_tot_MB_Down= max(0,yield_tot_MB_SR_Down  / yield_tot_MB_CR_Down)

      print rCS_tot_SB_Up , rCS_tot_MB_Up , rCS_tot_SB_Down , rCS_tot_MB_Down

      bin[srNJet][stb][htb]['kappa_up'] = rCS_tot_MB_Up / rCS_tot_SB_Up 
      print "kappa up :" , bin[srNJet][stb][htb]['kappa_up']

      bin[srNJet][stb][htb]['kappa_down'] = rCS_tot_MB_Down / rCS_tot_SB_Down
      print "kappa down :" , bin[srNJet][stb][htb]['kappa_down']


      bin[srNJet][stb][htb]['delta_Up'] = ((bin[srNJet][stb][htb]['kappa_up']/bin[srNJet][stb][htb]['kappa_original'])-1) 
      print "delta up central:" , bin[srNJet][stb][htb]['delta_Up']

      bin[srNJet][stb][htb]['delta_Down'] = ((bin[srNJet][stb][htb]['kappa_down']/bin[srNJet][stb][htb]['kappa_original'])-1) 
      print "delta down_central:" , bin[srNJet][stb][htb]['delta_Down']

      bin[srNJet][stb][htb]['delta_avarage'] = (abs(bin[srNJet][stb][htb]['delta_Up'])+abs(bin[srNJet][stb][htb]['delta_Down']))/2 


pickle.dump(bin,file('/data/easilar/Results2016/ICHEP/DiLep_SYS/V1/'+search_c['name']+'_'+'_syst_SRAll_pkl','w'))
#pickle.dump(bin,file('/data/easilar/Spring15/25ns/all_lepSF_syst_SRAll_pkl','w'))

