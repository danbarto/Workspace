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
import importlib
import copy
import operator
import collections
import errno


# imports user modules or functions

import ROOT

import Workspace.DegenerateStopAnalysis.cmgPostProcessing.cmgObjectSelection as cmgObjectSelection
import Workspace.DegenerateStopAnalysis.cmgPostProcessing.cmgPostProcessing_parser as cmgPostProcessing_parser
import Workspace.DegenerateStopAnalysis.tools.helpers as helpers

import Workspace.HEPHYPythonTools.helpers as hephyHelpers
import Workspace.HEPHYPythonTools.convertHelpers as convertHelpers

import Workspace.HEPHYPythonTools.user as user

from  veto_event_list import get_veto_list

def get_parser():
    ''' Argument parser for post-processing module.
    
    '''
     
    argParser = argparse.ArgumentParser(
        description="Argument parser for cmgPostProcessing", 
        parents=[cmgPostProcessing_parser.get_parser()]
        )
        
    # 
    return argParser

def getParameterSet(args):
    '''Return a dictionary containing all the parameters used for post-processing.
    
    Define in this function all the parameters used for post-processing. 
    No hard-coded values are allowed in the functions, explicitly or via "default value"
    
    More sets of parameters can be defined, with the set used in a job chosen via the argument parser,
    with the argument --parameterSet. 
    '''

    #
    # arguments to build the parameter set
    parameterSet = args.parameterSet
    processTracks = args.processTracks

    # parameter sets
    parSetFullName = 'Workspace.DegenerateStopAnalysis.cmgPostProcessing.parameterSets.' + parameterSet
    
    try:
        parameters = importlib.import_module(parSetFullName)
    except ImportError, err:      
        print 'ImportError:', err
        print "\n The required parameter set {0} \n ".format(parSetFullName) + \
            "can not be imported.", \
            "\n Correct the name and re-run the script. \n Exiting."
        sys.exit()

    # 
    params = parameters.getParameterSet(args)
    
    # list of variables for muon, electrons, leptons (electrons plus muons)
    
    LepSel = params['LepSel']
    
    # existing branches
    varsCommon = helpers.getVariableNameList(LepSel['branches']['common'])
    varsMu = helpers.getVariableNameList(LepSel['branches']['mu'])
    varsEl = helpers.getVariableNameList(LepSel['branches']['el'])
    
    varListMu = varsCommon + varsMu
    varListEl = varsCommon + varsEl
    varListLep = varsCommon + varsMu + varsEl
    
    # new branches
    varsCommon = helpers.getVariableNameList(LepSel['newBranches']['common'])
    varsMu = helpers.getVariableNameList(LepSel['newBranches']['mu'])
    varsEl = helpers.getVariableNameList(LepSel['newBranches']['el'])
    
    varListExtMu = varsCommon + varsMu
    varListExtEl = varsCommon + varsEl
    varListExtLep = varsCommon + varsMu + varsEl

    # add the lists to params
        
    LepVarList = {
        'mu': varListMu,
        'el': varListEl,
        'lep': varListLep,
        'extMu': varListExtMu,
        'extEl': varListExtEl,
        'extLep': varListExtLep,
        }

    params['LepVarList'] = LepVarList
    
    # list of variables for jets
    JetSel = params['JetSel']

    JetVarList = helpers.getVariableNameList(JetSel['branches'])
    params['JetVarList'] = JetVarList

    # track selectors
    TracksSel = params['TracksSel']
    if args.processGenTracks:
        GenTracksSel = params['GenTracksSel']
    
    # generated particle selector 
    GenSel = params['GenSel']
    

    # for the object selectors defined here, add the list of branches defined in the selector 

    vectors_DATAMC_List = [LepSel, JetSel]
    if args.processTracks:
        vectors_DATAMC_List.append(TracksSel)
        
    params['vectors_DATAMC_List'] = vectors_DATAMC_List

    vectors_MC_List = [GenSel]
    if args.processGenTracks:
        vectors_MC_List.append(GenTracksSel)

    params['vectors_MC_List'] = vectors_MC_List
    
    #
    return params

