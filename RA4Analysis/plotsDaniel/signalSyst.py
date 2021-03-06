import ROOT
import os, sys, copy
import pickle, operator

from math import *
from array import array
from Workspace.HEPHYPythonTools.helpers import *
from Workspace.RA4Analysis.helpers import *
from Workspace.RA4Analysis.signalRegions import *
from Workspace.RA4Analysis.cmgTuples_Spring15_MiniAODv2_25ns_postProcessed import *
from Workspace.RA4Analysis.cmgTuples_Spring15_MiniAODv2_25ns_postProcessed_2 import *

signalRegions = signalRegion3fb

triggers = "(HLT_EleHT350||HLT_MuHT350)"
filters = "(1)"
presel = "((!isData&&singleLeptonic)||(isData&&"+triggers+"&&((muonDataSet&&singleMuonic)||(eleDataSet&&singleElectronic))&&"+filters+"))"
presel += "&&nLooseHardLeptons==1&&nTightHardLeptons==1&&nLooseSoftLeptons==0&&Jet_pt[1]>80&&st>250&&nJet30>2&&htJet30j>500"

WSB   = (3,4)
TTSB  = (4,5)

lumi = 2.25

weight = 'weight*'+str(lumi)+'/3.'

weight_Central_0b     = weight+'*weightBTag0_SF*reweightLeptonFastSimSF'
weight_Central_1b     = weight+'*weightBTag1_SF*reweightLeptonFastSimSF'

weight_bUp_0b         = weight+'*weightBTag0_SF_b_Up*reweightLeptonFastSimSF'
weight_bDown_0b       = weight+'*weightBTag0_SF_b_Down*reweightLeptonFastSimSF'
weight_lightUp_0b     = weight+'*weightBTag0_SF_light_Up*reweightLeptonFastSimSF'
weight_lightDown_0b   = weight+'*weightBTag0_SF_light_Down*reweightLeptonFastSimSF'

weight_leptonUp_0b    = weight+'*weightBTag0_SF*reweightLeptonFastSimSFUp'
weight_leptonDown_0b  = weight+'*weightBTag0_SF*reweightLeptonFastSimSFDown'

weights = [weight_bUp_0b,weight_bDown_0b,weight_lightUp_0b,weight_lightDown_0b,weight_leptonUp_0b,weight_leptonDown_0b]
names = ['bUp', 'bDown', 'lightUp','lightDown','leptonUp','leptonDown']

savePickle = True

signalFile = '/data/dspitzbart/Results2016/signal_unc_pkl'
signalFile2 = signalFile + '_update'

try:
  unc = pickle.load(file(signalFile))
  print 'Loaded file from', signalFile
  if savePickle: print 'Will update it and save new one here:',signalFile2
except IOError:
  print 'Unable to load signal file!'
  if savePickle: print 'Creating new one here:',signalFile
  unc = {}

# update this
#allSignals = [T5qqqqVV_mGluino_800To975_mLSP_1To850, T5qqqqVV_mGluino_1000To1075_mLSP_1To950, T5qqqqVV_mGluino_1100To1175_mLSP_1to1050]


