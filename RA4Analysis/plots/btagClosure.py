import ROOT, pickle, itertools
from simplePlotsCommon import *
c = ROOT.TChain("Events")
c.Add("/data/schoef/convertedTuples_v10/copyMET/Mu/TTJets-53X/histo_TTJets-53X.root")

#c.Draw("met>>hmetMC0(35,0,1050)", "weight*(nbtags==0)")
#c.Draw("met>>hmetRW0(35,0,1050)", "weightBTag0")
#
#c.Draw("met>>hmetMC1(35,0,1050)", "weight*(nbtags==1)")
#c.Draw("met>>hmetRW1(35,0,1050)", "weightBTag1")
#
#c.Draw("met>>hmetMC2(35,0,1050)", "weight*(nbtags==2)")
#c.Draw("met>>hmetRW2(35,0,1050)", "weightBTag2")
#
#c.Draw("met>>hmetMC3(35,0,1050)", "weight*(nbtags==3)")
#c.Draw("met>>hmetRW3(35,0,1050)", "weightBTag3")
#
#c.Draw("met>>hmetMC4(35,0,1050)", "weight*(nbtags==4)")
#c.Draw("met>>hmetRW4(35,0,1050)", "weightBTag4")
#
#hmetMC0 = ROOT.gDirectory.Get("hmetMC0")
#hmetMC0.GetYaxis().SetTitle("Events / 30 GeV")
#hmetMC0.GetXaxis().SetTitle("#slash{E}_{T} (GeV)")
#hmetRW0 = ROOT.gDirectory.Get("hmetRW0")
#hmetRW0.SetLineStyle(2)
#hmetRW0.SetMarkerStyle(0)
#hmetMC0.SetMarkerStyle(0)
#
#hmetMC1 = ROOT.gDirectory.Get("hmetMC1")
#hmetRW1 = ROOT.gDirectory.Get("hmetRW1")
#hmetMC1.SetLineColor(ROOT.kBlue)
#hmetRW1.SetLineColor(ROOT.kBlue)
#hmetRW1.SetLineStyle(2)
#hmetRW1.SetMarkerStyle(0)
#hmetMC1.SetMarkerStyle(0)
#hmetRW1.SetMarkerColor(ROOT.kBlue)
#hmetMC1.SetMarkerColor(ROOT.kBlue)
#
#hmetMC2 = ROOT.gDirectory.Get("hmetMC2")
#hmetRW2 = ROOT.gDirectory.Get("hmetRW2")
#hmetMC2.SetLineColor(ROOT.kGreen)
#hmetRW2.SetLineColor(ROOT.kGreen)
#hmetRW2.SetLineStyle(2)
#hmetRW2.SetMarkerStyle(0)
#hmetMC2.SetMarkerStyle(0)
#hmetRW2.SetMarkerColor(ROOT.kGreen)
#hmetMC2.SetMarkerColor(ROOT.kGreen)
#
#hmetMC3 = ROOT.gDirectory.Get("hmetMC3")
#hmetRW3 = ROOT.gDirectory.Get("hmetRW3")
#hmetMC3.SetLineColor(ROOT.kMagenta)
#hmetRW3.SetLineColor(ROOT.kMagenta)
#hmetRW3.SetLineStyle(2)
#hmetRW3.SetMarkerStyle(0)
#hmetMC3.SetMarkerStyle(0)
#hmetRW3.SetMarkerColor(ROOT.kMagenta)
#hmetMC3.SetMarkerColor(ROOT.kMagenta)
#
#hmetMC4 = ROOT.gDirectory.Get("hmetMC4")
#hmetRW4 = ROOT.gDirectory.Get("hmetRW4")
#hmetMC4.SetLineColor(ROOT.kCyan)
#hmetRW4.SetLineColor(ROOT.kCyan)
#hmetRW4.SetLineStyle(2)
#hmetRW4.SetMarkerStyle(0)
#hmetMC4.SetMarkerStyle(0)
#hmetRW4.SetMarkerColor(ROOT.kCyan)
#hmetMC4.SetMarkerColor(ROOT.kCyan)
#
#l = ROOT.TLegend(0.7,0.5,1,1)
#l.AddEntry( hmetMC0, "0 tags, MC")
#l.AddEntry( hmetRW0, "0 tags, reweighted")
#l.AddEntry( hmetMC1, "1 tags, MC")
#l.AddEntry( hmetRW1, "1 tags, reweighted")
#l.AddEntry( hmetMC2, "2 tags, MC")
#l.AddEntry( hmetRW2, "2 tags, reweighted")
#l.AddEntry( hmetMC3, "3 tags, MC")
#l.AddEntry( hmetRW3, "3 tags, reweighted")
#l.AddEntry( hmetMC4, "4 tags, MC")
#l.AddEntry( hmetRW4, "4 tags, reweighted")
#l.SetFillColor(0)
#l.SetBorderSize(1)
#c1 = ROOT.TCanvas()
#c1.SetLogy(True)
#hmetMC0.GetYaxis().SetRangeUser(10**(-2), 2*10**4)
#hmetMC0.Draw("")
#hmetRW0.Draw("same")
#hmetMC1.Draw("same")
#hmetRW1.Draw("same")
#hmetMC2.Draw("same")
#hmetRW2.Draw("same")
#hmetMC3.Draw("same")
#hmetRW3.Draw("same")
#hmetMC4.Draw("same")
#hmetRW4.Draw("same")
#l.Draw()
#c1.Print("/afs/hephy.at/user/s/schoefbeck/www/pngBTag/btag_reweighting_log.png")

