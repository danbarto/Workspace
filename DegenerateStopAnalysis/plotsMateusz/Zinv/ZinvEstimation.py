# ZinvEstimation.py
import ROOT
import os, sys
import argparse
import Workspace.DegenerateStopAnalysis.toolsMateusz.ROOToptions
from Workspace.DegenerateStopAnalysis.toolsMateusz.drawFunctions import *
from Workspace.DegenerateStopAnalysis.toolsMateusz.pythonFunctions import *
from Workspace.DegenerateStopAnalysis.tools.degTools import CutClass, Plots, getPlots, drawPlots, Yields, setup_style
from Workspace.DegenerateStopAnalysis.tools.getSamples_8011 import getSamples
from Workspace.DegenerateStopAnalysis.samples.cmgTuples_postProcessed.cmgTuplesPostProcessed_mAODv2_2016 import cmgTuplesPostProcessed

from array import array
from math import pi, sqrt #cos, sin, sinh, log

#Sets TDR style
setup_style()

#Input options
parser = argparse.ArgumentParser(description = "Input options")
parser.add_argument("--SR", dest = "SR",  help = "SR", type = str, default = "SR1") # 'SR1', 'SR1a', 'SR1b', 'SR1c', 'SRL1', 'SRH1', 'SRV1', 'SRL1a', 'SRH1a', 'SRV1a', 'SRL1b', 'SRH1b', 'SRV1b', 'SRL1c', 'SRH1c', 'SRV1c'
parser.add_argument("--CT2", dest = "CT2",  help = "CT2 Cut", type = str, default = "75")
#parser.add_argument("--MET", dest = "MET",  help = "MET Cut", type = str, default = "200")
#parser.add_argument("--HT", dest = "HT",  help = "HT Cut", type = str, default = "200")
parser.add_argument("--Zpeak", dest = "Zpeak",  help = "Zpeak plot", type = int, default = 0)
parser.add_argument("--emulated", dest = "emulated",  help = "Emulated plot", type = int, default = 1)
parser.add_argument("--peak", dest = "peak",  help = "Z-peak selection", type = int, default = 0)
parser.add_argument("--leptons", dest = "leptons",  help = "Extra lepton distributions", type = int, default = 0)
parser.add_argument("--doYields", dest = "doYields",  help = "Calulate yields", type = int, default = 1)
parser.add_argument("--getData", dest = "getData",  help = "Get data samples", type = int, default = 1)
parser.add_argument("--plot", dest = "plot",  help = "Toggle plot", type = int, default = 0)
parser.add_argument("--logy", dest = "logy",  help = "Toggle logy", type = int, default = 1)
parser.add_argument("--save", dest = "save",  help = "Toggle save", type = int, default = 1)
parser.add_argument("-b", dest = "batch",  help = "Batch mode", action = "store_true", default = False)
args = parser.parse_args()
if not len(sys.argv) > 1:
   print makeLine()
   print "No arguments given. Using default settings."
   print makeLine()
   #exit()

#Arguments
SR = args.SR
CT2cut = args.CT2
Zpeak = args.Zpeak
emulated = args.emulated
peak = args.peak
leptons = args.leptons
#METcut = args.MET
#HTcut = args.HT
doYields = args.doYields
getData = args.getData
plot = args.plot
logy = args.logy
save = args.save

print makeDoubleLine()
print "Performing Zinv estimation."
print makeDoubleLine()

#Samples
cmgPP = cmgTuplesPostProcessed()#mc_path, signal_path, data_path)
samplesList = ["tt", "dy"] #"qcd", "w", "z", 
if getData: samplesList.append("d1muBlind")

samples = getSamples(cmgPP = cmgPP, skim = 'oneLep', sampleList = samplesList, scan = False, useHT = True, getData = getData) 
selectedSamples = samplesList #["qcd", "z", "tt", "w"]

print makeLine()
print "Using samples:"
newLine()
for s in selectedSamples:
   if s: print samples[s].name,":",s
   else: 
      print "!!! Sample " + sample + " unavailable."
      sys.exit(0)

collection = "LepAll" 
print makeLine()
print "Using " + collection + " collection."
print makeLine()

#Geometric cuts
#etaAcc = 2.1
#ebSplit = 0.8 #barrel is split into two regions
#ebeeSplit = 1.479 #division between barrel and endcap

