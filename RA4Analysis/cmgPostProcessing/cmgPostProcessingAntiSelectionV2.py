import ROOT
import pickle
import sys, os, copy, random, subprocess, datetime
from array import array
from Workspace.RA4Analysis.cmgObjectSelection import *
from Workspace.HEPHYPythonTools.xsec import xsec
from Workspace.HEPHYPythonTools.helpers import getObjFromFile, getObjDict, getFileList, deltaR, deltaPhi, deltaR2
from Workspace.HEPHYPythonTools.convertHelpers import compileClass, readVar, printHeader, typeStr, createClassString

from math import *
from Workspace.HEPHYPythonTools.user import username

ROOT.gROOT.ProcessLine(".L ../../HEPHYPythonTools/scripts/root/WPolarizationVariation.C+")
ROOT.gROOT.ProcessLine(".L ../../HEPHYPythonTools/scripts/root/TTbarPolarization.C+")
ROOT.gSystem.Load("libFWCoreFWLite.so")
ROOT.AutoLibraryLoader.enable()

from Workspace.HEPHYPythonTools.helpers import getChunks

from Workspace.RA4Analysis.cmgTuples_Spring16_MiniAODv2 import *
from Workspace.RA4Analysis.cmgTuples_Data25ns_PromptRecoV2 import *


from btagEfficiency import *
from readVetoEventList import *
from systematics_helper import calc_btag_systematics, calc_LeptonScale_factors_and_systematics, calc_TopPt_Weights , calcDLDictionary, calc_diLep_contributions , fill_branch_WithJEC

bTagEffFile     = '/data/dspitzbart/Spring16/btagEfficiency/effs_presel_JECv6_pkl'
scaleFactorDir  = '$CMSSW_BASE/src/Workspace/RA4Analysis/cmgPostProcessing/data/'

try:
  mcEffDict = pickle.load(file(bTagEffFile))
except IOError:
  print 'Unable to load MC efficiency file!'
  mcEffDict = False

target_lumi = 3000 #pb-1

separateBTagWeights = True

defSampleStr = "TTJets_LO_HT600to800_25ns"

#subDir = "postProcessed_Spring16_antiSelection_3fb_v2"
subDir = "postProcessing_Run2016BCD_antiSelection"

#branches to be kept for data and MC
branchKeepStrings_DATAMC = ["run", "lumi", "evt", "isData", "rho", "nVert",
                     "nJet25", "nBJetLoose25", "nBJetMedium25", "nBJetTight25", "nJet40", "nJet40a", "nBJetLoose40", "nBJetMedium40", "nBJetTight40", 
                     "nLepGood20", "nLepGood15", "nLepGood10", "htJet25", "mhtJet25", "htJet40j", "htJet40", "mhtJet40", 
                     "met*","Flag_*","HLT_*",
#                     "nFatJet","FatJet_*", 
                     "nJet", "Jet_*", 
                     "nLepGood", "LepGood_*", 
                     "nLepOther", "LepOther_*", 
                     "nTauGood", "TauGood_*",
                     ] 

#branches to be kept for MC samples only
branchKeepStrings_MC = [ "nTrueInt", "genWeight", "xsec", "puWeight", 
                     "GenSusyMScan1", "GenSusyMScan2", "GenSusyMScan3", "GenSusyMScan4", "GenSusyMGluino", "GenSusyMGravitino", "GenSusyMStop", "GenSusyMSbottom", "GenSusyMStop2", "GenSusyMSbottom2", "GenSusyMSquark", "GenSusyMNeutralino", "GenSusyMNeutralino2", "GenSusyMNeutralino3", "GenSusyMNeutralino4", "GenSusyMChargino", "GenSusyMChargino2", 
                     "ngenLep", "genLep_*", 
                     "nGenPart", "GenPart_*",
                     "ngenTau", "genTau_*", 
                     "ngenLepFromTau", "genLepFromTau_*"]

#branches to be kept for data only
branchKeepStrings_DATA = []

from optparse import OptionParser
parser = OptionParser()
parser.add_option("--samples", dest="allsamples", default=defSampleStr, type="string", action="store", help="samples:Which samples.")
parser.add_option("--inputTreeName", dest="inputTreeName", default="treeProducerSusySingleLepton", type="string", action="store", help="samples:Which samples.")
parser.add_option("--targetDir", dest="targetDir", default="/afs/hephy.at/data/"+username+"01/cmgTuples/"+subDir+'/', type="string", action="store", help="target directory.")
parser.add_option("--skim", dest="skim", default="", type="string", action="store", help="any skim condition?")
parser.add_option("--leptonSelection", dest="leptonSelection", default="hard", type="string", action="store", help="which lepton selection? 'soft', 'hard', 'none', 'dilep'?")
parser.add_option("--small", dest="small", default = False, action="store_true", help="Just do a small subset.")
parser.add_option("--overwrite", dest="overwrite", default = False, action="store_true", help="Overwrite?")
parser.add_option("--calcbtagweights", dest="systematics", default = False, action="store_true", help="Calculate b-tag weights for systematics?")
parser.add_option("--btagWeight", dest="btagWeight", default = 2, action="store", help="Max nBJet to calculate the b-tag weight for")
parser.add_option("--hadronicLeg", dest="hadronicLeg", default = False, action="store_true", help="Use only the hadronic leg of the sample?")
parser.add_option("--manScaleFactor", dest="manScaleFactor", default = 1, action="store", help="define a scale factor for the whole sample")

(options, args) = parser.parse_args()
assert options.leptonSelection in ['soft', 'hard', 'none', 'dilep'], "Unknown leptonSelection: %s"%options.leptonSelection
skimCond = "(1)"
ht500 = "Sum$(Jet_pt)>500"
common_skim = 'HT500'
if options.skim.startswith('met'):
  skimCond = "met_pt>"+str(float(options.skim[3:]))
if options.skim=='HT400':
  skimCond = "Sum$(Jet_pt)>400"
if options.skim=='HT400ST200':   ##tuples have already ST200 skim
  skimCond = "Sum$(Jet_pt)>400&&(LepGood_pt[0]+met_pt)>200"
if options.skim=='HT500':  
  skimCond = ht500
if options.skim=='LHEHT600':
  skimCond = "lheHTIncoming>600"
if options.skim=='LHEHTsm600':
  skimCond = "lheHTIncoming<=600&&"+ht500
if options.skim=='LHEHTlg600':
  skimCond = "lheHTIncoming>600&&"+ht500


####dilep skim##
if options.skim=='diLep':
  skimCond = "((ngenLep+ngenTau)==2)&&lheHTIncoming<=1000"#+ht500
###semilep skim###
if options.skim=='semiLep':
  skimCond = "((ngenLep+ngenTau)==1)&&lheHTIncoming<=1000"#+ht500
###Full hadronic###
if options.skim=='LHE_FullHadronic_inc':
  skimCond = "((ngenLep+ngenTau)==0)&&lheHTIncoming<=600"#+ht500
###Full hadronic for the ht binned###
if options.skim=='LHE_FullHadronic': 
  skimCond = "lheHTIncoming>600&&lheHTIncoming<=1000&&((ngenLep+ngenTau)==0)"#+ht500
###Full inclusive for high HT
if options.skim=='LHEHT1000':
  skimCond = "lheHTIncoming>1000"#+ht500

##In case a lepton selection is required, loop only over events where there is one 
if options.leptonSelection.lower()=='none':
  #skimCond += "&&Sum$(LepGood_pt>10&&abs(LepGood_eta)<2.5)>=1"
  #skimCond += "&&(nLepGood+nLepOther)>=1"
  skimCond += "&&(1)"
