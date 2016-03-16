
import sys,os

#oldargv = sys.argv[ : ]
#sys.argv = [ '-b-' ]
#import ROOT
#ROOT.gROOT.SetBatch(True)
#sys.argv = oldargv

from Workspace.DegenerateStopAnalysis.cuts.cuts import *
from Workspace.DegenerateStopAnalysis.navidTools.NavidTools import *

#from Workspace.DegenerateStopAnalysis.navidTools.makeTable import *

from Workspace.DegenerateStopAnalysis.navidTools.limitCalc import  getLimit, plotLimits
import Workspace.DegenerateStopAnalysis.navidTools.limitTools as limitTools



from Workspace.DegenerateStopAnalysis.cmgTuplesPostProcessed_mAODv2 import *
from Workspace.DegenerateStopAnalysis.navidTools.getSamples_PP_mAODv2_7412pass2_scan import getSamples


import plots





mc_path     = "/afs/hephy.at/data/nrad01/cmgTuples/postProcessed_mAODv2/7412pass2_SMSScan_v3/RunIISpring15DR74_25ns"
signal_path = "/afs/hephy.at/data/nrad01/cmgTuples/postProcessed_mAODv2/7412pass2_SMSScan_v3/RunIISpring15DR74_25ns"
data_path   = "/afs/hephy.at/data/nrad01/cmgTuples/postProcessed_mAODv2/7412pass2_SMSScan_v3/Data_25ns"

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
sampleList= args.sampleList

#cutInstStr = args.cutInst
process = args.process
useHT   = args.useHT

runTag = "isrweight_v5_FixedCuts"

doscan = True


scanTag = "_Scan" if doscan else ""

print args, sampleList ,  process
htString = "HT" if useHT else "Inc"

fullTag = "%s_%s_%s"%( runTag , lumiTag , htString )

saveDir = '/afs/hephy.at/user/n/nrad/www/T2Deg13TeV/mAODv2_7412pass2/%s/%s'%(runTag,htString)
plotDir = saveDir +"/DataPlots/" 

#sampleList         = [ 's30'   , 's10FS' , 's40FS'  ,'s30FS', 't2tt30FS','wtau','wnotau' , 'qcd'     ,'z'    , 'tt' ,  'w' ,'dblind','d']
#sampleList          = [ 's30'   , 's10FS' , 's40FS'  ,'s30FS', 't2tt30FS', 's225_215', 's225_145' ,'qcd'     ,'z'    , 'tt' ,  'w' ,'dblind','d']
sampleList          = [ 's30'   , 's10FS' , 's40FS'  ,'s30FS', 't2tt30FS', 's225_215', 's225_145' ,'qcd'     ,'z'    , 'tt' ,  'w' ,'dblind','d']
try:
    samples
except NameError:
    cmgPP = cmgTuplesPostProcessed(mc_path, signal_path, data_path)
    samples = getSamples(wtau=False,sampleList=sampleList,useHT=useHT,skim='presel', scan=doscan, cmgPP=cmgPP, getData=True)


samples.s225_215.color = ROOT.kRed
samples.s225_145.color = ROOT.kBlue



plotList = ["ht","ct"]
plotList = ["met", "mt","ht","ct", "LepPhi", "LepEta", "nJets30", "nJets60", "nBJets", "nSoftBJets", "nHardBJets" ,"LepPt"]
plotListSR = ["LepPtSR","mtSR"] + plotList
plotListCR = plotList


#doDataPlots = False
doDataPlots = process

#tfile = ROOT.TFile(saveDir+"/%s.root"%fullTag ,"recreate")      
ROOT.gDirectory.cd("PyROOT:/")
tfile = ROOT.TFile("%s.root"%fullTag ,"recreate")      

