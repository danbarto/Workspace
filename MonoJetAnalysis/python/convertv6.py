import ROOT 
from DataFormats.FWLite import Events, Handle
from PhysicsTools.PythonAnalysis import *
from math import *
import sys, os, copy
from datetime import datetime
import xsec

chmode = "copy" #what variations you applied (i.e. JES, etc.)
from defaultMETSamples_mc import *

mode = "MC"
allSamples = [wjets, wjetsInc, ttbar, dy, qcd, ww]

# from first parameter get mode, second parameter is sample type
if len(sys.argv)>=3:
  modeinp = sys.argv[1]
  sampinp = sys.argv[2]

  #steerable
  mode = modeinp    #what dataset (i.e. require MET cut, or maybe Mu<->muon, etc.)
  exec("allSamples = [" + sampinp + "]")

small  = False
overwrite = True
target_lumi = 19375 #pb-1

from localInfo import username
outputDir = "/data/"+username+"/"

ROOT.gSystem.Load("libFWCoreFWLite.so")
ROOT.AutoLibraryLoader.enable()

def deltaPhi(phi1, phi2):
  dphi = phi2-phi1
  if  dphi > pi:
    dphi -= 2.0*pi
  if dphi <= -pi:
    dphi += 2.0*pi
  return abs(dphi)

def minAbsDeltaPhi(phi, phis):
  if len(phis) > 0:
    return min([abs(deltaPhi(phi, x)) for x in phis])
  else: return float('inf')

def minAbsPiMinusDeltaPhi(phi, phis):
  if len(phis)>0:
    return min([abs(abs(deltaPhi(phi, x)) - pi) for x in phis])
  else: return float('inf')
  
def invMassOfLightObjects(p31, p32):
  [px1, py1, pz1] = p31
  [px2, py2, pz2] = p32
  px = px1+px2 
  py = py1+py2
  pz = pz1+pz2
  p1 = sqrt(px1*px1+py1*py1+pz1*pz1)
  p2 = sqrt(px2*px2+py2*py2+pz2*pz2)
  p = sqrt(px*px+py*py+pz*pz)  
  return   sqrt((p1 + p2)*(p1 + p2) - p*p)
    
def deltaR(l1, l2):
  return sqrt(deltaPhi(l1['phi'], l2['phi'])**2 + (l1['eta'] - l2['eta'])**2)
  
def getVarValue(c, var, n=0):
  varNameHisto = var
  leaf = c.GetAlias(varNameHisto)
  if leaf!='':
    return c.GetLeaf(leaf).GetValue(n) 
  else: 
    return float('nan') 
    
def getValue(chain, varname):
  alias = chain.GetAlias(varname)
  if alias!='':
    return chain.GetLeaf( alias ).GetValue()
  else:
    return chain.GetLeaf( varname ).GetValue()

def goodMuID_POG(c, imu ):  
# POG MU Tight
#  return getVarValue(c, 'muonsPt', imu)>20. and getVarValue(c, 'muonsisPF', imu) and getVarValue(c, 'muonsisGlobal', imu) and abs(getVarValue(c, 'muonsEta', imu)) < 2.4  and getVarValue(c, 'muonsPFRelIso', imu)<0.20 and getVarValue(c, 'muonsNormChi2', imu)<10. and getVarValue(c, 'muonsNValMuonHits', imu)>0 and getVarValue(c, 'muonsNumMatchedStadions', imu) > 1 and getVarValue(c, 'muonsPixelHits', imu) > 0 and getVarValue(c, 'muonsNumtrackerLayerWithMeasurement', imu) > 5 and getVarValue(c, 'muonsDxy', imu) < 0.2 and getVarValue(c, 'muonsDz', imu) < 0.5 
# POG MU Loose
  return getVarValue(c, 'muonsisPF', imu) and ( getVarValue(c, 'muonsisGlobal', imu) or getVarValue(c, 'muonsisTracker', imu)) and getVarValue(c, 'muonsPt', imu)>5.

# -------------------------------------------