if options.leptonSelection.lower()=='soft':
  #skimCond += "&&Sum$(LepGood_pt>5&&LepGood_pt<25&&LepGood_relIso03<0.4&&abs(LepGood_eta)<2.4)>=1"
  skimCond += "&&Sum$(LepGood_pt>5&&LepGood_pt<25&&abs(LepGood_eta)<2.4)>=1"
if options.leptonSelection.lower()=='hard':
  #skimCond += "&&Sum$(LepGood_pt>25&&LepGood_relIso03<0.4&&abs(LepGood_eta)<2.4)>=1"
  skimCond += "&&Sum$(LepGood_pt>25&&abs(LepGood_eta)<2.5)>=0"
if options.leptonSelection.lower()=='dilep':
  #skimCond += "&&Sum$(LepGood_pt>25&&LepGood_relIso03<0.4&&abs(LepGood_eta)<2.4)>=1"
  skimCond += "&&Sum$(LepGood_pt>15&&abs(LepGood_eta)<2.4)>1"

if options.hadronicLeg:
  skimCond += "&&(nGenLep+nGenTau)==0"

if options.manScaleFactor!=1:
  targetlumi = targetlumi*options.manScaleFactor

if options.skim=='inc':
  skimCond = "(1)"

if sys.argv[0].count('ipython'):
  options.small=True

####get evt Veto List  for filters####
#evt_veto_list = evt_veto_list()

###For PU reweight###
PU_dir = "/data/easilar/PU_Histos/"
PU_File_59p85mb = ROOT.TFile(PU_dir+"/h_ratio_59p85.root")
PU_File_63mb = ROOT.TFile(PU_dir+"/h_ratio_63.root")
PU_File_66p15mb = ROOT.TFile(PU_dir+"/h_ratio_66p15.root")
PU_histo_59p85 = PU_File_59p85mb.Get("h_ratio")
PU_histo_63 = PU_File_63mb.Get("h_ratio")
PU_histo_66p15 = PU_File_66p15mb.Get("h_ratio")
#####################

###For Lepton SF#####
mu_mediumID_File  = ROOT.TFile(scaleFactorDir+'TnP_MuonID_NUM_MediumID_DENOM_generalTracks_VAR_map_pt_eta.root')
mu_looseID_File   = ROOT.TFile(scaleFactorDir+'TnP_MuonID_NUM_LooseID_DENOM_generalTracks_VAR_map_pt_eta.root')
mu_miniIso02_File = ROOT.TFile(scaleFactorDir+'TnP_MuonID_NUM_MiniIsoTight_DENOM_MediumID_VAR_map_pt_eta.root')
mu_sip3d_File     = ROOT.TFile(scaleFactorDir+'TnP_MuonID_NUM_TightIP3D_DENOM_MediumID_VAR_map_pt_eta.root')
mu_HIP_File       = ROOT.TFile(scaleFactorDir+'general_tracks_and_early_general_tracks_corr_ratio.root')
ele_kin_File      = ROOT.TFile(scaleFactorDir+'eleScaleFactors.root')
ele_gsf_File      = ROOT.TFile(scaleFactorDir+'egammaEffi_txt_SF2D.root')
#
histos_LS = {
'mu_mediumID_histo':  mu_mediumID_File.Get("pt_abseta_PLOT_pair_probeMultiplicity_bin0"),\
'mu_looseID_histo':   mu_looseID_File.Get("pt_abseta_PLOT_pair_probeMultiplicity_bin0"),\
'mu_miniIso02_histo': mu_miniIso02_File.Get("pt_abseta_PLOT_pair_probeMultiplicity_bin0_&_Medium2016_pass"),\
'mu_sip3d_histo':     mu_sip3d_File.Get("pt_abseta_PLOT_pair_probeMultiplicity_bin0_&_Medium2016_pass"),\
'mu_HIP_histo':       mu_HIP_File.Get("mutrksfptg10"),\
'ele_cutbased_histo': ele_kin_File.Get("GsfElectronToTight"),\
'ele_miniIso01_histo':ele_kin_File.Get("MVAVLooseElectronToMini"),\
'ele_gsf_histo':      ele_gsf_File.Get("EGamma_SF2D"),\
}
#####################


maxConsideredBTagWeight = options.btagWeight
calcSystematics = options.systematics

def getTreeFromChunk(c, skimCond, iSplit, nSplit):
  if not c.has_key('file'):return
  rf = ROOT.TFile.Open(c['file'])
  assert not rf.IsZombie()
  rf.cd()
  tc = rf.Get("tree")
  nTot = tc.GetEntries()
  fromFrac = iSplit/float(nSplit)
  toFrac   = (iSplit+1)/float(nSplit)
  start = int(fromFrac*nTot)
  stop  = int(toFrac*nTot)
  ROOT.gDirectory.cd('PyROOT:/')
  print "Copy tree from source: total number of events found:",nTot,"Split counter: ",iSplit,"<",nSplit,"first Event:",start,"nEvents:",stop-start
  t = tc.CopyTree(skimCond,"",stop-start,start)
  tc.Delete()
  del tc
  rf.Close()
  del rf
  return t
   
exec('allSamples=['+options.allsamples+']')
for isample, sample in enumerate(allSamples):
  #chunks, sumWeight = getChunks(sample, options.inputTreeName)
  chunks, sumWeight = getChunks(sample)
  #chunks, nTotEvents = getChunksFromDPM(sample, options.inputTreeName)