if doDataPlots:
    yields={}
    plts=[]

    #sampleList         = [  's10FS' , 's30FS' ,'s60FS'   , 'z', 'qcd'      , 'tt' ,  'w' ] 
    #sampleList         = [  's225_215', 's225_145', 'z', 'qcd'      , 'tt' ,  'w' ] 
    sigList     = [ 's225_215', 's225_145' ]
    #sigList     = [ 's10FS' , 's30FS' ,'s60FS'  ] 
    bkgList     = [ 'z', 'qcd'      , 'tt' ,  'w' ]

    sampleList = sigList + bkgList

    print sampleList


    crSampleList       = sampleList + ['dblind']
    srSampleList       = sampleList + ['d']
    fomLimits          = [0,3]



    cutInst = cr1
    sampleList = crSampleList
    setEventListToChains(samples,sampleList, cutInst)
    getPlots(samples, plots.plots , cutInst, sampleList= sampleList, plotList=plotListCR , addOverFlowBin='both',weight="weight"  )
    pl_cr1 = drawPlots(samples,    plots.plots , cutInst, sampleList= sampleList,
                    plotList= plotListCR ,save=plotDir, plotMin=0.01,
                    normalize=False, denoms=["bkg"], noms=["dblind"], fom="RATIO", fomLimits=fomLimits)
    plts.append(pl_cr1)

    

    cutInst = cr2
    sampleList = crSampleList
    setEventListToChains(samples,sampleList,cutInst)
    getPlots(samples, plots.plots , cutInst , sampleList= sampleList , plotList=plotListCR , addOverFlowBin='both',weight="weight"  )
    pl_cr2 = drawPlots(samples,    plots.plots , cutInst, sampleList= [ "z","qcd","w","tt"]+sigList+[ "dblind"],
                    plotList= plotListCR ,save=plotDir, plotMin=0.01,
                    normalize=False, denoms=["bkg"], noms=["dblind"], fom="RATIO", fomLimits=fomLimits)
    plts.append(pl_cr2)




    cutInst = crtt2
    sampleList = crSampleList
    setEventListToChains(samples,sampleList ,cutInst)
    getPlots(samples, plots.plots , cutInst , sampleList= sampleList , plotList=plotListCR , addOverFlowBin='both',weight="weight"  )
    pl_crtt2 = drawPlots(samples,    plots.plots , cutInst, sampleList= [ "z","qcd","w","tt"]+ sigList + ["dblind"],
                    plotList= plotListCR ,save=plotDir, plotMin=0.01,
                    normalize=False, denoms=["bkg"], noms=["dblind"], fom="RATIO", fomLimits=fomLimits)
    plts.append(pl_crtt2)

    cutInst = presel
    sampleList = srSampleList
    setEventListToChains(samples, sampleList, cutInst)
    getPlots(samples, plots.plots , cutInst  , sampleList= sampleList   , plotList=plotListSR , addOverFlowBin='both',weight="weight"  )
    pl_presel = drawPlots(samples,    plots.plots , cutInst, sampleList= sampleList,
                    plotList= plotListSR ,save=plotDir, plotMin=0.001,
                    normalize=False, denoms=["bkg"], noms=["d"], fom="RATIO", fomLimits=fomLimits)
    plts.append(pl_presel)

    cutInst = sr1
    sampleList = srSampleList
    setEventListToChains(samples, sampleList ,cutInst)
    getPlots(samples, plots.plots , cutInst  , sampleList= sampleList    , plotList=plotListSR , addOverFlowBin='both',weight="weight"  )
    pl_sr1 = drawPlots(samples,    plots.plots , cutInst, sampleList= sampleList,
                    plotList= plotListSR ,save=plotDir, plotMin=0.001,
                    normalize=False, denoms=["bkg"], noms=["d"], fom="RATIO", fomLimits=fomLimits)
    plts.append(pl_sr1)

    cutInst = sr2
    sampleList = srSampleList
    setEventListToChains(samples, sampleList ,cutInst)
    getPlots(samples, plots.plots , cutInst  , sampleList=sampleList      , plotList=plotListSR , addOverFlowBin='both',weight="weight"  )
    setEventListToChains(samples, sampleList ,presel)
    getPlots(samples, plots.plots , cutInst  , sampleList=sampleList     , nMinus1="B" ,plotList=["nBJets","nSoftBJets","nHardBJets"] , addOverFlowBin='both',weight="weight"  )
    pl_sr2 = drawPlots(samples,    plots.plots , cutInst, sampleList= ["z", 'qcd',"w",'tt'] +sigList+["d"],
                    plotList= plotListSR ,save=plotDir, plotMin=0.001,
                    normalize=False, denoms=["bkg"], noms=["d"], fom="RATIO", fomLimits=fomLimits)
    plts.append(pl_sr2)

    for pl in plts:
        saveDrawOutputToFile(pl, tfile)


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

