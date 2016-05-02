import Workspace.DegenerateStopAnalysis.navidTools.limitTools as limitTools
from Workspace.DegenerateStopAnalysis.navidTools.NavidTools import makeStopLSPPlot, getTH2FbinContent, makeStopLSPRatioPlot, makeDir, setup_style
from Workspace.DegenerateStopAnalysis.navidTools.ColorPalette import *
import pickle
import ROOT
import glob
from array import array
import os

#if len(args)==2:
#    pass
#else:
#    raise Exception("Needs Two Arguments, path to the limit.pkl, and savedir")


#
#bins13tev_dir  = args[0]
#ratios_savedir = args[1]
#
#print bins13tev_dir
#
#
#
#bins8tev_dir  ="/afs/hephy.at/user/n/nrad/CMSSW/fork/CMSSW_7_4_12_patch4/src/Workspace/DegenerateStopAnalysis/plotsNavid/data/cards/8TeV/Bins_v2"
#bins8tev_pkls = glob.glob(bins8tev_dir+"/*.pkl")
#bins8tev_savedir = ratios_savedir 
#bins8tev = [
#            { "name":limitTools.get_filename(b) , "pkl":b, "savedir":bins8tev_savedir+"/8TeV_%s.png"%limitTools.get_filename(b) } for b in bins8tev_pkls
#           ]
#
#
#
#bins13tev_pkls = glob.glob(bins13tev_dir+"/SRSL*.pkl")
#bins13tev_pkls.append(bins13tev_dir+"/ALL.pkl")
#bins13tev_savedir = ratios_savedir 
#makeDir(bins13tev_savedir)
#bins13tev = [
#            { "name":limitTools.get_filename(b) , "pkl":b, "savedir":bins13tev_savedir+"/%s.png"%limitTools.get_filename(b) } for b in bins13tev_pkls
#            ]
#
#
#
#
#
#bins13tev_names = [x['name'] for x in bins13tev]
#
#ratios={}
#ratio_plots={}
#
#ROOT.gStyle.SetPaintTextFormat("0.2f")
#bins= [13,87.5,412.5, 75, 17.5, 392.5 ]
#
#for cardDict_8tev in bins8tev:
#    pkl_8tev = cardDict_8tev['pkl']
#    limit_8tev = pickle.load(file(pkl_8tev))
#    name_8tev = cardDict_8tev['name']
#    saveDir_8tev = cardDict_8tev['savedir']
#
#
#
#    if name_8tev in bins13tev_names:
#        cardDict_13tev  = bins13tev[bins13tev_names.index(name_8tev) ]
#        pkl_13tev = cardDict_13tev['pkl']
#        limit_13tev = pickle.load(file(pkl_13tev))
#        name_13tev = cardDict_13tev['name']
#        saveDir_13tev = cardDict_13tev['savedir']
#        print limit_13tev[375][305]
#    
#        ROOT.gStyle.SetPalette(len(excl_cols), excl_cols)
#
#        limitTools.drawExpectedLimit(limit_13tev,saveDir_13tev,title= name_13tev)
#        limitTools.drawExpectedLimit(limit_8tev,saveDir_8tev,  title=name_8tev)
#        c1 = ROOT.TCanvas("c%s"%name_13tev,"c%s"%name_13tev,1500,1026)
#
#
#        assert name_13tev == name_8tev
#            
#        ratio_plots[name_13tev] , ratios[name_13tev] = makeStopLSPRatioPlot(name_13tev, limit_13tev, limit_8tev, bins=bins, key= lambda x:float(x['0.500']) if x.has_key("0.500") else 999 )
#
#        
#        
#        ROOT.gStyle.SetPalette(len(ratio_cols), ratio_cols)
#    
#
#        ratio_plots[name_13tev].SetContour(len(ratio_conts), ratio_conts)
#
#        ratio_plots[name_13tev].Draw("COLZ TEXT")
#        ratio_plots[name_13tev].GetZaxis().SetRangeUser(0,2)
#
#        ltitle = ROOT.TLatex()
#        ltitle.SetNDC()
#        ltitle.SetTextAlign(12)
#        #ytop = 1.05- canv.GetTopMargin()
#        #ltitle_info = [0.1, ytop]
#        ltitle.DrawLatex(0.2, 0.8, "#frac{R_{13TeV}}{R_{8TeV}}  %s"%name_13tev  )
#
#
#        c1.SaveAs(ratios_savedir+"/Ratio_%s.png"%name_13tev)




