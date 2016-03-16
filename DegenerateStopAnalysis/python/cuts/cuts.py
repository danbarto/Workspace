import math
from Workspace.DegenerateStopAnalysis.navidTools.NavidTools import CutClass, joinCutStrings, splitCutInPt


## --------------------------------------------------------------
##                           Variables
## --------------------------------------------------------------

less = lambda var,val: "(%s < %s)"%(var,val)
more = lambda var,val: "(%s > %s)"%(var,val)
btw = lambda var,minVal,maxVal: "(%s > %s && %s < %s)"%(var, min(minVal,maxVal), var, max(minVal,maxVal))
minAngle = lambda phi1, phi2 : "TMath::Min( (2*pi) - abs({phi1}-{phi2}) , abs({phi1}-{phi2}) )".format(phi1=phi1,phi2=phi2)  


## --------------------------------------------------------------
##                            CUT LISTS
## --------------------------------------------------------------




preselOnly1Mu = CutClass ("preselOnly1Mu", [
                              ["MET200","met>200"],
                              ["ISR110","nJet110>=1" ],
                              #["HT300","htJet30j>300"],
                              ["HT200","htJet30j>200"],
                              #["2ndJetPt60","nJet60<=2 "],
                              ["AntiQCD", "deltaPhi_j12 < 2.5" ], #,  monojet
                              ["singleMu",    "nlep==1"  ],
                            ] ,
                baseCut=None,
                ) 

preselNoMuSel = CutClass ("presel", [
                              ["MET200","met>200"],
                              ["ISR110","nJet110>=1" ],
                              ["HT300","htJet30j>300"],
                              ["AntiQCD", " (deltaPhi_j12 < 2.5)" ], # monojet
                             ],
                baseCut=None,
                )
muSel       = CutClass("muSel", [
                            ["presel(noMuSel)","(1)"],
                            ["oneMuon", 'Sum$(((abs(LepGood_pdgId)==13)))==1'],
                            ["pt_gt_5", 'Sum$(((abs(LepGood_pdgId)==13) && ((LepGood_pt > 5))))==1'],
                            ["eta2.4", 'Sum$(((abs(LepGood_pdgId)==13) && ((LepGood_pt > 5)) ))==1'],
                            ["dz0.2_dxy0.05", 'Sum$(((abs(LepGood_pdgId)==13) && ((LepGood_pt > 5))  && (abs(LepGood_eta)<2.4) && (abs(LepGood_dz)<0.2) && (abs(LepGood_dxy)<0.05)))==1'],
                            ["sip3d4", 'Sum$(((abs(LepGood_pdgId)==13) && ((LepGood_pt > 5))  && (abs(LepGood_eta)<2.4) && (abs(LepGood_dz)<0.2) && (abs(LepGood_dxy)<0.05) && ((LepGood_sip3d < 4))))==1'],
                            ["hybIso", 'Sum$(((abs(LepGood_pdgId)==13) && ((LepGood_pt > 5))  && (abs(LepGood_eta)<2.4) && (abs(LepGood_dz)<0.2) && (abs(LepGood_dxy)<0.05) && ((LepGood_sip3d < 4)) && ((((LepGood_pt >= 25) && (LepGood_relIso04 < 0.2) ) || ( (LepGood_pt < 25) && (( LepGood_pt*LepGood_relIso04 ) < 5))))))==1'],
                            ["medMuId", 'Sum$(((abs(LepGood_pdgId)==13) && ((LepGood_pt > 5))  && (abs(LepGood_eta)<2.4) && (abs(LepGood_dz)<0.2) && (abs(LepGood_dxy)<0.05) && ((LepGood_sip3d < 4)) && ((((LepGood_pt >= 25) && (LepGood_relIso04 < 0.2) ) || ( (LepGood_pt < 25) && (( LepGood_pt*LepGood_relIso04 ) < 5)))) && (LepGood_mediumMuonId==1)))==1'],
                            ],
                    baseCut=preselNoMuSel
                )



