
import ROOT




from Workspace.DegenerateStopAnalysis.cuts.cuts import *
from Workspace.DegenerateStopAnalysis.navidTools.NavidTools import *
#from Workspace.DegenerateStopAnalysis.navidTools.makeTable import *
from Workspace.DegenerateStopAnalysis.navidTools.limitCalc import  getLimit, plotLimits
import Workspace.DegenerateStopAnalysis.navidTools.limitTools as limitTools
from Workspace.DegenerateStopAnalysis.cmgTuplesPostProcessed_mAODv2 import *
from Workspace.DegenerateStopAnalysis.navidTools.getSamples_PP_mAODv2_7412pass2_scan import getSamples



dos={
        "make_plots":True,
        "get_yields":True,
        "muSel"     :True,
    }




saveDir = "/afs/hephy.at/user/n/nrad/www/T2Deg13TeV/mAODv2_7412pass2_v6/8TeVComp_v1/"
makeDir( saveDir )



#mc_path     = "/afs/hephy.at/data/nrad01/cmgTuples/postProcessed_mAODv2/7412pass2_SMSScan_v3/RunIISpring15DR74_25ns"
#signal_path = "/afs/hephy.at/data/nrad01/cmgTuples/postProcessed_mAODv2/7412pass2_SMSScan_v3/RunIISpring15DR74_25ns"
#data_path   = "/afs/hephy.at/data/nrad01/cmgTuples/postProcessed_mAODv2/7412pass2_SMSScan_v3/Data_25ns"


ppTag="7412pass2_SMSScan_v1"
mc_path     = "/afs/hephy.at/data/nrad01/cmgTuples/postProcessed_mAODv2_v6/{ppTag}/RunIISpring15DR74_25ns".format(ppTag=ppTag)
signal_path     = "/afs/hephy.at/data/nrad01/cmgTuples/postProcessed_mAODv2_v6/{ppTag}/RunIISpring15DR74_25ns".format(ppTag=ppTag)
data_path     = "/afs/hephy.at/data/nrad01/cmgTuples/postProcessed_mAODv2_v6/{ppTag}/Data_25ns".format(ppTag=ppTag)


lumis = {
            #'lumi_mc':10000, 
            'lumi_target':2300.,
            'lumi_data_blinded':2245.386,
            'lumi_data_unblinded':139.63,
        }

lumi_tag = lambda l: "%0.0fpbm1"%(l)

lumiTag = lumi_tag(lumis['lumi_target'])


useHT=False

try:
    samples
except NameError:
    cmgPP = cmgTuplesPostProcessed(mc_path, signal_path, data_path)
    samples = getSamples(wtau=False,sampleList=['w','tt'],useHT=useHT,skim='presel', scan=True, do8tev=True, cmgPP=cmgPP, getData=False)


## Scaling the 8tev samples to the 13tev xsec, lumi (xsec13/xsec8) ~= 4.26, (2.3fb-1/19.7fb-1) ~= 0.12 .... a factor of ~0.5
#samples.addWeight( 4.26,  sampleList=samples.otherSigList() )

samples.w8tev.weight="puWeight"
samples.tt8tev.weight="puWeight"


sampleDir8tev = "/data/imikulec/monoJetTuples_v8/copyfiltered"

sr1_8tev_ =  "isrJetPt>110.&&isrJetBTBVetoPassed&&(nHardElectrons+nHardTaus)==0&&mediumMuIndex>-1&&(muPt[mediumMuIndex]<20.||nHardMuonsMediumWP==1)&&njet60<3&&ht>400.&&type1phiMet>300.&&muPdg[mediumMuIndex]>0&&abs(muEta[mediumMuIndex])<1.5&&nbtags==0&& muPt[mediumMuIndex]<=30."
sr1a_8tev_ = "isrJetPt>110.&&isrJetBTBVetoPassed&&(nHardElectrons+nHardTaus)==0&&mediumMuIndex>-1&&(muPt[mediumMuIndex]<20.||nHardMuonsMediumWP==1)&&njet60<3&&ht>400.&&type1phiMet>300.&&muPdg[mediumMuIndex]>0&&abs(muEta[mediumMuIndex])<1.5&&nbtags==0&& muMT[mediumMuIndex]<60.&&muPt[mediumMuIndex]<=30."
sr1b_8tev_ = "isrJetPt>110.&&isrJetBTBVetoPassed&&(nHardElectrons+nHardTaus)==0&&mediumMuIndex>-1&&(muPt[mediumMuIndex]<20.||nHardMuonsMediumWP==1)&&njet60<3&&ht>400.&&type1phiMet>300.&&muPdg[mediumMuIndex]>0&&abs(muEta[mediumMuIndex])<1.5&&nbtags==0&& muMT[mediumMuIndex]>=60.&&muMT[mediumMuIndex]<88.&&muPt[mediumMuIndex]<=30."
sr1c_8tev_ = "isrJetPt>110.&&isrJetBTBVetoPassed&&(nHardElectrons+nHardTaus)==0&&mediumMuIndex>-1&&(muPt[mediumMuIndex]<20.||nHardMuonsMediumWP==1)&&njet60<3&&ht>400.&&type1phiMet>300.&&muPdg[mediumMuIndex]>0&&abs(muEta[mediumMuIndex])<1.5&&nbtags==0&& muMT[mediumMuIndex]>=88.&&muPt[mediumMuIndex]<=30."
sr2_8tev_ = "isrJetPt>110.&&isrJetBTBVetoPassed&&(nHardElectrons+nHardTaus)==0&&mediumMuIndex>-1&&(muPt[mediumMuIndex]<20.||nHardMuonsMediumWP==1)&&njet60<3&&isrJetPt>325.&&type1phiMet>300.&&nHardbtags==0&&nSoftbtags>0&&muPt[mediumMuIndex]<=30."
weight_8tev = "puWeight*wpts4X*(1.+7.5e-5*Max$(gpM*(gpPdg==1000006)))*(1.*(ptISR<120.)+0.95*(ptISR>=120.&&ptISR<150.)+0.9*(ptISR>=150.&&ptISR<250.)+0.8*(ptISR>=250.))"