ratio_conts = array("d", [-1.e300] + [0.2+0.2*x for x in range(10) ] ) 
ratio_cols = getNiceColors(num=5, bands=10)
ratio_conts = array("d", [-1.e300 ,0.5,1,1.5,2,1000])
ratio_cols = array('i', [  925, 927, 929, 931, 932, 933, 934] )


excl_conts = array("d",[-1.e300,0.99999])
excl_cols  = array("i",[ROOT.kGreen-7,ROOT.kRed-7])



def getValueFromDict(x, val="0.500", default=999):
    try:
        ret = x[1][val]
    except KeyError:
        ret = default
    return ret


def getExpLimitRatio(lim1, lim2, title1=False, title2=False, title_ratio = False, saveDir=False, csize=(1500,1026) , draw_ratio_only=True):
    
    ROOT.gStyle.SetPaintTextFormat("0.2f")
    bins= [13,87.5,412.5, 75, 17.5, 392.5 ]

    ROOT.gStyle.SetPalette(len(excl_cols), excl_cols)


    il = 1
    limits = {}
    for l,t in [(lim1,title1), (lim2,title2)]:
        il +=1
        if t: ltitle = t
        else:
            if type(l) == type({}):
                ltitle = "lim_%s"%il
            elif type( l ) == type(""):
                ltitle = os.path.basename(l).rstrip(".pkl")
        limits[l]={ 'limit': l , 'title':ltitle}
        if not draw_ratio_only:
            cl , pl = limitTools.drawExpectedLimit(l, saveDir +"/%s.png"%ltitle,  title= ltitle, csize=csize, key=getValueFromDict)
            limits[l]['canv']= cl
            limits[l]['plot']= pl

    if not title_ratio:
        title_ratio= "Ratio"

    canv_ratio_title = "CanvRatio_%s_%s"%(limits[lim1]['title'],limits[lim2]['title'] )
    c1 = ROOT.TCanvas("cRatio","cRatio", *csize)



    ratio_plots  , ratios  = makeStopLSPRatioPlot( title_ratio , pickle.load( file( lim1)), pickle.load(file(lim2)) , 
                                                   bins=bins, key= lambda x:float(x[1]['0.500']) if x[1].has_key("0.500") else 999 )
    ROOT.gStyle.SetPalette(len(ratio_cols), ratio_cols)
    ratio_plots.SetContour(len(ratio_conts), ratio_conts)
    ratio_plots.Draw("COLZ TEXT")
    ratio_plots.GetZaxis().SetRangeUser(0,2)
    ltitle = ROOT.TLatex()
    ltitle.SetNDC()
    ltitle.SetTextAlign(12)
    ltitle.DrawLatex(0.2, 0.8, "%s"%title_ratio  )
    c1.SaveAs( saveDir+"/%s.png"%title_ratio)


                



if __name__=='__main__':

    #from optparse import OptionParser
    #parser = OptionParser()
    #(options,args) = parser.parse_args()
    lim1 = '/data/nrad/results/cards_and_limits/13TeV/HT/2300pbm1_newSR_v4/BasicSys.pkl'
    lim2 = '/data/nrad/results/cards_and_limits/13TeV/HT/2300pbm1_newSR_v3/BasicSys.pkl'
    getExpLimitRatio(lim1, lim2 , "l1","l2", "ratios", saveDir="./")

