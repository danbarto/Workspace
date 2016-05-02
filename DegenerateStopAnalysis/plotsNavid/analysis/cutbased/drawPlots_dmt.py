
import sys,os
import pprint as pp
#oldargv = sys.argv[ : ]
#sys.argv = [ '-b-' ]
#import ROOT
#ROOT.gROOT.SetBatch(True)
#sys.argv = oldargv

from Workspace.DegenerateStopAnalysis.cuts.mu import *
import Workspace.DegenerateStopAnalysis.cuts.mu as cuts  
import Workspace.DegenerateStopAnalysis.cuts.newSR as newSR 
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
runTagKey = "dmt_v2"





## Setting UP TDR Style
#setup_style()

info = infos[runTagKey]

runTag = info.runTag  +"_nTrk%s"%plots.wp
ppTag  = info.ppTag
saveDirBase = info.saveDirBase

dos = {
        "dmtregions":  False,
        "fomplots":    True,
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
    sampleList = ['qcd','z','tt', 'w' ,'s300_220','s300_270','s300_290']

#cutInstStr = args.cutInst
process = args.process
useHT   = args.useHT


doscan = True
wtau = False

scanTag = "_Scan" if doscan else ""

print args, sampleList ,  process
htString = "HT" if useHT else "Inc"

fullTag = "%s_%s_%s"%( runTag , lumiTag , htString )

#saveDirBase = '/afs/hephy.at/user/n/nrad/www/T2Deg13TeV/mAODv2_7412pass2_v6/'

saveDir = saveDirBase+'/%s/%s'%(runTag,htString)
#plotDir = saveDir +"/DataPlots/" 
plotDir = saveDir +"/FOMPlots/" 
makeDir(plotDir)

#sampleList         = [ 's30'   , 's10FS' , 's40FS'  ,'s30FS', 't2tt30FS','wtau','wnotau' , 'qcd'     ,'z'    , 'tt' ,  'w' ,'dblind','d']
#sampleList          = [ 's30'   , 's10FS' , 's40FS'  ,'s30FS', 't2tt30FS', 's225_215', 's225_145' ,'qcd'     ,'z'    , 'tt' ,  'w' ,'dblind','d']
#sampleList          = [ 's30'   , 's10FS' , 's40FS'  ,'s30FS', 't2tt30FS', 's225_215', 's225_145' ,'qcd'     ,'z'    , 'tt' ,  'w' ,'dblind','d']

try:
    samples
except NameError:
    cmgPP = cmgTuplesPostProcessed(mc_path, signal_path, data_path)
    samples = getSamples(wtau=wtau ,sampleList=sampleList,useHT=useHT,skim='presel', scan=doscan, cmgPP=cmgPP, getData=True)


samples.s225_215.color = ROOT.kRed
samples.s225_145.color = ROOT.kBlue


plotList2D = ['DMT','DMTSR' ,  'cosNTrk', 'QnTrk', 'QnGenTrk', 'cosNGenTrk' , 'MTnTrk', 'MTnGenTrk' ]
plotList   = ['met','ht','LepPt','mt', 'nBJets', 'nSoftBJets', 'nHardBJets' , 'LepEta' , 'CosPhiJet', 'Q80',  'CosLMet',  ] 
plotListTrk = [  "TrkJetDr", "TrkDz",  "TrkDxy",  "TrkEta",  "TrkPt", "TrkCosPhiMet"]
plotListTrkMultip = ['nTrk', 'nGenTrk' ] 

plotList = plotList + plotListTrk + plotListTrkMultip

plotList = plotListMultip

nminus1s=   {

                    "met":          ["met","CT"]   , 
                    "mt":           ["mt"]   , 
                    "ht":           ["ht","CT"]   , 
                    "ct":           ["CT"]   , 
                    "LepPhi":       ["lepPhi"]   , 
                    "LepEta":       ["lepEta"]   , 
                    "nJets30":      ["Jet",]   , 
                    "nJets60":      ["Jet"]   , 
                    #"nBJets":       ["BVeto"]   , 
                    "nBJets":       ["CRTT2", "BVeto"]   , 
                    "nSoftBJets":   ["BVeto"]   , 
                    "nHardBJets" :  ["BVeto"]   , 
                    "LepPt":        ["lepPt","MuPt"]

            }



#sigList     = [ 's225_215', 's225_145' ]
#bkgList     = [ 'z', 'qcd'   ,"tt" ,"w"] 
#mcList = sigList + bkgList
mcList = sampleList



bins= {
            "presel"   :   {"cut":presel   ,  "opt":"list", "mcList":mcList, "data":"d"          , "plotList": plotList },
            "sr1"      :   {"cut":sr1      ,  "opt":"list", "mcList":mcList, "data":"d"          , "plotList": plotList },
            "sr1Loose" :   {"cut":sr1Loose ,  "opt":"list", "mcList":mcList, "data":"d"          , "plotList": plotList },
            "sr2"      :   {"cut":sr2      ,  "opt":"list", "mcList":mcList, "data":"d"          , "plotList": plotList },
          }


ROOT.gDirectory.cd("PyROOT:/")
#tfile = ROOT.TFile("%s.root"%fullTag ,"recreate")      
pp.pprint( {x:weights[x].weight_dict for x in weights} , open( saveDir+"/weights.txt" ,"w") ) 
#tfile = ROOT.TFile(saveDir+"/%s.root"%fullTag ,"recreate")      
ROOT.gStyle.SetOptStat(0)
ROOT.gStyle.SetPaintTextFormat("0.2f")
plts_dict={}

bkgList = [x for x in samples.bkgList() if x in sampleList]
sigList = [x for x in samples.sigList() if x in sampleList]    

dmtDir = saveDir+'/DMTRegions/'
if dos['dmtregions'] and process:
    shutil.copy( cuts.__file__.replace(".pyc",".py") , saveDir+"/cuts.py" )
    pp.pprint( samples, open( saveDir+"/samples.txt" ,"w") ) 
    #fombkgs = ['wtau', 'wnotau', 'w','bkg']
    fombkgs = ['w','bkg']
    ws = []

    for cutInst in [presel, sr1Loose, sr1, sr2, newSR.dmt.wp_dmta,  newSR.dmt.wp_dmtb, newSR.dmt.wp_dmtc , newSR.dmt.wp_dmtd]:
        setEventListToChains(samples, sampleList ,cutInst )
        getPlots(samples, plots.plots , cutInst , sampleList=sampleList  + ws , plotList=plotList2D , nMinus1=None , addOverFlowBin='both',weight="weight" )
        makeDir( dmtDir)
        plt = draw2DPlots(samples, plots.plots, cutInst, sampleList=sampleList +  ws , plotList=plotList2D , save= dmtDir, leg=False)
        dmtplots = getSamplePlots(samples,plots,cutInst, sampleList +  ws  , plotList2D , plots_first=True)

        for p in plotList2D:
            bkgtot = dmtplots[p][ bkgList[0] ]
            bkgtot.Reset()
            for bkg in bkgList + ws:
                bkgtot.Add( dmtplots[p][bkg]   ) 
            dmtplots[p]['bkg'] = bkgtot    

            for bkg in fombkgs:
                for sig in sigList:
                    fomplt =  getFOMFromTH2F( dmtplots[p][sig] , dmtplots[p][bkg] )
                    plt['canv']['%s_%s'%(p,sig)].cd()
                    fomplt.Draw("COLZ TEXT")
                    if "DMT" in p:
                        ROOT.WP_DMTa.Draw("same")
                        ROOT.WP_DMTd.Draw("same")
                        ROOT.WP_DMTc.Draw("same")
                    plt['canv']['%s_%s'%(p,sig)].SaveAs( dmtDir + "/%s/%s.png"%(cutInst.saveDir, "FOM_%s_%s_%s"%(p,sig,bkg)) )


setup_style()

if dos['fomplots'] and process:

    def getAndDrawFull(cutInst, mcList , plotList , plotMin = 0.001 ):
        sampleList = mcList 
        print "----------"
        print cutInst
        print sampleList
        print "----------"
        #[samples[samp].tree.SetEventList(0) for samp in samples]
        #setEventListToChains(samples, sampleList ,cutInst.baseCut)

        #setEventListToChains(samples, mcList ,cutInst.baseCut )
        setEventListToChains(samples, mcList ,cutInst )

        #setEventListToChains(samples, ['dblind'] , cutInst)

        for plot in plotList:
            if nminus1s.has_key(plot) and len(nminus1s[plot]) and nminus1s[plot][0]:
                nminus_list = nminus1s[plot]
                #[samples[samp].tree.SetEventList(0) for samp in samples]
            else:
                nminus_list = []
                #setEventListToChains(samples, sampleList ,cutInst)
            getPlots(samples, plots.plots , cutInst  , sampleList=sampleList      , plotList=[plot] , nMinus1=nminus_list , addOverFlowBin='both',weight="weight"  )
        plt = drawPlots(samples,    plots.plots , cutInst, sampleList=sampleList,
                        plotList= plotList ,save=plotDir, plotMin=0.01,
                        normalize=False, denoms=["bkg"], noms=sigList, fom="AMSSYS", fomLimits=[] )
        #plts.append(pl_sr2)
        return plt


    plts_dict={}
    for bname in bins:
        b = bins[bname]
        plts_dict[bname] = getAndDrawFull( b['cut'], b['mcList'] , b['plotList'] )

    #for pl in plts_dict:
    #    saveDrawOutputToFile(plts_dict[pl], tfile)

            

            

    #   yields={}

    #   #sampleList         = [  's10FS' , 's30FS' ,'s60FS'   , 'z', 'qcd'      , 'tt' ,  'w' ] 
    #   #sampleList         = [  's225_215', 's225_145', 'z', 'qcd'      , 'tt' ,  'w' ] 

    #   #sampleList = mcList
    #   print sampleList


    #   for pl in plts_dict:
    #       saveDrawOutputToFile(plts_dict[pl], tfile)


   







 
