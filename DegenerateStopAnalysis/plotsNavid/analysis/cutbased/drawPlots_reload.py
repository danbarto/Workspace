
import sys

#oldargv = sys.argv[ : ]
#sys.argv = [ '-b-' ]
#import ROOT
#ROOT.gROOT.SetBatch(True)
#sys.argv = oldargv

from Workspace.DegenerateStopAnalysis.cuts.cuts import *
from Workspace.DegenerateStopAnalysis.navidTools.getSamples_PP_mAODv2_7412pass2 import getSamples
from Workspace.DegenerateStopAnalysis.navidTools.NavidTools import *
from Workspace.DegenerateStopAnalysis.navidTools.makeTable import *
from Workspace.DegenerateStopAnalysis.navidTools.limitCalc import  getLimit, plotLimits



import plots


print sys.argv
parser = ArgParser()
args=parser.parse(sys.argv)
sampleList= args.sampleList

#cutInstStr = args.cutInst
process = args.process
useHT   = args.useHT
print args, sampleList ,  process
htString = "HT" if useHT else "Inc"


saveDir = '/afs/hephy.at/user/n/nrad/www/T2Deg13TeV/mAODv2_7412pass2/reload_v2/%s/'%htString
plotDir = saveDir +"DataPlots/"

sampleList         = [ 's30'   , 's10FS' , 's40FS'  ,'s30FS', 't2tt30FS','wtau','wnotau' , 'qcd'     ,'z'    , 'tt' ,  'w' ,'dblind','d']
try:
    samples
except NameError:
    samples = getSamples(wtau=True,sampleList=sampleList,useHT=useHT,skim='presel')




cutInsts= {
            "presel"    :   {"cut":presel      ,  "opt":"flow"},
            "sr1abc"    :   {"cut":sr1abc      ,  "opt":"list"},
            "sr1"       :   {"cut":sr1      ,  "opt":"flow"},
            "sr1Loose"  :   {"cut":sr1Loose    ,  "opt":"flow"}, 
            "sr1LooseFull"  :   {"cut":sr1Loose  ,  "opt":"fullFlow"},
            "sr2"       :   {"cut":sr2      ,  "opt":"flow"},
            #"R1"        :   {"cut":dmt.dmtR1   ,  "opt","flow"},
            #"R2"        :   {"cut":dmt.dmtR2   ,  "opt","flow"},
            #"R3"        :   {"cut":dmt.dmtR3   ,  "opt","flow"},
            #"Rej"       :   {"cut":dmt.dmtRej  ,  "opt","flow"},
          }

#cutInst = cutInsts[cutInstStr]



print sampleList

plotList = ["met", "mt", "LepPhi", "LepEta", "nJets30", "nJets60", "nBJets", "nSoftBJets", "nHardBJets" ,"LepPt"]
plotListSR = ["LepPtSR","mtSR"] + plotList
plotListCR = plotList