#Indicies of leading muons
ind1 = "IndexLepAll_mu[0]"
ind2 = "IndexLepAll_mu[1]"

dimuon_mass = "sqrt(2*(LepAll_pt[" + ind1 + "] * LepAll_pt[" + ind2 + "]*(cosh(LepAll_eta[" + ind1 + "] - LepAll_eta[" + ind2 + "]) - cos(LepAll_phi[" + ind1 + "] - LepAll_phi[" + ind2 + "]))))"
dimuon_pt = "sqrt(LepAll_pt[" + ind1 + "]*LepAll_pt[" + ind1 + "] + LepAll_pt[" + ind2 + "]*LepAll_pt[" + ind2 + "] + 2*(LepAll_pt[" + ind1 + "]*LepAll_pt[" + ind2 + "]*cos(LepAll_phi[" + ind1 + "] - LepAll_phi[" + ind2 + "])))"
met2 = "met + dimuon_pt"
#met2_phi = 
#electron_mt2 = "sqrt(2*met2*LepAll_pt[IndexLepAll_el[0]]*(1 - cos(met2_phi - LepAll_phi[IndexLepAll_el[0]])))"
#muon_mt2 = "sqrt(2*met2*LepAll_pt[IndexLepAll_mu[2]]*(1 - cos(met2_phi - LepAll_phi[IndexLepAll_mu[2]])))"

for s in selectedSamples: 
   samples[s].tree.SetAlias("dimuon_mass", dimuon_mass)
   samples[s].tree.SetAlias("dimuon_pt", dimuon_pt)
   samples[s].tree.SetAlias("met2", met2)
   #samples[s].tree.SetAlias("met2_phi", met2_phi)
   #samples[s].tree.SetAlias("electron_mt2", electron_mt2)
   #samples[s].tree.SetAlias("muon_mt2", muon_mt2)

def regions(ind):
   SRs = {\
      'SR1':["SR1","LepAll_pt[" + ind + "] < 30"],
   
      'SR1a':["SR1a", combineCuts("LepAll_mt[" + ind + "] < 60", "LepAll_pt[" + ind + "] < 30")],
      'SR1b':["SR1b", combineCuts(btw("LepAll_mt[" + ind + "]", 60, 95), "LepAll_pt[" + ind + "] < 30")],
      'SR1c':["SR1c", combineCuts("LepAll_mt[" + ind + "] > 95", "LepAll_pt[" + ind + "] < 30")],
      
      'SRL1':["SRL1", btw("LepAll_pt[" + ind + "]", 5, 12)],
      'SRH1':["SRH1", btw("LepAll_pt[" + ind + "]", 12, 20)],
      'SRV1':["SRV1", btw("LepAll_pt[" + ind + "]", 20, 30)],
   
      'SRL1a':["SRL1a", combineCuts("LepAll_mt[" + ind + "] < 60", btw("LepAll_pt[" + ind + "]", 5, 12))],
      'SRH1a':["SRH1a", combineCuts("LepAll_mt[" + ind + "] < 60", btw("LepAll_pt[" + ind + "]", 12, 20))],
      'SRV1a':["SRV1a", combineCuts("LepAll_mt[" + ind + "] < 60", btw("LepAll_pt[" + ind + "]", 20, 30))],
   
      'SRL1b':["SRL1b", combineCuts(btw("LepAll_mt[" + ind + "]", 60, 95), btw("LepAll_pt[" + ind + "]", 5, 12))],
      'SRH1b':["SRH1b", combineCuts(btw("LepAll_mt[" + ind + "]", 60, 95), btw("LepAll_pt[" + ind + "]", 12, 20))],
      'SRV1b':["SRV1b", combineCuts(btw("LepAll_mt[" + ind + "]", 60, 95), btw("LepAll_pt[" + ind + "]", 20, 30))],
   
      'SRL1c':["SRL1c", combineCuts("LepAll_mt[" + ind + "] > 95", btw("LepAll_pt[" + ind + "]", 5, 12))],
      'SRH1c':["SRH1c", combineCuts("LepAll_mt[" + ind + "] > 95", btw("LepAll_pt[" + ind + "]", 12, 20))],
      'SRV1c':["SRV1c", combineCuts("LepAll_mt[" + ind + "] > 95", btw("LepAll_pt[" + ind + "]", 20, 30))]}
   return SRs

