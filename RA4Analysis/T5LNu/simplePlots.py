import ROOT
from array import array
from math import *
import os, copy, sys

ROOT.TH1F().SetDefaultSumw2()

from Workspace.HEPHYCommonTools.helpers import getObjFromFile, passPUJetID, getISRweight, minDeltaRLeptonJets#, findClosestJet, invMass 

from Workspace.RA4Analysis.simplePlotsCommon import *
#from monoJetFuncs import *
#from monoJetEventShapeVars import circularity2D, foxWolframMoments, thrust

from Workspace.HEPHYCommonTools.xsec import xsec
small = False

targetLumi = 19700.

from defaultConvertedTuples import * 

wjetsSample = wJetsHT150v2 
allSamples = [dy, ttJetsPowHeg, wjetsSample, singleTop, vv, qcd]

allVars=[]
allStacks=[]

## plots for studying preselection 

minimum=10**(-0.5)

chmode = "copy"
presel = "refSel"
ver = "v5"
#region = "preSel"
region = "signal"
preprefix = region+"_"+ver
if region == "preSel":
  #isrjet>350, met>250, mT<70
  additionalCut = "(1)"
  addData = False
  addSignals = True
  normalizeToData = False
  normalizeSignalToMCSum = False
if region == "signal":
  #isrjet>350, met>250, mT<70
  additionalCut = "(ht>750&&met>350)"
  addData = False
  addSignals = True
  normalizeToData = False
  normalizeSignalToMCSum = False

subdir = "/pngT5LNu/"
doOnlyOne=True
doAnalysisVars            = True
doAllDiscriminatingVars   = True 
doOtherVars               = True 

chainstring = "Events"
commoncf = "(0)"
prefix="empty_"
if presel == "refSel":
  commoncf="njets>=4&&ht>400&&nTightMuons+nTightElectrons==1&&nbtags==0"

if additionalCut!="":
  commoncf+="&&"+additionalCut

prefix = "Test_"+preprefix+"_"+presel+"_"+chmode+"_"

def getT5LNu(mgl, mn, color = ROOT.kBlue):
  res = {} 
  res["dirname"] = ["/data/schoef/convertedTuples_v22/copy/"]
  res["bins"] = ["T5LNu_"+str(mgl)+"_"+str(mn)]
  res["hasWeight"] = True
  res["weight"] = "weight"
  res["color"] = color
  res["name"] = res["bins"][0]
  return res


signals=[getT5LNu(1000,100, ROOT.kBlue + 3), getT5LNu(1000, 600, ROOT.kRed + 3)]
if addSignals:
  allSamples += signals

for sample in allSamples:
  sample["Chain"] = chainstring
  sample["dirname"] = "/data/schoef/convertedTuples_v22/"+chmode+"/"
for sample in allSamples[1:]:
  sample["weight"] = "puWeight"

def getStack(varstring, binning, cutstring, signals, varfunc = "", addData=True, additionalCutFunc = ""):
  DATA          = variable(varstring, binning, cutstring,additionalCutFunc=additionalCutFunc)
  DATA.sample   = data
#  DATA.color    = ROOT.kGray
  DATA.color    = dataColor
  DATA.legendText="Data"

  MC_WJETS                     = variable(varstring, binning, cutstring, additionalCutFunc=additionalCutFunc) 
  MC_WJETS.sample              = wjetsSample
  MC_TTJETS                    = variable(varstring, binning, cutstring, additionalCutFunc=additionalCutFunc)
  MC_TTJETS.sample             = ttJetsPowHeg
  MC_STOP                      = variable(varstring, binning, cutstring, additionalCutFunc=additionalCutFunc) 
  MC_STOP.sample               = singleTop
  MC_Z                         = variable(varstring, binning, cutstring, additionalCutFunc=additionalCutFunc) 
  MC_Z.sample                  = dy
  MC_VV                        = variable(varstring, binning, cutstring, additionalCutFunc=additionalCutFunc) 
  MC_VV.sample                 = vv
  MC_QCD                       = variable(varstring, binning, cutstring, additionalCutFunc=additionalCutFunc)
  MC_QCD.sample                = qcd

  MC_WJETS.legendText          = "W + Jets"
  MC_WJETS.style               = "f0"
  MC_WJETS.add                 = [MC_TTJETS]
  MC_WJETS.color               = ROOT.kYellow
  MC_TTJETS.legendText         = "t#bar{t} + Jets"
  MC_TTJETS.style              = "f0"
  MC_TTJETS.color              = ROOT.kRed - 3
  MC_TTJETS.add                =  [MC_STOP]
  MC_STOP.legendText           = "single Top"
  MC_STOP.style                = "f0"
  MC_STOP.add                  = [MC_Z]
  MC_STOP.color                = ROOT.kOrange + 4
  MC_Z.legendText             = "DY + Jets"
  MC_Z.style                  = "f0"
  MC_Z.add                    = [MC_VV]
  MC_Z.color                  = ROOT.kGreen + 3
  MC_VV.legendText          = "VV (WZ,WW,ZZ)"
  MC_VV.style               = "f0"
  MC_VV.add                 = [MC_QCD]
  MC_VV.color               = ROOT.kViolet + 8

  MC_QCD.color                 = myBlue
  MC_QCD.legendText            = "QCD"
  MC_QCD.style                 = "f0"
  MC_QCD.add                   = []

  res = [MC_WJETS, MC_TTJETS, MC_STOP, MC_Z, MC_VV, MC_QCD]
  for v in res:
