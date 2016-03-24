import ROOT
import pickle
from Workspace.HEPHYPythonTools.user import username
from Workspace.HEPHYPythonTools.helpers import getObjFromFile, getChain, getChunks, getCutYieldFromChain, getYieldFromChain
#from Workspace.DegenerateStopAnalysis.cmgTuples_Spring15_7412pass2_mAODv2_v4 import *
import Workspace.DegenerateStopAnalysis.cmgTuples_Spring15_7412pass2_mAODv2_v5 as cmgTuples
from Workspace.HEPHYPythonTools.xsecSMS import *

#samples = [T5qqqqVV_mGluino_1000To1075_mLSP_1To950] #, T5qqqqVV_mGluino_1200To1275_mLSP_1to1150]
samples = [     

            cmgTuples.SMS_T2_4bd_mStop_100_mLSP_20to90              ,  
            cmgTuples.SMS_T2_4bd_mStop_125_mLSP_45to115             ,  
            cmgTuples.SMS_T2_4bd_mStop_150_mLSP_70to140             ,  
            cmgTuples.SMS_T2_4bd_mStop_175_mLSP_95to165             ,  
            cmgTuples.SMS_T2_4bd_mStop_200_mLSP_120to190            ,  
            cmgTuples.SMS_T2_4bd_mStop_225_mLSP_145to225            ,  
            cmgTuples.SMS_T2_4bd_mStop_250_mLSP_170to240            ,  
            cmgTuples.SMS_T2_4bd_mStop_275_mLSP_195to265            ,  
            cmgTuples.SMS_T2_4bd_mStop_300_mLSP_220to290            ,  
            cmgTuples.SMS_T2_4bd_mStop_325_mLSP_245to315            ,  
            cmgTuples.SMS_T2_4bd_mStop_350_mLSP_270to340            , 
            cmgTuples.SMS_T2_4bd_mStop_375_mLSP_295to365            , 
            cmgTuples.SMS_T2_4bd_mStop_400_mLSP_320to390            , 
            cmgTuples.SMS_T2_4bd_mStop_425to475_mLSP_345to465       ,
            cmgTuples.SMS_T2_4bd_mStop_500to550_mLSP_420t540        ,
            cmgTuples.SMS_T2_4bd_mStop_550to600_mLSP_470t590        ,

        ]

#samples = [T5qqqqVV_mGluino_1400To1550_mLSP_1To1275, T5qqqqVV_mGluino_1100To1175_mLSP_1to1050]
#T5qqqqVV_mGluino_1200To1275_mLSP_1to1150, 

#pickleDir = './'
pickleDir = cmgTuples.sample_path

mass_dict_all={}

for sample in samples: 
    print sample["name"]
    mass_dict = {}  


    chunks = getChunks(sample, maxN=-1)

    #cut_common = "Sum$(abs(GenPart_pdgId)==1000006 && abs(GenPart_motherId)==1000024 && abs(GenPart_grandmotherId)==1000021)==2&&(Sum$(abs(GenPart_pdgId)==24)==2)"
    #for chunk in chunks:

    #chain = ROOT.TChain("tree")
    #for chunk in chunks:
    #    chain.Add(chunk['file'])
    #    
    #    chain.Draw("GenSusyMStop>>h_stop")
    #    nbins = ROOT.h_stop.GetNbinsX():
            

    if True:
        hstop = ROOT.TH1D("hstop","hstop",2000,0,2000)
        hlsp = ROOT.TH1D("hlsp","hlsp",2000,0,2000)
        cut_common = "Sum$(abs(GenPart_pdgId)==1000006)"

        chunk = chunks[0]
        chain = getChain(chunk, minAgeDPM=0, histname='histo', xrootPrefix='root://hephyse.oeaw.ac.at/', maxN=-1, treeName='tree')

        #cpTree = chain.CopyTree("Sum$(abs(GenPart_pdgId)==1000022&&abs(GenPart_motherId)==1000024&&abs(GenPart_grandmotherId)==1000021)==2&&(Sum$(abs(GenPart_pdgId)==24)==2)")
        cpTree = chain
        print "tree is copied"
        cpTree.Draw("GenSusyMStop>>hstop")
        bin_cont_temp = 0
        for cbin in range(0,hstop.GetNbinsX()):
          if hstop.GetBinContent(cbin) != 0: 
             bin_cont = hstop.GetBin(cbin)
             if bin_cont != bin_cont_temp :
               mstop = hstop.GetBin(cbin)-1
               print "stop mass:" , mstop
               mass_dict[mstop] = {}
               cpTree.Draw("GenSusyMNeutralino>>hlsp",cut_common+"&&GenSusyMStop=="+str(mstop)) 
               lspbin_content_temp = 0
               for cnbin in range(0,hlsp.GetNbinsX()):
                if hlsp.GetBinContent(cnbin) != 0:
                  bin_cont_lsp = hlsp.GetBin(cnbin) 
                  if bin_cont_lsp != lspbin_content_temp :
                    mlsp = hlsp.GetBin(cnbin)-1
                    print "=====lsp mass:" , mlsp
                    mass_dict[mstop][mlsp] = {}
                    nEntry = cpTree.GetEntries(cut_common+"&&GenSusyMStop=="+str(mstop)+"&&GenSusyMNeutralino=="+str(mlsp))
                    m_xsec = stop13TeV_NLONLL[mstop]
                    mass_dict[mstop][mlsp] = {"nEntry": nEntry , "xsec":m_xsec }
                  lspbin_content_temp = bin_cont_lsp
             bin_cont_temp = bin_cont
        print mass_dict
        mass_dict_all.update(mass_dict)

        pickle.dump(mass_dict, file(pickleDir+sample["name"]+'_mass_nEvents_xsec.pkl','w'))
        print "written:" , pickleDir+sample["name"]+'_mass_nEvents_xsec.pkl'

pickle.dump(mass_dict_all, file(pickleDir+"mass_dict_all.pkl","w"))

    