def goodEleID_POG(c, iele, eta = 'none'): # POG Ele veto
  if eta=='none':
    eta = getVarValue(c, 'elesEta', iele)
  sietaieta = getVarValue(c, 'elesSigmaIEtaIEta', iele)
  dphi = getVarValue(c, 'elesDPhi', iele)
  deta = getVarValue(c, 'elesDEta', iele)
  HoE  = getVarValue(c, 'elesHoE', iele)
  isEB = abs(eta) < 1.4442
  isEE = abs(eta) > 1.566
  relIso = getVarValue(c, 'elesPfRelIso', iele)
  pt = getVarValue(c, 'elesPt', iele)
  relIsoCut = 0.15
  return ( isEE or isEB)\
    and ( relIso < relIsoCut ) and (abs(eta) < 2.5)\
    and ( (isEB and HoE < 0.15 ) or (isEE and HoE < 0.10))\
    and ( (isEB and sietaieta < 0.01 ) or (isEE and sietaieta < 0.03))\
    and ( (isEB and dphi < 0.8) or (isEE and dphi < 0.7)) and ( (isEB and deta < 0.007) or (isEE and deta < 0.01) )\
    and getVarValue(c, 'elesDxy', iele) < 0.04 and getVarValue(c, 'elesDz', iele) < 0.2 and getVarValue(c, 'elesPt', iele)>5.

# -------------------------------------------

def goodTauID_POG(c, itau ): 
  return getVarValue(c, 'tauisPF', itau) and getVarValue(c, 'tausDecayModeFinding', itau) and getVarValue(c, 'tausAgainstMuonLoose', itau) and getVarValue(c, 'tausAgainstElectronLoose', itau) and getVarValue(c, 'tausByLooseCombinedIsolationDBSumPtCorr', itau) and getVarValue(c, 'tausPt', itau)>5.

def getAllMuons(c, nmuons ):
  res=[]
  for i in range(0, int(nmuons)):
    if goodMuID_POG(c, i):
      res.append({'pt':getVarValue(c, 'muonsPt', i),'eta':getVarValue(c, 'muonsEta', i), 'phi':getVarValue(c, 'muonsPhi', i),\
      'pdg':getVarValue(c, 'muonsPdg', i), 'relIso':getVarValue(c, 'muonsPFRelIso', i),\
      'dxy':getVarValue(c, 'muonsDxy', i), 'dz':getVarValue(c, 'muonsDz', i)})
  res = sorted(res, key=lambda k: -k['pt'])
  return res

def getAllElectrons(c, neles ):
  res=[]
  for i in range(0, int(neles)):
    eta = getVarValue(c, 'elesEta', i)
    if goodEleID_POG(c, i, abs(eta)):
      res.append({'pt':getVarValue(c, 'elesPt', i),'eta':eta, 'phi':getVarValue(c, 'elesPhi', i),\
      'pdg':getVarValue(c, 'elesPdg', i), 'relIso':getVarValue(c, 'elesPfRelIso', i),\
      'dxy':getVarValue(c, 'elesDxy', i), 'dz':getVarValue(c, 'elensDz', i)} )
  res = sorted(res, key=lambda k: -k['pt'])
  return res

def getAllTaus(c, ntaus ):
  res=[]
  for i in range(0, int(ntaus)):
    if goodTauID_POG(c, i):
      res.append({'pt':getVarValue(c, 'tausPt', i),'eta':getVarValue(c, 'tausEta', i), 'phi':getVarValue(c, 'tausPhi', i),\
      'pdg':getVarValue(c, 'tausPdg', i)})
  res = sorted(res, key=lambda k: -k['pt'])
  return res

def splitListOfObjects(var, val, s):
  resLow = []
  resHigh = []
  for x in s:
    if x[var]<=val:
      resLow.append(x)
    else:
      resHigh.append(x)
  return resLow, resHigh
    