def get_logger(logLevel, logFile):
    ''' Logger for post-processing module.
    
    Use the basic definition of the logger from helpers.
    
    '''

    get_logger_rtuple = helpers.get_logger('cmgPostProcessing', logLevel, logFile)
    logger = get_logger_rtuple.logger
    numeric_level = get_logger_rtuple.numeric_level
    fileHandler = get_logger_rtuple.fileHandler

    cmgObjectSelection.logger.setLevel(numeric_level)
    cmgObjectSelection.logger.addHandler(fileHandler)

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
    
    Return also the output main directory, to be created eventually.
    '''

    cmgTuples = args.cmgTuples
    processSample = args.processSample
    
    targetDir = args.targetDir
    
    processingEra = args.processingEra
    cmgProcessingTag = args.cmgProcessingTag
    cmgPostProcessingTag = args.cmgPostProcessingTag
    parameterSet = args.parameterSet


    # cmg samples definition file
    cmgTuplesFullName = 'Workspace.DegenerateStopAnalysis.samples.cmgTuples.' + cmgTuples
    
    cmssw_base = os.environ['CMSSW_BASE']
    sampleFile = os.path.join(cmssw_base, 'src/Workspace/DegenerateStopAnalysis/python/samples/cmgTuples') + \
        '/' + cmgTuples + '.py'
    
    try:
        cmgSamples = importlib.import_module(cmgTuplesFullName)
    except ImportError, err:      
        print "\n The required set of CMG tuples \n cmgTuples: {0} \n ".format(cmgTuples) + \
            "with expected sample definition file \n {0} \n does not exist.".format(sampleFile), \
            "\n Correct the name and re-run the script. \n Exiting."
        sys.exit()


    if args.skimPreselect:
        outDir = os.path.join(
            targetDir, processingEra, cmgProcessingTag, cmgPostProcessingTag, parameterSet, 
            cmgTuples, args.skimGeneral, 'skimPreselect', args.skimLepton
            )
    else:
        outDir = os.path.join(
            targetDir, processingEra, cmgProcessingTag, cmgPostProcessingTag, parameterSet, 
            cmgTuples, args.skimGeneral, args.skimLepton
            )
    

    # samples
    
    allComponentsList = [] 
    
    processSampleList = [processSample]
    for sampleName in processSampleList:
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
    
    if hasattr(cmgSamples,"mass_dict"):
        mass_dict = cmgSamples.mass_dict_samples
    else:
        mass_dict = {}

    # define the named tuple to return the values
    rtuple = collections.namedtuple(
        'rtuple', 
        [
            'sampleFile', 
            'componentList', 
            'outputDirectory', 
            'mass_dict'
            ]
        )
    
    getSample_rtuple = rtuple(sampleFile, allComponentsList, outDir, mass_dict) 
    
    #    
    return getSample_rtuple
    

def eventsSkimPreselect(skimGeneral, skimLepton, skimPreselectFlag, params, skimSignalMasses=[]):
    '''Define the skim condition, including preselection if required.
    
    The skim condition depends on the general skim name, the lepton skim selection, and on the
    event preselection. 
    
    FIXME remove hardcoded values, read them from params
    '''

    logger = logging.getLogger('cmgPostProcessing.eventsSkimPreselect')
    
    #
    SkimParameters = params['SkimParameters']
    
    lheHThighIncoming = SkimParameters['lheHThigh']['lheHTIncoming']
    lheHTlowIncoming = SkimParameters['lheHTlow']['lheHTIncoming']
    
    skimCond = "(1)"
    
    if not skimGeneral:
        pass
    elif skimGeneral.startswith('met'):
        skimCond = "met_pt>" + str(float(skimGeneral[3:]))
    elif skimGeneral == 'HT400':
        skimCond = "Sum$(Jet_pt)>400"
    elif skimGeneral == 'HT400ST200': 
        skimCond = "Sum$(Jet_pt)>400&&(LepGood_pt[0]+met_pt)>200"
    elif skimGeneral == 'lheHThigh': 
        skimCond += "&&(lheHTIncoming>={0})".format(lheHThighIncoming)
    elif skimGeneral == 'lheHTlow': 
        skimCond += "&&(lheHTIncoming<{0})".format(lheHTlowIncoming)
    else:
        raise Exception("Skim Condition not recognized: %s"%skimGeneral)
        pass
    
    # lepton skimming, loop only over events fulfilling the lepton skimming condition 
    if skimLepton == 'inc':
        # no lepton skim selection is applied for the inclusive skim 
        skimCond += ""
    else:
        pass
    
    # for inclusive skim, no skim selection is done, the skim condition is reset 
    if skimGeneral == 'inc':
        skimCond = "(1)"
      
    logger.info("\n Jobs running with skim = '%s' \n Initial skimming condition: \n  %s \n ", skimGeneral, skimCond)
    
    if skimPreselectFlag:
        metCut = "(met_pt>200)"
        leadingJet100 = "((Max$(Jet_pt*(abs(Jet_eta)<2.4 && Jet_id) ) > 100 ) >=1)"
        HTCut    = "(Sum$(Jet_pt*(Jet_pt>30 && abs(Jet_eta)<2.4 && (Jet_id)) ) >200)"

        preselectionCuts = "(%s)"%'&&'.join([metCut,leadingJet100,HTCut])
        skimCond += "&&%s"%preselectionCuts

        logger.info("\n Applying preselection cuts: %s ", preselectionCuts)
        logger.info("\n Skimming condition with preselection: \n  %s \n", skimCond)
    else:
        logger.info("\n No preselection cuts are applied for skim %s \n Skimming condition unchanged \n", skimGeneral)
        pass

    if skimSignalMasses:
        mstop = skimSignalMasses[0]
        mlsp  = skimSignalMasses[1]
        skimCond +="&& (GenSusyMStop==%s && GenSusyMNeutralino==%s)"%(mstop,mlsp)
        logger.info("\n Processing Signal Scan for MStop:%s  MLSP: %s "%(mstop, mlsp ))
        

    #
    return skimCond

 
 
def rwTreeClasses(sample, isample, args, temporaryDir, params={} ):
    '''Define the read / write tree classes for data and MC.
    
    '''
    logger = logging.getLogger('cmgPostProcessing.rwTreeClasses')

    # define some internal functions
    
    def appendVectors(params, key, vectorType, vectorsList):
        ''' Append to vectorsList the vectors defied as dictionary in the getParameterSet
        
        '''
        
        if params.has_key(key):
            
            for sel in params[key]:
                
                # get the list of branches 
                if vectorType == 'read':
                    if sel.has_key('branches'):
                        branches = sel['branches']
                    else:
                         return vectorsList                        
                elif vectorType == 'new':
                    if sel.has_key('newBranches'):
                        branches = sel['newBranches']
                    else:
                         return vectorsList
                else:
                    raise Exception("\n No such vector type defined to append to {0}.".format(vectorType))
                    sys.exit()
                    
                varList = []
                if isinstance(branches, dict):
                    # dictionary with list of branches
                    for key, value in branches.iteritems():
                        varList.extend(value)
                elif isinstance(branches, list):
                    # list of branches
                    varList = branches
                else:
                    raise Exception("\n Not possible to build list of branches for {0}.".format(branches))
                    sys.exit()
            
                vec = {
                    'prefix': sel['branchPrefix'], 'nMax': sel['nMax'],
                        'vars': varList,
                    }
                vectorsList.append(vec)
                
        #
        return vectorsList

    
    # define the branches and the variables to be kept and/or read for data and MC
        
    # common branches for data and MC samples 
    
    # common branches already defined in cmgTuples
    keepBranches_DATAMC = [
        'run', 'lumi', 'evt', 'isData', 'rho', 'nVert', 
        'met*','puppi*',
        'Flag_*','HLT_*',
        'nJet', 'Jet_*', 
        'nLepGood', 'LepGood_*', 
        'nLepOther', 'LepOther_*', 
        'nTauGood', 'TauGood_*',
        'Tracks_*', 'isoTrack_*',
        ] 

    readVariables_DATAMC = []
    aliases_DATAMC = []
    newVariables_DATAMC = []
    readVectors_DATAMC = []
    
    readVariables_DATAMC.extend(['met_pt/F', 'met_phi/F'])
    aliases_DATAMC.extend([ 'met:met_pt', 'metPhi:met_phi'])
    
    readVectors_DATAMC = appendVectors(params, 'vectors_DATAMC_List', 'read', readVectors_DATAMC)
                        
    newVariables_DATAMC.extend([
        'Flag_Veto_Event_List/I/1',
        ])
        
    newVariables_DATAMC.extend([
        'weight/F/-999.',
        'ht_basJet/F/-999.'
        ])
    
    newVariables_DATAMC.extend([
        'nBasJet/I/-1', 'nVetoJet/I/-1', 'nIsrJet/I/-1', 'nIsrHJet/I/-1',
        'nBJet/I/-1', 'nBSoftJet/I/-1', 'nBHardJet/I/-1',
        ])
    
    newVariables_DATAMC.extend([
        "nMuon/I/-1", "nElectron/I/-1", "nLepton/I/-1",
        ])
    
    newVariables_DATAMC.extend([
        'basJet_dR_j1j2/F/-999.', 'basJet_dPhi_j1j2/F/-999.', 'vetoJet_dPhi_j1j2/F/-999.',
        ])
    
    newVariables_DATAMC.extend([
        'basJet_mu_invMass_mu1jmindR/F/-999.','basJet_mu_dR_j1mu1/F/-999.', 'basJet_mu_invMass_3j/F/-999.',
        'basJet_el_invMass_el1jmindR/F/-999.','basJet_el_dR_j1el1/F/-999.', 'basJet_el_invMass_3j/F/-999.',
        'basJet_lep_invMass_lep1jmindR/F/-999.','basJet_lep_dR_j1lep1/F/-999.', 'basJet_lep_invMass_3j/F/-999.',
        'bJet_mu_dR_jHdmu1/F/-999.','bJet_el_dR_jHdel1/F/-999.', 'bJet_lep_dR_jHdlep1/F/-999.',
        ])

    newVectors_DATAMC = []
    
    newVectors_DATAMC = appendVectors(params, 'vectors_DATAMC_List', 'new', newVectors_DATAMC)

    # index sorting
    
    # leptons are sorted after pt
    newVectors_DATAMC.extend([
        {'prefix':'IndexLepton', 'nMax': params['LepSel']['nMax'], 
            'vars':[
                'mu/I/-1',
                'el/I/-1',
                'lep/I/-1',
                ] 
            },
        ])

    # basJet, vetoJet, isrJet, isrHJet are sorted after pt
    # bJet, bSoftJet, bHardJet are sorted also after pt
    newVectors_DATAMC.extend([
        {'prefix':'IndexJet', 'nMax': params['JetSel']['nMax'], 
            'vars':[
                'basJet/I/-1',
                'vetoJet/I/-1',
                'isrJet/I/-1',
                'isrHJet/I/-1',
                'bJet/I/-1',
                'bSoftJet/I/-1',
                'bHardJet/I/-1',
                'bJetDiscSort/I/-1',                
                ] 
            },
        ])
    

    # MC samples only
    
    # common branches already defined in cmgTuples
    keepBranches_MC = [ 
        'nTrueInt', 'genWeight', 'xsec', 'puWeight', 
        'GenSusyMStop', 
        'GenSusyMNeutralino',        
        'ngenLep', 'genLep_*', 
        'nGenPart', 'GenPart_*',
        'ngenPartAll','genPartAll_*',
        'ngenTau', 'genTau_*', 
        'ngenLepFromTau', 'genLepFromTau_*', 
        'GenJet_*',
        'GenTracks_*',
        ]
    
    readVariables_MC = []
    aliases_MC = []
    newVariables_MC = []
    
    readVectors_MC = []
    newVectors_MC = []
    
    aliases_MC.extend(['genMet:met_genPt', 'genMetPhi:met_genPhi'])
    
    newVariables_MC.extend([
        "Gen_stop_pt_12/F/-999.", "Gen_stop_eta_12/F/-999.", "Gen_stop_phi_12/F/-999.", 
        "Gen_lsp_pt_12/F/-999.", "Gen_lsp_eta_12/F/-999.", "Gen_lsp_phi_12/F/-999.", 
        ])

    
    readVectors_MC = appendVectors(params, 'vectors_MC_List', 'read', readVectors_MC)
    
    newVectors_MC.extend([
        {'prefix':'IndexGen', 'nMax': params['GenSel']['nMax'], 
            'vars':[
                'stop/I/-1',
                'lsp/I/-1',
                'b/I/-1',
                'lep/I/-1',
                ] 
            },
        ])

    # data samples only
    
    # branches already defined in cmgTuples
    keepBranches_DATA = []
    
    readVariables_DATA = []
    aliases_DATA = []
    newVariables_DATA = []
    
    readVectors_DATA = []
    newVectors_DATA = []
    
    
    # branches for tracks (DATAMC/MC/DATA)
    TracksSel = params['TracksSel']
      
    trackMinPtList = TracksSel['trackMinPtList'] 
    hemiSectorList = TracksSel['hemiSectorList']
    nISRsList      = TracksSel['nISRsList']
       
    if args.processTracks:
        trkVar=TracksSel['branchPrefix']
        trkCountVars = [ "n%s"%trkVar ] 
        trkCountVars.extend([ 
                    "n%sOpp%sJet%s"%(trkVar,hemiSec,nISRs) for hemiSec in hemiSectorList  for nISRs in nISRsList     
                    ])
        newTrackVars = []
        for minTrkPt in trackMinPtList:
            ptString = str(minTrkPt).replace(".","p")
            newTrackVars.extend( [ x+"_pt%s"%ptString+"/I" for x in  trkCountVars  ] )
        newVariables_DATAMC.extend(newTrackVars) 
        
        # readVectors for tracks added already to readVectors_DATAMC via TracksSel
        
                      
    # branches for generated tracks (DATAMC/MC/DATA)

    if args.processGenTracks:
        genTrkVar=params['GenTracksSel']['branchPrefix']
        genTrkCountVars = [ "n%s"%genTrkVar ] 
        genTrkCountVars.extend([ 
                    "n%sOpp%sJet%s"%(genTrkVar,hemiSec,nISRs) for hemiSec in hemiSectorList  for nISRs in nISRsList     
                    ])
        newGenTrackVars = []
        for minGenTrkPt in trackMinPtList:
            ptString = str(minGenTrkPt).replace(".","p")
            newGenTrackVars.extend( [ x+"_pt%s"%ptString+"/I" for x in  genTrkCountVars  ] )
        newVariables_DATAMC.extend(newGenTrackVars)        

        # readVectors for generated tracks added already via GenTracksSel to 
        # readVectors_MC
   

    # sum up branches to be defined for each sample, depending on the sample type (data or MC)
    
    if sample['isData']: 
        keepBranches = keepBranches_DATAMC + keepBranches_DATA
    
        readVariables = readVariables_DATAMC + readVariables_DATA
        aliases = aliases_DATAMC + aliases_DATA
        readVectors = readVectors_DATAMC + readVectors_DATA
        newVariables = newVariables_DATAMC + newVariables_DATA
        newVectors = newVectors_DATAMC + newVectors_DATA
    else:
        keepBranches = keepBranches_DATAMC + keepBranches_MC
    
        readVariables = readVariables_DATAMC + readVariables_MC
        aliases = aliases_DATAMC + aliases_MC
        readVectors = readVectors_DATAMC + readVectors_MC
        newVariables = newVariables_DATAMC + newVariables_MC
        newVectors = newVectors_DATAMC + newVectors_MC


    readVars = [convertHelpers.readVar(v, allowRenaming=False, isWritten=False, isRead=True) for v in readVariables]
    newVars = [convertHelpers.readVar(v, allowRenaming=False, isWritten = True, isRead=False) for v in newVariables]
  
    for v in readVectors:
        readVars.append(convertHelpers.readVar('n'+v['prefix']+'/I', allowRenaming=False, isWritten=False, isRead=True))
        v['vars'] = [convertHelpers.readVar(
            v['prefix']+'_'+vvar, allowRenaming=False, isWritten=False, isRead=True) for vvar in v['vars']
            ]


    for v in newVectors:
        v['vars'] = [convertHelpers.readVar(
            v['prefix']+'_'+vvar, allowRenaming=False, isWritten=True, isRead=False
            ) for vvar in v['vars']
            ]

    logger.debug("\n read variables (readVars) definition: \n %s \n", pprint.pformat(readVars))
    logger.debug("\n aliases definition: \n %s \n", pprint.pformat(aliases))
    logger.debug("\n read vectors (readVectors) definition: \n %s \n", pprint.pformat(readVectors))
    logger.debug("\n new variable (newVars) definition: \n %s \n", pprint.pformat(newVars))
    logger.debug("\n new vectors (newVectors) definition: \n %s \n", pprint.pformat(newVectors))

    convertHelpers.printHeader("Compiling class to write")
    writeClassName = "ClassToWrite_"+str(isample)
    writeClassString = convertHelpers.createClassString(className=writeClassName, vars= newVars, vectors=newVectors, 
        nameKey = 'stage2Name', typeKey = 'stage2Type')
    logger.debug("\n writeClassString definition: \n%s \n", writeClassString)
    saveTree = convertHelpers.compileClass(className=writeClassName, classString=writeClassString, tmpDir=temporaryDir)

    readClassName = "ClassToRead_"+str(isample)
    readClassString = convertHelpers.createClassString(className=readClassName, vars=readVars, vectors=readVectors, 
        nameKey = 'stage1Name', typeKey = 'stage1Type', stdVectors=False)
    convertHelpers.printHeader("Class to Read")
    logger.debug("\n readClassString definition: \n%s \n", readClassString)
    readTree = convertHelpers.compileClass(className=readClassName, classString=readClassString, tmpDir=temporaryDir)

    # define the named tuple to return the values
    rtuple = collections.namedtuple(
        'rtuple', 
        [
            'keepBranches', 
            'readVars', 
            'aliases', 
            'readVectors',
            'newVars',
            'newVectors',
            'readTree',
            'saveTree',
            ]
        )
    
    rwTreeClasses_rtuple = rtuple(
        keepBranches, 
        readVars, 
        aliases, 
        readVectors, 
        newVars, 
        newVectors, 
        readTree, 
        saveTree
        )
    #    
    return rwTreeClasses_rtuple
   
   
def getTreeFromChunk(c, skimCond, iSplit, nSplit):
    '''Get a tree from a chunk.
    
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