#SRs
ind_el = "IndexLepAll_el[0]"
ind_mu = "IndexLepAll_el[2]"

SRs_el = regions(ind_el)
SRs_mu = regions(ind_mu)

#regions = ['SR1', 'SR1a', 'SR1b', 'SR1c', 'SRL1', 'SRH1', 'SRV1', 'SRL1a', 'SRH1a', 'SRV1a', 'SRL1b', 'SRH1b', 'SRV1b', 'SRL1c', 'SRH1c', 'SRV1c']
#
#for reg in regions:

#Save
if save: #web address: http://www.hephy.at/user/mzarucki/plots
   savedir = "/afs/hephy.at/user/m/mzarucki/www/plots/Zinv/2016"
   savedir += "/" + SR
   
   savedir1 = savedir + "/beforeEmul"
   savedir2 = savedir + "/afterEmul/" + CT2cut
   
   suffix = "_" + SR

   if peak: 
      suffix = "_peak"
      savedir1 += "/peak"
      savedir2 += "/peak"

   if not os.path.exists("%s/root"%(savedir1)): os.makedirs("%s/root"%(savedir1))
   if not os.path.exists("%s/pdf"%(savedir1)): os.makedirs("%s/pdf"%(savedir1))
   if not os.path.exists("%s/root"%(savedir2)): os.makedirs("%s/root"%(savedir2))
   if not os.path.exists("%s/pdf"%(savedir2)): os.makedirs("%s/pdf"%(savedir2))

if peak:
   peak = CutClass("Zpeak", [
      ["2mu", "nLepAll_mu >= 2"],
      ["Zpeak","abs(dimuon_mass - 91.1876) < 15"],
      ], baseCut = None)
else:
   peak = CutClass("None", [["None","1"]], baseCut = None)

#Preselection & basic SR cuts
dimuon = CutClass("dimuon", [
   ["ISR100", "nIsrJet >= 1"],
   ["TauVeto","Sum$(TauGood_idMVANewDM && TauGood_pt > 20) == 0"],
   ["BVeto","nBSoftJet == 0 && nBHardJet == 0"],
   ["No3rdJet60","nVetoJet <= 2"],
   ["2mu", "nLepAll_mu >= 2"], 
   ["2mu-Lep30Veto-2Lep20Veto", "((nLepAll_mu == 2 && nLepAll_el == 0) ||" +\
                                 "(nLepAll_mu == 2 && nLepAll_el == 1 && LepAll_pt[IndexLepAll_el[0]] < 30) ||" +\
                                 "(nLepAll_mu == 2 && nLepAll_el == 2 && LepAll_pt[IndexLepAll_el[0]] < 30 && LepAll_pt[IndexLepAll_el[1]] < 20) ||" +\
                                 "(nLepAll_mu == 3 && nLepAll_el == 0 && LepAll_pt[IndexLepAll_mu[2]] < 30) ||" +\
                                 "(nLepAll_mu == 4 && nLepAll_el == 0 && LepAll_pt[IndexLepAll_mu[2]] < 30 && LepAll_pt[IndexLepAll_mu[3]] < 20))"],
    
   ["muon1", "abs(LepAll_pdgId[" + ind1 + "]) == 13"],
   ["relIso", "LepAll_relIso03[" + ind1 + "] < 0.12"],
   ["pt28", "LepAll_pt[" + ind1 + "] > 28"],
   # 
   ["muon2", "abs(LepAll_pdgId[" + ind2 + "]) == 13"],
   ["relIso", "LepAll_relIso03[" + ind2 + "] < 0.12"],
   ["pt20", "LepAll_pt[" + ind2 + "] > 20"],
   #
   ["OS", "LepAll_pdgId[" + ind1 + "] == -LepAll_pdgId[" + ind2 + "]"],
   #
   ["dimuon_mass","dimuon_mass > 55"],
   #["dimuon_pt","dimuon_pt > 75"],
   ["met2","met2 > 75"],
   ], baseCut = peak)

emulated = CutClass("emulated", [
   ["CT2","min(met2, ht_basJet - 100) >" + CT2cut],
   ], baseCut = dimuon)