def getGoodJets(c, crosscleanobjects, relIsoCleaningRequ = 0.2):
  njets = getVarValue(c, 'nsoftjets')   # jet.pt() > 10.
  res = []
  bres = []
  ht = 0.
  nbtags = 0
  for i in range(int(njets)):
    eta = getVarValue(c, 'jetsEta', i)
    pt  = getVarValue(c, 'jetsPt', i)
    id  = getVarValue(c, 'jetsID', i)
    if abs(eta) <= 4.5 and pt >= 30.:
      phi = getVarValue(c, 'jetsPhi', i)
      parton = int(abs(getVarValue(c, 'jetsParton', i)))
      jet = {'pt':pt, 'eta':eta,'phi':phi, 'pdg':parton,\
#      'ptUncorr':getVarValue(c, 'jetsPtUncorr', i),\
      'chef':getVarValue(c, 'jetsChargedHadronEnergyFraction', i), 'nhef':getVarValue(c, 'jetsNeutralHadronEnergyFraction', i),\
      'ceef':getVarValue(c, 'jetsChargedEmEnergyFraction', i), 'neef':getVarValue(c, 'jetsNeutralEmEnergyFraction', i), 'id':id,\
      'hfhef':getVarValue(c, 'jetsHFHadronEnergyFraction', i), 'hfeef':getVarValue(c, 'jetsHFEMEnergyFraction', i),\
      'muef':getVarValue(c, 'jetsMuonEnergyFraction', i), 'elef':getVarValue(c, 'jetsElectronEnergyFraction', i), 'phef':getVarValue(c, 'jetsPhotonEnergyFraction', i),\
      'jetCutBasedPUJetIDFlag':getVarValue(c, 'jetsCutBasedPUJetIDFlag', i),'jetMET53XPUJetIDFlag':getVarValue(c, 'jetsMET53XPUJetIDFlag', i),'jetFull53XPUJetIDFlag':getVarValue(c, 'jetsFull53XPUJetIDFlag', i) 
      }
      isolated = True
#      if max([jet['muef'],jet['elef']]) > 0.6 : print jet
      for obj in crosscleanobjects:   #Jet cross-cleaning
        if deltaR(jet, obj) < 0.4 and (obj['pt']/jet['pt']) > 0.4 and obj['relIso']< relIsoCleaningRequ:  
          isolated = False
#          print "Cleaned", 'deltaR', deltaR(jet, obj), 'maxfrac', max([jet['muef'],jet['elef']]), 'pt:jet/obj', jet['pt'], obj['pt']
#          print 'Not this one!', jet, obj, deltaR(jet, obj)
          break
#      for obj in crosscleanobjects:   #Jet cross-cleaning
      if isolated:
        ht += jet['pt']
        btag = getVarValue(c, 'jetsBtag', i)
        jet['btag'] = btag
        res.append(jet)
        if btag >= 0.679:   # bjets
          bres.append(jet)
          nbtags = nbtags+1

  res  = sorted(res,  key=lambda k: -k['pt'])
  bres = sorted(bres, key=lambda k: -k['pt'])
  return {"jets":res, "bjets":bres,"ht": ht, "nbtags":nbtags}

def isrJetID(j):
  return j['chef'] > 0.2 and j['neef']<0.7 and j['nhef']<0.7

# helpers for GenParticle serching
def find(x,lp):
  for ip,p in enumerate(lp):
    if x == p:
      break
  if ip == len(lp)-1:
    ip = -1
  return ip
  
def findSec(x,lp):
  gp = x
  while gp.status() != 3:
    gp = gp.mother(0)
  return gp

##################################################################################

commoncf = ""
if mode=="MET":
#  commoncf = "met>200"
  commoncf = "met>150"
if mode == "MC":
#  commoncf = "met>200"
  commoncf = "met>150"

for sample in allSamples:
  sample['filenames'] = {}
  sample['weight'] = {}
  for bin in sample['bins']:
    subdirname = sample['dirname']+'/'+bin+'/'
    if sample['bins'] == ['']:
      subdirname = sample['dirname']+'/'
    c = ROOT.TChain('Events')
    d = ROOT.TChain('Runs')
    sample['filenames'][bin] = [subdirname+'/h*.root']
    #if small: Chain only a few files

    sample['filenames'][bin] = []
    prefix = ""
    if subdirname[0:5] != "/dpm/":
      filelist = os.listdir(subdirname)
    else:
# this is specific to rfio    
      filelist = []
      allFiles = os.popen("rfdir %s | awk '{print $9}'" % (subdirname))
      for file in allFiles.readlines():
        file = file.rstrip()
        if(file.find("histo_548_1_nmN") > -1): continue
        filelist.append(file)
      prefix = "rfio:"
####
    nf = 20 
    for tfile in filelist:
#      if os.path.isfile(subdirname+tfile) and tfile[-5:] == '.root' and tfile.count('histo') == 1:
        sample['filenames'][bin].append(subdirname+tfile)
        if small and not nf:
          break
        nf-=1

    for tfile in sample['filenames'][bin]:
      c.Add(prefix+tfile)
      d.Add(prefix+tfile)
    nevents = 0
    nruns = d.GetEntries()
    for i in range(0, nruns):
      d.GetEntry(i)
      nevents += getValue(d,'uint_EventCounter_runCounts_PAT.obj')
    if mode == "MC":
      weight = xsec.xsec[bin]*target_lumi/nevents
    else:
      weight = 1.
    print 'Sample', sample['name'], 'bin', bin, 'n-events',nevents,'weight',weight
    sample["weight"][bin]=weight