def processGenSusyParticles(readTree, splitTree, saveTree, params):


    genPart = cmgObjectSelection.cmgObject(readTree, splitTree, params['GenSel']['branchPrefix'])

    stopIndices = genPart.getSelectionIndexList(readTree,
                            lambda readTree, gp, igp: abs(gp.pdgId[igp]) == 1000006
                            )
    if len(stopIndices) == 0:  # not a susy event... move on
        return saveTree


    isrIndices = genPart.getSelectionIndexList(readTree,
                            lambda readTree, gp, igp: abs(gp.pdgId[igp]) != 1000006 and gp.motherId == -9999
                            )
    lspIndices = genPart.getSelectionIndexList(readTree,
                            lambda readTree, gp, igp: abs(gp.pdgId[igp]) == 1000022
                            )
    bIndices = genPart.getSelectionIndexList(readTree,
                            lambda readTree, gp, igp: abs(gp.pdgId[igp]) == 5
                            )
    lepIndices = genPart.getSelectionIndexList(readTree,
                            lambda readTree, gp, igp: abs(gp.pdgId[igp]) in [11, 13]
                            )

    for ind, val in enumerate(stopIndices):
        saveTree.IndexGen_stop[ind] = val

    for ind, val in enumerate(lspIndices):
        saveTree.IndexGen_lsp[ind] = val

    for ind, val in enumerate(bIndices):
        saveTree.IndexGen_b[ind] = val

    for ind, val in enumerate(lepIndices):
        saveTree.IndexGen_lep[ind] = val


    stop1_lv = ROOT.TLorentzVector()
    stop2_lv = ROOT.TLorentzVector()

    stop1_lv.SetPtEtaPhiM(
        genPart.pt[stopIndices[0]], genPart.eta[stopIndices[0]], genPart.phi[stopIndices[0]],
        genPart.mass[stopIndices[0]]
        )
    stop2_lv.SetPtEtaPhiM(
        genPart.pt[stopIndices[1]], genPart.eta[stopIndices[1]], genPart.phi[stopIndices[1]],
        genPart.mass[stopIndices[1]]
        )

    stops = stop1_lv + stop2_lv

    saveTree.Gen_stop_pt_12 = stops.Pt()
    saveTree.Gen_stop_eta_12 = stops.Eta()
    saveTree.Gen_stop_phi_12 = stops.Phi()



    lsp1_lv = ROOT.TLorentzVector()
    lsp2_lv = ROOT.TLorentzVector()
    
    lsp1_lv.SetPtEtaPhiM(
        genPart.pt[lspIndices[0]], genPart.eta[lspIndices[0]], genPart.phi[lspIndices[0]],
        genPart.mass[lspIndices[0]]
        )
    lsp2_lv.SetPtEtaPhiM(
        genPart.pt[lspIndices[1]], genPart.eta[lspIndices[1]], genPart.phi[lspIndices[1]],
        genPart.mass[lspIndices[1]]
        )
    lsps = lsp1_lv + lsp2_lv
    
    saveTree.Gen_lsp_pt_12 = lsps.Pt()
    saveTree.Gen_lsp_eta_12 = lsps.Eta()
    saveTree.Gen_lsp_phi_12 = lsps.Phi()
    
    return saveTree


