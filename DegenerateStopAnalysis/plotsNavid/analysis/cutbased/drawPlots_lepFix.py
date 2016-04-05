
import sys,os
import pprint as pp
#oldargv = sys.argv[ : ]
#sys.argv = [ '-b-' ]
#import ROOT
#ROOT.gROOT.SetBatch(True)
#sys.argv = oldargv

from Workspace.DegenerateStopAnalysis.cuts.cuts import *
import Workspace.DegenerateStopAnalysis.cuts.cuts as cuts  ## for copy purpose
import shutil

from Workspace.DegenerateStopAnalysis.navidTools.NavidTools import *

#from Workspace.DegenerateStopAnalysis.navidTools.makeTable import *

from Workspace.DegenerateStopAnalysis.navidTools.limitCalc import  getLimit, plotLimits
import Workspace.DegenerateStopAnalysis.navidTools.limitTools as limitTools



from Workspace.DegenerateStopAnalysis.cmgTuplesPostProcessed_mAODv2 import cmgTuplesPostProcessed
from Workspace.DegenerateStopAnalysis.navidTools.getSamples_PP_mAODv2_7412pass2_scan import getSamples , weights


from plot_info import infos
import plots



#
# Choosing the RunTag... should be a key of infos from plot_infos
#
runTagKey = "lepFix_v4"





## Setting UP TDR Style
setup_style()

info = infos[runTagKey]

runTag = info.runTag
ppTag  = info.ppTag
saveDirBase = info.saveDirBase

dos = {
        "dataplots":    True,
        "calclimit":    False,
        "redo_limit":   False, 
        "yields":       False,
       }


#mc_path     = "/afs/hephy.at/data/nrad01/cmgTuples/postProcessed_mAODv2/%s/RunIISpring15DR74_25ns"%ppTag
#signal_path = "/afs/hephy.at/data/nrad01/cmgTuples/postProcessed_mAODv2/%s/RunIISpring15DR74_25ns"%ppTag
#data_path   = "/afs/hephy.at/data/nrad01/cmgTuples/postProcessed_mAODv2/%s/Data_25ns"%ppTag

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



print sys.argv
parser = ArgParser()
args=parser.parse(sys.argv)

if args.sampleList:
    sampleList= args.sampleList
else:
    #sampleList = ['tt','w','s30','qcd','z']
    sampleList = ['tt', 'w','qcd','z','d']

#cutInstStr = args.cutInst
process = args.process
useHT   = args.useHT


doscan = True


scanTag = "_Scan" if doscan else ""

print args, sampleList ,  process
htString = "HT" if useHT else "Inc"

fullTag = "%s_%s_%s"%( runTag , lumiTag , htString )

#saveDirBase = '/afs/hephy.at/user/n/nrad/www/T2Deg13TeV/mAODv2_7412pass2_v6/'

saveDir = saveDirBase+'/%s/%s'%(runTag,htString)
plotDir = saveDir +"/DataPlots/" 
makeDir(plotDir)

#sampleList         = [ 's30'   , 's10FS' , 's40FS'  ,'s30FS', 't2tt30FS','wtau','wnotau' , 'qcd'     ,'z'    , 'tt' ,  'w' ,'dblind','d']
#sampleList          = [ 's30'   , 's10FS' , 's40FS'  ,'s30FS', 't2tt30FS', 's225_215', 's225_145' ,'qcd'     ,'z'    , 'tt' ,  'w' ,'dblind','d']
#sampleList          = [ 's30'   , 's10FS' , 's40FS'  ,'s30FS', 't2tt30FS', 's225_215', 's225_145' ,'qcd'     ,'z'    , 'tt' ,  'w' ,'dblind','d']
try:
    samples
except NameError:
    cmgPP = cmgTuplesPostProcessed(mc_path, signal_path, data_path)
    samples = getSamples(wtau=False,sampleList=sampleList,useHT=useHT,skim='presel', scan=doscan, cmgPP=cmgPP, getData=True)


samples.s225_215.color = ROOT.kRed
samples.s225_145.color = ROOT.kBlue



plotList = ["ht","ct"]
plotList =["met", "mt","ht","ct", "LepPhi", "LepEta", "nJets30", "nJets60", "nBJets", "nSoftBJets", "nHardBJets" ,"LepPt"] 
plotListSR = ["LepPtSR","mtSR"] + plotList
plotListCR = plotList