electrons = CutClass("electrons", [
   ["ele","nLepAll_el >= 1"],
   SRs_el[SR]
   ], baseCut = emulated)

muons = CutClass("muons", [
   ["mu","nLepAll_mu >= 3"],
   SRs_mu[SR]
   ], baseCut = emulated)

yields = {}
if doYields and peak:
   yields['Zpeak'] = Yields(samples, selectedSamples, emulated, cutOpt = "combinedList", pklOpt = False, nDigits = 2, err = True, verbose = True, nSpaces = 10)
   yields['Nel'] = Yields(samples, selectedSamples, electrons, cutOpt = "combinedList", pklOpt = False, nDigits = 2, err = True, verbose = True, nSpaces = 10)
   yields['Nmu'] = Yields(samples, selectedSamples, muons, cutOpt = "combinedList", pklOpt = False, nDigits = 2, err = True, verbose = True, nSpaces = 10)
   
   if not os.path.isfile(savedir + "/ZinvYields" + suffix + ".txt"):
      outfile = open(savedir + "/ZinvYields" + suffix + ".txt", "w")
      outfile.write("Zinv Estimation Yields\n")
      outfile.write("CT        Zpeak_data                  Zpeak_DY                   Zpeak_TT                    Nel_data                   Nel_DY                   Nel_TT                   Nmu_data                  Nmu_DY                 Nmu_TT\n")
   
   with open(savedir + "/ZinvYields" + suffix + ".txt", "a") as outfile:
      outfile.write(CT2cut + "     " +\
      str(yields['Zpeak'].yieldDictFull['d1muBlind']['emulated'].round(2)) + "              " +\
      str(yields['Zpeak'].yieldDictFull['dy']['emulated'].round(2)) + "              " +\
      str(yields['Zpeak'].yieldDictFull['tt']['emulated'].round(2)) + "              " +\
      str(yields['Nel'].yieldDictFull['d1muBlind']['electrons'].round(2)) + "              " +\
      str(yields['Nel'].yieldDictFull['dy']['electrons'].round(2)) + "              " +\
      str(yields['Nel'].yieldDictFull['tt']['electrons'].round(2)) + "              " +\
      str(yields['Nmu'].yieldDictFull['d1muBlind']['muons'].round(2)) + "              " +\
      str(yields['Nmu'].yieldDictFull['dy']['muons'].round(2)) + "              " +\
      str(yields['Nmu'].yieldDictFull['tt']['muons'].round(2)) + "\n")

   Zpeak_dMC = (yields['Zpeak'].yieldDictFull['d1muBlind']['emulated']/(yields['Zpeak'].yieldDictFull['dy']['emulated'] + yields['Zpeak'].yieldDictFull['tt']['emulated'])).round(3)
   prob_el_data = (yields['Nel'].yieldDictFull['d1muBlind']['electrons']/yields['Zpeak'].yieldDictFull['d1muBlind']['emulated'])
   prob_el_MC = ((yields['Nel'].yieldDictFull['dy']['electrons'] + yields['Nel'].yieldDictFull['tt']['electrons'])/(yields['Zpeak'].yieldDictFull['dy']['emulated'] + yields['Zpeak'].yieldDictFull['tt']['emulated']))
   prob_el_dMC = (prob_el_data/prob_el_MC).round(3)
   prob_mu_data = (yields['Nmu'].yieldDictFull['d1muBlind']['muons']/yields['Zpeak'].yieldDictFull['d1muBlind']['emulated'])
   prob_mu_MC = ((yields['Nmu'].yieldDictFull['dy']['muons'] + yields['Nmu'].yieldDictFull['tt']['muons'])/(yields['Zpeak'].yieldDictFull['dy']['emulated'] + yields['Zpeak'].yieldDictFull['tt']['emulated']))
   prob_mu_dMC = (prob_mu_data/prob_mu_MC).round(3)
   ratio_el = (Zpeak_dMC*prob_el_dMC).round(3)
   ratio_mu = (Zpeak_dMC*prob_mu_dMC).round(3)
 
   if not os.path.isfile(savedir + "/ZinvRatios" + suffix + ".txt"):
      outfile = open(savedir + "/ZinvRatios" + suffix + ".txt", "w")
      outfile.write("Zinv Estimation Ratios\n")
      outfile.write("CT       Zpeak_data_MC           prob_el_data           prob_el_MC           prob_el_data_MC           prob_mu_data          prob_mu_MC          prob_mu_data_MC          Ratio_el         Ratio_mu\n")
   
   with open(savedir + "/ZinvRatios" + suffix + ".txt", "a") as outfile:
      outfile.write(CT2cut + "       " +\
      str(Zpeak_dMC) + "            " +\
      str(prob_el_data.round(3)) + "            " +\
      str(prob_el_MC.round(3)) + "            " +\
      str(prob_el_dMC) + "            " +\
      str(prob_mu_data.round(3)) + "            " +\
      str(prob_mu_MC.round(3)) + "            " +\
      str(prob_mu_dMC) + "            " +\
      str(ratio_el) + "            " +\
      str(ratio_mu)+ "\n")