#  print "Chunks:" , chunks 
  targetDir = options.targetDir
  if sample.has_key('outDirOption'): outDir = targetDir+"/".join([common_skim, sample['name']+sample['outDirOption']])
  else: outDir = targetDir+"/".join([common_skim, sample['name']])
  #outDir = options.targetDir+'/'+"/".join([options.skim, options.leptonSelection, sample['name']])
  if os.path.exists(outDir) and os.listdir(outDir) != [] and not options.overwrite:
    print "Found non-empty directory: %s -> skipping!"%outDir
    continue

  tmpDir = outDir+'/tmp/'
  os.system('mkdir -p ' + outDir) 
  os.system('mkdir -p '+tmpDir)
  os.system('rm -rf '+tmpDir+'/*')
  
  if sample['isData']: 
    lumiScaleFactor=1
    branchKeepStrings = branchKeepStrings_DATAMC + branchKeepStrings_DATA 
  else:
    #if "TTJets" in sample['dbsName']: lumiScaleFactor = xsec[sample['dbsName']]*target_lumi/float(sumWeight)
    #else:
    lumiScaleFactor = target_lumi/float(sumWeight)
    branchKeepStrings = branchKeepStrings_DATAMC + branchKeepStrings_MC
  
  readVariables = ['met_pt/F', 'met_phi/F']
  newVariables = ['weight/F', 'muonDataSet/I', 'eleDataSet/I']#, 'veto_evt_list/I/1']
  aliases = [ "met:met_pt", "metPhi:met_phi"]

  readVectors = [\
    {'prefix':'LepGood', 'nMax':8, 'vars':['pt/F', 'eta/F', 'phi/F', 'pdgId/I', 'relIso03/F','SPRING15_25ns_v1/I','eleCBID_SPRING15_25ns/I', 'eleCBID_SPRING15_25ns_ConvVetoDxyDz/I', 'tightId/I', 'miniRelIso/F','mass/F','sip3d/F','mediumMuonId/I', 'ICHEPmediumMuonId/I', 'mvaIdSpring15/F','lostHits/I', 'convVeto/I', 'charge/I', 'hOverE/F']},
    {'prefix':'LepOther', 'nMax':8, 'vars':['pt/F', 'eta/F', 'phi/F', 'pdgId/I', 'relIso03/F','eleCBID_SPRING15_25ns/I', 'eleCBID_SPRING15_25ns_ConvVetoDxyDz/I' ,'tightId/I', 'miniRelIso/F','mass/F','sip3d/F','mediumMuonId/I', 'ICHEPmediumMuonId/I', 'lostHits/I', 'convVeto/I', 'charge/I', 'hOverE/F']},
    {'prefix':'Jet',  'nMax':100, 'vars':['pt/F', 'eta/F', 'phi/F', 'id/I','btagCSV/F', 'btagCMVA/F']},
  ]
  if not sample['isData']: 
    readVectors.append({'prefix':'GenPart', 'nMax':100, 'vars':['eta/F','pt/F','phi/F','mass/F','charge/F', 'pdgId/I', 'motherId/F', 'grandmotherId/F']})
    newVariables.extend(['puReweight_true/F', 'puReweight_true_max4/F','puReweight_true_Down/F','puReweight_true_Up/F', 'weight_XSecTTBar1p1/F','weight_XSecTTBar0p9/F','weight_WPolPlus10/F', 'weight_WPolMinus10/F', 'weight_TTPolPlus5/F', 'weight_TTPolMinus5/F'])
    newVariables.extend(['GenTopPt/F/-999.','GenAntiTopPt/F/-999.','TopPtWeight/F/1.','GenTTBarPt/F/-999.','GenTTBarWeight/F/1.','nGenTops/I/0.'])
    aliases.extend(['genMet:met_genPt', 'genMetPhi:met_genPhi'])
    #readVectors[1]['vars'].extend('partonId/I')
  if options.leptonSelection.lower() in ['soft', 'hard']:
    newVariables.extend( ['nLooseSoftLeptons/I', 'nLooseHardLeptons/I', 'nTightSoftLeptons/I', 'nTightHardLeptons/I' ])
    newVariables.extend( ['deltaPhi_Wl/F', 'Lp/F', 'Lt/F', 'nBJetMediumCSV30/I','nJet30/I','htJet30j/F', 'st/F', 'leptonPt/F','leptonMiniRelIso/F','leptonRelIso03/F' ,'leptonEta/F', 'leptonPhi/F', 'leptonSPRING15_25ns_v1/I/-2', 'leptonPdg/I/0', 'leptonInd/I/-1', 'leptonMass/F', 'singleMuonic/I', 'singleElectronic/I', 'singleLeptonic/I', 'lslJet80/I' ]) #, 'mt2w/F'] )
  if options.leptonSelection.lower() == 'none':
    newVariables.extend( ['nLep/I', 'nVeto/I', 'nTightLep/I', 'nTightEl/I', 'nTightMu/I', 'nEl/I', 'nMu/I', 'Selected/I'] )
    newVariables.extend( ['deltaPhi_Wl/F', 'Lp/F', 'Lt/F', 'nBJetMediumCSV30/I','nJet30clean/I','htJet30clean/F', 'st/F', 'leptonPt/F','leptonMiniRelIso/F','leptonRelIso03/F' ,'leptonEta/F', 'leptonPhi/F', 'leptonPdg/I', 'leptonInd/I', 'leptonMass/F','leptonHoverE/F', 'leptonEt/F', 'lslJet80/I', 'Jet1_pt/F', 'Jet2_pt/F', 'nJet30nonClean/I', 'htJet30nonClean/F', 'singleMuonic/I', 'singleElectronic/I', 'singleLeptonic/I' ]) #, 'mt2w/F'] )
    newVariables.extend( ['lepton_muSF_HIP/D/1.','lepton_muSF_looseID/D/1.','lepton_muSF_mediumID/D/1.','lepton_muSF_miniIso02/D/1.','lepton_muSF_sip3d/D/1.','lepton_eleSF_cutbasedID/D/1.','lepton_eleSF_miniIso01/D/1.', 'lepton_eleSF_gsf/D/1.'])
    newVariables.extend( ['lepton_muSF_HIP_err/D/0.','lepton_muSF_looseID_err/D/0.','lepton_muSF_mediumID_err/D/0.','lepton_muSF_miniIso02_err/D/0.','lepton_muSF_sip3d_err/D/0.','lepton_eleSF_cutbasedID_err/D/0.','lepton_eleSF_miniIso01_err/D/0.', 'lepton_eleSF_gsf_err/D/0.', 'lepton_muSF_systematic/D/0.'])

    if calcSystematics:
      #newVariables.extend( ["weightBTag/F", "weightBTag_SF/F", "weightBTag_SF_b_Up/F", "weightBTag_SF_b_Down/F", "weightBTag_SF_light_Up/F", "weightBTag_SF_light_Down/F"])
      for i in range(maxConsideredBTagWeight+1):
        newVariables.extend( ["weightBTag"+str(i)+"/F/1", "weightBTag"+str(i)+"_SF/F/1", "weightBTag"+str(i)+"_SF_b_Up/F/1", "weightBTag"+str(i)+"_SF_b_Down/F/1", "weightBTag"+str(i)+"_SF_light_Up/F/1", "weightBTag"+str(i)+"_SF_light_Down/F/1"])
        #if i>0:
        newVariables.extend( ["weightBTag"+str(i+1)+"p/F/1", "weightBTag"+str(i+1)+"p_SF/F/1", "weightBTag"+str(i+1)+"p_SF_b_Up/F/1", "weightBTag"+str(i+1)+"p_SF_b_Down/F/1", "weightBTag"+str(i+1)+"p_SF_light_Up/F/1", "weightBTag"+str(i+1)+"p_SF_light_Down/F/1"])

  newVars = [readVar(v, allowRenaming=False, isWritten = True, isRead=False) for v in newVariables]
  
  readVars = [readVar(v, allowRenaming=False, isWritten=False, isRead=True) for v in readVariables]
  for v in readVectors:
    readVars.append(readVar('n'+v['prefix']+'/I', allowRenaming=False, isWritten=False, isRead=True))
    v['vars'] = [readVar(v['prefix']+'_'+vvar, allowRenaming=False, isWritten=False, isRead=True) for vvar in v['vars']]

  printHeader("Compiling class to write")
  writeClassName = "ClassToWrite_"+str(isample)
  writeClassString = createClassString(className=writeClassName, vars= newVars, vectors=[], nameKey = 'stage2Name', typeKey = 'stage2Type')
#  print writeClassString
  s = compileClass(className=writeClassName, classString=writeClassString, tmpDir='/data/'+username+'/tmp/')

  readClassName = "ClassToRead_"+str(isample)
  readClassString = createClassString(className=readClassName, vars=readVars, vectors=readVectors, nameKey = 'stage1Name', typeKey = 'stage1Type', stdVectors=False)
  printHeader("Class to Read")
#  print readClassString
  r = compileClass(className=readClassName, classString=readClassString, tmpDir='/data/'+username+'/tmp/')

  filesForHadd=[]
  if options.small: chunks=chunks[:1]
  #print "CHUNKS:" , chunks
  for chunk in chunks:
    sourceFileSize = os.path.getsize(chunk['file'])
    nSplit = 1+int(sourceFileSize/(200*10**6)) #split into 200MB
    if nSplit>1: print "Chunk too large, will split into",nSplit,"of appox 200MB"
    for iSplit in range(nSplit):
      cut = "("+skimCond+")&&("+sample['postProcessingCut']+")" if sample.has_key('postProcessingCut') else skimCond
      t = getTreeFromChunk(chunk, cut, iSplit, nSplit)
      if not t: 
        print "Tree object not found:", t
        continue
      t.SetName("Events")
      nEvents = t.GetEntries()
      for v in newVars:
#        print "new VAR:" , v
        v['branch'] = t.Branch(v['stage2Name'], ROOT.AddressOf(s,v['stage2Name']), v['stage2Name']+'/'+v['stage2Type'])
      for v in readVars:
#        print "read VAR:" , v
        t.SetBranchAddress(v['stage1Name'], ROOT.AddressOf(r, v['stage1Name']))
      for v in readVectors:
        for var in v['vars']:
          t.SetBranchAddress(var['stage1Name'], ROOT.AddressOf(r, var['stage1Name']))
      for a in aliases:
        t.SetAlias(*(a.split(":")))
      print "File: %s Chunk: %s nEvents: %i (skim: %s) condition: %s lumiScaleFactor: %f"%(chunk['file'],chunk['name'], nEvents, options.skim, skimCond, lumiScaleFactor)
      
      for i in range(nEvents):
        if (i%10000 == 0) and i>0 :
          print i,"/",nEvents  , "name:" , chunk['name']
        s.init()
        r.init()
        t.GetEntry(i)
        lumi_branch = t.GetLeaf('lumi').GetValue()
        evt_branch = t.GetLeaf('evt').GetValue()
        
        if sample['isData']:
          #vetoEvt = str(t.GetLeaf('run').GetValue())+":"+str(t.GetLeaf('lumi').GetValue())+":"+str(t.GetLeaf('evt').GetValue())+"\n"
          vetoEvt = str(int(t.GetLeaf('run').GetValue()))+":"+str(int(lumi_branch))+":"+str(int(evt_branch))+"\n"
          #if vetoEvt in evt_veto_list["ultimate"]:
          #  s.veto_evt_list = False

        genWeight = 1 if sample['isData'] else t.GetLeaf('genWeight').GetValue()
        xsectemp = 1 if sample['isData'] else t.GetLeaf('xsec').GetValue()

        if sample['isData']:
          if "Muon" in sample['name']:
            s.muonDataSet = True
            s.eleDataSet = False
          if "Electron" in sample['name']:
            s.muonDataSet = False
            s.eleDataSet = True
            
        #calculatedWeight = True
        if not sample['isData']:
          s.muonDataSet = False
          s.eleDataSet = False
          nTrueInt = t.GetLeaf('nTrueInt').GetValue()
          s.puReweight_true = PU_histo_63.GetBinContent(PU_histo_63.FindBin(nTrueInt))
          s.puReweight_true_max4 = min(4,s.puReweight_true)
          s.puReweight_true_Down = PU_histo_59p85.GetBinContent(PU_histo_59p85.FindBin(nTrueInt))
          s.puReweight_true_Up = PU_histo_66p15.GetBinContent(PU_histo_66p15.FindBin(nTrueInt))

          #if "TTJets" in sample["name"] :
          #  s.weight = lumiScaleFactor*genWeight
          #else:
          s.weight = lumiScaleFactor*genWeight*xsectemp

          if "TTJets" in sample['dbsName']:
            s.weight_XSecTTBar1p1 = s.weight*1.1 
            s.weight_XSecTTBar0p9 = s.weight*0.9
          else :
            s.weight_XSecTTBar1p1 = s.weight
            s.weight_XSecTTBar0p9 = s.weight
        
        if options.leptonSelection.lower() in ['soft','hard']:
          #get all >=loose lepton indices
          looseLepInd = cmgLooseLepIndices(r) 
          #split into soft and hard leptons
          looseSoftLepInd, looseHardLepInd = splitIndList(r.LepGood_pt, looseLepInd, 25.)
          #select tight soft leptons (no special tight ID for now)
          tightSoftLepInd = looseSoftLepInd #No tight soft selection as of yet 
          #select tight hard leptons (use POG ID)
          ###tightHardLepInd = filter(lambda i:(abs(r.LepGood_pdgId[i])==11 and r.LepGood_relIso03[i]<0.14 and r.LepGood_tightId[i]>=3) \
          ###                               or (abs(r.LepGood_pdgId[i])==13 and r.LepGood_relIso03[i]<0.12 and r.LepGood_tightId[i]), looseHardLepInd)
          tightHardLepInd = filter(lambda i:(abs(r.LepGood_pdgId[i])==11 and cmgTightEleID(r,i)) \
                                         or (abs(r.LepGood_pdgId[i])==13 and cmgTightMuID(r,i)), looseHardLepInd)  

          #print "s lepgood pt: " ,s.LepGood_pt[0]
          s.nLooseSoftLeptons = len(looseSoftLepInd)
          s.nLooseHardLeptons = len(looseHardLepInd)
          s.nTightSoftLeptons = len(tightSoftLepInd)
          s.nTightHardLeptons = len(tightHardLepInd)
          #print "tightHardLepInd:" , tightHardLepInd
          vars = ['pt', 'eta', 'phi', 'miniRelIso','relIso03', 'pdgId', 'eleCBID_SPRING15_25ns_ConvVetoDxyDz', 'mass']
          allLeptons = [getObjDict(t, 'LepGood_', vars, i) for i in looseLepInd]
          looseSoftLep = [getObjDict(t, 'LepGood_', vars, i) for i in looseSoftLepInd] 
          looseHardLep = [getObjDict(t, 'LepGood_', vars, i) for i in looseHardLepInd]
          tightSoftLep = [getObjDict(t, 'LepGood_', vars, i) for i in tightSoftLepInd]
          tightHardLep =  [getObjDict(t, 'LepGood_', vars, i) for i in tightHardLepInd]
          #print "tightHardLep" , tightHardLep 
          leadingLepInd = None
        if options.leptonSelection=='hard':
          if s.nTightHardLeptons>=1:
            leadingLepInd = tightHardLepInd[0]
            #print "highest pt: " , r.LepGood_pt[0]
            s.leptonPt  = r.LepGood_pt[leadingLepInd]
            s.leptonMiniRelIso = r.LepGood_miniRelIso[leadingLepInd]
            s.leptonRelIso03 = r.LepGood_relIso03[leadingLepInd]
            #print s.leptonMiniRelIso ,s.leptonPt, 'met:', r.met_pt, r.nLepGood, r.LepGood_pt[leadingLepInd],r.LepGood_eta[leadingLepInd], r.LepGood_phi[leadingLepInd] , r.LepGood_pdgId[leadingLepInd], r.LepGood_relIso03[leadingLepInd], r.LepGood_tightId[leadingLepInd], r.LepGood_mass[leadingLepInd]
            s.leptonInd = leadingLepInd 
            s.leptonEta = r.LepGood_eta[leadingLepInd]
            s.leptonPhi = r.LepGood_phi[leadingLepInd]
            s.leptonPdg = r.LepGood_pdgId[leadingLepInd]
            s.leptonMass= r.LepGood_mass[leadingLepInd]
            s.leptonSPRING15_25ns_v1= r.LepGood_eleCBID_SPRING15_25ns_ConvVetoDxyDz[leadingLepInd]
            s.st = r.met_pt + s.leptonPt
          s.singleLeptonic = s.nTightHardLeptons==1
          if s.singleLeptonic:
            s.singleMuonic      =  abs(s.leptonPdg)==13
            s.singleElectronic  =  abs(s.leptonPdg)==11
            if "TTJets" in sample["name"]: #W polarization in TTbar
              p4t, p4w, p4lepton = getGenTopWLepton(t)
              if not p4t and not p4w and not p4lepton:
                s.weight = s.weight
                s.weight_WPolPlus10 = s.weight
                s.weight_WPolMinus10 = s.weight
                s.weight_TTPolPlus5 = s.weight
                s.weight_TTPolMinus5 = s.weight
              else:
                cosTheta = ROOT.ttbarPolarizationAngle(p4t, p4w, p4lepton)
                s.weight = s.weight
                s.weight_WPolPlus10 = s.weight
                s.weight_WPolMinus10 = s.weight
                s.weight_TTPolPlus5 = s.weight * (1. + 0.05*(1.-cosTheta)**2) * 1./(1.+0.05*2./3.) * (1./1.0323239521945559)
                s.weight_TTPolMinus5 = s.weight * (1. - 0.05*(1.-cosTheta)**2) * 1./(1.-0.05*2./3.) * (1.034553190276963956)
            elif "WJets" in sample["name"] and not "TTW" in sample["name"]: #W polarization in W+jets
              p4w, p4lepton = getGenWandLepton(t)
              if not p4w and not p4lepton: 
                s.weight = s.weight
                s.weight_WPolPlus10 = s.weight
                s.weight_WPolMinus10 = s.weight
                s.weight_TTPolPlus5 = s.weight
                s.weight_TTPolMinus5 = s.weight
              else:
                cosTheta = ROOT.WjetPolarizationAngle(p4w, p4lepton)
                s.weight = s.weight
                s.weight_WPolPlus10 = s.weight * (1. + 0.1*(1.-cosTheta)**2) * 1./(1.+0.1*2./3.) * (1./1.04923678332724659) 
                s.weight_WPolMinus10 = s.weight * (1. - 0.1*(1.-cosTheta)**2) * 1./(1.-0.1*2./3.) * (1.05627060952003952)
                s.weight_TTPolPlus5 = s.weight
                s.weight_TTPolMinus5 = s.weight 
            else:
              s.weight = s.weight
              s.weight_WPolPlus10 = s.weight
              s.weight_WPolMinus10 = s.weight
              s.weight_TTPolPlus5 = s.weight
              s.weight_TTPolMinus5 = s.weight
          else:
            s.weight = s.weight
            s.weight_WPolPlus10 = s.weight
            s.weight_WPolMinus10 = s.weight
            s.weight_TTPolPlus5 = s.weight
            s.weight_TTPolMinus5 = s.weight

            s.singleMuonic      = False 
            s.singleElectronic  = False 

        if options.leptonSelection=='soft':
          #Select hardest tight lepton among soft leptons
          if s.nTightSoftLeptons>=1:
            leadingLepInd = tightSoftLepInd[0]
  #          print s.leptonPt, r.LepGood_pt[leadingLepInd],r.LepGood_eta[leadingLepInd], leadingLepInd
            s.leptonPt  = r.LepGood_pt[leadingLepInd]
            s.leptonInd = leadingLepInd 
            s.leptonEta = r.LepGood_eta[leadingLepInd]
            s.leptonPhi = r.LepGood_phi[leadingLepInd]
            #s.leptonPdg = r.LepGood_pdgId[leadingLepInd]
            s.leptonPdg = (-1)*r.LepGood_pdgId[leadingLepInd] if (sample['name']=="ST_tchannel_top_4f_leptonDecays_powheg") else r.LepGood_pdgId[leadingLepInd]
            s.leptonMass= r.LepGood_mass[leadingLepInd]
            s.st = r.met_pt + s.leptonPt
          s.singleLeptonic = s.nTightSoftLeptons==1
          if s.singleLeptonic:
            s.singleMuonic      =  abs(s.leptonPdg)==13
            s.singleElectronic  =  abs(s.leptonPdg)==11
          else:
            s.singleMuonic      = False 
            s.singleElectronic  = False 
  #      print "Selected",s.leptonPt
        if options.leptonSelection in ['soft','hard']:
          j_list=['eta','pt','phi','btagCMVA', 'btagCSV', 'id']
          #if not sample['isData']: j_list.extend('partonId')
          jets = filter(lambda j:j['pt']>30 and abs(j['eta'])<2.4 and j['id'], get_cmg_jets_fromStruct(r,j_list))
          #print "jets:" , jets