def processLeptons(readTree, splitTree, saveTree, params):
    '''Process leptons. 
    
    TODO describe here the processing.
    '''

    logger = logging.getLogger('cmgPostProcessing.processLeptons')
    
    # initialize returned variables (other than saveTree)
    
    lepObj = None
    
    # lepton selection
    
    LepVarList = params['LepVarList'] 
    LepSel = params['LepSel']
    
    objBranches = LepSel['branchPrefix']
    lepObj = cmgObjectSelection.cmgObject(readTree, splitTree, objBranches)
    
    # compute the additional quantities for leptons
    
    for lepIndex in range(lepObj.nObj):
        
        lep_pt = getattr(lepObj, 'pt')[lepIndex]
        lep_phi = getattr(lepObj, 'phi')[lepIndex]
        lep_relIso04 = getattr(lepObj, 'relIso04')[lepIndex]

        q80 = 1 - 80 ** 2 / (2 * lep_pt * readTree.met_pt)
        cosdPhiLepMet = math.cos(lep_phi - readTree.met_phi)
    
        mt = math.sqrt(2 * lep_pt * readTree.met_pt * (1 - cosdPhiLepMet))
        lt = readTree.met_pt + lep_pt
  
        dPhiLepW = math.acos(
            (lep_pt + readTree.met_pt * math.cos(lep_phi - readTree.met_phi)) / 
            (math.sqrt(lep_pt ** 2 + readTree.met_pt ** 2 + 
                      2 * readTree.met_pt * lep_pt * math.cos(lep_phi - readTree.met_phi))
                )
            ) 
        
        absIso = lep_relIso04 * lep_pt
    
        saveTree.LepGood_q80[lepIndex] = q80
        saveTree.LepGood_cosdPhiLepMet[lepIndex] = cosdPhiLepMet
        saveTree.LepGood_mt[lepIndex] = mt
        saveTree.LepGood_lt[lepIndex] = lt
        saveTree.LepGood_dPhiLepW[lepIndex] = dPhiLepW
        saveTree.LepGood_absIso[lepIndex] = absIso 
        
              
    if logger.isEnabledFor(logging.DEBUG):
        printStr = "\n List of " + objBranches + " leptons before selector: " + \
            lepObj.printObjects(None, LepVarList['lep'])

        for ind in range(lepObj.nObj):
            printStr += "\n Extended quantities for " + objBranches + " leptons before selector: " + \
            "\n Lepton index {0}: \n".format(ind)
            for var in LepVarList['extLep']:
                varName = objBranches + '_' + var
                varValue = getattr(saveTree, varName)[ind]
                printStr += varName + " = " + str(varValue) + '\n'
            printStr += '\n'
            
        logger.debug(printStr)
        

    muSelector = cmgObjectSelection.objSelectorFunc(LepSel['mu'] )
    elSelector = cmgObjectSelection.objSelectorFunc(LepSel['el'])

    muList = lepObj.getSelectionIndexList(readTree, muSelector)
    elList = lepObj.getSelectionIndexList(readTree, elSelector)
    # 
    sumElMuList = muList + elList
    lepList = lepObj.sort('pt', sumElMuList)
 
    saveTree.nMuon = len(muList)
    for ind, val in enumerate(muList):
        saveTree.IndexLepton_mu[ind] = val
        
    saveTree.nElectron = len(elList)
    for ind, val in enumerate(elList):
        saveTree.IndexLepton_el[ind] = val

    saveTree.nLepton = len(lepList)
    for ind, val in enumerate(lepList):
        saveTree.IndexLepton_lep[ind] = val

    if logger.isEnabledFor(logging.DEBUG):

        printStr = "\n  " + objBranches + " muon selector \n " + \
            pprint.pformat(LepSel['mu']) + \
            '\n ' + lepObj.printObjects(muList, LepVarList['mu']) + \
            "\n saveTree.nMuon = %i \n  Index list: " + pprint.pformat(muList) + "\n "
        logger.debug(printStr, saveTree.nMuon)

        printStr = "\n  " + objBranches + " electron selector \n " + \
            pprint.pformat(LepSel['el']) + \
            '\n ' + lepObj.printObjects(elList, LepVarList['el']) + \
            "\n saveTree.nElectron = %i \n  Index list: " + pprint.pformat(elList) + "\n "
        logger.debug(printStr, saveTree.nElectron)

        printStr = "\n  " + objBranches + " lepton (mu + el) selection \n " + \
            '\n ' + lepObj.printObjects(lepList, LepVarList['lep']) + \
            "\n saveTree.nLepton = %i \n  Index list:  " + pprint.pformat(lepList) + "\n "        
        logger.debug(printStr, saveTree.nLepton)
        
    # define the named tuple to return the values
    rtuple = collections.namedtuple(
        'rtuple', 
        [
            'lepObj',
            'muList',
            'elList',
            'lepList',
            ]
        )
    
    processLeptons_rtuple = rtuple(
        lepObj, 
        muList, 
        elList, 
        lepList
        )
    #    
    return saveTree, processLeptons_rtuple