if not os.path.isdir(outputDir+"/"+chmode):
  os.system("mkdir "+outputDir+"/"+chmode)
if not os.path.isdir(outputDir+"/"+chmode+"/"+mode):
  os.system("mkdir "+outputDir+"/"+chmode+"/"+mode)

nc = 0
for isample, sample in enumerate(allSamples):
  if not os.path.isdir(outputDir+"/"+chmode+"/"+mode+"/"+sample["name"]):
    os.system("mkdir "+outputDir+"/"+chmode+"/"+mode+"/"+sample["name"])
  else:
    print "Directory", outputDir+"/"+chmode+"/"+mode, "already found"

  variables = ["weight", "run", "lumi", "ngoodVertices", "met", "metphi"]
  if mode != "MC":
    alltriggers =  [ "HLTL1ETM40", "HLTMET120", "HLTMET120HBHENoiseCleaned", "HLTMonoCentralPFJet80PFMETnoMu105NHEF0p95", "HLTMonoCentralPFJet80PFMETnoMu95NHEF0p95"]
    for trigger in alltriggers:
      variables.append(trigger)
      variables.append(trigger.replace("HLT", "pre") )
  else:
    variables.extend(["nTrueGenVertices", "genmet", "genmetphi"])
  
  jetvars = ["jetPt", "jetEta", "jetPhi", "jetPdg", "jetBtag", "jetCutBasedPUJetIDFlag","jetFull53XPUJetIDFlag","jetMET53XPUJetIDFlag", "jetChef", "jetNhef", "jetCeef", "jetNeef", "jetHFhef", "jetHFeef", "jetMuef", "jetElef", "jetPhef"]
  muvars = ["muPt", "muEta", "muPhi", "muPdg", "muRelIso", "muDxy", "muDz"]
  elvars = ["elPt", "elEta", "elPhi", "elPdg", "elRelIso", "elDxy", "elDz"]
  tavars = ["taPt", "taEta", "taPhi", "taPdg"]
  if mode == "MC":
    mcvars = ["gpPdg", "gpM", "gpPt", "gpEta", "gpPhi", "gpMo1", "gpMo2", "gpDa1", "gpDa2", "gpSta"]

  extraVariables=["nbtags", "ht", "nSoftMuons", "nSoftIsolatedMuons", "nHardMuons", "nSoftElectrons", "nHardElectrons", "nSoftTaus", "nHardTaus"]
  extraVariables += ["isrJetPt", "isrJetEta", "isrJetPhi", "isrJetPdg", "isrJetBtag", "isrJetChef", "isrJetNhef", "isrJetCeef", "isrJetNeef", "isrJetHFhef", "isrJetHFeef", "isrJetMuef", "isrJetElef", "isrJetPhef", "isrJetCutBasedPUJetIDFlag", "isrJetFull53XPUJetIDFlag", "isrJetMET53XPUJetIDFlag", "isrJetBTBVetoPassed"]

  extraVariables += ["softIsolatedMuPt", "softIsolatedMuEta", "softIsolatedMuPhi", "softIsolatedMuPdg", "softIsolatedMuRelIso", "softIsolatedMuDxy", "softIsolatedMuDz"]

  structString = "struct MyStruct_"+str(nc)+"_"+str(isample)+"{ULong64_t event;"
  for var in variables:
    structString +="Float_t "+var+";"
  for var in extraVariables:
    structString +="Float_t "+var+";"
  structString +="Int_t njet;"
  for var in jetvars:
    structString +="Float_t "+var+"[10];"
  structString +="Int_t nmu;"
  for var in muvars:
    structString +="Float_t "+var+"[10];"
  structString +="Int_t nel;"
  for var in elvars:
    structString +="Float_t "+var+"[10];"
  structString +="Int_t nta;"
  for var in tavars:
    structString +="Float_t "+var+"[10];"
  structString +="Int_t ngp;"
  if mode == "MC":
    for var in mcvars:
      structString +="Float_t "+var+"[20];"
  structString   +="};"