##################################################################

bins={
        "met": range(200,500,50) + range(500,900,100) ,
        #"cosphi": [ ((x>=0) - (x<0)) * x**2/100. for x in range(-10,11)]
        "mtBins": [0,60,88,300],
        "cosphi": [12,-1,1], 
        "deltaPhi": [10,0,3.15],
        "lepPtSR":  [14,0,35],

      }

plotDict =\
      {
        "mt":          {'var':"mt"                              ,"bins":[20,0,300]          ,"nMinus1":""        ,"decor":{"title":"MT"          ,"x":"M_{T}"         ,"y":"Events  "  ,'log':[0,1,0] }},
        "mtBins":      {'var':"mt"                              ,"bins":bins['mtBins']       ,"nMinus1":""        ,"decor":{"title":"MT  "        ,"x":"M_{T}"         ,"y":"Events in MT bins"  ,'log':[0,1,0] } , 'binningIsExplicit':True},
        "LepPt":       {'var':"lepPt"                           ,"bins":[40,0,200]          ,"nMinus1":""        ,"decor":{"title":"LepPt"       ,"x":"Lepton P_{T}"  ,"y":"Events  "   ,'log':[0,1,0] }},
        "LepPtSR":     {'var':"lepPt"                           ,"bins":bins['lepPtSR']     ,"nMinus1":""        ,"decor":{"title":"LepPt"       ,"x":"Lepton P_{T}"   ,"y":"Events  "   ,'log':[0,1,0] }, 'binningIsExplicit':True },
        "met":         {'var':"met"                             ,"bins":bins['met']        ,"nMinus1":""        ,"decor":{"title":"MET"         ,"x":"E^{miss}_{T}"  ,"y":"Events "  ,'log':[0,1,0] } , 'binningIsExplicit':True },
        "isrPt":       {'var':"Jet_pt[0]"                       ,"bins":[20,200,900]        ,"nMinus1":""        ,"decor":{"title":"isrJetPt"    ,"x":"IsrJetPt"      ,"y":"Events "  ,'log':[0,1,0] }},
        "cosphi":      {'var':"CosLMet"                         ,"bins":bins['cosphi']           ,"nMinus1":""        ,"decor":{"title":"CosPhiLMet"    ,"x":"CosPhiLMet"      ,"y":"Events"  ,'log':[0,1,0] } , 'binningIsExplicit':False },
        "deltaPhi":    {'var':"acos(CosLMet)"                   ,"bins":bins['deltaPhi']           ,"nMinus1":""        ,"decor":{"title":"deltaPhiLMet"    ,"x":"CosPhiLMet"      ,"y":"Events"  ,'log':[0,1,0] } , 'binningIsExplicit':False },
        "stopsPt":     {'var':"stops_pt"                        ,"bins":[20,0,900]        ,"nMinus1":""        ,"decor":{"title":"stops_pt"    ,"x":"stops_p"      ,"y":"Events  "  ,'log':[0,1,0] }},
        "nJet30":      {'var':"nJet30"                          ,"bins":[10,0,10]        ,"nMinus1":""        ,"decor":{"title":"nJets30"    ,"x":"nJets30"      ,"y":"Events  "  ,'log':[0,1,0] }},
        "nJet60":      {'var':"nJet60"                          ,"bins":[7,0,7]           ,"nMinus1":""        ,"decor":{"title":"nJets60"    ,"x":"nJets60"      ,"y":"Events  "  ,'log':[0,1,0] }},
        "genLepPt":    {'var':"Max$(genLep_pt*(abs(genLep_pdgId)==13&&abs(genLep_eta)<2.1))"                       ,"bins":[35,0,35]         ,"nMinus1":""        ,"decor":{"title":"GenLepPt"       ,"x":"GenLepton P_{T}"   ,"y":"Events  "   ,'log':[0,1,0] }, 'binningIsExplicit':True },


        "mtLepPt":     {'var':"mt:lepPt"                        ,"bins":[20,0,20,7,0,140] ,"is2D":True  ,"nMinus1":""        ,"decor":{"title":"MTvsLepPt"    ,"x":"LepPt  "    ,"y":"M_{T}"         ,'log':[0,0,0] }},
        #"stopsPt_binned":     {'var':"stops_pt"                 ,"bins":[]        ,"nMinus1":""        ,"decor":{"title":"isrJetPt"    ,"x":"IsrJetPt"      ,"y":"Events / 35 GeV "  ,'log':[0,1,0] }},
      }