presel = CutClass ("presel", [
                              ["MET200","met>200"],
                              ["ISR110","nJet110>=1" ],
                              ["HT300","htJet30j>300"],
                              ["AntiQCD", " (deltaPhi_j12 < 2.5)" ], # monojet
                              #
                              ["nMuon>=1",    "nlep>=1 "  ], ## Add 2ndMu Veto Here
                              ["2ndMu20Veto", "(nlep==1 || nlep ==2 && LepGood_pt[looseMuonIndex2] < 20)"],
                              #["nMuon==1",    "nlep==1 "  ], ## Very Small Difference
                              ["No3rdJet60","nJet60<=2"]
                             ],
                baseCut=None,
                )
 
preselection = presel.combined


#2ndMuVeto = "nlep==1 ||" + 'Sum$(  \
#                    (abs(LepGood_pdgId)==13) && ((LepGood_pt > 5)) && (LepGood_pt < 30) && (abs(LepGood_eta)<2.4) && \
#                    (abs(LepGood_dz)<0.2) && (abs(LepGood_dxy)<0.05) && ((LepGood_sip3d < 4)) && (((LepGood_pt >= 25) \
#                 && (LepGood_relIso04 < 0.2) ) || ( (LepGood_pt < 25) && (( LepGood_pt*LepGood_relIso04 ) < 5))) && (LepGood_mediumMuonId==1))==1'


sr1   = CutClass ("SR1",    [
                              ["MuPt30","lepPt<30"],
                              ["negMuon","lepPdgId==13"],
                              ["MuEta1.5","abs(lepEta)<1.5"],
                              ["BVeto","(nSoftBJetsCSV == 0 && nHardBJetsCSV ==0)"],
                              ["CT300","min(met,htJet30j-100) > 300 "],
                              #["HT400","htJet30j>400"],
                              #["met300","met>300"],
                           ] , 
                  baseCut = presel,
                  )


mtabc   = CutClass ("MTabc",    [
                               ["MTa","mt<60"],
                               ["MTb",btw("mt",60,88)],
                               ["MTc","mt>88"],
                           ] , 
                  baseCut = sr1,
                  )


mtabc_pt = splitCutInPt(mtabc)



sr1Loose   = CutClass ("sr1Loose",    [
                              ["BVeto","(nSoftBJetsCSV == 0 && nHardBJetsCSV ==0)"],
                              ["MuPt30","lepPt<30"],
                              ["negMuon","lepPdgId==13"],
                              ["MuEta2.4","abs(lepEta)<2.4"],
                              #["met300","met>300"],
                              #["HT400","htJet30j>400"],
                           ] , 
                  baseCut = presel,
                  )


sr1abc_ptbin   = CutClass ("SR1abc_PtBinned",    [
                               #["SR1a","mt<60"],
                                  ["SRL1a",joinCutStrings(   ["mt<60",         btw("lepPt",5,12)]  )],
                                  ["SRH1a",joinCutStrings(   ["mt<60",         btw("lepPt",12,20)] )],
                                  ["SRV1a",joinCutStrings(   ["mt<60",         btw("lepPt",20,30)] )],
                               #["SR1b",btw("mt",60,88)],
                                  ["SRL1b",joinCutStrings(   [btw("mt",60,88), btw("lepPt",5,12)]  )],
                                  ["SRH1b",joinCutStrings(   [btw("mt",60,88), btw("lepPt",12,20)] )],
                                  ["SRV1b",joinCutStrings(   [btw("mt",60,88), btw("lepPt",20,30)] )],
                               #["SR1c","mt>88"],
                                  ["SRL1c",joinCutStrings(   ["mt>88",         btw("lepPt",5,12)]  )],
                                  ["SRH1c",joinCutStrings(   ["mt>88",         btw("lepPt",12,20)] )],
                                  ["SRV1c",joinCutStrings(   ["mt>88",         btw("lepPt",20,30)] )],
                           ] , 
                  baseCut = sr1,
                  )

