import ROOT
import pickle
from Workspace.HEPHYPythonTools.user import username
from Workspace.HEPHYPythonTools.helpers import getObjFromFile, getChain, getChunks, getCutYieldFromChain, getYieldFromChain
#from Workspace.DegenerateStopAnalysis.cmgTuples_Spring15_7412pass2_mAODv2_v4 import *
#import Workspace.DegenerateStopAnalysis.cmgTuples_Spring15_7412pass2_mAODv2_v5 as cmgTuples
import Workspace.DegenerateStopAnalysis.cmgTuples_Spring15_7412pass2_mAODv2_v6 as cmgTuples
from Workspace.HEPHYPythonTools.xsecSMS import *

import pickle
#samples = [T5qqqqVV_mGluino_1000To1075_mLSP_1To950] #, T5qqqqVV_mGluino_1200To1275_mLSP_1to1150]

dos={
      "get_sig_info":False,
      "get_chains":True,


    }



samples = [     

            cmgTuples.SMS_T2_4bd_mStop_100_mLSP_20to90              ,  
            cmgTuples.SMS_T2_4bd_mStop_125_mLSP_45to115             ,  
            #cmgTuples.SMS_T2_4bd_mStop_150_mLSP_70to140             ,  
            #cmgTuples.SMS_T2_4bd_mStop_175_mLSP_95to165             ,  
            #cmgTuples.SMS_T2_4bd_mStop_200_mLSP_120to190            ,  
            #cmgTuples.SMS_T2_4bd_mStop_225_mLSP_145to225            ,  
            #cmgTuples.SMS_T2_4bd_mStop_250_mLSP_170to240            ,  
            #cmgTuples.SMS_T2_4bd_mStop_275_mLSP_195to265            ,  
            #cmgTuples.SMS_T2_4bd_mStop_300_mLSP_220to290            ,  
            #cmgTuples.SMS_T2_4bd_mStop_325_mLSP_245to315            ,  
            #cmgTuples.SMS_T2_4bd_mStop_350_mLSP_270to340            , 
            #cmgTuples.SMS_T2_4bd_mStop_375_mLSP_295to365            , 
            #cmgTuples.SMS_T2_4bd_mStop_400_mLSP_320to390            , 
            #cmgTuples.SMS_T2_4bd_mStop_425to475_mLSP_345to465       ,
            #cmgTuples.SMS_T2_4bd_mStop_500to550_mLSP_420to540        ,
            #cmgTuples.SMS_T2_4bd_mStop_550to600_mLSP_470to590        ,

        ]


#chains={}
#info = {}
#hstoplsp = ROOT.TH2D("stop_lsp","stop_lsp", 23,87.5,662.5, 127 , 17.5, 642.5)
#mass_dict = {}




def tryStopLSP(mass_dict, mstop, mlsp, def_val = 0):
    try:
        mass_dict[mstop]
    except KeyError:
        mass_dict[mstop]={}
    try:
        mass_dict[mstop][mlsp]
    except KeyError:
        mass_dict[mstop][mlsp]=def_val


output_dir = cmgTuples.sample_path
#mass_dicts={}
#hists={}
#for sample in samples:

def getStopLSPInfo(sample): 
    sample_name = sample["name"]
    print sample_name
    chunks = getChunks(sample, maxN=-1)
    #cut_common = "Sum$(abs(GenPart_pdgId)==1000006)"
    chunk = chunks[0]
    chain = getChain(chunk, minAgeDPM=0, histname='histo', xrootPrefix='root://hephyse.oeaw.ac.at/', maxN=-1, treeName='tree')
    hist_name = "stop_lsp_%s"%sample_name

    #chains[sample_name]= chain       
    mass_dict_sample={}
    mass_dict={}
    #mass_dicts={}

    hist = ROOT.TH2D(hist_name, hist_name, 1000,0,1000, 1000 , 0, 1000)
    chain.Draw("GenSusyMNeutralino:GenSusyMStop>>%s"%hist_name)
    nBinsX = hist.GetNbinsX()
    nBinsY = hist.GetNbinsY()
    for xbin in xrange(nBinsX):
        for ybin in xrange(nBinsY):
            bin_cont = hist.GetBinContent(xbin,ybin)
            if bin_cont > 0.0000001:
                #print xbin, ybin, bin_cont
                mstop = xbin -1
                mlsp = ybin -1 
                print mstop, mlsp, bin_cont

                tryStopLSP(mass_dict_sample, mstop, mlsp, def_val= {"nEvents":0, "xSec":  stop13TeV_NLONLL[mstop]  } )
                mass_dict_sample[mstop][mlsp]['nEvents'] += bin_cont
                tryStopLSP(mass_dict, mstop, mlsp, def_val={"nEvents":0, "xSec":  stop13TeV_NLONLL[mstop] , "samples": set()    })
                mass_dict[mstop][mlsp]['samples'].add(sample_name)
                mass_dict[mstop][mlsp]['nEvents'] += mass_dict_sample[mstop][mlsp]['nEvents']


    #print mass_dicts[sample_name]
    return {"sample_name":sample_name, "mass_dict":mass_dict, "mass_dict_sample":mass_dict_sample}



if __name__ == "__main__":

    if dos['get_sig_info']:
        import multiprocessing
        nProc = 10
        pool = multiprocessing.Pool(nProc)
        results = pool.map(getStopLSPInfo , samples)
        pool.close()
        pool.join()


        mass_dicts_samples_all={}
        mass_dicts_all={}
        for result in results:
            mass_dicts_samples_all[result['sample_name']] =  result['mass_dict_sample']
            mass_dicts_all.update(result['mass_dict'])            

        pickle.dump(mass_dicts_samples_all, open(output_dir +"/mass_dict_samples.pkl","w") )
        pickle.dump(mass_dicts_all, open(output_dir +"/mass_dict.pkl","w") )


    if dos['get_chains']:
        chains={}
        for sample in samples:
            sample_name = sample["name"]
            print sample_name
            chunks = getChunks(sample, maxN=-1)
            #cut_common = "Sum$(abs(GenPart_pdgId)==1000006)"
            chunk = chunks[0]
            chain = getChain(chunk, minAgeDPM=0, histname='histo', xrootPrefix='root://hephyse.oeaw.ac.at/', maxN=-1, treeName='tree')
            chains[sample_name]=chain

    #pickle.dump( mass_dicts[sample_name]  , open(output_dir + "/%s.pkl"%sample_name,"w"))


#pickle.dump(mass_dicts, open(output_dir + "/mass_dict.pkl","w"))
#pickle.dump(mass_dict, open(output_dir + "/mass_dict_all.pkl","w"))
    #info[sample_name] = {}
    #info[sample_name]['nEvts']=chain.GetEntries()
    #info[sample_name]['mass_dict'] = {}

    #for iEvt in xrange( info[sample_name]['nEvts'] ):
    #    chain.GetEntry(iEvt)
    #    if iEvt % 100000 == 0: print iEvt

    #    mstop = int( chain.GetLeaf("GenSusyMStop").GetValue(0)  )   
    #    mlsp  = int( chain.GetLeaf("GenSusyMNeutralino").GetValue(0) )
    #    
    #    tryStopLSP(mass_dict, mstop, mlsp)
    #    tryStopLSP(info[sample_name]['mass_dict'], mstop, mlsp)

    #    mass_dict[mstop][mlsp]+=1
    #    info[sample_name]['mass_dict'][mstop][mlsp]+=1
    #    hstoplsp.Fill(mstop,mlsp)                    

    #print info[sample_name]

#pickle.dump( info, open("sample_info.pkl","w"))
#pickle.dump( mass_dict, open("sample_mass_dict.pkl","w"))