plots = Plots(**plotDict)

import copy
plotDict8tev = copy.deepcopy(plotDict)

plotDict8tev["mt"].update(       {'var':"muMT[mediumMuIndex]"                                })
plotDict8tev["mtBins"].update(   {'var':"muMT[mediumMuIndex]"                                })
plotDict8tev["LepPt"].update(    {'var':"muPt[mediumMuIndex]"                                })
plotDict8tev["LepPtSR"].update(  {'var':"muPt[mediumMuIndex]"                                })
plotDict8tev["met"].update(      {'var':"type1phiMet"                                        })
plotDict8tev["isrPt"].update(    {'var':"isrJetPt"                                           })
plotDict8tev["cosphi"].update(   {'var':"cos(muPhi[mediumMuIndex]-type1phiMetphi)"           })
plotDict8tev["deltaPhi"].update( {'var':"acos( cos(muPhi[mediumMuIndex]-type1phiMetphi))"    })
plotDict8tev["stopsPt"].update(  {'var':"ptISR"    })
plotDict8tev["nJet30"].update(   {'var':"njet"    })
plotDict8tev["nJet60"].update(   {'var':"njet60"    })
plotDict8tev["mtLepPt"].update(  {'var':"muMT[mediumMuIndex]:muPt[mediumMuIndex]"    })
plotDict8tev["genLepPt"].update(       {'var':"Max$(gpPt*(gpSta==3&&abs(gpPdg)==13&&abs(gpEta)<2.1))"   })

for pl in plotDict8tev.keys():
    plotDict8tev[pl]['decor']['style']=2
 
plots8tev = Plots(**plotDict8tev)


###############################################################################################################
##########################################                       ##############################################
##########################################                       ##############################################
##########################################                       ##############################################
###############################################################################################################

















preselNoMuSel_8tev = CutClass ("presel", [
                              ["MET200","type1phiMet>200."],
                              ["ISR110","isrJetPt>110." ],
                              ["HT300","ht>300"],
                              ["AntiQCD", "isrJetBTBVetoPassed" ], # monojet
                              #["TauElVeto","(nHardElectrons+nHardTaus)==0"],
                              #["1Mu-2ndMu20Veto", "mediumMuIndex>-1  &&   (muPt[mediumMuIndex]<20.||nHardMuonsMediumWP==1) "],
                              #["No3rdJet60","njet60<3"]
                             ],
                baseCut=None,
                )



preselNoMuSel = CutClass ("presel", [
                              ["MET200","met>200"],
                              ["ISR110","nJet110>=1" ],
                              ["HT300","htJet30j>300"],
                              ["AntiQCD", " (deltaPhi_j12 < 2.5)" ], # monojet
                              #["TauElVeto","(Sum$(TauGood_idMVA)==0) && (Sum$(abs(LepGood_pdgId)==11 && LepGood_SPRING15_25ns_v1==1)==0)"],
                              #["No3rdJet60","nJet60<=2"]
                             ],
                baseCut=None,
                )


muSelGen_8tev       = CutClass("muSelGen", [
                            ["1mu", "Sum$(gpSta==3 && abs(gpPdg)==13)>0"],
                            ["eta2.1", "Sum$(gpSta==3 && abs(gpPdg)==13 && abs(gpEta)<2.1)>0"],
                            ["pt5",    "Sum$(gpSta==3 && abs(gpPdg)==13 && abs(gpEta)<2.1 && gpPt>5)>0"],
                            ],
                    baseCut=preselNoMuSel_8tev
                )