nminus1s=   {
                    "met":          ["met","CT"]   , 
                    "mt":           ["mt"]   , 
                    "ht":           ["ht","CT"]   , 
                    "ct":           ["CT"]   , 
                    "LepPhi":       ["lepPhi"]   , 
                    "LepEta":       ["lepEta"]   , 
                    "nJets30":      ["Jet",]   , 
                    "nJets60":      ["Jet"]   , 
                    "nBJets":       ["BVeto"]   , 
                    "nSoftBJets":   ["BVeto"]   , 
                    "nHardBJets" :  ["BVeto"]   , 
                    "LepPt":        ["lepPt"]
            }



sigList     = [ 's225_215', 's225_145' ]
bkgList     = [ 'z', 'qcd'   ,"tt" ,"w"] 
mcList = sigList + bkgList




bins= {
            "cr1"      :   {"cut":cr1      ,  "opt":"list", "mcList":mcList, "data":"dblind"     , "plotList": plotList },
            "cr2"      :   {"cut":cr2      ,  "opt":"list", "mcList":mcList, "data":"dblind"     , "plotList": plotList },
            "crtt"     :   {"cut":crtt2    ,  "opt":"list", "mcList":mcList, "data":"dblind"     , "plotList": plotList },
            "presel"   :   {"cut":presel   ,  "opt":"list", "mcList":mcList, "data":"d"          , "plotList": plotList },
            "sr1"      :   {"cut":sr1      ,  "opt":"list", "mcList":mcList, "data":"d"          , "plotList": plotList },
            "sr2"      :   {"cut":sr2      ,  "opt":"list", "mcList":mcList, "data":"d"          , "plotList": plotList },
          }


#doDataPlots = process
#doDataPlots = False


ROOT.gDirectory.cd("PyROOT:/")
#tfile = ROOT.TFile("%s.root"%fullTag ,"recreate")      
pp.pprint( {x:weights[x].weight_dict for x in weights} , open( saveDir+"/weights.txt" ,"w") ) 