def processJets(args, readTree, splitTree, saveTree, params):
    '''Process jets. 
    
    TODO describe here the processing.
    '''

    #
    logger = logging.getLogger('cmgPostProcessing.processJets')
    
    verbose = args.verbose
    
    # selection of jets
    
    JetVarList = params['JetVarList'] 
    JetSel = params['JetSel']
    
    objBranches = JetSel['branchPrefix']
    jetObj = cmgObjectSelection.cmgObject(readTree, splitTree, objBranches)
    
    if logger.isEnabledFor(logging.DEBUG):
        printStr = "\n List of " + objBranches + " jets before selector: " + \
            jetObj.printObjects(None, JetVarList)
        logger.debug(printStr)
    
    # TODO modify the getSelectionIndexList to take as input a list of indices, instead of 
    # a PassFailList, then get rid of the two steps in basic jet selection 

    # basics jets
        
    basJetSel = JetSel['bas']
    basJetSelector = cmgObjectSelection.objSelectorFunc(basJetSel)
    basJetPassFailList = jetObj.getPassFailList(readTree, basJetSelector)
    basJetList = jetObj.getSelectionIndexList(readTree, basJetSelector, basJetPassFailList)
    
    saveTree.nBasJet = len(basJetList)
    for ind, val in enumerate(basJetList):
        saveTree.IndexJet_basJet[ind] = val


    if logger.isEnabledFor(logging.DEBUG):
        printStr = "\n  " + objBranches + " basic jet selector \n " + \
            pprint.pformat(basJetSel) + \
            '\n ' + jetObj.printObjects(basJetList, JetVarList) + \
            "\n saveTree.nBasJet = %i \n  Index list: " + pprint.pformat(basJetList) + "\n "
        logger.debug(printStr, saveTree.nBasJet)

    # veto jets
    
    vetoJetSel = JetSel['veto']
    vetoJetSelector = cmgObjectSelection.objSelectorFunc(vetoJetSel)
    vetoJetList = jetObj.getSelectionIndexList(readTree, vetoJetSelector, basJetPassFailList)

    saveTree.nVetoJet = len(vetoJetList)
    for ind, val in enumerate(vetoJetList):
        saveTree.IndexJet_vetoJet[ind] = val

    if logger.isEnabledFor(logging.DEBUG):
        printStr = "\n  " + objBranches + " veto jet selector (from basic jets) \n " + \
            pprint.pformat(vetoJetSel) + \
            '\n ' + jetObj.printObjects(vetoJetList, JetVarList) + \
            "\n saveTree.nVetoJet = %i \n  Index list: " + pprint.pformat(vetoJetList) + "\n "
        logger.debug(printStr, saveTree.nVetoJet)

    
    # ISR jets

    isrJetSel = JetSel['isr']
    isrJetSelector = cmgObjectSelection.objSelectorFunc(isrJetSel)
    isrJetList = jetObj.getSelectionIndexList(readTree, isrJetSelector, basJetPassFailList)

    saveTree.nIsrJet = len(isrJetList)
    for ind, val in enumerate(isrJetList):
        saveTree.IndexJet_isrJet[ind] = val

    if logger.isEnabledFor(logging.DEBUG):
        printStr = "\n  " + objBranches + " isr jet selector (from basic jets) \n " + \
            pprint.pformat(isrJetSel) + \
            '\n ' + jetObj.printObjects(isrJetList, JetVarList) + \
            "\n saveTree.nIsrJet = %i \n  Index list: " + pprint.pformat(isrJetList) + "\n "
        logger.debug(printStr, saveTree.nIsrJet)


    # ISR jet, higher threshold for SR2
    
    isrHJetSel = JetSel['isrH']
    isrHJetSelector = cmgObjectSelection.objSelectorFunc(isrHJetSel)
    isrHJetList = jetObj.getSelectionIndexList(readTree, isrHJetSelector, basJetPassFailList)
    
    saveTree.nIsrHJet = len(isrHJetList)
    for ind, val in enumerate(isrHJetList):
        saveTree.IndexJet_isrHJet[ind] = val

    if logger.isEnabledFor(logging.DEBUG):
        printStr = "\n  " + objBranches + " isr high jet selector (from basic jets) \n " + \
            pprint.pformat(isrHJetSel) + \
            '\n ' + jetObj.printObjects(isrHJetList, JetVarList) + \
            "\n saveTree.nIsrHJet = %i \n  Index list: " + pprint.pformat(isrHJetList) + "\n "
        logger.debug(printStr, saveTree.nIsrHJet)
        
    
    # save some additional jet quantities
    
    if len(basJetList) > 1:
        basJet_dR_j1j2 = helpers.dR(basJetList[0], basJetList[1], jetObj)
        saveTree.basJet_dR_j1j2 = basJet_dR_j1j2
        
        basJet_dPhi_j1j2 = helpers.dPhi(basJetList[0], basJetList[1], jetObj)
        saveTree.basJet_dPhi_j1j2 = basJet_dPhi_j1j2
                
    else:
        saveTree.basJet_dR_j1j2 = -999.
        saveTree.basJet_dPhi_j1j2 = -999.
                
        
    if len(vetoJetList) > 1:
        vetoJet_dPhi_j1j2 = helpers.dPhi(vetoJetList[0], vetoJetList[1], jetObj)
        saveTree.vetoJet_dPhi_j1j2 = vetoJet_dPhi_j1j2
                    
    else:
        saveTree.vetoJet_dPhi_j1j2 = -999.
        

    logger.debug(
        "\n Number of jets: \n  basic jets: %i \n  veto jets: %i " + \
        "\n  isr jet: %i \n  isr high Jet: %i \n" +\
        "\n Jet separation: " + \
        "\n   basJet_dR_j1j2 = %f \n   basJet_dPhi_j1j2 = %f \n" + \
        "\n   vetoJet_dPhi_j1j2 = %f \n" ,
        saveTree.nBasJet, saveTree.nVetoJet, 
        saveTree.nIsrJet, saveTree.nIsrHJet,
        saveTree.basJet_dR_j1j2, saveTree.basJet_dPhi_j1j2,
        saveTree.vetoJet_dPhi_j1j2
        )
     
    # b jet selection: bJet, bSoftJet and bHardJet are sorted after pt value, like other jets
    
    bJetSel = JetSel['bjet']
    bJetSelector = cmgObjectSelection.objSelectorFunc(bJetSel)
    bJetList = jetObj.getSelectionIndexList(readTree, bJetSelector, basJetPassFailList)
    
    # sort after discriminant variable
    bTagDisc = bJetSel['btag'][0]
    bJetDiscSortList = jetObj.sort(bTagDisc, bJetList)


    bJetSepPtSoftHard = JetSel['bjetSep']['ptSoftHard'][2]
    bSoftJetList, bHardJetList = jetObj.splitIndexList('pt', bJetSepPtSoftHard, bJetList)
    
    nBJets = len(bJetList)
    saveTree.nBJets = nBJets
    for ind, val in enumerate(bJetList):
        saveTree.IndexJet_bJet[ind] = val

    for ind, val in enumerate(bJetDiscSortList):
        saveTree.IndexJet_bJetDiscSort[ind] = val

    nBSoftJets = len(bSoftJetList)
    saveTree.nBSoftJets = nBSoftJets
    for ind, val in enumerate(bSoftJetList):
        saveTree.IndexJet_bSoftJet[ind] = val

    nBHardJets = len(bHardJetList)
    saveTree.nBHardJets = nBHardJets
    for ind, val in enumerate(bHardJetList):
        saveTree.IndexJet_bHardJet[ind] = val
    
    if logger.isEnabledFor(logging.DEBUG):
        printStr = "\n  " + objBranches + " b jet selector (from basic jets), sorted after jet pt \n " + \
            pprint.pformat(bJetSel) + \
            '\n ' + jetObj.printObjects(bJetList, JetVarList) + \
            "\n saveTree.nBJet = %i \n  Index list: " + pprint.pformat(bJetList) + "\n "
        logger.debug(printStr, saveTree.nBJets)
        
        printStr = "\n  " + objBranches + " b jet selector (from basic jets), sorted after jet b discriminant \n " + \
            "\n saveTree.nBJet = %i \n  Index list: " + pprint.pformat(bJetDiscSortList) + "\n "
        logger.debug(printStr, saveTree.nBJets)

        printStr = "\n  " + objBranches + " b soft jet selector, sorted after jet pt \n " + \
            '\n pt soft/hard threshold: %f ' + \
            '\n ' + jetObj.printObjects(bSoftJetList, JetVarList) + \
            "\n saveTree.nSoftBJets = %i \n  Index list: " + pprint.pformat(bSoftJetList) + "\n "
        logger.debug(printStr, bJetSepPtSoftHard, saveTree.nBSoftJets)

        printStr = "\n  " + objBranches + " b hard jet selector, sorted after jet pt \n " + \
            '\n pt soft/hard threshold: %f ' + \
            '\n ' + jetObj.printObjects(bHardJetList, JetVarList) + \
            "\n saveTree.nHardBJets = %i \n  Index list: " + pprint.pformat(bHardJetList) + "\n "
        logger.debug(printStr, bJetSepPtSoftHard, saveTree.nBHardJets)

    # HT as sum of basic jets
    
    ht_basJet = sum (jetObj.pt[ind] for ind in basJetList)
    saveTree.ht_basJet = ht_basJet
    
    logger.debug(
        "\n Missing transverse energy: \n  met_pt =  %f GeV \n  met_phi = %f \n" + \
        "\n Total hadronic energy: \n  ht_basJet = %f \n\n ", 
            readTree.met_pt, readTree.met_phi, ht_basJet
            )
    
    # define the named tuple to return the values
    rtuple = collections.namedtuple(
        'rtuple', 
        [
            'jetObj',
            'basJetList',
            'bJetDiscSortList',
            ]
        )
    
    processJets_rtuple = rtuple(
        jetObj,
        basJetList,
        bJetDiscSortList
        )

    #    
    return saveTree, processJets_rtuple