muSelGen       = CutClass("muSelGen", [
                            ["1mu",    "Sum$(abs(genLep_pdgId)==13)>0"],
                            ["eta2.1", "Sum$(abs(genLep_pdgId)==13 && abs(genLep_eta)<2.1)>0"],
                            ["pt5",    "Sum$(abs(genLep_pdgId)==13 && abs(genLep_eta)<2.1&& genLep_pt>5)>0"],
                            ],
                    baseCut=preselNoMuSel
                )


#muSelReco_8tev = CutClass("muSelReco",[
#                            ["recoMu","mediumMuIndex>-1  &&   (muPt[mediumMuIndex]<20.||nHardMuonsMediumWP==1) "],
#                                      ] )
#
#muSelReco = CutClass("muSelReco",[
#                            ["recoMu"," (nlep>0 || (nlep ==2 && LepGood_pt[looseMuonIndex2] < 20) ) "],
#                            ["recoMu2", "Sum$( abs(LepGood_pdgId)==13 && LepGood_pt > 5  && abs(LepGood_eta)<2.1 && abs(LepGood_dz)<0.5 && abs(LepGood_dxy)<0.02 &&   ( (LepGood_pt >= 25 && LepGood_relIso04 < 0.2 ) || ( LepGood_pt < 25 &&  LepGood_pt*LepGood_relIso04  < 5))    )>0 "],
#                            #["recoMu2", "Sum$(((abs(LepOther_pdgId)==13) && ((LepOther_pt > 5))  && (abs(LepOther_eta)<2.1) && (abs(LepOther_dz)<0.5) && (abs(LepOther_dxy)<0.02) && ((((LepOther_pt >= 25) && (LepOther_relIso04 < 0.2) ) || ( (LepOther_pt < 25) && (( LepOther_pt*LepOther_relIso04 ) < 5))))))"]
#                                  ] )
#


LepGoodFlow = {\
   "mu": 'Sum$( abs(LepGood_pdgId)==13 )>0',
   "pt": 'Sum$( abs(LepGood_pdgId)==13 && LepGood_pt > 5  )>0',
   "eta": 'Sum$( abs(LepGood_pdgId)==13 && LepGood_pt > 5  && abs(LepGood_eta)<2.1   )>0',
   "dz": 'Sum$( abs(LepGood_pdgId)==13 && LepGood_pt > 5  && abs(LepGood_eta)<2.1 && abs(LepGood_dz)<0.5   )>0',
   "dxy": 'Sum$( abs(LepGood_pdgId)==13 && LepGood_pt > 5  && abs(LepGood_eta)<2.1 && abs(LepGood_dz)<0.5 && abs(LepGood_dxy)<0.02 )>0',
   "hybIso03": 'Sum$( abs(LepGood_pdgId)==13 && LepGood_pt > 5  && abs(LepGood_eta)<2.1 && abs(LepGood_dz)<0.5 && abs(LepGood_dxy)<0.02 &&   ( (LepGood_pt >= 25 && LepGood_relIso03 < 0.2 ) || ( LepGood_pt < 25 &&  LepGood_pt*LepGood_relIso03  < 5))    )>0',
   "hybIso04": 'Sum$( abs(LepGood_pdgId)==13 && LepGood_pt > 5  && abs(LepGood_eta)<2.1 && abs(LepGood_dz)<0.5 && abs(LepGood_dxy)<0.02 &&   ( (LepGood_pt >= 25 && LepGood_relIso04 < 0.2 ) || ( LepGood_pt < 25 &&  LepGood_pt*LepGood_relIso04  < 5))    )>0',
   "hybIso04-12": 'Sum$( abs(LepGood_pdgId)==13 && LepGood_pt > 5  && abs(LepGood_eta)<2.1 && abs(LepGood_dz)<0.5 && abs(LepGood_dxy)<0.02 &&   ( (LepGood_pt >= 25 && LepGood_relIso04 < 0.48 ) || ( LepGood_pt < 25 &&  LepGood_pt*LepGood_relIso04  < 12))    )>0',
}

LepOtherFlow={x:LepGoodFlow[x].replace("Good","Other") for x in LepGoodFlow}







                        

muSelReco_8tev = CutClass("muSelReco", [
                                ["mu",        "Sum$( abs(muPdg)==13 )>0"   ],
                                ["pt",        "Sum$( abs(muPdg)==13 && muPt > 5 )>0"   ],
                                ["eta",       "Sum$( abs(muPdg)==13 && muPt > 5  && abs(muEta)<2.1 )>0"   ],
                                ["dz",        "Sum$( abs(muPdg)==13 && muPt > 5  && abs(muEta)<2.1 && abs(muDz)<0.5  )>0"   ],
                                ["dxy",       "Sum$( abs(muPdg)==13 && muPt > 5  && abs(muEta)<2.1 && abs(muDz)<0.5 && abs(muDxy)<0.02    )>0"   ],
                                ["hybIso03",  "Sum$( abs(muPdg)==13 && muPt > 5  && abs(muEta)<2.1 && abs(muDz)<0.5 && abs(muDxy)<0.02 &&   ( (muPt >= 25 && muRelIso < 0.2 ) || ( muPt < 25 &&  muPt*muRelIso  < 5))    )>0"   ],
                                #["hybIso04",  ""   ],
                                        ],
                    baseCut=None
                )