#          lightJets_, bJetsCMVA = splitListOfObjects('btagCMVA', 0.732, jets) 
          lightJets,  bJetsCSV = splitListOfObjects('btagCSV', 0.800, jets)
          #print "bjetsCMVA:" , bJetsCMVA , "bjetsCSV:" ,  bJetsCSV
          s.htJet30j = sum([x['pt'] for x in jets])
          s.nJet30 = len(jets)
#          s.nBJetMediumCMVA30 = len(bJetsCMVA)
          s.nBJetMediumCSV30 = len(bJetsCSV)
          #print "nbjetsCMVA:" , s.nBJetMediumCMVA30  ,"nbjetsCSV:" ,  s.nBJetMediumCSV30
          #s.mt2w = mt2w.mt2w(met = {'pt':r.met_pt, 'phi':r.met_phi}, l={'pt':s.leptonPt, 'phi':s.leptonPhi, 'eta':s.leptonEta}, ljets=lightJets, bjets=bJetsCSV)
          s.deltaPhi_Wl = acos((s.leptonPt+r.met_pt*cos(s.leptonPhi-r.met_phi))/sqrt(s.leptonPt**2+r.met_pt**2+2*r.met_pt*s.leptonPt*cos(s.leptonPhi-r.met_phi))) 
          #print "deltaPhi:" , s.deltaPhi_Wl
  #          print "Warning -> Why can't I compute mt2w?", s.mt2w, len(jets), len(bJets), len(allTightLeptons),lightJets,bJets, {'pt':s.type1phiMet, 'phi':s.type1phiMetphi}, {'pt':s.leptonPt, 'phi':s.leptonPhi, 'eta':s.leptonEta}

        if options.leptonSelection == 'none':

          ### LEPTONS
          vars = ['pt', 'eta', 'phi', 'mass', 'miniRelIso','relIso03', 'pdgId', 'eleCBID_SPRING15_25ns', 'eleCBID_SPRING15_25ns_ConvVetoDxyDz','ICHEPmediumMuonId', 'sip3d', 'hOverE', 'eleCutIdSpring15_25ns_v1']
          leptonIndices = [i for i in range(r.nLepGood)]
          leptons = [getObjDict(t, 'LepGood_', vars, i) for i in leptonIndices]
          nlep = len(leptonIndices)
          ## Isolation
          eleMiniIsoCut = 0.1
          muMiniIsoCut = 0.2
          looseMiniIsoCut = 0.4
          triggerMiniIsoCut = 0.8

          goodEl_lostHits = 0
          goodEl_sip3d = 4
          goodMu_sip3d = 4

          Selected = False
          #selected good leptons
          selTightLeptons = []
          selTightLepIndices = []
          selVetoLeptons = [] 

          #anti-selected leptons
          antiTightLeptons = []
          antiTightLepIndices = []
          antiVetoLeptons = []      

          #loop over all leptons and sort them to sel, anti-sel, selVeto and antiVeto
          for idx,lep in enumerate(leptons):

            # min Pt and abs eta for all Leptons
            if (abs(lep['eta'])>2.4): continue
            if lep['pt'] < 10: continue
            if lep['miniRelIso'] > triggerMiniIsoCut: continue

            ### MUONS
            if(abs(lep['pdgId']) == 13):

              if (abs(lep['eta'])>2.4): continue

              #ID, IP and Iso check:
              passID = True if lep['ICHEPmediumMuonId'] == 1 else False
              passIso = True if lep['miniRelIso'] < muMiniIsoCut else False
              passIP = True if lep['sip3d'] < goodMu_sip3d else False

              #selected muons
              if passIso and passID and passIP:
                selTightLeptons.append(lep)
                selTightLepIndices.append(idx)
                antiVetoLeptons.append(lep)
              else:
                selVetoLeptons.append(lep)

              #anti-selected muons
              if not passIso:
                antiTightLeptons.append(lep)
                antiTightLepIndices.append(idx)
              else:
                antiVetoLeptons.append(lep)
            
            ### ELECTRONS
            if(abs(lep['pdgId']) == 11):

              if abs(lep['eta'])>2.4: continue
                
              #pass variables
              passIso = False
              passConv = False

              #electron CutBased ID, ConvVeto, dxy,dz already included
              passTightID =   True if (lep['eleCBID_SPRING15_25ns_ConvVetoDxyDz'] == 4) else False
              passMediumID =  True if (lep['eleCBID_SPRING15_25ns_ConvVetoDxyDz'] >= 3) else False
              passVetoID =    True if (lep['eleCBID_SPRING15_25ns_ConvVetoDxyDz'] >= 1) else False

              #selected electrons
              if passTightID:
                #all selected leptons are veto for anti
                antiVetoLeptons.append(lep)

                #Iso check:
                if lep['miniRelIso'] < eleMiniIsoCut: passIso = True
                passConv = True #already included in CBID_SPRING15_25ns_ConvVetoDxyDz

                #fill
                if passIso and passConv:
                  selTightLeptons.append(lep)
                  selTightLepIndices.append(idx)
                else:
                  selVetoLeptons.append(lep)

              # anti-selected electrons
              elif not passMediumID:
                #all anti leptons are veto for selected
                selVetoLeptons.append(lep)

                passIso = True if lep['miniRelIso'] < looseMiniIsoCut else False #should be always true

                passOther = True if lep['hOverE'] > 0.01 else False

                #fill
                if passIso and passOther:
                  antiTightLeptons.append(lep)
                  antiTightLepIndices.append(idx)
                else:
                  antiVetoLeptons.append(lep)
              #Veto leptons
              elif passVetoID:
                #the rest is veto for selected and anti
                selVetoLeptons.append(lep)
                antiVetoLeptons.append(lep)

          #loop over lepOther Collection for anti-selected leptons
          otherIndices = [i for i in range(r.nLepOther)]
          other = [getObjDict(t, 'LepOther_', vars, i) for i in otherIndices]

          for idx,lep in enumerate(other):

            #again min Pt and max eta are the same
            if (abs(lep['eta']) > 2.4): continue
            if lep['pt'] < 10: continue
            if lep['miniRelIso'] > triggerMiniIsoCut: continue

            ### MUONS
            if (abs(lep['pdgId']) == 13):
              passIso = True if lep['miniRelIso'] > muMiniIsoCut else False

              if passIso:
                antiTightLeptons.append(lep)
                antiTightLepIndices.append(idx)
              else:
                antiVetoLeptons.append(lep)

            ### ELECTRONS
            if (abs(lep['pdgId']) == 11):

              if (abs(lep['eta']) > 2.4): continue
              #electron should have MiniIso < 0.4
              if lep['miniRelIso'] > 0.4: continue

              #use the eleCBID_SPRING15_25ns, ConvVeto, dxy, dz an not included
              passMediumIDother = True if (lep['eleCBID_SPRING15_25ns_ConvVetoDxyDz'] >= 3) else False
              passVetoIDother =   True if (lep['eleCBID_SPRING15_25ns_ConvVetoDxyDz'] >= 1) else False

              #Anti-selected electrons with CBID <3
              if not passMediumIDother:
                passOther = True if lep['hOverE'] > 0.01 else False
                
                if passOther: 
                  antiTightLeptons.append(lep)
                  antiTightLepIndices.append(idx)
                else:
                  antiVetoLeptons.append(lep)

              elif passVetoIDother:
                antiVetoLeptons.append(lep)

          #define common tight lep collection for selected leptons
          if len(selTightLeptons) > 0: #if there's at least one tight selected lepton Selected = 1 for this event
            tightLeptons = selTightLeptons
            tightLepIndices = selTightLepIndices
            vetoLeptons = selVetoLeptons

            #write the numbers to branches
            s.nTightLep = len(tightLeptons)
            s.nTightMu = sum([ abs(lep['pdgId']) == 13 for lep in tightLeptons])
            s.nTightEl = sum([ abs(lep['pdgId']) == 11 for lep in tightLeptons])

            #set selected to 1 for tight leptons 
            s.Selected = 1

          elif len(antiTightLeptons) > 0: #otherwise number of tight leptons is 0, but anti-selected leptons in the event,selected = -1
              tightLeptons = antiTightLeptons
              tightLepIndices = antiTightLepIndices
              vetoLeptons = antiVetoLeptons

              #write the numbers to branches
              s.nTightLep = 0
              s.nTightMu = 0
              s.nTightEl = 0

              s.Selected = -1

          else: # no tight sel and anti-sel leptons at all, selected = 0
              tightLeptons = []
              tightLepIndices = []
              vetoLeptons = []

              nTightLeptons = 0
              nTightMu = 0
              nTightEl = 0

              Selected = 0 

          #store Tight and Veto lepton numbers
          s.nLep = len(tightLeptons)
          s.nVeto = len(vetoLeptons)

          #get number of tight el and mu
          tightEl = [lep for lep in tightLeptons if abs(lep['pdgId']) == 11]
          tightMu = [lep for lep in tightLeptons if abs(lep['pdgId']) == 13]  
          s.nEl = len(tightEl)
          s.nMu = len(tightMu)

          # save leading lepton vars
          if len(tightLeptons) > 0:
            s.leptonInd         = tightLepIndices[0]
            s.leptonPt          = tightLeptons[0]['pt']
            s.leptonEta         = tightLeptons[0]['eta']
            s.leptonPhi         = tightLeptons[0]['phi']
            s.leptonPdg         = tightLeptons[0]['pdgId']
            s.leptonMass        = tightLeptons[0]['mass']
            s.leptonRelIso03    = tightLeptons[0]['relIso03']
            s.leptonMiniRelIso  = tightLeptons[0]['miniRelIso']
            s.leptonHoverE      = tightLeptons[0]['hOverE']
            lepVec = ROOT.TLorentzVector()
            lepVec.SetPtEtaPhiM(s.leptonPt,s.leptonEta,s.leptonPhi,s.leptonMass)
            s.leptonEt          = lepVec.Et()

          elif len(leptons) > 0: # if no tight but at least some leptons fill it
            s.leptonInd         = 0
            s.leptonPt          = leptons[0]['pt']
            s.leptonEta         = leptons[0]['eta']
            s.leptonPhi         = leptons[0]['phi']
            s.leptonPdg         = leptons[0]['pdgId']
            s.leptonMass        = leptons[0]['mass']
            s.leptonRelIso03    = leptons[0]['relIso03']
            s.leptonMiniRelIso  = leptons[0]['miniRelIso']
            s.leptonHoverE      = leptons[0]['hOverE']
            lepVec = ROOT.TLorentzVector()
            lepVec.SetPtEtaPhiM(s.leptonPt,s.leptonEta,s.leptonPhi,s.leptonMass)
            s.leptonEt          = lepVec.Et()

          s.singleLeptonic = True if (s.nTightLep==1) else False
          if s.singleLeptonic:
            s.singleMuonic     = True if (abs(s.leptonPdg)==13) else False
            s.singleElectronic = True if (abs(s.leptonPdg)==11) else False
          else:
            s.singleMuonic     = False
            s.singleElectronic = False

          mu_mediumID_histo   = histos_LS['mu_mediumID_histo']
          mu_looseID_histo    = histos_LS['mu_looseID_histo']
          mu_miniIso02_histo  = histos_LS['mu_miniIso02_histo']
          mu_sip3d_histo      = histos_LS['mu_sip3d_histo']
          ele_cutbased_histo  = histos_LS['ele_cutbased_histo']
          ele_miniIso01_histo = histos_LS['ele_miniIso01_histo']
          mu_HIP_histo        = histos_LS['mu_HIP_histo']
          ele_gsf_histo       = histos_LS['ele_gsf_histo']
          
          if s.singleMuonic and s.leptonPt<120:
            s.lepton_muSF_mediumID      = mu_mediumID_histo.GetBinContent(mu_mediumID_histo.FindBin(s.leptonPt,abs(s.leptonEta)))
            s.lepton_muSF_looseID       = mu_looseID_histo.GetBinContent(mu_looseID_histo.FindBin(s.leptonPt,abs(s.leptonEta)))
            s.lepton_muSF_miniIso02     = mu_miniIso02_histo.GetBinContent(mu_miniIso02_histo.FindBin(s.leptonPt,abs(s.leptonEta)))
            s.lepton_muSF_sip3d         = mu_sip3d_histo.GetBinContent(mu_sip3d_histo.FindBin(s.leptonPt,abs(s.leptonEta)))
            s.lepton_muSF_HIP           = mu_HIP_histo.GetBinContent(mu_HIP_histo.FindBin(s.leptonEta))
            s.lepton_muSF_mediumID_err  = mu_mediumID_histo.GetBinError(mu_mediumID_histo.FindBin(s.leptonPt,abs(s.leptonEta)))
            s.lepton_muSF_looseID_err   = mu_looseID_histo.GetBinError(mu_looseID_histo.FindBin(s.leptonPt,abs(s.leptonEta)))
            s.lepton_muSF_miniIso02_err = mu_miniIso02_histo.GetBinError(mu_miniIso02_histo.FindBin(s.leptonPt,abs(s.leptonEta)))
            s.lepton_muSF_sip3d_err     = mu_sip3d_histo.GetBinError(mu_sip3d_histo.FindBin(s.leptonPt,abs(s.leptonEta)))
            s.lepton_muSF_HIP_err       = mu_HIP_histo.GetBinError(mu_HIP_histo.FindBin(s.leptonEta))
          if s.singleMuonic and s.leptonPt>=120:
            s.lepton_muSF_mediumID      = mu_mediumID_histo.GetBinContent(mu_mediumID_histo.FindBin(119,abs(s.leptonEta)))
            s.lepton_muSF_looseID       = mu_looseID_histo.GetBinContent(mu_looseID_histo.FindBin(119,abs(s.leptonEta)))
            s.lepton_muSF_miniIso02     = mu_miniIso02_histo.GetBinContent(mu_miniIso02_histo.FindBin(119,abs(s.leptonEta)))
            s.lepton_muSF_sip3d         = mu_sip3d_histo.GetBinContent(mu_sip3d_histo.FindBin(119,abs(s.leptonEta)))
            s.lepton_muSF_HIP           = mu_HIP_histo.GetBinContent(mu_HIP_histo.FindBin(s.leptonEta))
            s.lepton_muSF_mediumID_err  = mu_mediumID_histo.GetBinError(mu_mediumID_histo.FindBin(119,abs(s.leptonEta)))
            s.lepton_muSF_looseID_err   = mu_looseID_histo.GetBinError(mu_looseID_histo.FindBin(119,abs(s.leptonEta)))
            s.lepton_muSF_miniIso02_err = mu_miniIso02_histo.GetBinError(mu_miniIso02_histo.FindBin(119,abs(s.leptonEta)))
            s.lepton_muSF_HIP_err       = mu_HIP_histo.GetBinError(mu_HIP_histo.FindBin(s.leptonEta))
          if s.singleElectronic and s.leptonEt<200:
            s.lepton_eleSF_cutbasedID     = ele_cutbased_histo.GetBinContent(ele_cutbased_histo.FindBin(s.leptonEt,abs(s.leptonEta)))
            s.lepton_eleSF_miniIso01      = ele_miniIso01_histo.GetBinContent(ele_miniIso01_histo.FindBin(s.leptonEt,abs(s.leptonEta)))
            s.lepton_eleSF_gsf            = ele_gsf_histo.GetBinContent(ele_gsf_histo.FindBin(s.leptonEta,100)) ##pt independent
            s.lepton_eleSF_cutbasedID_err = ele_cutbased_histo.GetBinError(ele_cutbased_histo.FindBin(s.leptonEt,abs(s.leptonEta)))
            s.lepton_eleSF_miniIso01_err  = ele_miniIso01_histo.GetBinError(ele_miniIso01_histo.FindBin(s.leptonEt,abs(s.leptonEta)))
            s.lepton_eleSF_gsf_err        = ele_gsf_histo.GetBinError(ele_gsf_histo.FindBin(s.leptonEta,100)) ##pt independent
          if s.singleElectronic and s.leptonEt>=200:
            s.lepton_eleSF_cutbasedID     = ele_cutbased_histo.GetBinContent(ele_cutbased_histo.FindBin(199,abs(s.leptonEta)))
            s.lepton_eleSF_miniIso01      = ele_miniIso01_histo.GetBinContent(ele_miniIso01_histo.FindBin(199,abs(s.leptonEta)))
            s.lepton_eleSF_gsf            = ele_gsf_histo.GetBinContent(ele_gsf_histo.FindBin(s.leptonEta,100)) ##pt independent
            s.lepton_eleSF_cutbasedID_err = ele_cutbased_histo.GetBinError(ele_cutbased_histo.FindBin(199,abs(s.leptonEta)))
            s.lepton_eleSF_miniIso01_err  = ele_miniIso01_histo.GetBinError(ele_miniIso01_histo.FindBin(199,abs(s.leptonEta)))
            s.lepton_eleSF_gsf_err        = ele_gsf_histo.GetBinError(ele_gsf_histo.FindBin(s.leptonEta,100)) ##pt independent
          

          ### JETS
          j_list=['eta','pt','phi','btagCMVA', 'btagCSV','id']
