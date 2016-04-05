''' Post processing script for CMG ntuples. 

'''
    
# imports python standard modules or functions
import argparse
import logging
import sys
import tempfile
import os
import shutil
import pprint
import math
import time
import io
import importlib
import copy
import pickle
# imports user modules or functions

import ROOT

import Workspace.DegenerateStopAnalysis.cmgObjectSelection as cmgObjectSelection
import Workspace.DegenerateStopAnalysis.helpers as helpers

import Workspace.HEPHYPythonTools.helpers as hephyHelpers
import Workspace.HEPHYPythonTools.convertHelpers as convertHelpers

import Workspace.HEPHYPythonTools.user as user

from  veto_event_list import get_veto_list

def get_parser():
    ''' Argument parser for post-processing module.
    
    '''
     
    argParser = argparse.ArgumentParser(description = "Argument parser for cmgPostProcessing")
        
    argParser.add_argument('--logLevel', 
        action='store',
        nargs='?',
        choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG', 'TRACE', 'NOTSET'],
        default='INFO',
        help="Log level for logging"
        )
    
    argParser.add_argument('--overwriteOutputFiles',
        action='store_true',
        help="Overwrite existing output files, bool flag set to True  if used")
    
    argParser.add_argument('--cmgTuples',
        dest='cmgTuples',
        action='store',
        nargs='?',
        type=str,
        default='RunIISpring15DR74_25ns',
        help="CMG ntuples to be post-processed"
        )
       
    argParser.add_argument('--processSamples',
        action='store',
        nargs='*',
        type=str,
        default='TTJets_LO',
        help="List of samples to be post-processed, given as CMG component name"
        )
    
    argParser.add_argument('--targetDir',
        action='store',
        nargs='?',
        type=str,
        default='/afs/hephy.at/data/' + user.afsDataName + '/cmgTuples',
        help="Name of the directory the post-processed files will be saved"
        )
    
    argParser.add_argument('--processingEra',
        action='store',
        nargs='?',
        type=str,
        default='postProcessed_mAODv2',
        help="Name of the processing era"
        )

    argParser.add_argument('--processingTag',
        action='store',
        nargs='?',
        type=str,
        default='v0',
        help="Name of the processing tag, preferably a tag for Workspace"
        )

    argParser.add_argument('--skim',
        action='store',
        nargs='?',
        type=str,
        default='',
        help="Skim conditions to be applied for post-processing"
        )
    
    argParser.add_argument('--processSignalScan',
        action='store',
        nargs='*',
        type=str,
        default='',
        help="Do Processing for a specific Stop and LSP mass"
        )
    
    argParser.add_argument('--leptonSelection',
        action='store',
        nargs='?',
        type=str,
        choices=['soft', 'hard', 'inc', 'dilep'],
        default='inc',
        help="Lepton selection to be applied for post-processing"
        )
    
    argParser.add_argument('--preselect',
        action='store_true',
        help="Apply preselection for the post processing, bool flag set to True if used"
        )
    
    argParser.add_argument('--processTracks',
        action='store_true',
        help="Process tracks for post-processing, bool flag set to True if used"
        )
    
    argParser.add_argument('--processGenTracks',
        action='store_true',
        help="Process packed generated particles for post-processing, bool flag set to True if used"
        )
     
    argParser.add_argument('--runSmallSample',
        action='store_true',
        help="Run the file on a small sample (for test purpose), bool flag set to True if used"
        )
    
    argParser.add_argument('--testMethods',
        action='store_true',
        help="Testing only the post-processing methods, without saving ROOT files, on runSmallSample files " + \
        "\n bool flag set to True if used. \n runSmallSample will be set automatically to True"
        )
    # 
    return argParser