#    v.reweightVar = "ngoodVertices"
#    v.reweightHisto = simplePUreweightHisto 
    v.legendCoordinates=[0.61,0.95 - 0.08*5,.98,.95]
  for signal in signals:
    MC_SIGNAL                    = variable(varstring, binning, cutstring,additionalCutFunc=additionalCutFunc)
    MC_SIGNAL.sample             = copy.deepcopy(signal)
    MC_SIGNAL.legendText         = signal["name"]
    MC_SIGNAL.style              = "l02"
    MC_SIGNAL.color              = signal['color'] 
    MC_SIGNAL.add = []
    MC_SIGNAL.reweightVar = lambda c:getISRweight(c, mode='Central')
    res.append(MC_SIGNAL)
    if normalizeSignalToMCSum:
      MC_SIGNAL.normalizeTo = res[0]
 
  getLinesForStack(res, targetLumi)
  nhistos = len(res)
  if addData:
    res.append(DATA)
    res[0].dataMCRatio = [DATA, res[0]]
#  else:
#    res[0].dataMCRatio = [MC_SIGNAL, res[0]]
#    res[0].ratioVarName = "SUS/SM" 
  if varfunc!="":
    for var in res:
      var.varfunc = varfunc
  return res

def cosDeltaPhiLepW(chain):
  lPt = getValue(chain, "leptonPt")
  lPhi = getValue(chain, "leptonPhi")
  metphi = getValue(chain, "type1phiMetphi")
  met = getValue(chain, "type1phiMet")
  cosLepPhi = cos(lPhi)
  sinLepPhi = sin(lPhi)
  mpx = met*cos(metphi)
  mpy = met*sin(metphi)
  pW = sqrt((lPt*cosLepPhi + mpx)**2 + (lPt*sinLepPhi + mpy)**2)

  return ((lPt*cosLepPhi + mpx)*cosLepPhi + (lPt*sinLepPhi + mpy)*sinLepPhi )/pW


if doAnalysisVars:
  htThrustLepSideRatio_stack = getStack(":htThrustLepSideRatio;htThrustLepSideRatio;Number of Events",[25,0,1], commoncf, signals, addData = addData)
  htThrustLepSideRatio_stack[0].addOverFlowBin = "upper"
  allStacks.append(htThrustLepSideRatio_stack)

  htThrustMetSideRatio_stack = getStack(":htThrustMetSideRatio;htThrustMetSideRatio;Number of Events",[25,0,1], commoncf, signals, addData = addData)
  htThrustMetSideRatio_stack[0].addOverFlowBin = "upper"
  allStacks.append(htThrustMetSideRatio_stack)

  htThrustWSideRatio_stack = getStack(":htThrustWSideRatio;htThrustWSideRatio;Number of Events",[25,0,1], commoncf, signals, addData = addData)
  htThrustWSideRatio_stack[0].addOverFlowBin = "upper"
  allStacks.append(htThrustWSideRatio_stack)

  mT_stack  = getStack(":mT;m_{T} (GeV);Number of Events / 10 GeV",[21,0,210], commoncf, signals, addData = addData)
  mT_stack[0].addOverFlowBin = "upper"
  allStacks.append(mT_stack)

  met_stack = getStack(":type1phiMet;#slash{E}_{T} (GeV);Number of Events / 50 GeV",[18,150,1050], commoncf, signals, addData = addData)
  met_stack[0].addOverFlowBin = "upper"
  allStacks.append(met_stack)

  njets_stack = getStack(":njets;n_{jet};Number of Events",[10,0,10], commoncf, signals, addData = addData)
  njets_stack[0].addOverFlowBin = "upper"
  allStacks.append(njets_stack)

  nbtags_stack = getStack(":nbtags;n_{b-tags};Number of Events",[10,0,10], commoncf, signals, addData = addData)
  nbtags_stack[0].addOverFlowBin = "upper"
  allStacks.append(nbtags_stack)

  ht_stack                          = getStack(":ht;H_{T} (GeV);Number of Events / 50 GeV",[31,0,1550 ], commoncf, signals, addData = addData)
  ht_stack[0].addOverFlowBin = "upper"
  allStacks.append(ht_stack)