if dos['dataplots'] and process:
    shutil.copy( cuts.__file__.replace(".pyc",".py") , saveDir+"/cuts.py" )
    pp.pprint( samples, open( saveDir+"/samples.txt" ,"w") ) 
    tfile = ROOT.TFile(saveDir+"/%s.root"%fullTag ,"recreate")      
    yields={}
    plts=[]

    #sampleList         = [  's10FS' , 's30FS' ,'s60FS'   , 'z', 'qcd'      , 'tt' ,  'w' ] 
    #sampleList         = [  's225_215', 's225_145', 'z', 'qcd'      , 'tt' ,  'w' ] 

    #sampleList = mcList
    print sampleList


    #crSampleList       = sampleList + ['dblind']
    #srSampleList       = sampleList + ['d']
    fomLimits          = [0,3]





    def getAndDrawFull(cutInst, mcList, data , plotList , plotMin = 0.001 ):
        sampleList = mcList + [data]
        print "----------"
        print cutInst
        print sampleList
        print "----------"
        #[samples[samp].tree.SetEventList(0) for samp in samples]
        for plot in plotList:
            if nminus1s.has_key(plot) and len(nminus1s[plot]) and nminus1s[plot][0]:
                nminus_list = nminus1s[plot]
                [samples[samp].tree.SetEventList(0) for samp in samples]
            else:
                nminus_list = []
                setEventListToChains(samples, sampleList ,cutInst)
            getPlots(samples, plots.plots , cutInst  , sampleList=sampleList      , plotList=[plot] , nMinus1=nminus_list , addOverFlowBin='both',weight="weight"  )
        plt = drawPlots(samples,    plots.plots , cutInst, sampleList=sampleList,
                        plotList= plotList ,save=plotDir, plotMin=0.001,
                        normalize=False, denoms=["bkg"], noms=[data], fom="RATIO", fomLimits=fomLimits)
        #plts.append(pl_sr2)
        return plt


    plts_dict={}
    for bname in bins:
        b = bins[bname]
        plts_dict[bname] = getAndDrawFull( b['cut'], b['mcList'], b['data'], b['plotList'] )





    #cutInst = cr1
    #sampleList = crSampleList
    #setEventListToChains(samples,sampleList, cutInst)
    #
    #plt_cr1 = getAndDrawFull(cutInst, cr



    #plts.append(pl_cr1)

    #

    #cutInst = cr2
    #sampleList = crSampleList

    #setEventListToChains(samples,sampleList,cutInst)
    #getPlots(samples, plots.plots , cutInst , sampleList= sampleList , plotList=plotListCR , addOverFlowBin='both',weight="weight"  )
    #pl_cr2 = drawPlots(samples,    plots.plots , cutInst, sampleList= [ "z","qcd","w","tt"]+sigList+[ "dblind"],
    #                plotList= plotListCR ,save=plotDir, plotMin=0.01,
    #                normalize=False, denoms=["bkg"], noms=["dblind"], fom="RATIO", fomLimits=fomLimits)

    #plts.append(pl_cr2)




    #cutInst = crtt2
    #sampleList = crSampleList
    #setEventListToChains(samples,sampleList ,cutInst)
    #getPlots(samples, plots.plots , cutInst , sampleList= sampleList , plotList=plotListCR , addOverFlowBin='both',weight="weight"  )
    #pl_crtt2 = drawPlots(samples,    plots.plots , cutInst, sampleList= [ "z","qcd","w","tt"]+ sigList + ["dblind"],
    #                plotList= plotListCR ,save=plotDir, plotMin=0.01,
    #                normalize=False, denoms=["bkg"], noms=["dblind"], fom="RATIO", fomLimits=fomLimits)
    #plts.append(pl_crtt2)

    #cutInst = presel
    #sampleList = srSampleList
    #setEventListToChains(samples, sampleList, cutInst)
    #getPlots(samples, plots.plots , cutInst  , sampleList= sampleList   , plotList=plotListSR , addOverFlowBin='both',weight="weight"  )
    #pl_presel = drawPlots(samples,    plots.plots , cutInst, sampleList= sampleList,
    #                plotList= plotListSR ,save=plotDir, plotMin=0.001,
    #                normalize=False, denoms=["bkg"], noms=["d"], fom="RATIO", fomLimits=fomLimits)
    #plts.append(pl_presel)

    #cutInst = sr1
    #sampleList = srSampleList
    #setEventListToChains(samples, sampleList ,cutInst)
    #getPlots(samples, plots.plots , cutInst  , sampleList= sampleList    , plotList=plotListSR , addOverFlowBin='both',weight="weight"  )
    #pl_sr1 = drawPlots(samples,    plots.plots , cutInst, sampleList= sampleList,
    #                plotList= plotListSR ,save=plotDir, plotMin=0.001,
    #                normalize=False, denoms=["bkg"], noms=["d"], fom="RATIO", fomLimits=fomLimits)
    #plts.append(pl_sr1)

    #cutInst = sr2
    #sampleList = srSampleList
    #setEventListToChains(samples, sampleList ,cutInst)
    #getPlots(samples, plots.plots , cutInst  , sampleList=sampleList      , plotList=plotListSR , addOverFlowBin='both',weight="weight"  )
    #setEventListToChains(samples, sampleList ,presel)
    #getPlots(samples, plots.plots , cutInst  , sampleList=sampleList     , nMinus1="B" ,plotList=["nBJets","nSoftBJets","nHardBJets"] , addOverFlowBin='both',weight="weight"  )
    #pl_sr2 = drawPlots(samples,    plots.plots , cutInst, sampleList= ["z", 'qcd',"w",'tt'] +sigList+["d"],
    #                plotList= plotListSR ,save=plotDir, plotMin=0.001,
    #                normalize=False, denoms=["bkg"], noms=["d"], fom="RATIO", fomLimits=fomLimits)
    #plts.append(pl_sr2)







    for pl in plts_dict:
        saveDrawOutputToFile(plts_dict[pl], tfile)













    #tfile.Write()
    #tfile.Close()

tableDir=saveDir+"/Tables/"
makeDir(tableDir)
#if not os.path.isdir(tableDir):
#    os.mkdir(tableDir)

cutInsts= {
            "runI"      :   {"cut":runI      ,  "opt":"list"},
          }



cutInstStr="runI"
cutInst = cutInsts[cutInstStr]['cut']
cutOpt = cutInsts[cutInstStr]['opt']


bkgListForTable = [  'qcd' ,'z'   ,    'tt',  'w' ] 
sigListForTable = [  's275_255', 's275_265', 's275_195' ] 
scanListForTable = samples.massScanList()