#calcTrkCutLimit = False
calcTrkCutLimit = process

redo = False
if calcTrkCutLimit:

    limits={}
    yields={}

    bkgListForTable = [  'qcd' ,'z'   ,    'tt',  'w' ] 
    sigListForTable = [  's30'   , 's30FS' , 's10FS' , 's60FS'   , 't2tt30FS' ] 

    scanListForTable = samples.massScanList()
    sampleList = scanListForTable  + bkgListForTable + sigListForTable
    print sampleList
    

    print "Getting Yields"
    cutName = "runI_%s"%htString
    runI.name = runI.name + "_" + htString


    if doscan:
        signalList=  scanListForTable

        limits = {}
        cardDirBase = "/afs/hephy.at/user/n/nrad/CMSSW/fork/CMSSW_7_4_12_patch4/src/Workspace/DegenerateStopAnalysis/plotsNavid/data/"
        cardDir = cardDirBase + "cards/13TeV/%s/%s_%s"%(htString,lumiTag,runTag)
        limitPkl = cardDirBase + "cards/13TeV/%s/%s_%s.pkl"%(htString,lumiTag,runTag)
        makeDir(cardDir)
        
        if os.path.isfile(limitPkl) and not redo:
            limits = pickle.load( file(limitPkl) )
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
                limits[mstop][mlsp] = getLimit(yields[cutName], sig=sig , outDir=cardDir , postfix= "" ) 
            pickle.dump(limits, open( limitPkl,'w'))
        canv , exclplot= limitTools.drawExpectedLimit( limits, plotDir=saveDir+"/ExpectedLimit_%s.png"%( lumiTag ) , bins=None, key=None )
        canv.SetName("ExpectedLimit_%s_%s_%s.pkl"%(htString,runTag,lumiTag ) )
        tfile.cd()
        canv.Write()
        #tfile.Write()

tfile.Close()



getYieldTables = True
if getYieldTables:
    samplesForTable = ['tt','z','qcd','w','s300_290','s300_270','s300_250','s300_240']

    ylds_presel = Yields(samples, samplesForTable, presel, cutOpt='flow', nSpaces=5, pklOpt=True, verbose=True) 
    JinjaTexTable(ylds_presel, pdfDir=tableDir, outputName="" , transpose=True)
    ylds_sr2 = Yields(samples, samplesForTable, sr2, cutOpt='flow2', nSpaces=5, pklOpt=True, verbose=True)
    JinjaTexTable(ylds_sr2, pdfDir=tableDir, outputName="" , transpose=True)
    ylds_sr1 = Yields(samples, samplesForTable, sr1, cutOpt='flow2', nSpaces=5, pklOpt=True, verbose=True)
    JinjaTexTable(ylds_sr1, pdfDir=tableDir, outputName="" , transpose=True)
    ylds_runIFlow = Yields(samples, samplesForTable, runIflow, cutOpt='inclList', nSpaces=5, pklOpt=True, verbose=True) 
    JinjaTexTable(ylds_runIFlow, pdfDir=tableDir, outputName="" , transpose=False)