if doAllDiscriminatingVars:


#  cosPhiMetJet_stack = getStack(":xxx;cos(#phi(#slash{E}_{T}, ISR-jet));Number of Events",[20,-1,1], commoncf, signals, addData = addData, varfunc = lambda c: cos(getVarValue(c, 'isrJetPhi') - getVarValue(c, 'leptonPhi')))
#  cosPhiMetJet_stack[0].addOverFlowBin = "both"
#  allStacks.append(cosPhiMetJet_stack)

  FWMT1_stack = getStack(":FWMT1;FMWT1 (jets,lep,MET);Number of Events",[20,0,1], commoncf, signals, addData = addData)
  FWMT1_stack[0].addOverFlowBin = "upper"
  allStacks.append(FWMT1_stack)

  FWMT2_stack = getStack(":FWMT2;FMWT2 (jets,lep,MET);Number of Events",[20,0,1], commoncf, signals, addData = addData)
  FWMT2_stack[0].addOverFlowBin = "upper"
  allStacks.append(FWMT2_stack)

  FWMT3_stack = getStack(":FWMT3;FMWT3 (jets,lep,MET);Number of Events",[20,0,1], commoncf, signals, addData = addData)
  FWMT3_stack[0].addOverFlowBin = "upper"
  allStacks.append(FWMT3_stack)

  FWMT4_stack = getStack(":FWMT4;FMWT4 (jets,lep,MET);Number of Events",[20,0,1], commoncf, signals, addData = addData)
  FWMT4_stack[0].addOverFlowBin = "upper"
  allStacks.append(FWMT4_stack)


  c2D_stack = getStack(":C2D;C2D (jets,lep,MET);Number of Events",[20,0,1], commoncf, signals, addData = addData)
  c2D_stack[0].addOverFlowBin = "upper"
  allStacks.append(c2D_stack)

  linC2D_stack = getStack(":linC2D;linC2D (jets,lep,MET);Number of Events",[20,0,1], commoncf, signals, addData = addData)
  linC2D_stack[0].addOverFlowBin = "upper"
  allStacks.append(linC2D_stack)

  thrust_stack = getStack(":thrust;thrust;Number of Events",[20,0.6,1], commoncf, signals, addData = addData)
  thrust_stack[0].addOverFlowBin = "upper"
  allStacks.append(thrust_stack)

#  sTlep_stack  = getStack(":XXX;S_{T, lep.} (GeV);Number of Events / 50 GeV",[21,0,1050], commoncf, signals, lambda c: c.GetLeaf('leptonPt').GetValue() + c.GetLeaf('type1phiMet').GetValue() , addData = addData)
#  sTlep_stack[0].addOverFlowBin = "upper"
#  allStacks.append(sTlep_stack)

  cosDeltaPhiLepMET_stack  = getStack(":xxx;cos(#Delta #phi(l, #slash{E}_{T}));Number of Events",[22,-1.1,1.1], commoncf, signals, lambda c: cos(c.GetLeaf('leptonPhi').GetValue() - c.GetLeaf('type1phiMetphi').GetValue()), addData = addData)
  allStacks.append(cosDeltaPhiLepMET_stack)

  cosDeltaPhiLepW_stack  = getStack(":xxx;cos(#Delta #phi(l, #slash{E}_{T}));Number of Events",[22,-1.1,1.1], commoncf, signals, cosDeltaPhiLepW, addData = addData)
  allStacks.append(cosDeltaPhiLepW_stack)


for stack in allStacks:
  stack[0].minimum = minimum
  
execfile("../../RA4Analysis/plots/simplePlotsLoopKernel.py")

if normalizeToData:
  for stack in allStacks:
    for var in stack[:-1]:
      var.normalizeTo = stack[-1]
      var.normalizeWhat = stack[0]
    stack[-1].normalizeTo=""
    stack[-1].normalizeWhat=""
