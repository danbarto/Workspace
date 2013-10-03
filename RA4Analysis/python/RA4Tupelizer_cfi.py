import FWCore.ParameterSet.Config as cms

RA4Tupelizer = cms.EDProducer ( "RA4Tupelizer",
    verbose         = cms.untracked.bool(False),
    doFastJetIsolationCorrection   = cms.untracked.bool(False),
    triggerCollection = cms.untracked.string("HLT"),
    patJets      = cms.untracked.InputTag("patJetsAK5PF"),
#    patJets      = cms.untracked.InputTag("cleanPatJetsAK5PF"),
    patMETs             = cms.untracked.InputTag("patPFMETsTypeIcorrected"),
    rawMETs             = cms.untracked.InputTag("patRAWPFMETs"),
    type01METs          = cms.untracked.InputTag("patPFMETsTypeIType0PFCandcorrected"),
    type1phiMETs        = cms.untracked.InputTag("patPFMETsTypeIPhicorrected"),
#    type01phiMETs       = cms.untracked.InputTag("patType1CorrectedPFMetPF"),

    patMuons     = cms.untracked.InputTag("cleanPatMuons"),
    pfPatMuons     = cms.untracked.InputTag("patMuonsPF"),
    patElectrons = cms.untracked.InputTag("cleanPatElectrons"),
    patTaus = cms.untracked.InputTag("patTaus"),
    vertices = cms.untracked.InputTag("goodVertices"),

    lowLeptonPtThreshold = cms.untracked.double(5.),

    muonPt = cms.untracked.double(20),
    muonEta = cms.untracked.double(2.4),
    muonIsGlobal = cms.untracked.bool(True),
    muonHasPFMatch = cms.untracked.bool(True),
    muonIsPF = cms.untracked.bool(True),
    muonNormChi2 = cms.untracked.double(10),
    muonNumValMuonHits = cms.untracked.int32(0),
    muonNumMatchedStations = cms.untracked.int32(1),
    muonNumPixelHits = cms.untracked.int32(0),
    muonNumTrackerLayersWithMeasurement = cms.untracked.int32(5),
    muonPFRelIso = cms.untracked.double(0.12),
    muonPFRelIsoDeltaBeta = cms.untracked.bool(True),
    muonDxy = cms.untracked.double(0.02),
    muonDz = cms.untracked.double(0.5),

    vetoMuonPt = cms.untracked.double(15),
    vetoMuonEta = cms.untracked.double(2.5),
    vetoMuonIsGlobalOrIsTracker = cms.untracked.bool(True),
    vetoMuonIsPF = cms.untracked.bool(True),
    vetoMuonPFRelIso = cms.untracked.double(0.2),
    vetoMuonPFRelIsoDeltaBeta = cms.untracked.bool(True),
    vetoMuonDxy = cms.untracked.double(0.2),
    vetoMuonDz = cms.untracked.double(0.5),

  # steerables Ele:
    elePt = cms.untracked.double(20) ,
    eleEta = cms.untracked.double(2.5),
    eleOneOverEMinusOneOverP = cms.untracked.double(0.05) ,
    eleDxy = cms.untracked.double(0.02) ,
    eleDz = cms.untracked.double(0.1) ,
    elePFRelIsoBarrel = cms.untracked.double(0.15) ,
    elePFRelIsoEndcap = cms.untracked.double(0.15) ,
    elePFRelIsoAreaCorrected = cms.untracked.bool(True) ,
#    eleRho = cms.untracked.InputTag('kt6PFJets','rho'),
    eleRho = cms.untracked.InputTag('kt6PFJetsForIsolation2011','rho'),
    eleSigmaIEtaIEtaBarrel = cms.untracked.double(0.01) ,
    eleSigmaIEtaIEtaEndcap = cms.untracked.double(0.03) ,
    eleHoEBarrel = cms.untracked.double(0.12) ,
    eleHoEEndcap = cms.untracked.double(0.10) ,
    eleDPhiBarrel = cms.untracked.double(0.06) ,
    eleDPhiEndcap = cms.untracked.double(0.03) ,
    eleDEtaBarrel = cms.untracked.double(0.004) ,
    eleDEtaEndcap = cms.untracked.double(0.007) ,
    eleMissingHits = cms.untracked.int32(1) ,
    eleConversionRejection = cms.untracked.bool(True),
    eleHasPFMatch = cms.untracked.bool(True),
  # steerables veto Ele:
    vetoElePt = cms.untracked.double(15) ,
    vetoEleEta = cms.untracked.double(2.5) ,
    vetoEleDxy = cms.untracked.double(0.04) ,
    vetoEleDz = cms.untracked.double(0.2) ,
    vetoElePFRelIsoBarrel = cms.untracked.double(0.15) ,
    vetoElePFRelIsoEndcap = cms.untracked.double(0.15) ,
    vetoEleSigmaIEtaIEtaBarrel = cms.untracked.double(0.01) ,
    vetoEleSigmaIEtaIEtaEndcap = cms.untracked.double(0.03) ,
    vetoEleHoEBarrel = cms.untracked.double(0.15) ,
    vetoEleHoEEndcap = cms.untracked.double(-1.) ,
    vetoEleDPhiBarrel = cms.untracked.double(0.8) ,
    vetoEleDPhiEndcap = cms.untracked.double(0.7) ,
    vetoEleDEtaBarrel = cms.untracked.double(0.007) ,
    vetoEleDEtaEndcap = cms.untracked.double(0.01) ,

    minJetPt          = cms.untracked.double(40.0),
    maxJetEta         = cms.untracked.double(2.4),
    btag              = cms.untracked.string("combinedSecondaryVertexBJetTags"),
    btagWP            = cms.untracked.double(0.679),
    btagPure          = cms.untracked.string("combinedSecondaryVertexBJetTags"),
    btagPureWP        = cms.untracked.double(0.244),
    hasL1Trigger      =  cms.untracked.bool(True),

    addRA4AnalysisInfo = cms.untracked.bool(True),
    addTriggerInfo = cms.untracked.bool(False),
    triggersToMonitor = cms.untracked.vstring(["HLT_IsoMu24_eta2p1"]),
    addFullBTagInfo = cms.untracked.bool(False),
    addFullJetInfo = cms.untracked.bool(False),
    addFullLeptonInfo = cms.untracked.bool(False),
    addFullTauInfo = cms.untracked.bool(False),
    addFullMETInfo = cms.untracked.bool(False),
    addFullMuonInfo = cms.untracked.bool(False),
    addFullEleInfo = cms.untracked.bool(False),
    addGeneratorInfo = cms.untracked.bool(False),
    addMSugraOSETInfo = cms.untracked.bool(False),
    addPDFWeights = cms.untracked.bool(False),
    addMetUncertaintyInfo = cms.untracked.bool(False),
    metsToMonitor = cms.untracked.vstring(["patType1CorrectedPFMet","patType1CorrectedPFMetElectronEnDown","patType1CorrectedPFMetElectronEnUp","patType1CorrectedPFMetJetEnDown","patType1CorrectedPFMetJetEnUp","patType1CorrectedPFMetJetResDown","patType1CorrectedPFMetJetResUp","patType1CorrectedPFMetMuonEnDown","patType1CorrectedPFMetMuonEnUp","patType1CorrectedPFMetTauEnDown","patType1CorrectedPFMetTauEnUp","patType1CorrectedPFMetUnclusteredEnDown","patType1CorrectedPFMetUnclusteredEnUp"]),
    useForDefaultAlias = cms.untracked.bool(False)

) 