#  print structString

  ROOT.gROOT.ProcessLine(structString)
  exec("from ROOT import MyStruct_"+str(nc)+"_"+str(isample))
  exec("s = MyStruct_"+str(nc)+"_"+str(isample)+"()")
  nc+=1

  ofile = outputDir+"/"+chmode+"/"+mode+"/"+sample["name"]+"/histo_"+sample["name"]+".root"
  if os.path.isfile(ofile) and overwrite:
    print "Warning! will overwrite",ofile
  if os.path.isfile(ofile) and not overwrite:
    print ofile, "already there! Skipping!!!"
    continue
  f = ROOT.TFile(ofile, "recreate")
  
  t = ROOT.TTree( "Events", "Events", 1 )
  t.Branch("event",   ROOT.AddressOf(s,"event"), 'event/l')
  for var in variables:
    t.Branch(var,   ROOT.AddressOf(s,var), var+'/F')
  for var in extraVariables:
    t.Branch(var,   ROOT.AddressOf(s,var), var+'/F')
  t.Branch("njet",   ROOT.AddressOf(s,"njet"), 'njet/I')
  for var in jetvars:
    t.Branch(var,   ROOT.AddressOf(s,var), var+'[njet]/F')
  t.Branch("nmu",   ROOT.AddressOf(s,"nmu"), 'nmu/I')
  for var in muvars:
    t.Branch(var,   ROOT.AddressOf(s,var), var+'[nmu]/F')
  t.Branch("nel",   ROOT.AddressOf(s,"nel"), 'nel/I')
  for var in elvars:
    t.Branch(var,   ROOT.AddressOf(s,var), var+'[nel]/F')
  t.Branch("nta",   ROOT.AddressOf(s,"nta"), 'nta/I')
  for var in tavars:
    t.Branch(var,   ROOT.AddressOf(s,var), var+'[nta]/F')
  if mode == "MC":
    t.Branch("ngp",   ROOT.AddressOf(s,"ngp"), 'ngp/I')
    for var in mcvars:
      t.Branch(var,   ROOT.AddressOf(s,var), var+'[ngp]/F')

  for bin in sample["bins"]:
    c = ROOT.TChain(sample["Chain"])
    for thisfile in sample["filenames"][bin]:
      prefix = ""
      if thisfile[0:5] == "/dpm/":
        prefix = "rfio:"
      c.Add(prefix+thisfile)
    ntot = c.GetEntries()
    if mode == "MC":
      mclist = []
      for thisfile in sample["filenames"][bin]:
        mclist.append(prefix+thisfile)
      events = Events(mclist)
      handle = Handle("vector<reco::GenParticle>")
      events.toBegin()
      label = ("genParticles")
    if sample.has_key("additionalCut"):
      if type(sample["additionalCut"])==type({}):
        if sample["additionalCut"].has_key(bin):
          commoncf = commoncf+"&&"+sample["additionalCut"][bin]
      else:
        commoncf = commoncf+"&&"+sample["additionalCut"]

    if ntot>0:
      c.Draw(">>eList", commoncf)
      elist = ROOT.gDirectory.Get("eList")
      number_events = elist.GetN()
      print "Reading: ", sample["name"], bin, "with",number_events,"Events using cut", commoncf
      if small:
        if number_events>1000:
          number_events=1000
      for i in range(0, number_events):
        if (i%10000 == 0) and i>0 :
          print i
  #      # Update all the Tuples
        if elist.GetN()>0 and ntot>0:
          c.GetEntry(elist.GetEntry(i))
# MC specific part
          if mode == "MC":
            events.to(elist.GetEntry(i))
            events.getByLabel(label,handle)
            gps = handle.product()
            
            lgp = []
            lgp2 = []
            igp = 0
            for gp in gps:
              if gp.status() == 3:
                lgp.append(gp)
              if (abs(gp.pdgId()==11) or abs(gp.pdgId()==13)) and gp.pt() > 3.:
                lgp2.append(gp)
            lgp2 = sorted(lgp2, key=lambda k: -k.pt())
            s.ngp = min(len(lgp)+len(lgp2),20)
            for igp,gp in enumerate(lgp):
              s.gpPdg[igp] = gp.pdgId()
              s.gpM[igp] = gp.mass()
              s.gpPt[igp] = gp.pt()
              s.gpEta[igp] = gp.eta()
              s.gpPhi[igp] = gp.phi()
              s.gpMo1[igp] = find(gp.mother(0),lgp)
              s.gpMo2[igp] = find(gp.mother(min(gp.numberOfMothers(),1)),lgp)
              s.gpDa1[igp] = find(gp.daughter(0),lgp)
              s.gpDa2[igp] = find(gp.daughter(min(gp.numberOfDaughters(),1)),lgp)
              s.gpSta[igp] = gp.status()
            for igp2,gp2 in enumerate(lgp2,igp+1):
              if igp2 == 20:
                break
              gpm = findSec(gp2,gps)
              s.gpPdg[igp2] = gp2.pdgId()
              s.gpM[igp2] = gp2.mass()
              s.gpPt[igp2] = gp2.pt()
              s.gpEta[igp2] = gp2.eta()
              s.gpPhi[igp2] = gp2.phi()
              s.gpMo1[igp2] = find(gpm,lgp)
              s.gpMo2[igp2] = -2
              s.gpDa1[igp2] = -1
              s.gpDa2[igp2] = -1
              s.gpSta[igp2] = gp2.status()