muSelReco = CutClass("muSelReco", [
                                ["mu",        "((%s) || (%s))"%(LepGoodFlow["mu"],        LepOtherFlow["mu"],      )   ],
                                ["pt",        "((%s) || (%s))"%(LepGoodFlow["pt"],        LepOtherFlow["pt"],      )   ],
                                ["eta",       "((%s) || (%s))"%(LepGoodFlow["eta"],       LepOtherFlow["eta"],     )   ],
                                ["dz",        "((%s) || (%s))"%(LepGoodFlow["dz"],        LepOtherFlow["dz"],      )   ],
                                ["dxy",       "((%s) || (%s))"%(LepGoodFlow["dxy"],       LepOtherFlow["dxy"],     )   ],
                                ["hybIso03",  "((%s) || (%s))"%(LepGoodFlow["hybIso03"],  LepOtherFlow["hybIso03"],)   ],
                                ["hybIso04",  "((%s) || (%s))"%(LepGoodFlow["hybIso04"],  LepOtherFlow["hybIso04"],)   ],
                                ["hybIso04-12",  "((%s) || (%s))"%(LepGoodFlow["hybIso04-12"],  LepOtherFlow["hybIso04-12"],)   ],
                                ["newMuSel", "(nlep>0) " ], 
                                        ],
                    baseCut=None
                )








muSelString = "((%s) || (%s)) >0"%(LepGoodFlow["hybIso03"],  LepOtherFlow["hybIso03"])
muSelString_8tev = "Sum$( abs(muPdg)==13 && muPt > 5  && abs(muEta)<2.1 && abs(muDz)<0.5 && abs(muDxy)<0.02 &&   ( (muPt >= 25 && muRelIso < 0.2 ) || ( muPt < 25 &&  muPt*muRelIso  < 5))    )>0"

presel = CutClass ("presel", [
                              ["MET200","met>200"],
                              ["ISR110","nJet110>=1" ],
                              ["HT300","htJet30j>300"],
                              ["AntiQCD", " (deltaPhi_j12 < 2.5)" ], # monojet
                              ["TauElVeto","(Sum$(TauGood_idMVA)==0) && (Sum$(abs(LepGood_pdgId)==11 && LepGood_SPRING15_25ns_v1==1)==0)"],
                              ["1Mu-2ndMu20Veto", "(nlep==1 || (nlep ==2 && LepGood_pt[looseMuonIndex2] < 20) )"],
                              #["1Mu", muSelString],
                              ["No3rdJet60","nJet60<=2"]
                             ],
                baseCut=None,
                )

presel_8tev = CutClass ("presel", [
                              ["MET200","type1phiMet>200."],
                              ["ISR110","isrJetPt>110." ],
                              ["HT300","ht>300"],
                              ["AntiQCD", "isrJetBTBVetoPassed" ], # monojet
                              ["TauElVeto","(nHardElectrons+nHardTaus)==0"],
                              ["1Mu-2ndMu20Veto", "mediumMuIndex>-1  &&   (muPt[mediumMuIndex]<20.||nHardMuonsMediumWP==1) "],
                              #["1Mu", muSelString_8tev],
                              ["No3rdJet60","njet60<3"]
                             ],
                baseCut=None,
                )





sr1_8tev   = CutClass ("SR1",   [
                              ["CT300","min(type1phiMet,ht -100) > 300 "],
                              ["negMuon","muPdg[mediumMuIndex]>0"],
                              ["MuEta1.5","abs(muEta[mediumMuIndex])<1.5"],
                              ["BVeto","nbtags==0"],
                              ["MuPt30","muPt[mediumMuIndex]<=30."],
                            ] ,
                  baseCut = presel_8tev,
                  )




sr2_8tev      = CutClass ("SR2", [  
                               ["ISR325 Met300","isrJetPt>325&&type1phiMet>300."],
                               ["SoftBJet","nHardbtags==0 && nSoftbtags>0 "],
                               [" MuPt<30","muPt[mediumMuIndex]<=30."],
                            ],
                  baseCut = presel_8tev,
                  )

sr1a   = CutClass("SR1a", [['SR1a', 'mt<60']] , baseCut = sr1)
sr1b   = CutClass("SR1b", [['SR1b', '(mt >= 60 && mt < 88)']] , baseCut = sr1)
sr1c   = CutClass("SR1c", [['SR1c', 'mt>=88']] , baseCut = sr1)