#c1.SetLogy(False)
#l = ROOT.TLegend(0.7,0.7,1,1)
#l.SetFillColor(0)
#l.SetBorderSize(1)
#l.AddEntry( hmetRW0, "0 tags")
#l.AddEntry( hmetRW1, "1 tags")
#l.AddEntry( hmetRW2, "2 tags")
#l.AddEntry( hmetRW3, "3 tags")
#l.AddEntry( hmetRW4, "4 tags")
#hmetMC0.SetLineStyle(1)
#hmetMC0.GetYaxis().SetRangeUser(0.8,1.2)
#hmetMC1.SetLineStyle(1)
#hmetMC2.SetLineStyle(1)
#hmetMC3.SetLineStyle(1)
#hmetMC4.SetLineStyle(1)
#hmetRW0.Divide(hmetMC0)
#hmetRW0.Draw()
#hmetRW1.Divide(hmetMC1)
#hmetRW1.Draw("same")
#hmetRW2.Divide(hmetMC2)
#hmetRW2.Draw("same")
#hmetRW3.Divide(hmetMC3)
#hmetRW3.Draw("same")
#hmetRW4.Divide(hmetMC4)
#hmetRW4.Draw("same")
#l.Draw()
#c1.Print("/afs/hephy.at/user/s/schoefbeck/www/pngBTag/btag_reweighting_ratio.png")

histo={}

for i, mode in enumerate(["", "_SF", "_SF_b_Up", "_SF_b_Down", "_SF_light_Up", "_SF_light_Down"]):
  c.Draw("met>>hmetRW0"+mode+"(35,0,1050)", "weightBTag0"+mode)
  histo[mode] = ROOT.gDirectory.Get("hmetRW0"+mode)
  histo[mode].SetLineColor(ROOT_colors[i])
  histo[mode].SetLineStyle(0)
  histo[mode].SetLineWidth(0)
  histo[mode].SetMarkerColor(ROOT_colors[i])
  histo[mode].SetMarkerStyle(0);
  histo[mode].GetXaxis().SetTitle("#slash{E}_{T} (GeV)")
  histo[mode].GetYaxis().SetTitle("Number of Events / 50 GeV")

c1 = ROOT.TCanvas()
c1.SetLogy()
l = ROOT.TLegend(0.5,0.7,1,1.0)
l.SetFillColor(0)
l.SetShadowColor(ROOT.kWhite)
l.SetBorderSize(1)

for i, mode in enumerate(["", "_SF", "_SF_b_Up", "_SF_b_Down", "_SF_light_Up", "_SF_light_Down"]):
  print i
  if i==0:
    histo[mode].Draw()
  else:
    histo[mode].Draw("same")
  l.AddEntry(histo[mode], "weight"+mode)

l.Draw()
c1.Print("/afs/hephy.at/user/s/schoefbeck/www/pngBTag/btag_reweighting_SF_variations.png")