#else:
#  for stack in allStacks:
#    for var in stack:
#      var.normalizeTo = ""
#      var.normalizeWhat = "" 
#
for stack in allStacks:
  if addData:
    stack[0].maximum = 6*10**2 *stack[-1].data_histo.GetMaximum()
  else:
    stack[0].maximum = 6*10**2 *stack[0].data_histo.GetMaximum()
  stack[0].logy = True
  stack[0].minimum = minimum
#  stack[0].legendCoordinates=[0.76,0.95 - 0.3,.98,.95]
#  stack[0].lines = [[0.2, 0.9, "#font[22]{CMS preliminary}"], [0.2,0.85,str(int(round(targetLumi)))+" pb^{-1},  #sqrt{s} = 7 TeV"]]
  stack[0].lines = [[0.2, 0.9, "#font[22]{CMS Collaboration}"], [0.2,0.85,str(int(round(targetLumi/10.))/100.)+" fb^{-1},  #sqrt{s} = 8 TeV"]]

if doAnalysisVars:
  htThrustMetSideRatio_stack[0].maximum = 6*10**5 *htThrustMetSideRatio_stack[0].data_histo.GetMaximum()
  drawNMStacks(1,1,[htThrustMetSideRatio_stack],             subdir+prefix+"htThrustMetSideRatio", False)
  htThrustLepSideRatio_stack[0].maximum = 6*10**5 *htThrustLepSideRatio_stack[0].data_histo.GetMaximum()
  drawNMStacks(1,1,[htThrustLepSideRatio_stack],             subdir+prefix+"htThrustLepSideRatio", False)
  htThrustWSideRatio_stack[0].maximum = 6*10**5 *htThrustWSideRatio_stack[0].data_histo.GetMaximum()
  drawNMStacks(1,1,[htThrustWSideRatio_stack],             subdir+prefix+"htThrustWSideRatio", False)
  drawNMStacks(1,1,[mT_stack],              subdir+prefix+"mT", False)
  drawNMStacks(1,1,[met_stack],             subdir+prefix+"met", False)
  drawNMStacks(1,1,[njets_stack],             subdir+prefix+"njets", False)
  drawNMStacks(1,1,[nbtags_stack],             subdir+prefix+"nbtags", False)
  drawNMStacks(1,1,[ht_stack],              subdir+prefix+"ht", False)
if doAllDiscriminatingVars:
#  drawNMStacks(1,1,[closestMuJetMass_stack] ,             subdir+prefix+"closestMuJetMass_stack", False)
#  drawNMStacks(1,1,[closestMuJetDeltaR_stack] ,        subdir+prefix+"closestMuJetDeltaR_stack", False)
#  drawNMStacks(1,1,[closestMuJetDeltaR_zoomed_stack] ,        subdir+prefix+"closestMuJetDeltaR_zoomed_stack", False)
  FWMT2_stack[0].maximum = 6*10**4 *FWMT2_stack[0].data_histo.GetMaximum()
  FWMT3_stack[0].maximum = 6*10**3 *FWMT3_stack[0].data_histo.GetMaximum()
  FWMT4_stack[0].maximum = 6*10**4 *FWMT4_stack[0].data_histo.GetMaximum()
#  cosPhiMetJet_stack[0].maximum = 6*10**3 *cosPhiMetJet_stack[0].data_histo.GetMaximum()
#  thrust_stack[0].maximum = 6*10**4 *thrust_stack[0].data_histo.GetMaximum()
#  drawNMStacks(1,1,[cosPhiMetJet_stack], subdir+prefix+"cosPhiMetJet", False)
  drawNMStacks(1,1,[FWMT1_stack],             subdir+prefix+"FWMT1", False)
  drawNMStacks(1,1,[FWMT2_stack],             subdir+prefix+"FWMT2", False)
  drawNMStacks(1,1,[FWMT3_stack],             subdir+prefix+"FWMT3", False)
  drawNMStacks(1,1,[FWMT4_stack],             subdir+prefix+"FWMT4", False)
  drawNMStacks(1,1,[c2D_stack],             subdir+prefix+"c2D", False)
  drawNMStacks(1,1,[linC2D_stack],             subdir+prefix+"linC2D", False)
  drawNMStacks(1,1,[thrust_stack],             subdir+prefix+"thrust", False)
  drawNMStacks(1,1,[sTlep_stack],             subdir+prefix+"sTlep", False)
  drawNMStacks(1,1,[cosDeltaPhiLepW_stack],             subdir+prefix+"cosDeltaPhiLepW", False)
  drawNMStacks(1,1,[cosDeltaPhiLepMET_stack],             subdir+prefix+"cosDeltaPhiLepMET", False)