sr1abc   = CutClass ("sr1abc",    [
                               ["SR1a","mt<60"],
                               ["SR1b",btw("mt",60,88)],
                               ["SR1c","mt>88"],
                           ] , 
                  baseCut = sr1,
                  )



  
sr2      = CutClass ("SR2",   [ 
                                ["ISR325","nJet325>0"],
                                ["OneOrMoreSoftB","nSoftBJetsCSV>=1"],
                                ["noHardB","nHardBJetsCSV==0"],
                                [" MuPt<30","lepPt<30"],
                              ],
                  baseCut = presel,
                  )


sr2_ptbin   = CutClass ("SR2_PtBinned",    [
                                  ["SRL2",  btw("lepPt",5,12)    ],
                                  ["SRH2",  btw("lepPt",12,20)   ],
                                  ["SRV2",  btw("lepPt",20,30)   ],
                           ] , 
                  baseCut = sr2,
                  )

################################################################################################
####################################                 ###########################################
#################################### Control Regions ###########################################
####################################                 ###########################################
################################################################################################




cr1Loose    = CutClass ( "cr1Loose", [
                          ["MuPt30","lepPt>30"],
                          ["negMuon","lepPdgId==13"],
                          ["MuEta1.5","abs(lepEta)<1.5"],
                          ["BVeto","(nSoftBJetsCSV == 0 && nHardBJetsCSV ==0)"],
                    ],
                    baseCut= presel,
                )


crtt2    = CutClass ( "CRTT2", [
                      ["CRTT2","( (nSoftBJetsCSV + nHardBJetsCSV) > 1 ) && ( nHardBJetsCSV > 0  )"],
                             ],
                    baseCut= presel ,
                )

cr1   = CutClass ("CR1",    [
                              ["MuPt_gt_30","lepPt>30"],
                              ["negMuon","lepPdgId==13"],
                              ["MuEta1.5","abs(lepEta)<1.5"],
                              ["BVeto","(nSoftBJetsCSV == 0 && nHardBJetsCSV ==0)"],
                              #["BVeto_Medium25","nBJetMedium25==0"],
                              ["CT300","min(met,htJet30j-100) > 300 "],
                              #["HT400 ","htJet30j>400"],
                              #["met300","met>300"],
                           ] , 
                  baseCut = presel,
                  )


cr1abc   = CutClass ("CR1abc",    [
                               ["CR1a", "mt<60"],
                               ["CR1b", btw("mt",60,88)],
                               ["CR1c", "mt>88"],
                           ] , 
                  baseCut = cr1,
                  )



cr2      = CutClass ("CR2",   [
                                ["Jet325","nJet325>0"],
                                #["met300","met>300"],
                                ["OneOrMoreSoftB","nSoftBJetsCSV>=1"],
                                ["noHardB","nHardBJetsCSV==0"],
                                ["MuPt_gt_30","lepPt>30"],
                              ],
                  baseCut = presel,
                  )
cr2_      = CutClass( "CR2", [ ["CR2", "(1)"] ],
                    baseCut = cr2
                    ) 



runI        =   CutClass( "Reload" , [] , baseCut = presel )
runI.add(   sr1abc_ptbin    , baseCutString = sr1.inclCombined )
runI.add(   sr2_ptbin       , baseCutString = sr2.inclCombined ) 
runI.add(   cr1abc          , baseCutString = cr1.inclCombined )
runI.add(   cr2_             , baseCutString = cr2.inclCombined ) 
runI.add(   crtt2        ) 




runIflow   =    CutClass( "RunIFlow", [], baseCut = None)
runIflow.add( presel, 'flow', baseCutString = None)
runIflow.add( sr1, 'inclFlow', baseCutString = presel.combined)
runIflow.add( sr2, 'inclFlow', baseCutString = presel.combined)