sr1a_8tev   = CutClass("SR1a", [['SR1a', 'muMT[mediumMuIndex]<60']]                 , baseCut = sr1_8tev)
sr1b_8tev   = CutClass("SR1b", [['SR1b', 'muMT[mediumMuIndex]>=60.&&muMT[mediumMuIndex]<88.']] , baseCut = sr1_8tev)
sr1c_8tev   = CutClass("SR1c", [['SR1c', 'muMT[mediumMuIndex]>=88']]                 , baseCut = sr1_8tev)


sr1   = CutClass ("SR1",    [
                              ["CT300","min(met,htJet30j-100) > 300 "],
                              ["negMuon","lepPdgId==13"],
                              ["MuEta1.5","abs(lepEta)<1.5"],
                              ["BVeto","(nSoftBJetsCSV == 0 && nHardBJetsCSV ==0)"],
                              ["MuPt30","lepPt<30"],
                           ] ,
                  baseCut = presel,
                  )





preselMu_8tev = CutClass("preselMu", [], baseCut=None)
preselMu_8tev.add(preselNoMuSel_8tev, cutOpt="inclFlow", baseCutString='')
preselMu_8tev.add(muSelGen_8tev, cutOpt="inclList", baseCutString=preselNoMuSel_8tev.combined)
preselMu_8tev.add(muSelReco_8tev, cutOpt="inclList", baseCutString=muSelGen_8tev.list[-1][1])


preselMu = CutClass("preselMu", [], baseCut=None)
preselMu.add(preselNoMuSel, cutOpt="inclFlow", baseCutString='')
preselMu.add(muSelGen, cutOpt="inclList", baseCutString=preselNoMuSel.combined)
preselMu.add(muSelReco, cutOpt="inclList", baseCutString=muSelGen.list[-1][1])









cutFlow_8tev = CutClass("cutFlow", [], baseCut=None)
cutFlow_8tev.add(presel_8tev, cutOpt="inclFlow", baseCutString='')
cutFlow_8tev.add(sr1_8tev, cutOpt="inclList", baseCutString=presel_8tev.combined)


cutFlow = CutClass("cutFlow", [], baseCut=None)
cutFlow.add(presel, cutOpt="inclFlow", baseCutString='')
cutFlow.add(sr1, cutOpt="inclList", baseCutString=presel.combined)



























###############################################################################################################
##########################################                       ##############################################
##########################################                       ##############################################
##########################################                       ##############################################
###############################################################################################################





mstop = "275"
#dms = [10,40,80]
dms = [10,80]
#dms = range(10,81,10)
mlsps = [ str(int(mstop)-x) for x in dms ]
sampleList_8tev  = [ 's8tev%s_%s'%(mstop, mlsp) for mlsp in mlsps]
sampleList_13tev = [ 's%s_%s'%(mstop, mlsp) for mlsp in mlsps]
#pairList = [[ ['s%s_%s'%(mstop, mlsp), 's8tev%s_%s'%(mstop, mlsp) ] for mlsp in mlsps ]]

mixStops=True
if mixStops:
    new_stops = [ int(mstop)+i*25 for i in [1,2] ]
    for mlsp in mlsps:
        dm = int(mstop) - int(mlsp)
        samples["s%s_%s"%(mstop, mlsp)].name      =  "13TeV#DeltaM(%s)"%dm
        samples["s8tev%s_%s"%(mstop, mlsp)].name =  "8TeV#DeltaM(%s)"%dm
        for new_stop in new_stops:
            new_lsp = new_stop - dm
            samples["s%s_%s"%(mstop, mlsp)]['tree'].Add(samples["s%s_%s"%(new_stop, new_lsp)]['tree']   )
            samples["s8tev%s_%s"%(mstop, mlsp)]['tree'].Add(samples["s8tev%s_%s"%(new_stop, new_lsp)]['tree']   )
    




pairList = [[ ['%s%s_%s'%(x,mstop, max(mlsps)),'%s%s_%s'%(x,mstop, min(mlsps) )] for x in ["s","s8tev"] ] ]

pairList2=[
           [['s275_265', 's275_195'], ['s8tev275_265', 's8tev275_195']],
           [['s275_265', 's8tev275_265'], ['s275_195', 's8tev275_195']]
           ]

#pairList =  [[ ['%s%s_%s'%(x,mstop, mlsps[0] ) for x in ["s","s8tev"] ] ]]
#pairList = [[ ["s8tev275_195","s8tev275_265"], ["s275_195","s275_265"]   ]]

sampleList = sampleList_8tev +sampleList_13tev