doDataPlots = process
#doDataPlots = False
if doDataPlots:
    yields={}
          

    sampleList         = [  's10FS' , 's30FS' ,'s60FS'   , 'z', 'qcd'      , 'tt' ,  'w' ] 
    crSampleList       = sampleList + ['dblind']
    srSampleList       = sampleList + ['d']
    fomLimits          = [0,3]

    cutInst = cr1
    setEventListToChains(samples,samples.keys(), cutInst)
    getPlots(samples, plots.plots , cutInst, sampleList= crSampleList, plotList=plotListCR , addOverFlowBin='both',weight="weight"  )
    pl_cr1 = drawPlots(samples,    plots.plots , cutInst, sampleList= crSampleList,
                    plotList= plotListCR ,save=plotDir, plotMin=0.01,
                    normalize=False, denoms=["bkg"], noms=["dblind"], fom="RATIO", fomLimits=fomLimits)


    cutInst = cr2
    setEventListToChains(samples,samples.keys(),cutInst)
    getPlots(samples, plots.plots , cutInst , sampleList= crSampleList , plotList=plotListCR , addOverFlowBin='both',weight="weight"  )
    pl_cr2 = drawPlots(samples,    plots.plots , cutInst, sampleList= [ "z","qcd","w","tt","s30FS","s10FS", "s60FS", "dblind"],
                    plotList= plotListCR ,save=plotDir, plotMin=0.01,
                    normalize=False, denoms=["bkg"], noms=["dblind"], fom="RATIO", fomLimits=fomLimits)

    cutInst = crtt2
    setEventListToChains(samples,samples.keys(),cutInst)
    getPlots(samples, plots.plots , cutInst , sampleList= crSampleList , plotList=plotListCR , addOverFlowBin='both',weight="weight"  )
    pl_crtt = drawPlots(samples,    plots.plots , cutInst, sampleList= [ "z","qcd","w","tt","s30FS","s10FS", "s60FS", "dblind"],
                    plotList= plotListCR ,save=plotDir, plotMin=0.01,
                    normalize=False, denoms=["bkg"], noms=["dblind"], fom="RATIO", fomLimits=fomLimits)

    cutInst = presel
    setEventListToChains(samples,samples.keys(), cutInst)
    getPlots(samples, plots.plots , cutInst  , sampleList= srSampleList   , plotList=plotListSR , addOverFlowBin='both',weight="weight"  )
    pl_presel = drawPlots(samples,    plots.plots , cutInst, sampleList= srSampleList,
                    plotList= plotListSR ,save=plotDir, plotMin=0.001,
                    normalize=False, denoms=["bkg"], noms=["d"], fom="RATIO", fomLimits=fomLimits)

    cutInst = sr1
    setEventListToChains(samples,samples.keys(),cutInst)
    getPlots(samples, plots.plots , cutInst  , sampleList= srSampleList    , plotList=plotListSR , addOverFlowBin='both',weight="weight"  )
    pl_sr1 = drawPlots(samples,    plots.plots , cutInst, sampleList= srSampleList,
                    plotList= plotListSR ,save=plotDir, plotMin=0.001,
                    normalize=False, denoms=["bkg"], noms=["d"], fom="RATIO", fomLimits=fomLimits)

    cutInst = sr2
    setEventListToChains(samples,samples.keys(),cutInst)
    getPlots(samples, plots.plots , cutInst  , sampleList=sampleList + ['d']      , plotList=plotListSR , addOverFlowBin='both',weight="weight"  )
    setEventListToChains(samples,samples.keys(),presel)
    getPlots(samples, plots.plots , cutInst  , sampleList=sampleList + ['d']      , nMinus1="B" ,plotList=["nBJets","nSoftBJets","nHardBJets"] , addOverFlowBin='both',weight="weight"  )
    pl_sr2 = drawPlots(samples,    plots.plots , cutInst, sampleList= ["z", 'qcd',"w",'tt', "s30FS","s10FS","s60FS", "d"],
                    plotList= plotListSR ,save=plotDir, plotMin=0.001,
                    normalize=False, denoms=["bkg"], noms=["d"], fom="RATIO", fomLimits=fomLimits)


#saveDir2 = '/afs/hephy.at/user/n/nrad/www/T2Deg13TeV/mAODv2_7412pass2/reload/%s/'%htString
tableDir=saveDir2+"/Tables/"
cutInsts= {
            "runI"      :   {"cut":runI      ,  "opt":"list"},
          }
cutInstStr="runI"
cutInst = cutInsts[cutInstStr]['cut']
cutOpt = cutInsts[cutInstStr]['opt']

calcTrkCutLimit = process
calcTrkCutLimit = True
if calcTrkCutLimit:

    limits={}
    yields={}

    sampleListForTable = [  's30'   , 's30FS' , 's10FS' , 's60FS'   , 't2tt30FS', 'qcd' ,'z'   ,    'tt',  'w' ] 
    sampleList = sampleListForTable
    print sampleList
    

    setEventListToChains(samples,sampleList,presel)
    cutName = "runI_%s"%htString
    runI.name = runI.name + "_" + htString
    yields[cutName]=Yields(samples, sampleList, runI, cutOpt= "list2" , weight="weight",pklOpt=True,nDigits=2,err=True)
    #limits[cutName]=getLimit(yields[cutName])
    JinjaTexTable(yields[cutName],pdfDir=tableDir, caption="" )
    getLimit(yields[cutName] )
    #pl2 = plotLimits(limits)
    #pl2.Draw()


    signalList = [s for s in sampleList if samples[s].isSignal ]

    limits = {}
    for sig in signalList:
        limits[sig] = getLimit(yields[cutName], sig=sig )

#####################a Remove below