def get_logger(logLevel, logFile):
    ''' Logger for post-processing module.
    
    '''

    # add TRACE (numerical level 5, less than DEBUG) to logging (similar to apache) 
    # see default levels at https://docs.python.org/2/library/logging.html#logging-levels
    logging.TRACE = 5
    logging.addLevelName(logging.TRACE, 'TRACE')
    
    logging.Logger.trace = lambda inst, msg, *args, **kwargs: inst.log(logging.TRACE, msg, *args, **kwargs)
    logging.trace = lambda msg, *args, **kwargs: logging.log(logging.TRACE, msg, *args, **kwargs)

    logger = logging.getLogger('cmgPostProcessing')

    numeric_level = getattr(logging, logLevel.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError("Invalid log level: %s" % logLevel)
     
    logger.setLevel(numeric_level)
     
    # create the logging file handler
    fileHandler = logging.FileHandler(logFile, mode='w')
 
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fileHandler.setFormatter(formatter)
 
    # add handler to logger object
    logger.addHandler(fileHandler)
  
    # log the exceptions to the logger
    def excepthook(*args):
        logger.error("Uncaught exception:", exc_info=args)

    sys.excepthook = excepthook

    return logger

def retryRemove(function, path, excinfo):
    ''' Take a nap and try again.
    
    Address AFS/NSF problems with left-over lock files which prevents
    the 'shutil.rmtree' to delete the directory. The idea is to wait at most 20 sec
    for the fs to automatically remove these lock files and try again.
    Inspired from some GANGA code.
    
    '''   
    
    logger = logging.getLogger('cmgPostProcessing.retryRemove')
    
    for delay in 1, 3, 6, 10:
        
        if not os.path.exists(path): 
            break
        
        time.sleep(delay) 
        shutil.rmtree(path, ignore_errors=True)
        
    # 
    if not os.path.exists(path): 
        logger.debug("\n Path \n    %s \n deleted \n", path)  
    else:
        os.system("lsof +D " + path) 
        
        # not nice, but try to force - however, even 'rm -rf' can fail for 'Device or resource busy'
        os.system("rm -rf " + path)
        logger.debug("\n Try to delete path \n    %s \n by force using 'rm -rf' \n", path)  
    
    # last check before giving up  
    if os.path.exists(path): 
        exctype, value = excinfo[:2]
        logger.debug(
            "\n Unable to remove path \n    %s \n from the system." + \
            "\n Reason: %s:%s" + \
            "\n There might be some AFS/NSF lock files left over. \n", 
            path, exctype, value
            )
        

def getSamples(args):
    '''Return a list of components to be post-processed.
    
    No logger here, as the log file is determined with variables computed here.
    Simply exit if the required cmgTuples set or one of the samples do not exist, 
    printing the non-existing required set name.
    
    The sample processed will be written eventually in the logger,
    after a call to this function.
    
    Create also the output main directory, if it does not exist.
    '''

    cmgTuples = args.cmgTuples
    processSamples = args.processSamples
    
    targetDir = args.targetDir
    processingEra = args.processingEra
    processingTag = args.processingTag



    if cmgTuples == "Data_25ns":
        # from Workspace.DegenerateStopAnalysis.cmgTuples_Data25ns import *
        #import Workspace.DegenerateStopAnalysis.cmgTuples_Data25ns as cmgSamples
        #import Workspace.DegenerateStopAnalysis.cmgTuples_Data25ns_scan as cmgSamples
        import Workspace.DegenerateStopAnalysis.cmgTuples_Data25ns_v6 as cmgSamples
    elif cmgTuples == "Data_50ns":
        import Workspace.DegenerateStopAnalysis.cmgTuples_Data50ns_1l as cmgSamples
    #elif cmgTuples == "RunIISpring15DR74_25ns":
    #    import Workspace.DegenerateStopAnalysis.cmgTuples_Spring15_7412pass2 as cmgSamples
    elif cmgTuples == "RunIISpring15DR74_25ns_v4":
        import Workspace.DegenerateStopAnalysis.cmgTuples_Spring15_7412pass2_mAODv2_v4 as cmgSamples
    elif cmgTuples == "RunIISpring15DR74_25ns":
        import Workspace.DegenerateStopAnalysis.cmgTuples_Spring15_7412pass2_mAODv2_v6 as cmgSamples
    elif cmgTuples == "RunIISpring15DR74_50ns":
        import Workspace.DegenerateStopAnalysis.cmgTuples_Spring15_50ns as cmgSamples
    else:
        # use the cmgTuples values to find the cmgSamples definition file
        moduleName = 'cmgTuples_'  + cmgTuples
        moduleFullName = 'Workspace.DegenerateStopAnalysis.' + moduleName
        
        cmssw_base = os.environ['CMSSW_BASE']
        sampleFile = os.path.join(cmssw_base, 'src/Workspace/DegenerateStopAnalysis/python') + \
            '/' + moduleName + '.py'

        try:
            cmgSamples = importlib.import_module(moduleFullName)
        except ImportError, err:      
            print 'ImportError:', err
            print "\n The required set of CMG tuples \n cmgTuples: {0} \n ".format(cmgTuples) + \
                "with expected sample definition file \n {0} \n does not exist.".format(sampleFile), \
                "\n Correct the name and re-run the script. \n Exiting."
            sys.exit()
   

    if args.preselect:
        outDir = os.path.join(targetDir, processingEra, processingTag, cmgTuples, args.skim, 'preselection',  args.leptonSelection )
    else:
        outDir = os.path.join(targetDir, processingEra, processingTag, cmgTuples, args.skim, args.leptonSelection )
    

    # samples
    
    allComponentsList = [] 
    
    #processSamples = processSamples.replace(' ', '')
    #if len(processSamples):
    #    processSamplesList = processSamples.split(',')
        
    processSamplesList = processSamples
    for sampleName in processSamplesList:
        foundSample = False
        
        # cmgSamples.samples contains components or list of components  
        try:
            sampleRequested = getattr(cmgSamples, sampleName)
            
            if isinstance(sampleRequested, dict):
                # single component
                if (sampleName == sampleRequested['cmgComp'].name):
                    allComponentsList.append(sampleRequested)
                    foundSample = True
                    continue      
                else:
                    print "WARNING:  Sample name is not consistant with the cmgComp name"
            elif isinstance(sampleRequested, list):
                # list of components - add all components
                for comp in sampleRequested:
                        allComponentsList.append(comp)
                        foundSample = True
                continue 
            else:
                print "\n Not possible to build list of components for {0} .".format(sampleName), \
                "\n Exiting."
                print "Requested Sample:", sampleRequested
                sys.exit()
                
                    
        except AttributeError:
            sampleRequested = cmgSamples.samples + cmgSamples.allSignals

            if isinstance(sampleRequested, dict):
                # single component
                if (sampleName == sampleRequested['cmgComp'].name):
                    allComponentsList.append(sampleRequested)
                    foundSample = True
                    break            
            elif isinstance(sampleRequested, list):
                # list of components
                for comp in sampleRequested:
                    print "\n sampleRequested \n", (pprint.pformat(comp)), "\n"
                    if (sampleName == comp['cmgComp'].name):
                        allComponentsList.append(comp)
                        foundSample = True
                        break 
            else:
                print "\n Not possible to build list of components for {0}".format(sampleName), \
                "\n Exiting."
                sys.exit()
                
                
        
        if not foundSample:
            print "\n List of available samples in cmgTuples set {0}: \n {1} \n".format(
                cmgTuples, pprint.pformat(cmgSamples.samples)
                )
            print "\n List of available signal samples in cmgTuples set {0}: \n {1} \n".format(
                cmgTuples, pprint.pformat(cmgSamples.allSignals)
                )
                    
            print "\n Requested sample {0} not available in CMG samples.".format(sampleName), \
                "\n Re-run the job with existing samples.", \
                "\n Exiting."
            sys.exit() 
    
    # create the target output directory, if it does not exist, if sample definition is OK
    if not os.path.exists(outDir):
        os.makedirs(outDir)

    if hasattr(cmgSamples,"mass_dict"):
        #mass_dict = cmgSamples.mass_dict
        mass_dict = cmgSamples.mass_dict_samples
    else:
        mass_dict = {}


    #    
    return allComponentsList, outDir, mass_dict
    

 



def eventsSkimPreselect(skimName, leptonSelection, preselectFlag, signalMasses=[]):
    '''Define the skim condition, including preselection if required.
    
    The skim condition depends on the skim name, the lepton selection, and on the
    event preselection. 
    '''

    logger = logging.getLogger('cmgPostProcessing.eventsSkimPreselect')
    
    # hard cut on lepton (fixed value, given here)
    lepton_soft_hard_cut  = 30 # GeV

    
    skimCond = "(1)"
    
    if not skimName:
        pass
    elif skimName.startswith('met'):
        skimCond = "met_pt>" + str(float(skimName[3:]))
    elif skimName == 'HT400':
        skimCond = "Sum$(Jet_pt)>400"
    elif skimName == 'HT400ST200': 
        skimCond = "Sum$(Jet_pt)>400&&(LepGood_pt[0]+met_pt)>200"
    elif skimName == 'lheHThigh': 
        skimCond += "&&(lheHTIncoming>=600)"
    elif skimName == 'lheHTlow': 
        skimCond += "&&(lheHTIncoming<600)"
    else:
        raise Exception("Skim Condition Not recognized: %s"%skimName)
        pass
    
    # In case a lepton selection is required, loop only over events where there is one 
    if leptonSelection == 'soft':
        skimCond += "&&(Sum$(LepGood_pt>5&&LepGood_pt<{ptCut} &&abs(LepGood_eta)<2.4)>=1" + \
                   " || Sum$(LepOther_pt>5&&LepOther_pt<{ptCut} && abs(LepOther_eta)<2.4)>=1 " + \
                   ")".format(ptCut=lepton_soft_hard_cut)
    elif leptonSelection == 'hard':
        # skimCond += "&&Sum$(LepGood_pt>25&&LepGood_relIso03<0.4&&abs(LepGood_eta)<2.4)>=1"
        skimCond += "&&Sum$(LepGood_pt>%s&&abs(LepGood_eta)<2.4)>=1" % lepton_soft_hard_cut
    elif leptonSelection == 'dilep':
        # skimCond += "&&Sum$(LepGood_pt>25&&LepGood_relIso03<0.4&&abs(LepGood_eta)<2.4)>=1"
        skimCond += "&&Sum$(LepGood_pt>15&&abs(LepGood_eta)<2.4)>1"
    elif leptonSelection == 'inc':
        # skimCond += "&&Sum$(LepGood_pt>25&&LepGood_relIso03<0.4&&abs(LepGood_eta)<2.4)>=1"
        # skimCond += "&&Sum$(abs(LepGood_eta)< 2.5)>=1"
        skimCond += ""
    else:
        pass
    
    # overwrite lepton selection for inclusive skim     
    if skimName == 'inc':
        skimCond = "(1)"
      
    logger.info("\n Jobs running with skim = '%s' \n Skimming condition: \n  %s \n ", skimName, skimCond)
    
    if preselectFlag:
        metCut = "(met_pt>200)"
        leadingJet100 = "((Max$(Jet_pt*(abs(Jet_eta)<2.4 && Jet_id) ) > 100 ) >=1)"
        HTCut    = "(Sum$(Jet_pt*(Jet_pt>30 && abs(Jet_eta)<2.4 && (Jet_id)) ) >200)"

        preselectionCuts = "(%s)"%'&&'.join([metCut,leadingJet100,HTCut])
        skimCond += "&&%s"%preselectionCuts

        logger.info("\n Applying preselection cuts: %s ", preselectionCuts)
        logger.info("\n Skimming condition with preselection: \n  %s \n", skimCond)
    else:
        logger.info("\n No preselection cuts are applied for skim %s \n Skimming condition unchanged \n", skimName)
        pass

    if signalMasses:
        mstop = signalMasses[0]
        mlsp  = signalMasses[1]
        skimCond +="&& (GenSusyMStop==%s && GenSusyMNeutralino==%s)"%(mstop,mlsp)
        logger.info("\n Processing Signal Scan for MStop:%s  MLSP: %s "%(mstop, mlsp ))
        

    #
    return skimCond

 
 
def rwTreeClasses(sample, isample, args, temporaryDir, params={} ):
    '''Define the read / write tree classes for data and MC.
    
    '''
    logger = logging.getLogger('cmgPostProcessing.rwTreeClasses')
    
    # define the branches and the variables to be kept and/or read for data and MC
    
    # MC samples only
    
    # common branches already defined in cmgTuples
    branchKeepStrings_MC = [ 
        'nTrueInt', 'genWeight', 'xsec', 'puWeight', 
        'GenSusyMScan1', 'GenSusyMScan2', 'GenSusyMScan3', 'GenSusyMScan4', 'GenSusyMGluino', 
        'GenSusyMGravitino', 'GenSusyMStop', 'GenSusyMSbottom', 'GenSusyMStop2', 'GenSusyMSbottom2', 
        'GenSusyMSquark', 'GenSusyMNeutralino', 'GenSusyMNeutralino2', 'GenSusyMNeutralino3', 
        'GenSusyMNeutralino4', 'GenSusyMChargino', 'GenSusyMChargino2', 
        'ngenLep', 'genLep_*', 
        'nGenPart', 'GenPart_*',
        'ngenPartAll','genPartAll_*' ,
        'ngenTau', 'genTau_*', 
        'ngenLepFromTau', 'genLepFromTau_*', 
        'GenJet_*',
        #'GenTracks_*',
                          ]
    
    readVariables_MC = []
    aliases_MC = []
    newVariables_MC = []
    
    readVectors_MC = []
    
    aliases_MC.extend(['genMet:met_genPt', 'genMetPhi:met_genPhi'])
    
    
    # data and MC samples 
    
    # common branches already defined in cmgTuples

    trackMinPtList = params['trackMinPtList'] 
    hemiSectorList = params['hemiSectorList']
    nISRsList      = params['nISRsList']


    branchKeepStrings_DATAMC = [
        'run', 'lumi', 'evt', 'isData', 'rho', 'nVert', 
        'nJet25', 'nBJetLoose25', 'nBJetMedium25', 'nBJetTight25', 
        'nJet40', 'nJet40a', 'nBJetLoose40', 'nBJetMedium40', 'nBJetTight40', 
        'nLepGood20', 'nLepGood15', 'nLepGood10', 
        'htJet25', 'mhtJet25', 'htJet40j', 'htJet40', 'mhtJet40', 
        'nSoftBJetLoose25', 'nSoftBJetMedium25', 'nSoftBJetTight25', 
        'met*','puppi*',
        'Flag_*','HLT_*',
        #'MET*','PFMET*','Calo*', 'Mono*', 'Mu*','TkMu*','L1Single*', 'L2Mu*',
        #'nFatJet','FatJet_*', 
        'nJet', 'Jet_*', 
        'nLepGood', 'LepGood_*', 
        'nLepOther', 'LepOther_*', 
        'nTauGood', 'TauGood_*',
        #'Tracks_*', 'isoTrack_*',
        ] 
    
    readVariables_DATAMC = []
    aliases_DATAMC = []
    newVariables_DATAMC = []
    readVectors_DATAMC = []
    

    
    readVariables_DATAMC.extend(['met_pt/F', 'met_phi/F'])
    aliases_DATAMC.extend([ 'met:met_pt', 'metPhi:met_phi'])
    newVariables_DATAMC.extend(['weight/F'])
    
    readVectors_DATAMC.extend([
        {'prefix':'LepOther',  'nMax':8, 
            'vars':['pt/F', 'eta/F', 'phi/F', 'pdgId/I', 'relIso03/F', 'tightId/I', 
                    'miniRelIso/F','mass/F','sip3d/F','mediumMuonId/I', 'dxy/F', 'dz/F',  "relIso04/F",
                    'mvaIdPhys14/F','lostHits/I', 'convVeto/I']},
        {'prefix':'LepGood',  'nMax':8, 
            'vars':['pt/F', 'eta/F', 'phi/F', 'pdgId/I', 'relIso03/F', 'tightId/I', 
                    'miniRelIso/F','mass/F','sip3d/F','mediumMuonId/I', 'dxy/F', 'dz/F', "relIso04/F",
                    'mvaIdPhys14/F','lostHits/I', 'convVeto/I']},
        {'prefix':'Jet',  'nMax':100, 
            'vars':['pt/F', 'eta/F', 'phi/F', 'id/I','btagCSV/F', 'btagCMVA/F', 'mass/F']},
      ])
    readVectors_MC.extend([
        {'prefix':'GenPart',  'nMax':30, 
            'vars':['pt/F', 'eta/F', 'phi/F', 'pdgId/I', 'mass/F', 'motherId/I' ]},
      ])
     
    if args.leptonSelection in ['soft', 'hard', 'inc']:
        
        newVariables_DATAMC.extend([
            'nBJetMediumCSV30/I', 'nSoftBJetsCSV/F', 'nHardBJetsCSV/F',  
            'nJet30/I','htJet30j/F','nJet60/I','nJet100/I', 'nJet110/I','nJet325/I' ,
            ])
        
        newVariables_DATAMC.extend([
            'nLooseSoftLeptons/I', 'nLooseSoftPt10Leptons/I', 'nLooseHardLeptons/I', 
            'nTightSoftLeptons/I', 'nTightHardLeptons/I',
            ])
        
        newVariables_DATAMC.extend([
            'singleMuonic/I', 'singleElectronic/I', 'singleLeptonic/I', 
            ])
        
        newVariables_DATAMC.extend([
            'leptonPt/F','leptonMiniRelIso/F','leptonRelIso03/F' ,
            'leptonEta/F',  'leptonPhi/F', 'leptonPdg/I/0', 'leptonInd/I/-1', 
            'leptonMass/F', 'leptonDz/F', 'leptonDxy/F', 
            
            'lepGoodPt/F','lepGoodMiniRelIso/F','lepGoodRelIso03/F' , 'lepGoodRelIso04/F',
            'lepGoodAbsIso/F' ,'lepGoodEta/F',  'lepGoodPhi/F', 'lepGoodPdgId/I/0', 'lepGoodInd/I/-1', 
            'lepGoodMass/F', 'lepGoodDz/F', 'lepGoodDxy/F','lepGoodMediumMuonId/I','lepGoodSip3d/F',
            
            'lepOtherPt/F','lepOtherMiniRelIso/F','lepOtherRelIso03/F' , 'lepOtherRelIso04/F',
            'lepOtherAbsIso/F' ,'lepOtherEta/F',  'lepOtherPhi/F', 'lepOtherPdgId/I/0', 'lepOtherInd/I/-1', 
            'lepOtherMass/F', 'lepOtherDz/F', 'lepOtherDxy/F','lepOtherMediumMuonId/I','lepOtherSip3d/F',
            
            'lepPt/F','lepMiniRelIso/F','lepRelIso03/F' , 'lepRelIso04/F',
            'lepAbsIso03/F' ,'lepAbsIso04/F', 'lepEta/F',  'lepPhi/F', 'lepPdgId/I/0', 'lepInd/I/-1', 
            'lepMass/F', 'lepDz/F', 'lepDxy/F','lepMediumMuonId/I','lepSip3d/F',
            'nlep/I',


            "Flag_Veto_Event_List/I/1",

            #Lepton Selection with Pt < 30 , for sync purposes
            #'lep30Pt/F','lep30MiniRelIso/F','lep30RelIso03/F' , 'lep30RelIso04/F',
            #'lep30AbsIso/F' ,'lep30Eta/F',  'lep30Phi/F', 'lep30PdgId/I/0', 'lep30Ind/I/-1', 
            #'lep30Mass/F', 'lep30Dz/F', 'lep30Dxy/F','lep30MediumMuonId/I','lep30Sip3d/F',
            #'nlep30/I',


            ])
            
        newVariables_DATAMC.extend([
            'Q80/F','CosLMet/F',
            'st/F', 'deltaPhi_Wl/F',
            'mt/F',
            ])
              
        newVariables_DATAMC.extend([
            'jet1Pt/F','jet1Eta/F','jet1Phi/F', 
            'jet2Pt/F','jet2Eta/F','jet2Phi/F',
            'deltaPhi_j12/F', 'dRJet1Jet2/F','deltaPhi30_j12/F' , 'deltaPhi60_j12/F',
            'JetLepMass/F','dRJet1Lep/F',
            'J3Mass/F',


            "stopIndex1/I/-1", "stopIndex2/I/-1",
            "lspIndex1/I/-1", "lspIndex2/I/-1",
            "gpLepIndex1/I/-1", "gpLepIndex2/I/-1",
            "gpBIndex1/I/-1", "gpBIndex2/I/-1",
            "stops_pt/F/-1", "stops_eta/F/-999", "stops_phi/F/-999", 
            "lsps_pt/F/-1", "lsps_eta/F/-999", "lsps_phi/F/-999", 

        
            "jet1Index/I", "jet2Index/I", "jet3Index/I", 
            "b1Index/I", "b2Index/I",
            #"lep1Index/I", "lep2Index/I", 
            "nMuons/I", "nMuonsPt30/I",
            #"nElectrons/I", "nElectronsPt30/I"
            "looseMuonIndex1/I", "looseMuonPt30Index1/I",
            "looseMuonIndex2/I", "looseMuonPt30Index2/I",
            "looseElectronIndex1/I", "looseElectronPt30Index1/I",
            "looseElectronIndex2/I", "looseElectronPt30Index2/I",
            "looseLeptonIndex1/I", "looseLeptonPt30Index1/I",
            "looseLeptonIndex2/I", "looseLeptonPt30Index2/I",
            #"mu0Index/I", "mu1Index/I",
            #"el0Index/I", "el1Index/I",
            ])
        
        #newVariables_DATAMC.extend([
        #    'mt2w/F'
        #    ] )
    
    
    if args.processTracks:
        trkVar="Tracks"
        trkCountVars = [ "n%s"%trkVar ] 
        trkCountVars.extend([ 
                    "n%sOpp%sJet%s"%(trkVar,hemiSec,nISRs) for hemiSec in hemiSectorList  for nISRs in nISRsList     
                    ])
        newTrackVars = []
        for minTrkPt in trackMinPtList:
            ptString = str(minTrkPt).replace(".","p")
            newTrackVars.extend( [ x+"_pt%s"%ptString+"/I" for x in  trkCountVars  ] )
        newVariables_DATAMC.extend(newTrackVars) 
        readVectors_DATAMC.append(
            {'prefix':'Tracks'  , 'nMax':300, 
                'vars':[
                          'pt/F', 'eta/F', 'phi/F', "dxy/F", "dz/F", 'pdgId/I' , 'fromPV/I' , 
                          "matchedJetIndex/I", "matchedJetDr/F", "CosPhiJet1/F", "CosPhiJet12/F", "CosPhiJetAll/F",
                          "mcMatchId/I", "mcMatchIndex/I", "mcMatchPtRatio/F", "mcMatchDr/F"
                       ]   })
                      


    if args.processGenTracks:
        genTrkVar="GenTracks"
        genTrkCountVars = [ "n%s"%genTrkVar ] 
        genTrkCountVars.extend([ 
                    "n%sOpp%sJet%s"%(genTrkVar,hemiSec,nISRs) for hemiSec in hemiSectorList  for nISRs in nISRsList     
                    ])
        newGenTrackVars = []
        for minGenTrkPt in trackMinPtList:
            ptString = str(minGenTrkPt).replace(".","p")
            newGenTrackVars.extend( [ x+"_pt%s"%ptString+"/I" for x in  genTrkCountVars  ] )
        newVariables_DATAMC.extend(newGenTrackVars)        
        readVectors_MC.append(
            {'prefix':genTrkVar  , 'nMax':300, 
                'vars':[
                          'pt/F', 'eta/F', 'phi/F', "dxy/F", "dz/F", 'pdgId/I' , 'fromPV/I' , 
                          "matchedJetIndex/I", "matchedJetDr/F", "CosPhiJet1/F", "CosPhiJet12/F", "CosPhiJetAll/F",
                          "mcMatchId/I", "mcMatchIndex/I", "mcMatchPtRatio/F", "mcMatchDr/F"
                       ]})
        readVectors_MC.extend([
            {'prefix':'GenJet'  , 'nMax':100, 'vars':['pt/F', 'eta/F', 'phi/F', 'mass/F' ] },
            ])
   


 
    
    # data samples only
    
    # branches already defined in cmgTuples
    branchKeepStrings_DATA = []
    
    readVariables_DATA = []
    aliases_DATA = []
    newVariables_DATA = []
    
    readVectors_DATA = []
 

    # sample dependent part
    
    if sample['isData']: 
        branchKeepStrings = branchKeepStrings_DATAMC + branchKeepStrings_DATA
    
        readVariables = readVariables_DATAMC + readVariables_DATA
        aliases = aliases_DATAMC + aliases_DATA
        readVectors = readVectors_DATAMC + readVectors_DATA
        newVariables = newVariables_DATAMC + newVariables_DATA
    else:
        branchKeepStrings = branchKeepStrings_DATAMC + branchKeepStrings_MC
    
        readVariables = readVariables_DATAMC + readVariables_MC
        aliases = aliases_DATAMC + aliases_MC
        readVectors = readVectors_DATAMC + readVectors_MC
        newVariables = newVariables_DATAMC + newVariables_MC


    readVars = [convertHelpers.readVar(v, allowRenaming=False, isWritten=False, isRead=True) for v in readVariables]
    newVars = [convertHelpers.readVar(v, allowRenaming=False, isWritten = True, isRead=False) for v in newVariables]
  
    for v in readVectors:
        readVars.append(convertHelpers.readVar('n'+v['prefix']+'/I', allowRenaming=False, isWritten=False, isRead=True))
        v['vars'] = [convertHelpers.readVar(
            v['prefix']+'_'+vvar, allowRenaming=False, isWritten=False, isRead=True) for vvar in v['vars']
            ]

    logger.debug("\n read variables (readVars) definition: \n %s \n", pprint.pformat(readVars))
    logger.debug("\n aliases definition: \n %s \n", pprint.pformat(aliases))
    logger.debug("\n read vectors (readVectors) definition: \n %s \n", pprint.pformat(readVectors))
    logger.debug("\n new variable (newVars) definition: \n %s \n", pprint.pformat(newVars))

    convertHelpers.printHeader("Compiling class to write")
    writeClassName = "ClassToWrite_"+str(isample)
    writeClassString = convertHelpers.createClassString(className=writeClassName, vars= newVars, vectors=[], 
        nameKey = 'stage2Name', typeKey = 'stage2Type')
    logger.debug("\n writeClassString definition: \n%s \n", writeClassString)
    saveTree = convertHelpers.compileClass(className=writeClassName, classString=writeClassString, tmpDir=temporaryDir)

    readClassName = "ClassToRead_"+str(isample)
    readClassString = convertHelpers.createClassString(className=readClassName, vars=readVars, vectors=readVectors, 
        nameKey = 'stage1Name', typeKey = 'stage1Type', stdVectors=False)
    convertHelpers.printHeader("Class to Read")
    logger.debug("\n readClassString definition: \n%s \n", readClassString)
    readTree = convertHelpers.compileClass(className=readClassName, classString=readClassString, tmpDir=temporaryDir)

    #
    return branchKeepStrings, readVars, aliases, readVectors, newVars, readTree, saveTree
   
   
def getTreeFromChunk(c, skimCond, iSplit, nSplit):
    '''Get a tree from a chunck.
    
    '''
     
    logger = logging.getLogger('cmgPostProcessing.getTreeFromChunk')
   
    if not c.has_key('file'):return
    rf = ROOT.TFile.Open(c['file'])
    assert not rf.IsZombie()
    rf.cd()
    tc = rf.Get('tree')
    nTot = tc.GetEntries()
    fromFrac = iSplit/float(nSplit)
    toFrac   = (iSplit+1)/float(nSplit)
    start = int(fromFrac*nTot)
    stop  = int(toFrac*nTot)
    ROOT.gDirectory.cd('PyROOT:/')

    logger.debug(
        "\n Copy tree from source. Statistics before skimming and preselection: " + \
        "\n    total number of events found: %i " + \
        "\n    split counter: %i < %i, first event: %i, last event %i (%i events) \n",
        nTot, iSplit, nSplit, start, stop, stop-start)

    t = tc.CopyTree(skimCond,"",stop-start,start)
    
    nTotSkim = t.GetEntries()
    logger.debug(
        "\n Statistics after skimming and preselection: " + \
        "\n    total number of events found: %i \n",
        nTotSkim)

    tc.Delete()
    del tc
    rf.Close()
    del rf
    return t



def processGenSusyParticles(readTree,splitTree,saveTree, sample):


    if sample['cmgComp'].isData:
        return


    genPart           =  cmgObject(readTree, "GenPart")

    stopIndices       =  genPart.getSelectionIndexList( readTree,
                            lambda readTree, gp, igp: abs( gp.pdgId[igp] ) == 1000006
                            )
    if len(stopIndices)==0:    # not a susy event... move on
        return 


    isrIndices       =  genPart.getSelectionIndexList( readTree,
                            lambda readTree, gp, igp: abs( gp.pdgId[igp] ) != 1000006 and gp.motherId==-9999
                            )
    lspIndices        =  genPart.getSelectionIndexList( readTree,
                            lambda readTree, gp, igp: abs( gp.pdgId[igp] ) == 1000022
                            )
    bIndices          =  genPart.getSelectionIndexList( readTree,
                            lambda readTree, gp, igp: abs( gp.pdgId[igp] ) == 5
                            )
    lepIndices        =  genPart.getSelectionIndexList( readTree,
                            lambda readTree, gp, igp: abs( gp.pdgId[igp] ) in [11,13]
                            )

    saveTree.stopIndex1 = stopIndices[0]
    saveTree.stopIndex2 = stopIndices[1]

    saveTree.lspIndex1 = lspIndices[0]
    saveTree.lspIndex2 = lspIndices[1]
    saveTree.gpBIndex1 = bIndices[0]
    saveTree.gpBIndex2 = bIndices[1]
    saveTree.gpLepIndex1 = lepIndices[0] if len(lepIndices) >0 else -1
    saveTree.gpLepIndex2 = lepIndices[1] if len(lepIndices) >1 else -1 

    stop1_lv = ROOT.TLorentzVector()
    stop2_lv = ROOT.TLorentzVector()

    stop1_lv.SetPtEtaPhiM( genPart.pt[saveTree.stopIndex1], genPart.eta[saveTree.stopIndex1], genPart.phi[saveTree.stopIndex1], genPart.mass[saveTree.stopIndex1]  )
    stop2_lv.SetPtEtaPhiM( genPart.pt[saveTree.stopIndex2], genPart.eta[saveTree.stopIndex2], genPart.phi[saveTree.stopIndex2], genPart.mass[saveTree.stopIndex2]  )

    stops = stop1_lv + stop2_lv

    saveTree.stops_pt = stops.Pt()
    saveTree.stops_eta = stops.Eta()
    saveTree.stops_phi = stops.Phi()



    lsp1_lv = ROOT.TLorentzVector()
    lsp2_lv = ROOT.TLorentzVector()
    lsp1_lv.SetPtEtaPhiM( genPart.pt[saveTree.lspIndex1], genPart.eta[saveTree.lspIndex1], genPart.phi[saveTree.lspIndex1], genPart.mass[saveTree.lspIndex1]  )
    lsp2_lv.SetPtEtaPhiM( genPart.pt[saveTree.lspIndex2], genPart.eta[saveTree.lspIndex2], genPart.phi[saveTree.lspIndex2], genPart.mass[saveTree.lspIndex2]  )
    lsps = lsp1_lv + lsp2_lv
    saveTree.lsps_pt = lsps.Pt()
    saveTree.lsps_eta = lsps.Eta()
    saveTree.lsps_phi = lsps.Phi()




cmgObject = cmgObjectSelection.cmgObject

ptSwitch = 25
relIso = 0.2
absIso = 5

#muSelector =    lambda readTree,lep,i: \
#                        ( abs(lep.pdgId[i])==13)\
#                        and (lep.pt[i] > 5 )\
#                        and abs(lep.eta[i]) < 2.5\
#                        and abs(lep.dxy[i]) < 0.05\
#                        and abs(lep.dz[i]) < 0.2\
#                        and lep.sip3d[i] < 4\
#                        and lep.mediumMuonId[i] == 1\
#                        and ((lep.pt[i] >= ptSwitch and lep.relIso04[i] < relIso ) or (lep.pt[i] < ptSwitch  and lep.relIso04[i] * lep.pt[i] < absIso ) )
#
#
#muPt30Selector =    lambda readTree,lep,i: \
#                        ( abs(lep.pdgId[i])==13)\
#                        and (lep.pt[i] > 5 )\
#                        and (lep.pt[i] < 30 )\
#                        and abs(lep.eta[i]) < 2.5\
#                        and abs(lep.dxy[i]) < 0.05\
#                        and abs(lep.dz[i]) < 0.2\
#                        and lep.sip3d[i] < 4\
#                        and lep.mediumMuonId[i] == 1\
#                        and ((lep.pt[i] >= ptSwitch and lep.relIso04[i] < relIso ) or (lep.pt[i] < ptSwitch  and lep.relIso04[i] * lep.pt[i] < absIso ) )





def processLeptons(leptonSelection, readTree, splitTree, saveTree, params):
    '''Process leptons. 
    
    TODO describe here the processing.
    '''

    logger = logging.getLogger('cmgPostProcessing.processLeptons')
    
    # initialize returned variables (other than saveTree)
    
    lep = None

    LepSel     = params['LepSel']  
    LepSelPt30 = params['LepSelPt30']  # use for Sync
    
    lepSelector =  cmgObjectSelection.lepSelectorFunc( LepSel)
    muSelector =  cmgObjectSelection.lepSelectorFunc( {"mu":LepSel['mu'] } )
    elSelector =  cmgObjectSelection.lepSelectorFunc( {"el":LepSel['el'] } )

    #lepSelectorPt30 =  cmgObjectSelection.lepSelectorFunc( LepSelPt30)
    muSelectorPt30 =  cmgObjectSelection.lepSelectorFunc( {"mu":LepSelPt30['mu'] } )
    #elSelectorPt302 =  cmgObjectSelection.lepSelectorFunc( {"el":LepSelPt30['el'] } )


    if leptonSelection in ['soft','hard','inc']:

        # get all >=loose lepton indices
        lepObj = cmgObject(readTree, "LepGood")


        #lepList      =  lepObj.getSelectionIndexList(readTree, muSelector )

        lepList     =  lepObj.getSelectionIndexList(readTree, muSelector )
        lepPt30List  =  lepObj.getSelectionIndexList(readTree, muSelectorPt30, lepList )

        #lepPt30List     =  lepObj.getSelectionIndexList(readTree, muSelectorPt302 )

        #for iLep in lepList:
        #    if lepObj.sip3d[iLep] > 4:
        #        print LepSel['mu']
        #        print iLep, lepObj.sip3d[iLep]

        #if lepList != lepList2:
        #    print "  ------------------------------------------------------"
        #    print lepList
        #    print lepList2
        #    assert False
        #if lepPt30List != lepPt30List2:
        #    varList = ['pt', 'eta', 'phi', 'miniRelIso','relIso03','relIso04', 'dxy', 'dz', 'pdgId', 'sip3d','mediumMuonId']
        #    print " 30 ----i--------------------------------------------------"
        #    print lepPt30List
        #    print lepPt30List2
        #    print [lepObj.pt[i] for i in range(lepObj.nObj)]
        #    print [ [i, var,  getattr(lepObj,var)[i] ] for i in range(lepObj.nObj) for var in varList ]
        #    assert False

        
        saveTree.nMuons = len(lepList)
        saveTree.nMuonsPt30 = len(lepPt30List)



        #print saveTree.looseMuonIndex1        
        #if saveTree.nMuons:
        #    saveTree.looseMuonIndex1 = lepList[0]
        #    print "yes", lepList[0], saveTree.looseMuonIndex1
        #else:
        #    saveTree.looseMuonIndex1 = -1
        #    print "no", lepList, saveTree.looseMuonIndex1

    

        saveTree.looseMuonIndex1     =  lepList[0]     if saveTree.nMuons     > 0 else -1
        saveTree.looseMuonPt30Index1 =  lepPt30List[0] if saveTree.nMuonsPt30 > 0 else -1
        saveTree.looseMuonIndex2     =  lepList[1]     if saveTree.nMuons     > 1 else -1
        saveTree.looseMuonPt30Index2 =  lepPt30List[1] if saveTree.nMuonsPt30 > 1 else -1

        #if saveTree.nMuons:
        #    print saveTree.nMuons, lepList, saveTree.looseMuonIndex1, saveTree.looseMuonIndex2
        #    print lepList[0], saveTree.nMuons 
        #    print lepList[0] if saveTree.nMuons > 0 else -1 
        #    print "---------------------"

        #lepPt30List



        looseLepInd = cmgObjectSelection.cmgLooseLepIndices(
            readTree, ptCuts=(7,5), absEtaCuts=(2.5,2.4), 
            ele_MVAID_cuts={'eta08':0.35 , 'eta104':0.20,'eta204': -0.52} 
            ) 
        
        # split loose leptons into soft (pT < lepton_soft_hard_cut) and hard 
        # leptons (> lepton_soft_hard_cut) 
        # FIXME: unify the cut from skimming with this cut?
        lepton_soft_hard_cut = 30.
        looseSoftLepInd, looseHardLepInd = cmgObjectSelection.splitIndList(
            readTree.LepGood_pt, looseLepInd, lepton_soft_hard_cut)
        
        # select tight hard leptons (use POG ID)
        tightHardLepInd = filter(lambda i:
            (
             abs(readTree.LepGood_pdgId[i])==11 and 
             readTree.LepGood_miniRelIso[i]<0.1 and 
             cmgObjectSelection.ele_ID_eta(
                readTree,nLep=i,ele_MVAID_cuts={'eta08':0.73 , 'eta104':0.57,'eta204':  0.05}) and 
             readTree.LepGood_tightId[i]>=3
             ) or 
            (
             abs(readTree.LepGood_pdgId[i])==13 and 
             readTree.LepGood_miniRelIso[i]<0.2 and 
             readTree.LepGood_tightId[i]), looseHardLepInd)  
        saveTree.nTightHardLeptons = len(tightHardLepInd)

        varList = ['pt', 'eta', 'phi', 'miniRelIso','relIso03','relIso04', 'dxy', 'dz', 'pdgId', 'sip3d','mediumMuonId']

        lepGoods =   [hephyHelpers.getObjDict(splitTree, 'LepGood_',varList, i ) for i in range(readTree.nLepGood)]
        lepOthers =  [hephyHelpers.getObjDict(splitTree, 'LepOther_',varList, i ) for i in range(readTree.nLepOther)]  # use LepGood for sync 
        allLeptons = lepGoods #+ lepOthers
        
        selectedLeptons = filter(cmgObjectSelection.isGoodLepton , allLeptons)
        #selectedLeptons = filter(cmgObjectSelection.isGoodLepton30 , allLeptons)   ## for the sync
        selectedLeptons = sorted(selectedLeptons ,key= lambda lep: lep['pt'], reverse=True)

        logger.debug(
            "\n nlepGood = %i,  nlepOther = %i " + \
            "\n Number of all leptons (Good + Other): %i (Good: %i + Other: %i)"  + \
            "\n Selected leptons:\n  %s  \n"  + \
            "\n Number of selected leptons: %i \n", 
            readTree.nLepGood, readTree.nLepOther, len(allLeptons), 
            len(lepGoods), len(lepOthers),
            pprint.pformat(selectedLeptons), len(selectedLeptons)
            )
                    
        varsToKeep = varList + []

        if selectedLeptons:
            lep = selectedLeptons[0]
            lepName = "lep"
            for var in varsToKeep:
                varName = lepName + var[0].capitalize() + var[1:]
                setattr(saveTree, varName, lep[var])
            saveTree.lepAbsIso04 = lep['relIso04'] * lep['pt'] 
            saveTree.lepAbsIso03 = lep['relIso03'] * lep['pt'] 
            saveTree.nlep = len(selectedLeptons)
            saveTree.singleLeptonic = (saveTree.nlep == 1)
             
            if logger.isEnabledFor(logging.DEBUG):
                logString = "\n Leading selected lepton: "
                for var in varsToKeep:
                    logString += "\n " + lepName + var[0].capitalize() + var[1:] + " = %f"
                logString += "\n"
                logger.debug(
                    logString % 
                    (tuple(getattr(saveTree, lepName + var[0].capitalize() + var[1:]) for var in varsToKeep))
                    )
    
        if saveTree.singleLeptonic:
            saveTree.singleMuonic      =  abs(saveTree.leptonPdg)==13
            saveTree.singleElectronic  =  abs(saveTree.leptonPdg)==11
        else:
            saveTree.singleMuonic      = False 
            saveTree.singleElectronic  = False 





    #
    return saveTree, lep

def selectionJets(readTree, ptCut,etaCut=2.4):
    '''Post-processing standard jet selection. 
    
    '''
    
    jetVariables = ['eta', 'pt', 'phi', 'btagCMVA', 'btagCSV', 'id', 'mass']

    jets = filter(lambda j:
        j['pt'] > ptCut and abs(j['eta']) < etaCut and j['id'], 
        cmgObjectSelection.get_cmg_jets_fromStruct(readTree, jetVariables))
    
    return jets


jetSelectorFunc = cmgObjectSelection.jetSelectorFunc
jetSelector = jetSelectorFunc(pt=30, eta=2.4)




def processJets(leptonSelection, readTree, splitTree, saveTree):
    '''Process jets. 
    
    TODO describe here the processing.
    '''

    logger = logging.getLogger('cmgPostProcessing.processJets')
    
    # initialize returned variables (other than saveTree)
    
    jets = None

    
    
    if leptonSelection in ['soft', 'hard', 'inc']:
        
        # selection of jets
        

        ptCut = 30 
        jets = selectionJets(readTree, ptCut)
        logger.debug("\n Selected jets: %i jets \n %s \n", len(jets), pprint.pformat(jets))
        
        ptCut = 60 
        jets60 = selectionJets(readTree, ptCut)

        ptCut = 100
        jets100 = selectionJets(readTree, ptCut)

        ptCut = 110
        jets110 = selectionJets(readTree, ptCut)



       


        jetObj      =  cmgObject(readTree,"Jet")

        #jet30List   =  jetObj.

        jet30List   =  jetObj.getSelectionIndexList(readTree, jetSelectorFunc(pt=30, eta=2.4)) 
        jet60List   =  jetObj.getSelectionIndexList(readTree, jetSelectorFunc(pt=60, eta=2.4), jet30List) 
        jet100List  =  jetObj.getSelectionIndexList(readTree, jetSelectorFunc(pt=100, eta=2.4), jet60List) 
        jet110List  =  jetObj.getSelectionIndexList(readTree, jetSelectorFunc(pt=110, eta=2.4), jet100List) 
        jet325List  =  jetObj.getSelectionIndexList(readTree, jetSelectorFunc(pt=325, eta=2.4), jet110List) 

        assert jet60List   == jetObj.getSelectionIndexList(readTree, jetSelectorFunc(pt=60, eta=2.4) )
        assert jet100List  == jetObj.getSelectionIndexList(readTree, jetSelectorFunc(pt=100, eta=2.4))
        assert jet110List  == jetObj.getSelectionIndexList(readTree, jetSelectorFunc(pt=110, eta=2.4)) 


        if not len(jets)== len(jet30List):
            print "-------------------------"
            print jets
            print jet30List
        assert len(jets60)==  len(jet60List)
        assert len(jets100)== len(jet100List)
        assert len(jets110)== len(jet110List)




        saveTree.nJet30  = len(jet30List)
        saveTree.nJet60  = len(jet60List)
        saveTree.nJet100 = len(jet100List)
        saveTree.nJet110 = len(jet110List)
        saveTree.nJet325 = len(filter(lambda j: j["pt"] > 325 , jets110))
        
        logger.debug(
            "\n Number of jets: \n  pt > 30 GeV: %i \n  pt > 60 GeV: %i \n  pt > 100 GeV: %i \n  pt > 110 GeV: %i \n  pt > 325 GeV: %i \n", 
            saveTree.nJet30, saveTree.nJet60,  saveTree.nJet100, saveTree.nJet110, saveTree.nJet325
            )
               
        # separation of jets and bJets according to discriminant (CMVA;  CSV - default)
        
        # CMVA Obsolete
        # discCMVA = 0.732                       
        # lightJetsCMVA, bJetsCMVA = cmgObjectSelection.splitListOfObjects('btagCMVA', discCMVA, jets) 

        discCSV = 0.890
        cutSoftHardBJets = 60
        
        lightJetsCSV, bJetsCSV = cmgObjectSelection.splitListOfObjects('btagCSV', discCSV, jets)
        
        #logger.debug("\n Selected CMVA b jets: %i jets \n %s \n", len(bJetsCMVA), pprint.pformat(bJetsCMVA))
        logger.debug("\n Selected CSV b jets: %i jets \n %s \n", len(bJetsCSV), pprint.pformat(bJetsCSV))

        bJets = filter(lambda j: j["btagCSV"] > discCSV , jets)
        
        softBJetsCSV, hardBJetsCSV = cmgObjectSelection.splitListOfObjects('pt', cutSoftHardBJets, bJets)
        
        saveTree.nSoftBJetsCSV = len(softBJetsCSV)
        saveTree.nHardBJetsCSV = len(hardBJetsCSV)
        saveTree.nBJetMediumCSV30 = len(bJetsCSV)
        
        logger.debug(
            "\n Number of soft and hard b jets (CSV): \n  soft: %i \n  hard: %i \n  total: %i \n", 
            saveTree.nSoftBJetsCSV, saveTree.nHardBJetsCSV, saveTree.nBJetMediumCSV30
            )

        # HT as sum of jets pT > 30 GeV
        
        saveTree.htJet30j = sum([x['pt'] for x in jets])

        # save some additional jet quantities, after initialization

        saveTree.jet1Pt = -999.
        saveTree.jet1Eta = -999.
        saveTree.jet1Phi = -999.
        
        saveTree.jet2Pt = -999.
        saveTree.jet2Eta = -999.
        saveTree.jet2Phi = -999.
        
        saveTree.dRJet1Jet2 = -999.
        saveTree.deltaPhi_j12 = -999.


        ### Get indecies for jet1,2,3
        saveTree.jet1Index    = jet30List[0] if saveTree.nJet30 >0       else -1
        saveTree.jet2Index    = jet30List[1] if saveTree.nJet30 >1       else -1
        saveTree.jet3Index    = jet30List[2] if saveTree.nJet30 >2       else -1


        ## USE INDEX FIX
        #print "-------------------------"
        #print saveTree.nJet30 , jetObj.nObj
        #print saveTree.jet1Index, saveTree.jet2Index, saveTree.jet3Index

        saveTree.deltaPhi30_j12 = hephyHelpers.deltaPhi( jetObj.phi[saveTree.jet1Index], jetObj.phi[saveTree.jet2Index]) if saveTree.nJet30 >= 2 else -999
        saveTree.deltaPhi60_j12 = hephyHelpers.deltaPhi( jetObj.phi[ jet60List[0] ], jetObj.phi[ jet60List[1] ]) if saveTree.nJet60 >= 2 else -999

        #saveTree.dRJet1Jet2 = hephyHelpers.deltaR(jets[0], jets[1])

        if saveTree.nJet30 > 0:    
            saveTree.jet1Pt = jets[0]['pt']
            saveTree.jet1Eta = jets[0]['eta']
            saveTree.jet1Phi = jets[0]['phi']
            saveTree.dRJet1Jet2 = -999.

        if saveTree.nJet30 > 1:
            saveTree.jet2Pt = jets[1]['pt']
            saveTree.jet2Eta = jets[1]['eta']
            saveTree.jet2Phi = jets[1]['phi']
            
            saveTree.dRJet1Jet2 = hephyHelpers.deltaR(jets[0], jets[1])
            
        if saveTree.nJet60 == 0:
            saveTree.deltaPhi_j12 = -999.
        elif saveTree.nJet60 == 1:
            saveTree.deltaPhi_j12 = -999.
        else:
            saveTree.deltaPhi_j12 = hephyHelpers.deltaPhi( jets60[0]['phi'], jets60[1]['phi'] ) 
 
        logger.debug(
            "\n Jet separation: \n  dRJet1Jet2: %f \n  deltaPhi_j12: %f \n", 
            saveTree.dRJet1Jet2, saveTree.deltaPhi_j12
            )
    
    #
    return saveTree, jets

def processLeptonJets(leptonSelection, readTree, splitTree, saveTree, lep, jets):
    '''Process correlations between the leading selected lepton and jets. 
    
    Compute:
        dR separation of selected lepton and first jet
        invariant mass of the selected leading lepton and the dR-closest jet
        invariant mass of 1, 2, 3 jets, other than the closest jet associated to lepton 
        
        Jets are considered having mass here, lepton have mass zero.

    '''
    
    logger = logging.getLogger('cmgPostProcessing.processLeptonJets')

    if leptonSelection in ['soft', 'hard', 'inc']:
         
        if (lep is not None) and (saveTree.nJet30 > 0):
            
            saveTree.dRJet1Lep = hephyHelpers.deltaR(jets[0], lep)
            
            # find the dR-closest jet to selected muon
            closestJetIndex = min(range(len(jets)), key=lambda j:hephyHelpers.deltaR(jets[j], lep))
            logger.debug("\n Lepton: \n %s, \n \n Closest jet index: %i, \n Jet: \n %s \n dR(lep, jet): %f \n",
                pprint.pformat(lep), closestJetIndex, pprint.pformat(jets[closestJetIndex]),
                hephyHelpers.deltaR(jets[closestJetIndex], lep))
                    
            # invariant mass of the selected leading lepton and the dR-closest jet            
            saveTree.JetLepMass = helpers.invMass([jets[closestJetIndex], lep])
            
            # invariant mass of 1, 2, 3 jets, other than the closest jet associated to lepton 
        
            indexList = [i for i in xrange(len(jets)) if i != closestJetIndex]  
            logger.debug(
                "\n Number of jets, excluding the closest jet: %i jets \n List of jet indices: \n %s \n ", 
                len(indexList), pprint.pformat(indexList)
                )
                   
            if saveTree.nJet30 == 1: 
                saveTree.J3Mass = 0.
            elif saveTree.nJet30 == 2:
                jetList = [jets[indexList[0]]]
                saveTree.J3Mass = helpers.invMass(jetList)
            elif saveTree.nJet30 == 3:
                jetList = [jets[indexList[0]], jets[indexList[1]]]
                saveTree.J3Mass = helpers.invMass(jetList)
            else:
                jetList = [jets[indexList[0]], jets[indexList[1]], jets[indexList[2]]]
                saveTree.J3Mass = helpers.invMass(jetList)
       
    
            logger.debug(
                "\n dRJet1Lep: %f \n JetLepMass: %f \n J3Mass: %f \n", 
                saveTree.dRJet1Lep, saveTree.JetLepMass, saveTree.J3Mass
                )
            
    #
    return saveTree



def hemiSectorCosine(x):
    return round( math.cos(math.pi- 0.5*(x* math.pi/180)),3)


def processTracksFunction(readTree, splitTree, saveTree, lep, jets, params):
    '''Process tracks. 
    
    TODO describe here the processing.
    '''
    logger = logging.getLogger('cmgPostProcessing.processTracksFunction')

    trackMinPtList = params['trackMinPtList']
    hemiSectorList = params['hemiSectorList']
    nISRsList      = params['nISRsList']



    jets =  cmgObjectSelection.get_cmg_jets_fromStruct(readTree, ['eta', 'pt', 'phi', 'btagCMVA', 'btagCSV', 'id', 'mass'])  
    ### corresponding to 90, 135, 150 degree diff between jet and track
    hemiSectorCosines = {  x:hemiSectorCosine(x) for x in hemiSectorList }   
    jetPtThreshold = 30
    varList = [
        'pt', 'eta', 'phi', "dxy", "dz", 'pdgId' ,
        "matchedJetIndex", "matchedJetDr",
        "CosPhiJet1", "CosPhiJet12", "CosPhiJetAll"
        ]
    trkVar="Tracks"
    nTracks = getattr(readTree,"n%s"%trkVar)
    tracks = (hephyHelpers.getObjDict(splitTree, trkVar+"_", varList, i) for i in range(nTracks))
    nTrkDict = {
                 "nTracks": { minPt : 0 for minPt in trackMinPtList}
               }

    nTrkDict.update({
                "nTracksOpp%sJet%s"%(hemiSec,nISRs) : { minPt : 0 for minPt in trackMinPtList} 
                                         for nISRs in nISRsList for hemiSec in hemiSectorList          
                })
    for track in tracks:
        if not (
                abs(track['eta']) < 2.5 and track['pt']>=1.0 and
                abs(track['dxy']) < 0.1 and abs( track['dz'] ) < 0.1 
                ) :
            continue
        if abs(track['pdgId']) in [13,11]:
            #if len(selectedLeptons)>0 and hephyHelpers.deltaR(track, selectedLeptons[0] ) <0.1:
            if lep and hephyHelpers.deltaR(track, lep) < 0.1 and lep['pdgId']==track['pdgId'] :
                #Possible lepton track... shouldn't count the lepton that's being used, let's check Pt first ", deltaR(track, lep)
                if lep['pt']/track['pt'] < 1.1 and lep['pt']/track['pt'] > 0.9:
                    #print "   yes most definitely is!"
                    continue
        if  (track['matchedJetDr']<=0.4  ): 
            # Possible ISR track, will not count track if the jet pt greater than jetPtThreshold
            #matchedJet = allJets[int(track['matchedJetIndex'])]
            matchedJet = jets[int(track['matchedJetIndex'])]
            if matchedJet['pt'] > jetPtThreshold:
                # Track is matched with dr<0.4 to a jet with pt higher than jetpthtreshold. Dont want to count such a track!
                continue
        for minTrkPt in trackMinPtList:
            if track['pt'] > minTrkPt:
                nTrkDict['nTracks'][minTrkPt] +=1
                ## tracks in the opp sectors
                for hemiSector in hemiSectorList:
                    for nISRs in nISRsList:
                        nTrkVarName = "nTracksOpp%sJet%s"%(hemiSector,nISRs)
                        #print "trk cosine", track['CosPhiJet%s'%nISRs ], hemiSectorCosines[hemiSector]
                        if track['CosPhiJet%s'%nISRs ] < hemiSectorCosines[hemiSector]:
                            #print "  yes" 
                            nTrkDict[nTrkVarName][minTrkPt]+=1
    for minTrkPt in trackMinPtList:
        ptString = str(minTrkPt).replace(".","p")
        setattr(saveTree, "n"+trkVar+"_pt%s"%ptString , nTrkDict["n"+trkVar][minTrkPt] )
        for hemiSector in hemiSectorList:
            for nISRs in nISRsList:
                nTrkVarName = "nTracksOpp%sJet%s"%(hemiSector,nISRs)
                setattr(saveTree,nTrkVarName+"_pt%s"%ptString, nTrkDict[nTrkVarName][minTrkPt] )
    for hemiSector in hemiSectorList:
        for nISRs in nISRsList:
            nTrkVarName = "nTracksOpp%sJet%s"%(hemiSector,nISRs)
            #print nTrkVarName, { trkPt: getattr(saveTree,nTrkVarName+"_pt%s"%str(trkPt).replace(".","p") ) for trkPt in trackMinPtList }
    return saveTree 
 

  
def processGenTracksFunction(readTree, splitTree, saveTree):
    '''Process generated particles. 
    
    TODO describe here the processing.
    '''
    
    logger = logging.getLogger('cmgPostProcessing.processGenTracksFunction')
    
    # 
    genPartMinPtList = [1,1.5,2]

    varList = ['pt', 'eta', 'phi', 'pdgId' ]
    genPartPkds = (hephyHelpers.getObjDict(splitTree, 'genPartPkd_', varList, i) for i in range(readTree.ngenPartPkd))
    
    ngenPartPkds = { minPt : 0 for minPt in genPartMinPtList}
    ngenPartPkdsOppJet1 = { minPt : 0 for minPt in genPartMinPtList}
    ngenPartPkdsOpp90ISR = { minPt : 0 for minPt in genPartMinPtList}
    ngenPartPkdsOppJet12 = { minPt : 0 for minPt in genPartMinPtList}
    ngenPartPkdsOpp90ISR2 = { minPt : 0 for minPt in genPartMinPtList}
    
    for genPartPkd in genPartPkds:
        if not (abs(genPartPkd['eta']) < 2.5 and genPartPkd['pt'] >= 1.0) :
            continue
        
        logger.trace("\n Selected generated particle: \n %s \n", pprint.pformat(genPartPkd))

        if math.cos(genPartPkd['phi'] - saveTree.jet1Phi) < 0:
            for genPartPkdMinPt in genPartMinPtList:
                if genPartPkd['pt'] > genPartPkdMinPt:
                    ngenPartPkdsOppJet1[genPartPkdMinPt] += 1
            if math.cos(genPartPkd['phi'] - saveTree.jet1Phi) < - math.sqrt(2) / 2:
                for genPartPkdMinPt in genPartMinPtList:
                    if genPartPkd['pt'] > genPartPkdMinPt:
                        ngenPartPkdsOpp90ISR[genPartPkdMinPt] += 1

        for genPartPkdMinPt in genPartMinPtList:
            if genPartPkd['pt'] > genPartPkdMinPt:
                ngenPartPkds[genPartPkdMinPt] += 1
                logger.trace("\n added one genPartPkd to genPartPkdMinPt = %f with ngenPartPkds[genPartPkdMinPt] %i \n ", 
                    genPartPkdMinPt, ngenPartPkds[genPartPkdMinPt])
     
    saveTree.ngenPartPkd_1 = ngenPartPkds[1]    
    saveTree.ngenPartPkd_1p5 = ngenPartPkds[1.5]    
    saveTree.ngenPartPkd_2 = ngenPartPkds[2]    
     

    saveTree.ngenPartPkdOppJet1_1 = ngenPartPkdsOppJet1[1]  
    saveTree.ngenPartPkdOppJet1_1p5 = ngenPartPkdsOppJet1[1.5]  
    saveTree.ngenPartPkdOppJet1_2 = ngenPartPkdsOppJet1[2]  

    saveTree.ngenPartPkdO90isr_1 = ngenPartPkdsOpp90ISR[1]  
    saveTree.ngenPartPkdO90isr_1p5 = ngenPartPkdsOpp90ISR[1.5]  
    saveTree.ngenPartPkdO90isr_2 = ngenPartPkdsOpp90ISR[2]  

    #
    return saveTree

def processMasses(readTree, saveTree):
    '''Process various tranverse masses and other variables 
    
    TODO describe here the processing.
    '''

    logger = logging.getLogger('cmgPostProcessing.processMasses')
        
    if (saveTree.nlep >= 1):
        saveTree.Q80 = 1 - 80 ** 2 / (2 * saveTree.lepPt * readTree.met_pt)
        saveTree.CosLMet = math.cos(saveTree.lepPhi - readTree.met_phi)
    
        saveTree.mt = math.sqrt(2 * saveTree.lepPt * readTree.met_pt * (1 - saveTree.CosLMet))
        saveTree.st = readTree.met_pt + saveTree.lepPt
  
        saveTree.deltaPhi_Wl = math.acos(
            (saveTree.lepPt + readTree.met_pt * math.cos(saveTree.lepPhi - readTree.met_phi)) / 
            (math.sqrt(saveTree.lepPt ** 2 + readTree.met_pt ** 2 + 
                      2 * readTree.met_pt * saveTree.lepPt * math.cos(saveTree.lepPhi - readTree.met_phi))
                )
            ) 
    
    logger.debug(
        "\n Q80: %f \n CosLMet: %f \n mt: %f \n \n st: %f \n deltaPhi_Wl %f \n", 
        saveTree.Q80, saveTree.CosLMet, saveTree.mt, saveTree.st, saveTree.deltaPhi_Wl
        )

    #
    return saveTree

def processEventVetoList(readTree,splitTree, saveTree, sample,  veto_event_list):
    ''' 
        
    '''
    if not sample['cmgComp'].isData:
        return

    run  = int(splitTree.GetLeaf('run').GetValue()      )
    lumi = int(splitTree.GetLeaf('lumi').GetValue()     )
    evt  = int(splitTree.GetLeaf('evt').GetValue()      )

    run_lumi_evt = "%s:%s:%s\n"%(run,lumi,evt) 
    #print run_lumi_evt
    if run_lumi_evt in veto_event_list:
        saveTree.Flag_Veto_Event_List = 0
        #print "=====   evt Failed veto list %s"%run_lumi_evt
    #else:
        #print "=   evt  veto list %s"%run_lumi_evt
        





def computeWeight(sample, sumWeight,  splitTree, saveTree, params, xsec=None):
    ''' Compute the weight of each event.
    
    Include all the weights used:
        genWeight - weight of generated events (MC only, set to 1 for data)
        luminosity weight 
    '''

    target_lumi = params['target_lumi']
    logger = logging.getLogger('cmgPostProcessing.computeWeight')
        
    # sample type (data or MC, taken from CMG component)
    isDataSample = sample['cmgComp'].isData
    
    # weight according to required luminosity 
    
    genWeight = 1 if isDataSample else splitTree.GetLeaf('genWeight').GetValue()


    if isDataSample: 
        lumiScaleFactor = 1
    else:
        if not xsec:
            xSection = sample['cmgComp'].xSection
        else:
            xSection = xsec
        lumiScaleFactor = xSection * target_lumi / float(sumWeight)
        
    saveTree.weight = lumiScaleFactor * genWeight
    
    logger.debug(
        "\n Computing weight for: %s sample " + \
        "\n    target luminosity: %f "
        "\n    genWeight: %f " + \
        "\n    %s" + \
        "\n    sum of event weights: %f" + \
        "\n    luminosity scale factor: %f " + \
        "\n    Event weight: %f \n",
        ('Data ' + sample['cmgComp'].name if isDataSample else 'MC ' + sample['cmgComp'].name),
        target_lumi, genWeight,
        ('' if isDataSample else 'cross section: ' + str(sample['cmgComp'].xSection) + ' pb^{-1}'),
        sumWeight, lumiScaleFactor, saveTree.weight)
    
        
    #
    return saveTree


def haddFiles(sample_name, filesForHadd, temporaryDir, outputWriteDirectory):
    ''' Add the histograms using ROOT hadd script
        
        If
            input files to be hadd-ed sum to more than maxFileSize MB or
            the number of files to be added is greater than  maxNumberFiles
        then split the hadd
    '''

    logger = logging.getLogger('cmgPostProcessing.haddFiles')
        
    maxFileSize = 500 # split into maxFileSize MB
    maxNumberFiles = 200
    logger.debug(
        "\n " + \
        "\n Sum up the split files in files smaller as %f MB \n",
         maxFileSize
         )

    size = 0
    counter = 0
    files = []
    #print "VERBOSE:  ",  filesForHadd
    for f in filesForHadd:
        #print "VERBOSE:  ",  f
        size += os.path.getsize(temporaryDir + '/' + f)
        files.append(f)
        if size > (maxFileSize * (10 ** 6)) or f == filesForHadd[-1] or len(files) > maxNumberFiles:
            #ofile = outputWriteDirectory + '/' + sample['name'] + '_' + str(counter) + '.root'
            ofile = outputWriteDirectory + '/' + sample_name+ '_' + str(counter) + '.root'
            logger.debug(
                "\n Running hadd on directory \n %s \n files: \n %s \n", 
                temporaryDir, pprint.pformat(files)
                )
            os.system('cd ' + temporaryDir + ';hadd -f -v 0 ' + ofile + ' ' + ' '.join(files))
            logger.debug("\n Written output file \n %s \n", ofile)
            size = 0
            counter += 1 
            files = []
    
    # remove the temporary directory  
    os.system('cd ' + outputWriteDirectory)
    ROOT.gDirectory.cd("..")
    shutil.rmtree(temporaryDir, onerror=retryRemove)
    if not os.path.exists(temporaryDir): 
        logger.debug("\n Temporary directory \n    %s \n deleted. \n", temporaryDir)
    else:
        logger.info(
            "\n Temporary directory \n    %s \n not deleted. \n" + \
            "\n Delete it by hand.", 
            temporaryDir
            )
        
    return



def cmgPostProcessing(argv=None):
    
    if argv is None:
        argv = sys.argv[1:]
    
    # parse command line arguments
    args = get_parser().parse_args()
    

    # job control parameters
    
    overwriteOutputFiles = args.overwriteOutputFiles
    skim = args.skim
    leptonSelection = args.leptonSelection
    preselect = args.preselect
    runSmallSample = args.runSmallSample

    # for ipython, run always on small samples   
    if sys.argv[0].count('ipython'):
        runSmallSample = True
    
    testMethods = args.testMethods
    # for testMethods, run always on small samples 
    if testMethods:
        runSmallSample = True
        
    
    # load FWLite libraries
    
    ROOT.gSystem.Load("libFWCoreFWLite.so")
    ROOT.AutoLibraryLoader.enable()
    
    # choose the sample(s) to process (allSamples), with results saved in outputDirectory
    
    cmgTuples = args.cmgTuples
    allSamples, outputDirectory , mass_dict = getSamples(args)
     
    # logging configuration

    logLevel = args.logLevel
    
    # use a unique name for the log file, write file in the dataset directory
    prefixLogFile = 'cmgPostProcessing_' + '_'.join([sample['cmgComp'].name for sample in allSamples]) + \
         '_' + logLevel + '_'
    logFile = tempfile.NamedTemporaryFile(suffix='.log', prefix=prefixLogFile, dir=outputDirectory, delete=False) 

    logger = get_logger(logLevel, logFile.name)

    #
    logger.info(
        "\n Running on CMG ntuples %s " + \
        "\n Samples to be processed: %i \n %s \n" + \
        "\n Results will be written to directory \n %s \n",
        cmgTuples, len(allSamples), 
        pprint.pformat([sample['cmgComp'].name for sample in allSamples]),
        outputDirectory
        )
    logger.debug("\n Samples to be processed: %i \n %s \n",  
        len(allSamples), pprint.pformat(allSamples))
    
    # define job parameters
    # TODO include here all the selection parameters, to avoid hardcoded values in multiple places in the code 
    params={}


    ptSwitch = 25
    relIso = 0.2
    absIso = 5
    
    LepSel={
            "mu":{
                    "pdgId":13 , 
                    "pt":5     ,
                    "eta":2.1  ,
                    "dxy":0.02 ,
                    "dz":0.5   ,
                    #"dxy":0.05 ,
                    #"dz":0.2   ,
                    #"sip3d":4  , 
                    #"mediumMuonId": 1 , 
                    #"hybIso":{  "ptSwitch": 25, "relIso":0.2 , "absIso":5  }
                    "hybIso03":{  "ptSwitch": 25, "relIso":0.2 , "absIso":5  }
                 },
            "el":{
                    "pdgId":11  ,  
                    "SPRING15_25ns_v1": 2 #">="
                    #"pt"   :5
                    #"pt"   :5      ,
                    #"eta"  :2.4   ,
                    #"dxy"  :0.05,
                    #"dz"   :0.2 ,
                 }
            }


    LepSelPt30 = copy.deepcopy(LepSel)
    LepSelPt30['mu']['ptMax'] = 30 

    params['LepSel'] = LepSel
    params['LepSelPt30'] = LepSelPt30



    
    event_veto_list = get_veto_list()['all']
    

    # target luminosity (fixed value, given here)
    params['target_lumi'] = 10000  # pb-1
    
    logger.info("\n Target luminosity: %f pb^{-1} \n", params['target_lumi'])
    
    if args.processTracks:
        params.update( {
            "trackMinPtList" :  [1,1.5,2,2.5,3,3.5],
            "hemiSectorList" :  [ 270, 180, 90, 60 , 360], # 360 is here just to as to doublecheck. It should also be the same for jets 1,12 and All
            "nISRsList"      :  ['1','12','All'],
                    })
        logger.info("\n Parameters: %s \n", pprint.pformat(params))
        #logger.info("\n trackMinPtList: %s \n", pprint.pformat(trackMinPtList))
        #logger.info("\n hemiSectorList: %s \n", pprint.pformat(hemiSectorList))
        #logger.info("\n nISRsList: %s \n", pprint.pformat(nISRsList))
    else:
        params.update( {
            "trackMinPtList" :  [],
            "hemiSectorList" :  [],
            "nISRsList"      :  [],
                    } )

    
    # loop over each sample, process all variables and fill the saved tree
    
    for isample, sample in enumerate(allSamples):
        
        sampleName = sample['cmgComp'].name
        sampleType = 'Data' if sample['cmgComp'].isData else 'MC'

        #   prepare for signal scan
        if args.processSignalScan:
            if len(mass_dict) ==0:
                print "Mass Dict Not Avail. It's needed to split signal scan mass points"
                raise Exception("Mass Dict Not Avail. It's needed to split signal scan mass points")
            mass_dict = mass_dict[sample['name']]
            mstop = args.processSignalScan[0]
            mlsp = args.processSignalScan[1]
            xsec = mass_dict[int(mstop)][int(mlsp)]['xSec']
            nEntries = mass_dict[int(mstop)][int(mlsp)]['nEvents']

        # skim condition 
        signalMasses =[mstop, mlsp] if args.processSignalScan else []
        skimCond =  eventsSkimPreselect(skim, leptonSelection, preselect, signalMasses)
        logger.info("\n Final skimming condition: \n  %s \n", skimCond)


                      
        chunks, sumWeight = hephyHelpers.getChunks(sample)





            

            #sumWeight = mass_dict[mstop][mlsp]
                
        logger.info(
            "\n Running on sample %s of type %s" + \
            "\n Number of chunks: %i"\
            "\n SumWeights: %s \n", sampleName, sampleType, len(chunks) , sumWeight
            
            ) 
        logger.debug("\n Chunks: %s", pprint.pformat(chunks)) 
        
        if runSmallSample: 
            chunks=chunks[:1]
            logger.debug("\n Chunks for runSmallSample option: \n %s\n", pprint.pformat(chunks)) 
        
        # create the output sample directory, if it does not exist. 
        # If it exists and overwriteOutputFiles is set to True, clean up the directory; if overwriteOutputFiles is 
        # set to False, skip the post-processing of this component.
        #
        # create also a temporary directory (within the output directory)
        # that will be deleted automatically at the end of the job. If the directory exists,
        # it will be deleted and re-created.


        sample_name = sample['name']
        if args.processSignalScan:
            sample_name = "SMS_T2_4bd_mStop_%s_mLSP_%s"%(mstop,mlsp)        
        outputWriteDirectory = os.path.join(outputDirectory, sample_name)
        #print "VERBOSE:  name: ", sample['name']
        #print "VERBOSE:  outputWriteDirectory", outputWriteDirectory

        if not os.path.exists(outputWriteDirectory):
            os.makedirs(outputWriteDirectory)
            logger.debug(
                "\n Requested sample directory \n %s \n does not exists." + \
                "\n Created new directory. \n", 
                outputWriteDirectory
                )
        else:
            if overwriteOutputFiles:
                shutil.rmtree(outputWriteDirectory, onerror=retryRemove)
                os.makedirs(outputWriteDirectory)
                logger.info(
                    "\n Requested sample directory \n %s \n exists, and overwriteOutputFiles is set to True." + \
                    "\n Cleaned up and recreated the directory done. \n", 
                    outputWriteDirectory
                    )
            else:
                logger.error(
                    "\n Requested sample directory \n %s \n exists, and overwriteOutputFiles is set to False." + \
                    "\n Skip post-processing sample %s \n", 
                    outputWriteDirectory, sample_name
                    )
                
                continue
        
        # python 2.7 version - must be removed by hand, preferably in a try: ... finalize:
        temporaryDir = tempfile.mkdtemp(dir=outputDirectory) 
        #
        # for 3.X use
        # temporaryDir = tempfile.TemporaryDirectory(suffix=None, prefix=None, dir=None)
             
        logger.info("\n Output sample directory \n  %s \n" , outputWriteDirectory) 
        logger.debug("\n Temporary directory \n  %s \n" , temporaryDir) 
        
        branchKeepStrings, readVars, aliases, readVectors, newVars, readTree, saveTree = \
            rwTreeClasses(sample, isample, args, temporaryDir, params)
                   
        filesForHadd=[]

        nEvents_total = 0
        for chunk in chunks:
          
            sourceFileSize = os.path.getsize(chunk['file'])


            maxFileSize = 200 # split into maxFileSize MB
            
            #if args.processSignalScan:
            #    maxFileSize *= 5
            #    print "---------------------"*10
            #    print mstop, mlsp
            #    print "---------------------"*10

            nSplit = 1+int(sourceFileSize/(maxFileSize*10**6)) 
            if nSplit>1: 
                logger.debug("\n Chunk %s too large \n will split it in %i fragments of approx %i MB \n", 
                    chunk['name'], nSplit, maxFileSize)
            
            for iSplit in range(nSplit):
                
                splitTree = getTreeFromChunk(chunk, skimCond, iSplit, nSplit)
                if not splitTree: 
                    logger.warning("\n Tree object %s not found\n", splitTree)
                    continue
                else:
                    logger.debug("\n Running on tree object %s \n from split fragment %i \n", splitTree, iSplit)
                    
                splitTree.SetName("Events")
                nEvents = splitTree.GetEntries()
                if not nEvents:
                    #print "Chunk empty....continuing"
                    continue
                # addresses for all variables (read and write) must be done here to take the correct address
                
                for v in readVars:
                    splitTree.SetBranchAddress(v['stage1Name'], ROOT.AddressOf(readTree, v['stage1Name']))
                for v in readVectors:
                    for var in v['vars']:
                        splitTree.SetBranchAddress(var['stage1Name'], ROOT.AddressOf(readTree, var['stage1Name']))
                for a in aliases:
                    splitTree.SetAlias(*(a.split(":")))
                
                for v in newVars:
                    v['branch'] = splitTree.Branch(v['stage2Name'], 
                        ROOT.AddressOf(saveTree,v['stage2Name']), v['stage2Name']+'/'+v['stage2Type'])
    
                # get entries for tree and loop over events
                
            
                logger.debug(
                    "\n Number of events after skimming and preselection: \n    chunk: %s \n    " + \
                    "split fragment %i of %i fragments in this chunk: \n    %i events \n", 
                    chunk['name'], iSplit, nSplit, nEvents
                    )


                #if args.processSignalScan:
                #    #mstop = args.processSignalScan[0]
                #    #mlsp  = args.processSignalScan[1]
                #    #eListName = "eList_%s_stp%s_lsp%s"%(iSplit, mstop,mlsp)
                #    #splitTree.Draw(">>%s"%eListName, "(GenSusyMStop==%s) && (GenSusyMNeutralino==%s)"%(mstop,mlsp)  )
                #    #eList = getattr(ROOT,eListName)
                #    #splitTree.SetEventList(eList)
                #    #nEvents_mscan = eList.GetN()
                #    ##assert nEvents_mscan, "CANNOT PROCESS SIGNAL SAMPL mStop:%s  mLSP:%s "%(mstop, mlsp)
                #    #print iSplit, mlsp, mstop, nEvents_mscan 
                #    logger.info(
                #        "Processing Signal Scan For iSplit:%s mStop:%s  mLSP:%s "%(iSplit, mstop, mlsp)
                #        )

                #    events = xrange(nEvents_mscan)
                #else:
                #    events = xrange(nEvents)

                
                #print "{:-^80}".format(" Processing Chunk with %s  Events "%(nEvents) )
                start_time = int(time.time())
                last_time = start_time
                nVerboseEvents = 10000
                
                for iEv in xrange(nEvents):
                    nEvents_total +=1
                    if (nEvents_total%nVerboseEvents == 0) and nEvents_total>0:
                        passed_time = int(time.time() ) - last_time
                        last_time = time.time()
                        if passed_time:
                            print "Event:{:<8}".format(nEvents_total), "@ {} events/sec".format(round(float(nVerboseEvents)/passed_time ))                      
                            logger.debug(
                                "\n Processing event %i from %i events from chunck \n %s \n",
                                nEvents_total, iEv, nEvents, chunk['name']
                                )
            
                    saveTree.init()
                    readTree.init()
                    splitTree.GetEntry(iEv)
                    
                    logger.debug(
                        "\n " + \
                        "\n ================================================" + \
                        "\n * Processing Run:Luminosity segment:Event number " + \
                        "\n *     %i : %i : %i \n", 
                        splitTree.run, splitTree.lumi, splitTree.evt 
                        )
                    
                    # leptons processing
                    saveTree, lep  = processLeptons(leptonSelection, readTree, splitTree, saveTree, params)
                    
                    # jets processing
                    saveTree, jets = processJets(leptonSelection, readTree, splitTree, saveTree)
                    
                    # selected leptons - jets processing
                    saveTree = processLeptonJets(leptonSelection, readTree, splitTree, saveTree, lep, jets)

                    if args.processTracks:
                        saveTree = processTracksFunction(readTree, splitTree, saveTree, lep, jets, params)

                    if args.processGenTracks:
                        saveTree = processGenTracksFunction(readTree, splitTree, saveTree)
                    
                    # process various tranverse masses and other variables
                    saveTree = processMasses(readTree, saveTree)
              
                    # process event veto list flags
                    processEventVetoList(readTree,splitTree,saveTree, sample, event_veto_list)

                    processGenSusyParticles(readTree,splitTree,saveTree,sample)


                    # compute the weight of the event
                    if not args.processSignalScan:
                        saveTree = computeWeight(sample, sumWeight, splitTree, saveTree, params)
                    else:
                        saveTree = computeWeight(sample, nEntries, splitTree, saveTree, params, xsec=xsec)
                            
                
                    # fill all the new variables          
                    for v in newVars:
                        v['branch'].Fill()
                        

                # 
                
                #fileTreeSplit = sample['name'] + '_' + chunk['name'] + '_' + str(iSplit) + '.root' 
                fileTreeSplit = sample_name + '_' + chunk['name'] + '_' + str(iSplit) + '.root' 
                if len(fileTreeSplit)> 256:
                    fileTreeSplit = sample_name[:50] + '_' + chunk['name'][:50] + '_' + str(iSplit) + '.root'
                    #print "---------------------- VERBOSE: %s, %s"%( len(fileTreeSplit), fileTreeSplit )


                filesForHadd.append(fileTreeSplit)

                if not testMethods:
                    tfileTreeSplit = ROOT.TFile(temporaryDir + '/' + fileTreeSplit, 'recreate')
                    splitTree.SetBranchStatus("*", 0)
                    for b in (branchKeepStrings + 
                              [v['stage2Name'] for v in newVars] + 
                              [v.split(':')[1] for v in aliases]):
                        splitTree.SetBranchStatus(b, 1)
                    t2 = splitTree.CloneTree()
                    t2.Write()
                    tfileTreeSplit.Close()
                    logger.debug("\n ROOT file \n %s \n written \n ", temporaryDir + '/' + fileTreeSplit)
                    del tfileTreeSplit
                    del t2
                    splitTree.Delete()
                    del splitTree
                for v in newVars:
                    del v['branch']
    
        logger.debug(
            "\n " + \
            "\n End of processing events for sample %s . Start summing up the chunks. " + \
            "\n *******************************************************************************\n",
            sample_name
            #sampleName
            )
        
        # add the histograms using ROOT hadd script         
        if not testMethods: 
            haddFiles(sample_name, filesForHadd, temporaryDir, outputWriteDirectory)
            
    logger.info(
        "\n " + \
        "\n End of post-processing sample %s " + \
        "\n *******************************************************************************\n",
        sample_name
        #sampleName
        )
    print "Log File Stored in:"
    print logFile.name
    print "Output Directory:"
    print outputWriteDirectory 
 
if __name__ == "__main__":
    sys.exit(cmgPostProcessing())