def processLeptonJets(
        readTree, splitTree, saveTree, 
        processLeptons_rtuple, processJets_rtuple
        ):
    '''Process correlations between the leading selected lepton and jets. 
    
    Compute:
        dR separation of selected lepton and first jet
        invariant mass of the selected leading lepton and the dR-closest jet
        invariant mass of 1, 2, 3 jets, other than the closest jet associated to lepton 
        
        Jets are considered having mass here, lepton have mass zero.
        
    '''
    
    logger = logging.getLogger('cmgPostProcessing.processLeptonJets')
    
    def variablesLeptonJets (getFieldsOnly, lepObj, jetObj, objList, basJetList, bJetDiscSortList):
        
        # define the named tuple to return the values
        rtuple = collections.namedtuple(
            'rtuple',
            [
                'basJet_obj_dR_j1obj1',
                'basJet_obj_invMass_obj1jmindR',
                'basJet_obj_invMass_3j',
                'bJet_obj_dR_jHdobj1',
                ]
            )

        if getFieldsOnly:
            rtuple_fields = rtuple._fields
            return rtuple_fields
        
        #
        
        basJet_obj_dR_j1obj1 = helpers.dR(basJetList[0], objList[0], jetObj, lepObj)
        
        # find the dR-closest jet to selected muon / electron / lepton
        # basJet_obj1_indexClosestJet gives the position in basJetList of the jet index closestJetIndex 
        # giving the minimum dR
        basJet_obj1_indexClosestJet = min(
            range(len(basJetList)), key=lambda j:helpers.dR(basJetList[j], objList[0], jetObj, lepObj)
            )
        closestJetIndex = basJetList[basJet_obj1_indexClosestJet]
        logger.debug(
            "\n Leading lepton index: %i \n Closest basic jet index: %i \n dR(obj1, jet): %f \n",
            objList[0], closestJetIndex,
            helpers.dR(closestJetIndex, objList[0], jetObj, lepObj)
            )
        
        # list of variables needed to compute invariant mass        
        varList = ['pt', 'eta', 'phi', 'mass', ]

        # invariant mass of the selected leading lepton and the dR-closest jet  
        jlList = jetObj.getObjDictList(varList, [closestJetIndex]) + lepObj.getObjDictList(varList, [objList[0]])
        basJet_obj_invMass_obj1jmindR = helpers.invMass(jlList)
        
        # invariant mass of 1, 2, 3 jets, other than the closest jet associated to lepton 
    
        indexList = [i for i in basJetList if i != closestJetIndex]  
        logger.debug(
            "\n Number of jets, excluding the closest jet: %i jets \n List of jet indices: \n %s \n ",
            len(indexList), pprint.pformat(indexList)
            )
         
        basJet_obj_invMass_3j = -999.
              
        if saveTree.nBasJet == 1: 
            basJet_obj_invMass_3j = 0.
        elif saveTree.nBasJet == 2:
            jetList = jetObj.getObjDictList(varList, [indexList[0]])
            basJet_obj_invMass_3j = helpers.invMass(jetList)
        elif saveTree.nBasJet == 3:
            jetList = jetObj.getObjDictList(varList, ([indexList[i] for i in range(2)]))
            basJet_obj_invMass_3j = helpers.invMass(jetList)
        else:
            jetList = jetObj.getObjDictList(varList, ([indexList[i] for i in range(3)]))
            basJet_obj_invMass_3j = helpers.invMass(jetList)
   
        # dR between leading lepton and b jet with highest discriminant
        if len(bJetDiscSortList) > 0:
            bJet_obj_dR_jHdobj1 = helpers.dR(bJetDiscSortList[0], objList[0], jetObj, lepObj)
        else:
            bJet_obj_dR_jHdobj1 = -999.
        #
        
        # fill the return tuple    
        variablesLeptonJets_rtuple = rtuple(
            basJet_obj_dR_j1obj1,
            basJet_obj_invMass_obj1jmindR,
            basJet_obj_invMass_3j,
            bJet_obj_dR_jHdobj1
            )
    
        #    
        return variablesLeptonJets_rtuple
    #    
            
    #
    lepObj = processLeptons_rtuple.lepObj
    jetObj = processJets_rtuple.jetObj
     
    basJetList = processJets_rtuple.basJetList
    bJetDiscSortList = processJets_rtuple.bJetDiscSortList
    
    objNameList = ['mu', 'el', 'lep']
    
    # get here the list of fields only, to be used also for debug when lepjObj is empty
    getFieldsOnly = True
    rtuple_fields = variablesLeptonJets(
        getFieldsOnly, lepObj, jetObj, processLeptons_rtuple.muList, basJetList, bJetDiscSortList
        )
    getFieldsOnly = False
     
    # normal usage: fill the variables            
    if (lepObj is not None) and (saveTree.nBasJet > 0):
 
        for obj in objNameList:
            
            objList = getattr(processLeptons_rtuple, obj + 'List')
            if not objList: continue
            
            variablesLeptonJets_rtuple = variablesLeptonJets(
                getFieldsOnly, lepObj, jetObj, objList, basJetList, bJetDiscSortList
                )
            
            for var in rtuple_fields:
                varName = var.replace('obj', obj)
                setattr(saveTree, varName, getattr(variablesLeptonJets_rtuple, var))
                              
    if logger.isEnabledFor(logging.DEBUG):
         
        logString = ''
        
        for obj in objNameList:            
            for var in rtuple_fields:
                varName = var.replace('obj', obj)
                varValue = getattr(saveTree, varName)
                
                logString += ('\n ' + varName + ' = {}').format(varValue)
            #
            logString += '\n\n'     
        #
        logger.debug(logString)

    #
    return saveTree



def hemiSectorCosine(x):
    return round( math.cos(math.pi- 0.5*(x* math.pi/180)),3)