#          jetsIndices = [i for i in range(r.nJet)]
#          jets = [getObjDict(t, 'Jet_', j_list, i) for i in jetsIndices]

          jet30 = filter(lambda j:j['pt']>30 and abs(j['eta'])<2.4 and j['id'], get_cmg_jets_fromStruct(r,j_list)) 
#          jet30 = []
#          jet30Indices =[]
#          for i,j in enumerate(jets):
#            if j['pt']>30 and abs(j['eta'])<2.4:
#              jet30.append(j)
#              jet30Indices.append(i)

          s.nJet30nonClean = len(jet30)
          s.htJet30nonClean = sum([j['pt'] for j in jet30]) 

          jet30Clean = filter(lambda j:j['pt']>30 and abs(j['eta'])<2.4 and j['id'], get_cmg_jets_fromStruct(r,j_list))
          dRminCut = 0.4

#          jet30Clean = jet30          
          if len(tightLeptons)>=1:
            # clean jets from tight leptons
            for lep in tightLeptons:
#              print 'Jet cleaning!'
              if lep not in other: 
#                print 'lep not in other' 
                continue
              jNear, dRmin = None, 99
              for jet in jet30Clean:
                dR = deltaR(jet,lep)
#                print 'Lep candidate: ',lep,'Jet candidate: ',jet
#                print 'dR: ',dR
                if dR < dRmin:
                  jNear, dRmin = jet, dR
              if dRmin < dRminCut:
#                print 'remove jet!'
#                print jNear
                jet30Clean.remove(jNear)
#                print len(jet30Clean)

#          if s.nJet30nonClean !=  len(jet30Clean) and False:
#            print "Non-clean jets: ", len(jet30), "\tclean jets:", len(jet30Clean)
#            print jet
#            print leptons
#            print other

          if len(jet30Clean) > 0:
            s.Jet1_pt = jet30Clean[0]['pt']
          if len(jet30Clean) > 1:
            s.Jet2_pt = jet30Clean[1]['pt']

          #use Jet2_pt > 80 instead
          s.lslJet80 = 1 if sum([j['pt']>80 for j in jet30Clean])>=2 else 0

          s.nJet30clean = len(jet30Clean)
          s.htJet30clean = sum([j['pt'] for j in jet30Clean])
#          lightJets,  bJetsCSV = splitListOfObjects('btagCSV', 0.800, jet30Clean)

#          print s.nJet30nonClean, s.nJet30clean
#          print s.htJet30nonClean, s.htJet30clean

          bJetsCSV = []
          for i, j in enumerate(jet30Clean):
            if j['btagCSV'] > 0.800:
              bJetsCSV.append(j)

          s.nBJetMediumCSV30 = len(bJetsCSV)

          if len(tightLeptons)>=1:
            s.deltaPhi_Wl = acos((s.leptonPt+r.met_pt*cos(s.leptonPhi-r.met_phi))/sqrt(s.leptonPt**2+r.met_pt**2+2*r.met_pt*s.leptonPt*cos(s.leptonPhi-r.met_phi))) 
            s.Lt = s.leptonPt + r.met_pt
            s.st = s.leptonPt + r.met_pt
            s.Lp = ((s.leptonPt/sqrt(s.leptonPt**2+r.met_pt**2+2*r.met_pt*s.leptonPt*cos(s.leptonPhi-r.met_phi)))*((s.leptonPt+r.met_pt*cos(s.leptonPhi-r.met_phi))/sqrt(s.leptonPt**2+r.met_pt**2+2*r.met_pt*s.leptonPt*cos(s.leptonPhi-r.met_phi)))) 
        if not sample['isData']:
          g_list=['eta','pt','phi','mass','charge', 'pdgId', 'motherId', 'grandmotherId']
          genParts = get_cmg_genParts_fromStruct(r,g_list)
          calc_TopPt_Weights(s,genParts)
        if calcSystematics:
#          separateBTagWeights = False
          zeroTagWeight = 1.
          mceff = getMCEfficiencyForBTagSF(t, mcEffDict[sampleKey], sms='')
          #print
          #print mceff["mceffs"]
          mceffW                = getTagWeightDict(mceff["mceffs"], maxConsideredBTagWeight)
          mceffW_SF             = getTagWeightDict(mceff["mceffs_SF"], maxConsideredBTagWeight)
          mceffW_SF_b_Up        = getTagWeightDict(mceff["mceffs_SF_b_Up"], maxConsideredBTagWeight)
          mceffW_SF_b_Down      = getTagWeightDict(mceff["mceffs_SF_b_Down"], maxConsideredBTagWeight)
          mceffW_SF_light_Up    = getTagWeightDict(mceff["mceffs_SF_light_Up"], maxConsideredBTagWeight)
          mceffW_SF_light_Down  = getTagWeightDict(mceff["mceffs_SF_light_Down"], maxConsideredBTagWeight)
          if not separateBTagWeights:
            lweight = str(s.weight)
          else: lweight = "(1.)"
          #if not separateBTagWeights:
          for i in range(1, maxConsideredBTagWeight+2):
            exec("s.weightBTag"+str(i)+"p="+lweight)
            exec("s.weightBTag"+str(i)+"p_SF="+lweight)
            exec("s.weightBTag"+str(i)+"p_SF_b_Up="+lweight)
            exec("s.weightBTag"+str(i)+"p_SF_b_Down="+lweight)
            exec("s.weightBTag"+str(i)+"p_SF_light_Up="+lweight)
            exec("s.weightBTag"+str(i)+"p_SF_light_Down="+lweight)
          for i in range(maxConsideredBTagWeight+1):
            exec("s.weightBTag"+str(i)+"="              +str(mceffW[i])+'*'+lweight)
            exec("s.weightBTag"+str(i)+"_SF="           +str(mceffW_SF[i])+'*'+lweight)
            exec("s.weightBTag"+str(i)+"_SF_b_Up="      +str(mceffW_SF_b_Up[i])+'*'+lweight)
            exec("s.weightBTag"+str(i)+"_SF_b_Down="    +str(mceffW_SF_b_Down[i])+'*'+lweight)
            exec("s.weightBTag"+str(i)+"_SF_light_Up="  +str(mceffW_SF_light_Up[i])+'*'+lweight)
            exec("s.weightBTag"+str(i)+"_SF_light_Down="+str(mceffW_SF_light_Down[i])+'*'+lweight)
            for j in range(i+1, maxConsideredBTagWeight+2):
              exec("s.weightBTag"+str(j)+"p               -="+str(mceffW[i])+'*'+lweight) #prob. for >=j b-tagged jets
              exec("s.weightBTag"+str(j)+"p_SF            -="+str(mceffW_SF[i])+'*'+lweight)
              exec("s.weightBTag"+str(j)+"p_SF_b_Up       -="+str(mceffW_SF_b_Up[i])+'*'+lweight)
              exec("s.weightBTag"+str(j)+"p_SF_b_Down     -="+str(mceffW_SF_b_Down[i])+'*'+lweight)
              exec("s.weightBTag"+str(j)+"p_SF_light_Up   -="+str(mceffW_SF_light_Up[i])+'*'+lweight)
              exec("s.weightBTag"+str(j)+"p_SF_light_Down -="+str(mceffW_SF_light_Down[i])+'*'+lweight)
          for i in range (int(r.nJet)+1, maxConsideredBTagWeight+1):
            exec("s.weightBTag"+str(i)+"               = 0.")
            exec("s.weightBTag"+str(i)+"_SF            = 0.")
            exec("s.weightBTag"+str(i)+"_SF_b_Up       = 0.")
            exec("s.weightBTag"+str(i)+"_SF_b_Down     = 0.")
            exec("s.weightBTag"+str(i)+"_SF_light_Up   = 0.")
            exec("s.weightBTag"+str(i)+"_SF_light_Down = 0.")
            exec("s.weightBTag"+str(i)+"p              = 0.")
            exec("s.weightBTag"+str(i)+"p_SF           = 0.")
            exec("s.weightBTag"+str(i)+"p_SF_b_Up      = 0.")
            exec("s.weightBTag"+str(i)+"p_SF_b_Down    = 0.")
            exec("s.weightBTag"+str(i)+"p_SF_light_Up  = 0.")
            exec("s.weightBTag"+str(i)+"p_SF_light_Down= 0.")
            
        for v in newVars:
          v['branch'].Fill()
      newFileName = sample['name']+'_'+chunk['name'][0:100]+'_'+chunk['name'][-8:-1]+chunk['name'][-1]+'_'+str(iSplit)+'.root'
      #newFileName = sample['name']+'_'+chunk['name']+'_'+str(iSplit)+'.root'
      filesForHadd.append(newFileName)
      if not options.small:
      #if options.small:
        f = ROOT.TFile(tmpDir+'/'+newFileName, 'recreate')
        t.SetBranchStatus("*",0)
        for b in branchKeepStrings + [v['stage2Name'] for v in newVars] +  [v.split(':')[1] for v in aliases]:
          t.SetBranchStatus(b, 1)
        t2 = t.CloneTree()
        t2.Write()
        f.Close()
        print "Written",tmpDir+'/'+newFileName
        del f
        del t2
        t.Delete()
        del t
      for v in newVars:
        del v['branch']

  print "Event loop end"
  if not options.small: 
    size=0
    counter=0
    files=[]
    for f in filesForHadd:
      size+=os.path.getsize(tmpDir+'/'+f)
      files.append(f)
      if size>(0.5*(10**9)) or f==filesForHadd[-1] or len(files)>200:
        ofile = outDir+'/'+sample['name']+'_'+str(counter)+'.root'
        print "Running hadd on", tmpDir, files
        os.system('cd '+tmpDir+';hadd -f '+ofile+' '+' '.join(files))
        print "Written", ofile
        size=0
        counter+=1
        files=[]
    os.system("rm -rf "+tmpDir)