#colors = {
#            290: ROOT.kViolet   ,
#            270: ROOT.kBlue   ,
#            250: ROOT.kRed   ,
#            240: ROOT.kOrange   ,
#         }

colorList=[ROOT.kViolet   ,ROOT.kBlue   ,ROOT.kRed   ,ROOT.kOrange   ,]

color_dict ={
                10: ROOT.kBlue     ,
                20: ROOT.kViolet   ,
                30: ROOT.kMagenta   ,
                40: ROOT.kOrange      ,
                50: ROOT.kYellow   ,
                60: ROOT.kGreen   ,
                70: ROOT.kSpring   ,
                80: ROOT.kRed   ,
            }
colors ={
          #int(mlsp):colorList[i] for i,mlsp in enumerate(mlsps)
          int(mlsp):color_dict[int(mstop)-int(mlsp)] for i,mlsp in enumerate(mlsps)
        }


for s in sampleList:
    mstop, mlsp =  limitTools.getMasses(s)
    samples[s]['tree'].SetLineColor(colors[mlsp])
    samples[s]['color'] = colors[mlsp]

    if s in sampleList_8tev:
        samples[s]['tree'].SetLineStyle(3)









def getSamp(mstop,mlsp, samp_dir):
    chain = ROOT.TChain("Events")    
    samp_template = "T2DegStop_{mstop}_{mlsp}"
    hist_template = "histo_T2DegStop_{mstop}_{mlsp}.root"
    samp_file = samp_template + "/" + hist_template
    print samp_dir+"/"+samp_file.format(mstop=mstop, mlsp=mlsp)
    chain.Add(samp_dir+"/"+samp_file.format(mstop=mstop, mlsp=mlsp))
    return chain

    get8TevSample = lambda mstop, mlsp, sample_dir : sample_dir +"/"+"T2DegStop_{mstop}_{mlsp}/histo_T2DegStop_{mstop}_{mlsp}.root".format(mstop=mstop, mlsp=mlsp)


def getYieldRatios(mstop,mlsp, cut="sr1a"):
    cuts = { 
            'sr1a': {13:sr1abc.list[1][1]     ,   8:sr1a_8tev } ,  
            'sr1b': {13:sr1abc.list[2][1]     ,   8:sr1b_8tev } ,  
            'sr1c': {13:sr1abc.list[3][1]     ,   8:sr1c_8tev } ,  
            'sr2': {13:sr2.combined     ,   8:sr2_8tev.combined } ,  
            }
    yld13tev = getYieldFromChain(samples['s%s_%s'%(mstop,mlsp)].tree,      cuts[cut][13], samples['s%s_%s'%(mstop,mlsp)].weight )
    yld8tev  = getYieldFromChain(samples['s8tev%s_%s'%(mstop,mlsp)].tree, cuts[cut][8], samples['s8tev%s_%s'%(mstop,mlsp)].weight )
    return yld13tev, yld8tev, 1.*yld13tev/yld8tev


def getCutYields( samples, sample, cutList , weight="weight" , err=False, nDigits = 3 ):
    yields = []
    weightStr = decide_weight(samples[sample], weight)
    print "Sample %s , using Weight: %s"%(samples[sample].name, weightStr)
    for cut in cutList:
        yld = [ cut[0], getYieldFromChain( samples[sample]['tree'], cut[1], weightStr , returnError=err)]
        if err:
            yld[1]= u_float(yld[1])
            if nDigits: yld[1].round(nDigits)
        yields.append( tuple(yld) )
    return yields




cutInst ={
            "presel":{"8tev": presel_8tev , "13tev":presel} ,
            "sr1":{"8tev": sr1_8tev , "13tev":sr1} ,
            "sr1a":{"8tev": sr1a_8tev , "13tev":sr1a} ,
            "sr1b":{"8tev": sr1b_8tev , "13tev":sr1b} ,
            "sr1c":{"8tev": sr1c_8tev , "13tev":sr1c} ,
            "sr2":{"8tev": sr2_8tev , "13tev":sr2} ,
          }


#pairList= [ [   ['s300_290', 's8tev300_290'] ,['s300_270', 's8tev300_270'] ,['s300_250', 's8tev300_250']     ] ]
#pairList= [[ ['s275_265','s8tev275_265'], ['s275_235','s8tev275_235'], ['s275_215','s8tev275_215']       ]]
#plotList = ['stopsPt']

plotListAll = plotDict.keys()
#plotListAll=["genLepPt"]
plotList2D = [x for x in plotListAll if plotDict[x].has_key("is2D") and plotDict[x]['is2D'] ]
plotList =  [x for x in plotListAll if x not in plotList2D] 
#plotListAll = plotList + plotList2D