for srNJet in sorted(signalRegions):
  unc[srNJet] = {}
  for stb in sorted(signalRegions[srNJet]):
    unc[srNJet][stb] = {}
    for htb in sorted(signalRegions[srNJet][stb]):
      unc[srNJet][stb][htb] = {}
      dPhi = signalRegions[srNJet][stb][htb]['deltaPhi']
      
      print
      print '#################################################'
      print '## Uncertainties for SR',str(srNJet),str(stb),str(htb)
      print '## Using a dPhi cut value of',str(dPhi)
      print '#################################################'
      print
      
      nameMB, cutMB     = nameAndCut(stb, htb, srNJet, btb=None, presel = presel)
      nameWSB, cutWSB   = nameAndCut(stb, htb, WSB, btb=None, presel = presel)
      nameTTSB, cutTTSB = nameAndCut(stb, htb, TTSB, btb=None, presel = presel)

      #loop over signal points
      for signal in allSignals:
        for mGl in signal:
          unc[srNJet][stb][htb][mGl] = {}
          print
          print 'Gluino mass', mGl
          for mLSP in signal[mGl]:
            unc[srNJet][stb][htb][mGl][mLSP] = {}
            
            print 'LSP mass', mLSP
            
            c = getChain(signal[mGl][mLSP], histname='')
            
            # get central yields
            unc[srNJet][stb][htb][mGl][mLSP]['yield_MB_CR'], unc[srNJet][stb][htb][mGl][mLSP]['err_MB_CR'] = getYieldFromChain(c, cutString = cutMB+'&&deltaPhi_Wl<'+str(dPhi), weight = weight_Central_0b, returnError =True)
            unc[srNJet][stb][htb][mGl][mLSP]['yield_MB_SR'], unc[srNJet][stb][htb][mGl][mLSP]['err_MB_SR'] = getYieldFromChain(c, cutString = cutMB+'&&deltaPhi_Wl>='+str(dPhi), weight = weight_Central_0b, returnError =True)
            unc[srNJet][stb][htb][mGl][mLSP]['yield_SB_W_CR'], unc[srNJet][stb][htb][mGl][mLSP]['err_SB_W_CR'] = getYieldFromChain(c, cutString = cutWSB+'&&deltaPhi_Wl<'+str(dPhi), weight = weight_Central_0b, returnError =True)
            unc[srNJet][stb][htb][mGl][mLSP]['yield_SB_W_SR'], unc[srNJet][stb][htb][mGl][mLSP]['err_SB_W_SR'] = getYieldFromChain(c, cutString = cutWSB+'&&deltaPhi_Wl>='+str(dPhi), weight = weight_Central_0b, returnError =True)
            unc[srNJet][stb][htb][mGl][mLSP]['yield_SB_tt_CR'], unc[srNJet][stb][htb][mGl][mLSP]['err_SB_tt_CR'] = getYieldFromChain(c, cutString = cutTTSB+'&&deltaPhi_Wl<'+str(dPhi), weight = weight_Central_1b, returnError =True)
            unc[srNJet][stb][htb][mGl][mLSP]['yield_SB_tt_SR'], unc[srNJet][stb][htb][mGl][mLSP]['err_SB_tt_SR'] = getYieldFromChain(c, cutString = cutTTSB+'&&deltaPhi_Wl>='+str(dPhi), weight = weight_Central_1b, returnError =True)
            
            val_highDPhi = {}
            unc_highDPhi = {}
            for iw, w in enumerate(weights):
              val_highDPhi[names[iw]] = getYieldFromChain(c, cutString = cutMB+'&&deltaPhi_Wl>='+str(dPhi), weight = w)
            
            # calculate deltas
            for i in range(0,len(weights)):
              if unc[srNJet][stb][htb][mGl][mLSP]['yield_MB_SR']>0:
                unc_highDPhi[names[i]+'_MB_SR'] = (unc[srNJet][stb][htb][mGl][mLSP]['yield_MB_SR'] - val_highDPhi[names[i]]) / unc[srNJet][stb][htb][mGl][mLSP]['yield_MB_SR']
              else:
                unc_highDPhi[names[i]+'_MB_SR'] = val_highDPhi[names[i]]
                print 'Central value was zero!!'
                print val_highDPhi[names[i]]
              
              #print 'Var '+names[i]+':', unc_highDPhi
              #unc[srNJet][stb][htb][mGl][mLSP][names[i]+'_MB_SR'] = unc_highDPhi
            
            #unc[srNJet][stb][htb][mGl][mLSP]['sys_b_MB_SR']       = (abs(unc_highDPhi['bUp_MB_SR'])       + abs(unc_highDPhi['bDown_MB_SR']))/2 #asymmetric - take max?
            #unc[srNJet][stb][htb][mGl][mLSP]['sys_light_MB_SR']   = (abs(unc_highDPhi['lightUp_MB_SR'])   + abs(unc_highDPhi['lightDown_MB_SR']))/2 #asymmetric - take max?
            unc[srNJet][stb][htb][mGl][mLSP]['sys_b_MB_SR']       = max([abs(unc_highDPhi['bUp_MB_SR']), abs(unc_highDPhi['bDown_MB_SR'])]) #asymmetric - take max?
            unc[srNJet][stb][htb][mGl][mLSP]['sys_light_MB_SR']   = max([abs(unc_highDPhi['lightUp_MB_SR']), abs(unc_highDPhi['lightDown_MB_SR'])]) #asymmetric - take max?
            unc[srNJet][stb][htb][mGl][mLSP]['sys_lepton_MB_SR']  = (abs(unc_highDPhi['leptonUp_MB_SR'])  + abs(unc_highDPhi['leptonDown_MB_SR']))/2 #symmetric, so take average
            del c


if savePickle:
  pickle.dump(unc, file(signalFile,'w'))