if plot:
   plotSamples = selectedSamples #["z", "qcd", "tt", "w"]
   
   #if getData:
   #   #del plotRegions['SR']
   #   plotSamples.append("dblind")
   
   plotDict = {\
      "dimuon_mass":{'var':"dimuon_mass", "bins":[50, 0, 250], "decor":{"title": "Di-muon System Invariant Mass Distribution" ,"x":"M_{#mu#mu} / GeV" , "y":"Events", 'log':[0, logy,0]}},
      "dimuon_pt":{'var':"dimuon_pt", "bins":[50, 0, 250], "decor":{"title": "Di-muon System Transverse Momentum Distribution" ,"x":"p_{T_{#mu#mu}} / GeV" , "y":"Events", 'log':[0, logy,0]}},
      "MET":{'var':"met", "bins":[50,0,500], "decor":{"title": "MET Distribution" ,"x":"Missing E_{T} / GeV" , "y":"Events", 'log':[0,logy,0]}},
      "HT":{'var':"ht_basJet", "bins":[50,0,500], "decor":{"title": "H_{{T}} Distribution","x":"H_{T} / GeV" , "y":"Events", 'log':[0,logy,0]}},
      "nJets30":{'var':"nBasJet", "bins":[10,0,10], "decor":{"title":"Number of Jets with p_{{T}} > 30GeV", "x":"Number of Jets with p_{T} > 30GeV", "y":"Events", 'log':[0,1,0]}},      
      "nJets60":{'var':"nVetoJet", "bins":[10,0,10], "decor":{"title":"Number of Jets with p_{{T}} > 60GeV", "x":"Number of Jets with p_{T} > 60GeV", "y":"Events", 'log':[0,1,0]}},
      "ISRpt":{'var':"Jet_pt[IndexJet_basJet[0]]", "bins":[45,100,1000], "decor":{"title":"Leading Jet p_{{T}}","x":"ISR Jet p_{T}","y":"Events", 'log':[0,1,0]}},
   }
      
   plotDict2 = plotDict.copy()
   plotDict2["MET2"] = {'var':"met2", "bins":[50,0,500], "decor":{"title": "Emulated MET Distribution" ,"x":"Emulated Missing E_{T} / GeV" , "y":"Events", 'log':[0,logy,0]}}
   
   plotDict3 = {\
      "elePt":{'var':"LepAll_pt[IndexLepAll_el[0]]", "bins":[10,0,50], "decor":{"title": "Electron pT Distribution" ,"x":"Electron p_{T} / GeV" , "y":"Events", 'log':[0,logy,0]}},
      "muPt":{'var':"LepAll_pt[IndexLepAll_mu[2]]", "bins":[10,0,50], "decor":{"title": "Muon pT Distribution" ,"x":"Muon p_{T} / GeV" , "y":"Events", 'log':[0,logy,0]}},
      #"electron_mt2":{'var':"electron_mt2", "bins":[10,0,100], "decor":{"title": "Electron mT Distribution" ,"x":"Electron m_{T2} / GeV" , "y":"Events", 'log':[0,logy,0]}}, 
      #"muon_mt2":{'var':"muon_mt2", "bins":[10,0,100], "decor":{"title": "Muon mT Distribution" ,"x":"Muon m_{T2} / GeV" , "y":"Events", 'log':[0,logy,0]}}, 
   }
   
   plotsList = ["dimuon_mass", "dimuon_pt", "MET", "HT", "nJets30", "nJets60", "ISRpt"]
   plotsList2 = plotsList + ["MET2"]
   
   plotsDict = Plots(**plotDict)
   plotsDict2 = Plots(**plotDict2)
   plotsDict3 = Plots(**plotDict3)
   
   if Zpeak:
      dimuonPlots = getPlots(samples, plotsDict, dimuon, plotSamples, plotList = plotsList, addOverFlowBin='upper')
      dimuonPlots2 = drawPlots(samples, plotsDict, dimuon, plotSamples, plotList = plotsList, plotLimits = [10, 100], denoms=["bkg"], noms = ["d1muBlind"], fom="RATIO", fomLimits=[0,2.8], plotMin = 0.01, normalize = False, save=False)
   
   if emulated:
      emulatedPlots = getPlots(samples, plotsDict2, emulated, plotSamples, plotList = plotsList2, addOverFlowBin='upper')
      emulatedPlots2 = drawPlots(samples, plotsDict2, emulated, plotSamples, plotList = plotsList2, plotLimits = [10, 100], denoms=["bkg"], noms = ["d1muBlind"], fom="RATIO", fomLimits=[0,2.8], plotMin = 0.01, normalize = False, save=False)
   
   if leptons:
      elePlots = getPlots(samples, plotsDict3, electrons, plotSamples, plotList = ["elePt"], addOverFlowBin='upper')
      elePlots2 = drawPlots(samples, plotsDict3, electrons, plotSamples, plotList = ["elePt"], plotLimits = [10, 100], denoms=["bkg"], noms = ["d1muBlind"], fom="RATIO", fomLimits=[0,2.8], plotMin = 0.01, normalize = False, save=False)
      muPlots = getPlots(samples, plotsDict3, muons, plotSamples, plotList = ["muPt"], addOverFlowBin='upper')
      muPlots2 = drawPlots(samples, plotsDict3, muons, plotSamples, plotList = ["muPt"], plotLimits = [10, 100], denoms=["bkg"], noms = ["d1muBlind"], fom="RATIO", fomLimits=[0,2.8], plotMin = 0.01, normalize = False, save=False)
   
   #Save canvas
   if save: #web address: http://www.hephy.at/user/mzarucki/plots/electronID
      if Zpeak:
         for canv in dimuonPlots2['canvs']:
            #if plot['canvs'][canv][0]:
            dimuonPlots2['canvs'][canv][0].SaveAs("%s/%s%s.png"%(savedir1, canv, suffix))
            dimuonPlots2['canvs'][canv][0].SaveAs("%s/root/%s%s.root"%(savedir1, canv, suffix))
            dimuonPlots2['canvs'][canv][0].SaveAs("%s/pdf/%s%s.pdf"%(savedir1, canv, suffix))
      if emulated:   
         for canv in emulatedPlots2['canvs']:
            #if plot['canvs'][canv][0]:
            emulatedPlots2['canvs'][canv][0].SaveAs("%s/%s%s.png"%(savedir2, canv, suffix))
            emulatedPlots2['canvs'][canv][0].SaveAs("%s/root/%s%s.root"%(savedir2, canv, suffix))
            emulatedPlots2['canvs'][canv][0].SaveAs("%s/pdf/%s%s.pdf"%(savedir2, canv, suffix))
      if leptons:   
         for canv in elePlots2['canvs']:
            #if plot['canvs'][canv][0]:
            elePlots2['canvs'][canv][0].SaveAs("%s/%s%s.png"%(savedir2, canv, suffix))
            elePlots2['canvs'][canv][0].SaveAs("%s/root/%s%s.root"%(savedir2, canv, suffix))
            elePlots2['canvs'][canv][0].SaveAs("%s/pdf/%s%s.pdf"%(savedir2, canv, suffix))
         for canv in muPlots2['canvs']:
            #if plot['canvs'][canv][0]:
            muPlots2['canvs'][canv][0].SaveAs("%s/%s%s.png"%(savedir2, canv, suffix))
            muPlots2['canvs'][canv][0].SaveAs("%s/root/%s%s.root"%(savedir2, canv, suffix))
            muPlots2['canvs'][canv][0].SaveAs("%s/pdf/%s%s.pdf"%(savedir2, canv, suffix))