if dos['make_plots']:
    tfile = ROOT.TFile(saveDir+"/8TeVSignalComp.root" ,"recreate")
    plts = {}
    plts2 = {}
    plts2d ={} 
    #plotList=['mtBins']
    #plotList=['mtLepPt']
    for cut in cutInst:
        getPlots(samples, plots8tev, cutInst[cut]["8tev"]   , sampleList_8tev,  plotList=plotListAll, weight="weight" )
        getPlots(samples, plots,     cutInst[cut]["13tev"]  , sampleList_13tev, plotList=plotListAll, weight="weight" )
        #plts[cut] = drawPlots(samples, plots, cutInst[cut]["13tev"] , sampleList=sampleList , plotList = plotList, save=saveDir,  normalize=False, fom="RATIO", denoms=None, noms=None , pairList=pairList  , fomLimits=[0,3], fomTitle="Ratios (13TeV/8TeV) ", plotMin=0.001)
        ## two ratio pads, Signle ratios 13/8 and dm10/dm30

        if plotList:
            plts[cut] = drawPlots(samples, plots, cutInst[cut]["13tev"] , sampleList=sampleList , plotList = plotList, save=saveDir,  normalize=False, fom="RATIO", denoms=None, noms=None , pairList=pairList2  , fomLimits=[0,2], fomTitles=["dm10/dm80", "13Tev/8TeV"], plotMin=0.001)

            # one ratio pad, to use for double ratio plot .... (not the smartest way) 
            plts[cut] = drawPlots(samples, plots, cutInst[cut]["13tev"] , sampleList=sampleList , plotList = plotList, save=False,  normalize=False, fom="RATIO", denoms=None, noms=None , pairList=pairList  , fomLimits=[], fomTitles="Ratios (dm10/dm80)", plotMin=0.001)

            for plot in plotList:    
                plts[cut]['hists'][sampleList_13tev[0] ][plot]=plts[cut]['fomHists'][plot][tuple(pairList[0][0])]
                plts[cut]['hists'][sampleList_8tev[0]  ][plot]=plts[cut]['fomHists'][plot][tuple(pairList[0][1])]
                getFOMPlotFromStacksPair(plts[cut], plot, [sampleList_13tev[0] ,sampleList_8tev[0] ] , fom="RATIO", pairList=[[ [sampleList_13tev[0] ,sampleList_8tev[0]] ]], fomTitles=["(dm10/dm80)13Tev/8TeV"] , fomLimits=[0,5])
                saveCanvas( plts[cut]['canvs'][plot][0], saveDir+"/%s/"%cutInst[cut]["13tev"].saveDir   , "DoubleRatio_"+plot, formats=["png"], extraFormats=[] )
        
        if plotList2D:
            plts2d=draw2DPlots(samples, plots, cutInst[cut]['13tev'], sampleList=sampleList, plotList=plotList2D, save=saveDir, leg=False)

     
    tfile.Write()


if dos['get_yields']:
    ##### Yields
    tableDir= saveDir+"/Tables"
    makeDir(tableDir)
    
    ylds={}
    yld={}
    for cut in cutInst:
        ylds[cut]={}
        ylds[cut][8] = Yields(samples, sampleList_8tev ,  cutInst[cut]['8tev'], cutOpt='flow2', nSpaces=5, pklOpt=False, verbose=True )
        ylds[cut][13] = Yields(samples, sampleList_13tev ,cutInst[cut]['13tev'], cutOpt='flow2', nSpaces=5, pklOpt=False, verbose=True )
        yld[cut] = ylds[cut][8]
        yld[cut].fomNames.update( ylds[cut][13].fomNames) ## stupid workaround due to the updateSampleList
        yld[cut].addYieldDict(samples,  ylds[cut][13].yieldDict )
    
    
    import pprint as pp
    tables  = {} 
    for cut in cutInst:
        print "---------------------------------" ,cutInst[cut]['13tev'].name
        c= yld[cut]
        tables[cut] = c.pprint(c.makeNumpyFromDict( c.yieldDict), ret=True)



if dos['muSel']:

    sampleList_8tev = [x for x in samples.keys() if all( [tag in samples[x]['name'] for tag in ['8TeV', 'Delta']] )]
    sampleList_13tev = [x for x in samples.keys() if all( [tag in samples[x]['name'] for tag in ['13TeV', 'Delta']] )]
   

    yld8tev = Yields(samples, sampleList_8tev, preselMu_8tev, cutOpt='inclList', tableName="{cut}_8TeV", verbose=True)
    yld13tev = Yields(samples, sampleList_13tev, preselMu, cutOpt='inclList', tableName="{cut}_13TeV", verbose=True)




    sample_map_8to13= {x:x.replace("s8tev","s")  for x in sampleList_8tev  } 


    #yld13tev.pprint()