###################
          s.weight = sample["weight"][bin]
          for var in variables[1:]:
            getVar = var
            exec("s."+var+"="+str(getVarValue(c, getVar)).replace("nan","float('nan')"))
          s.event = long(c.GetLeaf(c.GetAlias('event')).GetValue())

          if len(extraVariables)>0: #Fill struct with nan's
            for var in extraVariables:
              exec("s."+var+"=float('nan')")
            nmuons = getVarValue(c, 'nmuons')   #Number of muons in Muon Vec
            neles  = getVarValue(c, 'neles')    #Number of eles in Ele Vec
            ntaus  = getVarValue(c, 'ntaus')    #Number of eles in Ele Vec

#            allGoodLeptons = getGoodLeptons(c, nmuons, neles, ntaus)   #get all good leptons
            allGoodMuons = getAllMuons(c,nmuons)
            allGoodElectrons = getAllElectrons(c, neles)
            allGoodTaus = getAllTaus(c, ntaus)

            softMuons, hardMuons         = splitListOfObjects('pt', 20, allGoodMuons)
            softElectrons, hardElectrons = splitListOfObjects('pt', 20, allGoodElectrons)
            softTaus, hardTaus           = splitListOfObjects('pt', 20, allGoodTaus)

            softMuons = sorted(softMuons, key=lambda k: -k['pt'])
            s.nSoftMuons = len(softMuons)
            softIsolatedMuons = filter(lambda m:m['relIso']*m['pt']<5.0, softMuons) 
            s.nSoftIsolatedMuons = len(softIsolatedMuons)
            s.nHardMuons = len(hardMuons)
            s.nSoftElectrons = len(softElectrons)
            s.nHardElectrons = len(hardElectrons)
            s.nSoftTaus = len(softTaus)
            s.nHardTaus = len(hardTaus)
 

            jetResult = getGoodJets(c, hardMuons + hardElectrons, relIsoCleaningRequ = 0.2)
            s.ht = jetResult["ht"]
            s.nbtags = jetResult["nbtags"]
            s.njet = len(jetResult["jets"])

            if len( jetResult['jets'] )>=1 and jetResult['jets'][0]['pt']>110 and isrJetID(jetResult['jets'][0]):
              leadingJet = jetResult['jets'][0]
              s.isrJetPt = leadingJet['pt']
              s.isrJetEta = leadingJet['eta']
              s.isrJetPhi = leadingJet['phi']
              s.isrJetPdg = leadingJet['pdg']
              s.isrJetBtag = leadingJet['btag']
              s.isrJetChef = leadingJet['chef']
              s.isrJetNhef = leadingJet['nhef']
              s.isrJetCeef = leadingJet['ceef']
              s.isrJetNeef = leadingJet['neef']
              s.isrJetHFhef = leadingJet['hfhef']
              s.isrJetHFeef = leadingJet['hfeef']
              s.isrJetMuef = leadingJet['muef']
              s.isrJetElef = leadingJet['elef']
              s.isrJetPhef = leadingJet['phef']
              s.isrJetCutBasedPUJetIDFlag = leadingJet['jetCutBasedPUJetIDFlag']
              s.isrJetFull53XPUJetIDFlag = leadingJet['jetFull53XPUJetIDFlag']
              s.isrJetMET53XPUJetIDFlag = leadingJet['jetMET53XPUJetIDFlag']
              
              recoilJets = filter(lambda j:j['pt']>60 and deltaPhi(j['phi'], leadingJet['phi']) >=2.5, jetResult['jets'][1:])
              s.isrJetBTBVetoPassed = (len(recoilJets)==0)
            
            if len(softIsolatedMuons)>=1:
              s.softIsolatedMuPt = softIsolatedMuons[0]['pt']
              s.softIsolatedMuEta = softIsolatedMuons[0]['eta']
              s.softIsolatedMuPhi = softIsolatedMuons[0]['phi']
              s.softIsolatedMuPdg = softIsolatedMuons[0]['pdg']
              s.softIsolatedMuRelIso = softIsolatedMuons[0]['relIso']
              s.softIsolatedMuDxy = softIsolatedMuons[0]['dxy']
              s.softIsolatedMuDz = softIsolatedMuons[0]['dz']
 