def processTracksFunction(
    readTree, splitTree, saveTree, params,
    processLeptons_rtuple, processJets_rtuple
    ):
    '''Process tracks. 
    
    TODO describe here the processing.
    FIXME the function needs a serious clean up...
    '''
    logger = logging.getLogger('cmgPostProcessing.processTracksFunction')
    
    # get the track parameters and matching parameters outside the track loop
    # to speed the program
    
    TracksSel = params['TracksSel']

    trackMinPtList = TracksSel['trackMinPtList']
    hemiSectorList = TracksSel['hemiSectorList']
    nISRsList      = TracksSel['nISRsList']
    
    # track selection
    TracksSelBas = TracksSel['bas']
    basTrackPt = TracksSelBas['pt']
    basTrackEta = TracksSelBas['eta']
    basTrackDxy = TracksSelBas['dxy']
    basTrackDz = TracksSelBas['dz']
    basTrackPdgId = TracksSelBas['pdgId']

    # track - jet matching
    jetPtThreshold = TracksSel['ptMatchJet']
    dRmatchJetTrack = TracksSel['dRmatchJetTrack']
    
    # track - leading lepton matching
    dRLepTrack = TracksSel['dRLepTrack']
    ratioPtLepTrackMin = TracksSel['ratioPtLepTrackMin']
    ratioPtLepTrackMax = TracksSel['ratioPtLepTrackMax']
    
    # selected leptons and jets 

    lepObj = processLeptons_rtuple.lepObj
    jetObj = processJets_rtuple.jetObj
    
    muList = processLeptons_rtuple.muList
    elList = processLeptons_rtuple.elList
    lepList = processLeptons_rtuple.lepList
    
    basJetList = processJets_rtuple.basJetList

    # leading lepton, jet collection as dictionaries

    if muList:
        lep = lepObj.getObjDictList(params['LepVarList']['mu'], muList[0])
    else:
        lep = {}
        
    jets = jetObj.getObjDictList(params['JetVarList'], basJetList)
     
    ### corresponding to 90, 135, 150 degree diff between jet and track
    hemiSectorCosines = {  x:hemiSectorCosine(x) for x in hemiSectorList } 
      
    varList = [
        'pt', 'eta', 'phi', "dxy", "dz", 'pdgId',
        "matchedJetIndex", "matchedJetDr",
        "CosPhiJet1", "CosPhiJet12", "CosPhiJetAll"
        ]
    trkVar=TracksSel['branchPrefix']
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
                abs(track['eta']) < basTrackEta and track['pt']>=basTrackPt and
                abs(track['dxy']) < basTrackDxy and abs( track['dz'] ) < basTrackDz 
                ) :
            continue
        if abs(track['pdgId']) in basTrackPdgId:
            #if len(selectedLeptons)>0 and hephyHelpers.deltaR(track, selectedLeptons[0] ) <0.1:
            if lep and hephyHelpers.deltaR(track, lep) < dRLepTrack and lep['pdgId']==track['pdgId'] :
                #Possible lepton track... shouldn't count the lepton that's being used, let's check Pt first ", deltaR(track, lep)
                if lep['pt']/track['pt'] < ratioPtLepTrackMax and lep['pt']/track['pt'] > ratioPtLepTrackMin:
                    #print "   yes most definitely is!"
                    continue
        if  (track['matchedJetDr'] < dRmatchJetTrack  ): 
            # Possible ISR track, will not count track if the jet pt greater than jetPtThreshold
            #matchedJet = allJets[int(track['matchedJetIndex'])]
            matchedJet = jets[int(track['matchedJetIndex'])]
            if matchedJet['pt'] > jetPtThreshold:
                # Track is matched with dr<dRmatchJetTrack to a jet with pt higher than jetpthtreshold. Dont want to count such a track!
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
        setattr(saveTree, "n"+trkVar+"_pt%s"%ptString, nTrkDict["n"+trkVar][minTrkPt] )
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
    FIXME the function needs a serious clean up...
    '''
    
    logger = logging.getLogger('cmgPostProcessing.processGenTracksFunction')
    
    # get the generated track parameters and matching parameters outside the track loop
    # to speed the program
    
    GenTracksSel = params['GenTracksSel']

    genPartMinPtList = TracksSel['genPartMinPtList']
    hemiSectorList = TracksSel['hemiSectorList']
    nISRsList      = TracksSel['nISRsList']
    
    # track selection
    GenTracksSelBas = GenTracksSel['bas']
    basGenTrack_pt = GenTracksSelBas['pt']
    basGenTrack_eta = GenTracksSelBas['eta']

    # 
    varList = ['pt', 'eta', 'phi', 'pdgId' ]
    genPartPkds = (hephyHelpers.getObjDict(splitTree, 'genPartPkd_', varList, i) for i in range(readTree.ngenPartPkd))
    
    ngenPartPkds = { minPt : 0 for minPt in genPartMinPtList}
    ngenPartPkdsOppJet1 = { minPt : 0 for minPt in genPartMinPtList}
    ngenPartPkdsOpp90ISR = { minPt : 0 for minPt in genPartMinPtList}
    ngenPartPkdsOppJet12 = { minPt : 0 for minPt in genPartMinPtList}
    ngenPartPkdsOpp90ISR2 = { minPt : 0 for minPt in genPartMinPtList}
    
    for genPartPkd in genPartPkds:
        if not (abs(genPartPkd['eta']) < basGenTrack_eta and genPartPkd['pt'] >= basGenTrack_pt) :
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

def processEventVetoList(readTree, splitTree, saveTree, veto_event_list):
    ''' 
        
    '''
    
    logger = logging.getLogger('cmgPostProcessing.processEventVetoList')

    run = int(splitTree.GetLeaf('run').GetValue())
    lumi = int(splitTree.GetLeaf('lumi').GetValue())
    evt = int(splitTree.GetLeaf('evt').GetValue())

    run_lumi_evt = "%s:%s:%s\n" % (run, lumi, evt) 
    
    if run_lumi_evt in veto_event_list:
        saveTree.Flag_Veto_Event_List = 0
        logger.debug(
            "\n Run:LS:Event %s failed veto list",
            run_lumi_evt
            )
    else:
        logger.debug(
            "\n Run:LS:Event %s passed veto list",
            run_lumi_evt
            )
        
    #
    return saveTree    

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
    for f in filesForHadd:
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
            "\n Delete it by hand. \n", 
            temporaryDir
            )
        
    return



def cmgPostProcessing(argv=None):
    
    if argv is None:
        argv = sys.argv[1:]
    
    # parse command line arguments
    args = get_parser().parse_args()
    

    # job control parameters
    
    verbose = args.verbose
    overwriteOutputFiles = args.overwriteOutputFiles
    
    skimGeneral = args.skimGeneral
    skimLepton = args.skimLepton
    skimPreselect = args.skimPreselect
    
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
    
    getSamples_rtuple = getSamples(args)
    
    allSamples = getSamples_rtuple.componentList
    outputDirectory = getSamples_rtuple.outputDirectory
    
    try:
        os.makedirs(outputDirectory)
        msg_logger_debug = \
            "\n Requested output directory \n {0} \n does not exists.".format(outputDirectory) + \
            "\n Created new directory. \n"
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise
        else:
            msg_logger_debug = \
                "\n Requested output directory \n {0} \n already exists.\n".format(outputDirectory)
    
     
    # logging configuration

    logLevel = args.logLevel
    
    # use a unique name for the log file, write file in the dataset directory
    prefixLogFile = 'cmgPostProcessing_' + '_'.join([sample['cmgComp'].name for sample in allSamples]) + \
         '_' + logLevel + '_'
    logFile = tempfile.NamedTemporaryFile(suffix='.log', prefix=prefixLogFile, dir=outputDirectory, delete=False) 

    logger = get_logger(logLevel, logFile.name)
    
    #
    logger.info("\n Job arguments: \n\n %s \n", pprint.pformat(vars(args)))

    #
    logger.info(
        "\n Running on CMG ntuples %s \n defined in the file \n %s" + \
        "\n Samples to be processed: %i \n\n %s \n\n Detailed sample description: \n\n  %s \n" + \
        "\n Results will be written to directory \n %s \n",
        cmgTuples, getSamples_rtuple.sampleFile, len(allSamples), 
        pprint.pformat([sample['cmgComp'].name for sample in allSamples]),
        pprint.pformat(allSamples),
        outputDirectory
        )
    
    # write the debug message kept in the msg_logger_debug
    logger.debug(msg_logger_debug)


    # define job parameters and log the parameters used in this job
    params = getParameterSet(args)

    # a more decent print of the dictionary of parameters 
    printParams = ''
    for key, value in params.iteritems():
        if 'vectors_' in key:
            continue
        printParams += "\n {0} =  \n {1} \n".format(key, pprint.pformat(value, indent=2))
        
    logger.info("\n Entries in the parameter dictionary: \n\n" + printParams + '\n\n')
    logger.info("\n Target luminosity: %f pb^{-1} \n", params['target_lumi'])
    
    # get the event veto list FIXME: are the values updated properly?   
    event_veto_list = get_veto_list()['all']

    
    # loop over each sample, process all variables and fill the saved tree
    
    for isample, sample in enumerate(allSamples):
        
        sampleName = sample['cmgComp'].name
        sample_name = sample['name']
        
        isDataSample = True if sample['cmgComp'].isData else False
        sampleType = 'Data' if isDataSample else 'MC'
                              
        logger.info(
            "\n Running on CMG sample component %s of type %s \n",
            sampleName, sampleType
            ) 

        #   prepare for signal scan
        
        if args.processSignalScan:
        
            mass_dict = getSamples_rtuple.mass_dict[sample_name]
            
            logger.debug("\n Mass dictionary: \n \n %s \n ", pprint.pformat(mass_dict)) 
    
            if len(mass_dict) ==0:
                print "Mass dictionary, needed to split signal scan mass points, not available. \nExiting job."
                raise Exception(
                    "Mass dictionary, needed to split signal scan mass points, not available. \nExiting job."
                    )
    
            mstop = args.processSignalScan[0]
            mlsp = args.processSignalScan[1]
            xsec = mass_dict[int(mstop)][int(mlsp)]['xSec']
            nEntries = mass_dict[int(mstop)][int(mlsp)]['nEvents']
            
            
        # skim condition 
        skimSignalMasses = [mstop, mlsp] if args.processSignalScan else []
        skimCond = eventsSkimPreselect(skimGeneral, skimLepton, skimPreselect, params, skimSignalMasses)
        logger.info("\n Final skimming condition: \n  %s \n", skimCond)

        # create the output sample directory, if it does not exist. 
        # If it exists and overwriteOutputFiles is set to True, clean up the directory; if overwriteOutputFiles is 
        # set to False, skip the post-processing of this component.
        #
        # create also a temporary directory (within the output directory)
        # that will be deleted automatically at the end of the job. If the directory exists,
        # it will be deleted and re-created.


        if args.processSignalScan:
            sample_name = "SMS_T2_4bd_mStop_%s_mLSP_%s"%(mstop,mlsp)
                
        logger.info(
            "\n Sample name (from sample file)  %s of type %s \n",
            sample_name, sampleType
            ) 

        outputWriteDirectory = os.path.join(outputDirectory, sample_name)

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
        temporaryDir = tempfile.mkdtemp(prefix='tmp_cmgPostProcessing_', dir=outputDirectory) 
        #
        # for 3.X use
        # temporaryDir = tempfile.TemporaryDirectory(suffix=None, prefix=None, dir=None)
             
        logger.info("\n Output sample directory \n  %s \n", outputWriteDirectory) 
        logger.debug("\n Temporary directory \n  %s \n", temporaryDir) 
        
        rwTreeClasses_rtuple = rwTreeClasses(sample, isample, args, temporaryDir, params) 
        #
        keepBranches = rwTreeClasses_rtuple.keepBranches 
             
        readVars = rwTreeClasses_rtuple.readVars
        aliases = rwTreeClasses_rtuple.aliases 
        readVectors = rwTreeClasses_rtuple.readVectors 
        
        newVars = rwTreeClasses_rtuple.newVars 
        newVectors = rwTreeClasses_rtuple.newVectors 
        
        readTree = rwTreeClasses_rtuple.readTree 
        saveTree = rwTreeClasses_rtuple.saveTree
        #
        
        chunks, sumWeight = hephyHelpers.getChunks(sample)
                
        logger.info(
            "\n Sample %s of type %s has " + \
            "\n   number of chunks: %i"\
            "\n   sumWeights: %s \n", sampleName, sampleType, len(chunks), sumWeight
            ) 
        logger.debug("\n Chunks: \n \n %s", pprint.pformat(chunks)) 
        
        if runSmallSample: 
            chunks=chunks[:1]
            logger.debug("\n\n Running with runSmallSample option. Run only over chunk \n %s\n", pprint.pformat(chunks)) 
        
        filesForHadd=[]

        nEvents_total = 0
        
        for chunk in chunks:
          
            sourceFileSize = os.path.getsize(chunk['file'])


            maxFileSize = 200 # split into maxFileSize MB
            
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
                    if verbose:
                        print "Chunk empty....continuing"
                    continue
                
                # addresses for all variables (read and write) 
                # must be done here to take the correct address
                
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
    
                for v in newVectors:
                    for var in v['vars']:
                        var['branch'] = splitTree.Branch(var['stage2Name'], 
                            ROOT.AddressOf(saveTree,var['stage2Name']), var['stage2Name']+'/'+var['stage2Type'])
                        

                # get entries for tree and loop over events
                
            
                logger.debug(
                    "\n Number of events after skimming and preselection: \n    chunk: %s \n    " + \
                    "split fragment %i of %i fragments in this chunk: \n    %i events \n", 
                    chunk['name'], iSplit, nSplit, nEvents
                    )

                start_time = int(time.time())
                last_time = start_time
                nVerboseEvents = 10000
                
                for iEv in xrange(nEvents):
                    
                    nEvents_total +=1
                    if (nEvents_total%nVerboseEvents == 0) and nEvents_total>0:
                        passed_time = int(time.time() ) - last_time
                        last_time = time.time()
                        if passed_time:
                            if verbose:
                                print "Event:{:<8}".format(nEvents_total), "@ {} events/sec".format(
                                    round(float(nVerboseEvents)/passed_time )
                                    )                      
                            logger.debug(
                                "\n Processing event %i from %i events from chunk \n %s \n" + \
                                "\n Total processed events from all chunks: %i \n",
                                iEv, nEvents, chunk['name'], nEvents_total
                                )
            
                    saveTree.init()
                    readTree.init()
                    splitTree.GetEntry(iEv)
                    
                    logger.debug(
                        "\n " + \
                        "\n ================================================" + \
                        "\n * Processing Run:LS:Event %i:%i:%i \n",
                        splitTree.run, splitTree.lumi, int(splitTree.evt) 
                        )
                    
                    # leptons processing
                    saveTree, processLeptons_rtuple = processLeptons(
                        readTree, splitTree, saveTree, params
                        )
                    
                    # jets processing
                    saveTree, processJets_rtuple = processJets(
                        args, readTree, splitTree, saveTree, params
                        )
                    
                    # selected leptons - jets processing
                    saveTree = processLeptonJets(
                        readTree, splitTree, saveTree,
                        processLeptons_rtuple, processJets_rtuple
                        )
                    
                    # tracks
                    if args.processTracks:
                        saveTree = processTracksFunction(
                            readTree, splitTree, saveTree, params, 
                            processLeptons_rtuple, processJets_rtuple
                            )

                    if (not isDataSample) and args.processGenTracks:
                        saveTree = processGenTracksFunction(readTree, splitTree, saveTree)
                    
                    # process event veto list flags
                    if isDataSample:
                        saveTree = processEventVetoList(
                            readTree, splitTree, saveTree, event_veto_list
                            )

                    if not isDataSample:
                        saveTree = processGenSusyParticles(readTree, splitTree, saveTree, params)


                    # compute the weight of the event
                    if not args.processSignalScan:
                        saveTree = computeWeight(sample, sumWeight, splitTree, saveTree, params)
                    else:
                        saveTree = computeWeight(sample, nEntries, splitTree, saveTree, params, xsec=xsec)
                            
                
                    # fill all the new variables and the new vectors        
                    for v in newVars:
                        v['branch'].Fill()
                        
                    for v in newVectors:
                        for var in v['vars']:
                            var['branch'].Fill()
                            

                # 
                
                fileTreeSplit_full = sample_name + '_' + chunk['name'] + '_' + str(iSplit) + '.root' 
                
                file_length_limit = 256
                if len(fileTreeSplit_full)> file_length_limit:
                    fileTreeSplit = sample_name[:50] + '_' + chunk['name'][:50] + '_' + str(iSplit) + '.root'
                    logger.debug(
                        "\n Length of fileTreeSplit name shortened to %d\n New file name: \n %s \n", 
                        len(fileTreeSplit), fileTreeSplit)
                else:
                    fileTreeSplit = fileTreeSplit_full
                
                
                filesForHadd.append(fileTreeSplit)

                if not testMethods:
                    tfileTreeSplit = ROOT.TFile(temporaryDir + '/' + fileTreeSplit, 'recreate')

                    splitTree.SetBranchStatus("*", 0)
                    for b in (keepBranches + 
                              [v['stage2Name'] for v in newVars] + 
                              [v.split(':')[1] for v in aliases]):
                        splitTree.SetBranchStatus(b, 1)
                    for v in newVectors:
                        for var in v['vars']:
                            splitTree.SetBranchStatus(var['stage2Name'], 1)
                        
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
                    
                for v in newVectors:
                    for var in v['vars']:
                        del var['branch']
    
        logger.debug(
            "\n " + \
            "\n End of processing events for sample %s." + \
            "\n Start summing up the chunks.\n",
            sample_name
            )
        
        # add the histograms using ROOT hadd script         
        if not testMethods: 
            haddFiles(sample_name, filesForHadd, temporaryDir, outputWriteDirectory)
                
        logger.info(
            "\n " + \
            "\n End of post-processing sample %s. \n Total number of event processed for this sample: %i" + \
            "\n *******************************************************************************\n",
            sample_name, nEvents_total
            )
    
    if verbose:
        print "Log File Stored in:"
        print logFile.name
        print "Output Directory:"
        print outputWriteDirectory 
 
if __name__ == "__main__":
    sys.exit(cmgPostProcessing())