if dos['calclimit'] and process:

    limits={}
    yields={}


    sampleList = scanListForTable  + bkgListForTable + sigListForTable

    print sampleList
    

    print "Getting Yields"
    cutName = "runI_%s"%htString
    runI.name = runI.name + "_" + htString




    if doscan:
        signalList=  scanListForTable


        def getValueFromDict(x, val="0.500", default=999):                                                                                                    
            try:                                      
                ret = x[1][val]
            except KeyError:
                    ret = default
            return float(ret)






        limits = {}
        #cardDirBase = "/afs/hephy.at/user/n/nrad/CMSSW/fork/CMSSW_7_4_12_patch4/src/Workspace/DegenerateStopAnalysis/plotsNavid/data/"
        cardDirBase = "/data/nrad/results/cards_and_limits/"
        cardDir = cardDirBase + "13TeV/%s/%s_%s/BasicSys"%(htString,lumiTag,runTag)
        limitPkl = cardDirBase + "13TeV/%s/%s_%s/BasicSys.pkl"%(htString,lumiTag,runTag)
        makeDir(cardDir)
        
        if os.path.isfile(limitPkl):
            if not dos['redo_limit']:
                limits = pickle.load( file(limitPkl) )
        else:


            #yield_pkl = "YieldInstance_{cut}_%s%s.pkl"%(runTag,scanTag)
            yield_pkl = "./pkl/YieldInstance_%s_%s%s.pkl"%(runI.name, runTag,scanTag)

            #if os.path.isfile( yield_pkl ) and not dos['redo_limit']:
            #    yields[cutName]= pickle.load( yield_pkl )
            #else
            #    yields[cutName]=Yields(samples, sampleList, runI, cutOpt="list2",weight="weight",pklOpt=True,tableName="{cut}_%s%s"%(runTag,scanTag),nDigits=2,err=True, verbose=True,nSpaces=10)
        
            if os.path.isfile(yield_pkl):
                if not dos['redo_limit']:
                    print "reading Yields from pickle:%s"%yield_pkl
                    yields[cutName] = pickle.load(file(yield_pkl)) 
            else: 
                setEventListToChains(samples,sampleList,presel)
                yields[cutName]=Yields(samples, sampleList, runI, cutOpt="list2",weight="weight",pklOpt=True,tableName="{cut}_%s%s"%(runTag,scanTag),nDigits=2,err=True, verbose=True,nSpaces=10)
        

            JinjaTexTable(yields[cutName],pdfDir=tableDir, caption="" , transpose=True)


            for sig in signalList:
                mstop, mlsp = [int(x) for x in sig[1:].rsplit("_")]
                try: 
                    limits[mstop]
                except KeyError:
                    limits[mstop]={}
                limits[mstop][mlsp] = getLimit(yields[cutName], sig=sig , outDir=cardDir , postfix= "" , calc_limit = False) 
            pickle.dump(limits, open( limitPkl,'w'))
        canv , exclplot= limitTools.drawExpectedLimit( limits, plotDir=saveDir+"/ExpectedLimit_%s.png"%( lumiTag ) , bins=None, key=getValueFromDict )
        canv.SetName("ExpectedLimit_%s_%s_%s.pkl"%(htString,runTag,lumiTag ) )
        tfile.cd()
        canv.Write()
        #tfile.Write()

    tfile.Close()




for samp in samples:
    samples[samp]['tree'].SetEventList(0)

if dos['yields'] and process: # and process
    samplesForTable = ['tt','z','qcd','w','s300_290','s300_270','s300_250','s300_240']

    sigForTable = ['s275_265']
    samplesForTableShort = bkgListForTable + sigForTable
    ylds_runI = Yields(samples, samplesForTableShort , runI, cutOpt="list2",weight="weight",pklOpt=True,tableName="{cut}_%s%s_%s"%(runTag,scanTag, "_".join(sigForTable) ),nDigits=2,err=True, verbose=True,nSpaces=10)
    JinjaTexTable(ylds_runI, pdfDir=tableDir, outputName="RunIBins" , transpose=False)
    JinjaTexTable(ylds_runI, pdfDir=tableDir, outputName="RunIBins_T" , transpose=True)


    ylds_presel = Yields(samples, samplesForTable, presel, cutOpt='flow', nSpaces=5, pklOpt=True, verbose=True) 
    JinjaTexTable(ylds_presel, pdfDir=tableDir, outputName="" , transpose=True)
    ylds_sr2 = Yields(samples, samplesForTable, sr2, cutOpt='flow', nSpaces=5, pklOpt=True, verbose=True)
    JinjaTexTable(ylds_sr2, pdfDir=tableDir, outputName="" , transpose=True)
    ylds_sr1 = Yields(samples, samplesForTable, sr1, cutOpt='flow', nSpaces=5, pklOpt=True, verbose=True)
    JinjaTexTable(ylds_sr1, pdfDir=tableDir, outputName="" , transpose=True)
    ylds_runIFlow = Yields(samples, samplesForTable, runIflow, cutOpt='inclList', nSpaces=5, pklOpt=True, verbose=True) 
    JinjaTexTable(ylds_runIFlow, pdfDir=tableDir, outputName="" , transpose=False)
    JinjaTexTable(ylds_runIFlow, pdfDir=tableDir, outputName="ReloadCutFlow" , transpose=True)


#sampleList=['w','tt','s300_250']
#Yields(samples, sampleList, muSel, cutOpt='list', nSpaces=5, pklOpt=True, verbose=True)