#            print "\nevent,run,lumi",s.event,int(s.run), int(s.lumi),"nbtags", int(s.nbtags)
            for i in xrange(min(10,s.njet)):
              s.jetPt[i] = jetResult["jets"][i]['pt']
              s.jetEta[i] = jetResult["jets"][i]['eta']
              s.jetPhi[i] = jetResult["jets"][i]['phi']
              s.jetPdg[i] = jetResult["jets"][i]['pdg']
              s.jetBtag[i] = jetResult["jets"][i]['btag']
              s.jetChef[i] = jetResult["jets"][i]['chef']
              s.jetNhef[i] = jetResult["jets"][i]['nhef']
              s.jetCeef[i] = jetResult["jets"][i]['ceef']
              s.jetNeef[i] = jetResult["jets"][i]['neef']
              s.jetHFhef[i] = jetResult["jets"][i]['hfhef']
              s.jetHFeef[i] = jetResult["jets"][i]['hfeef']
              s.jetMuef[i] = jetResult["jets"][i]['muef']
              s.jetElef[i] = jetResult["jets"][i]['elef']
              s.jetPhef[i] = jetResult["jets"][i]['phef']
              s.jetCutBasedPUJetIDFlag[i] = jetResult["jets"][i]['jetCutBasedPUJetIDFlag']
              s.jetFull53XPUJetIDFlag[i] = jetResult["jets"][i]['jetFull53XPUJetIDFlag']
              s.jetMET53XPUJetIDFlag[i] = jetResult["jets"][i]['jetMET53XPUJetIDFlag']
#              s.jetId[i] = jetResult["jets"][i]['id']
#              print "Jet pt's:",i,jetResult["jets"][i]['pt']
            s.nmu = len(allGoodMuons)
            for i in xrange(min(10,s.nmu)):
              s.muPt[i] = allGoodMuons[i]['pt']
              s.muEta[i] = allGoodMuons[i]['eta']
              s.muPhi[i] = allGoodMuons[i]['phi']
              s.muPdg[i] = allGoodMuons[i]['pdg']
              s.muRelIso[i] = allGoodMuons[i]['relIso']
              s.muDxy[i] = allGoodMuons[i]['dxy']
              s.muDz[i] = allGoodMuons[i]['dz']
#              print "Muon pt's:",i,allGoodMuons[i]['pt']
            s.nel = len(allGoodElectrons)
            for i in xrange(min(10,s.nel)):
              s.elPt[i] = allGoodElectrons[i]['pt']
              s.elEta[i] = allGoodElectrons[i]['eta']
              s.elPhi[i] = allGoodElectrons[i]['phi']
              s.elPdg[i] = allGoodElectrons[i]['pdg']
              s.elRelIso[i] = allGoodElectrons[i]['relIso']
              s.elDxy[i] = allGoodElectrons[i]['dxy']
              s.elDz[i] = allGoodElectrons[i]['dz']
#              print "Electron pt's:",i,allGoodElectrons[i]['pt']
            s.nta = len(allGoodTaus)
            for i in xrange(min(10,s.nta)):
              s.taPt[i] = allGoodTaus[i]['pt']
              s.taEta[i] = allGoodTaus[i]['eta']
              s.taPhi[i] = allGoodTaus[i]['phi']
              s.taPdg[i] = allGoodTaus[i]['pdg']
              
          t.Fill()
      del elist
    else:
      print "Zero entries in", bin, sample["name"]
    del c
  if True or not small: #FIXME
    f.cd()
    t.Write()
    f.Close()
    print "Written",ofile
  else:
    print "No saving when small!"
  del t
