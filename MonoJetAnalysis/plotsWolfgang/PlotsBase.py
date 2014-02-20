import ROOT
import time
import os
from EventHelper import EventHelper
from Variable import Variable

class MyTimer:
    def __init__(self):
        self.active = False
        self.start_ = 0.
        self.stop_ = 0.
        self.entries = 0
        self.sum = 0.

    def start(self):
        self.active = True
        self.start_ = time.clock()

    def stop(self):
        self.stop_ = time.clock()
        assert self.active
        self.entries += 1
        self.sum += self.stop_ - self.start_
        self.start_ = 0.
        self.stop_ = 0.
        self.active = False

    def meanTime(self):
        if self.entries==0:
            return 0.
        return self.sum/self.entries
        
class PlotsBase:

    variables = { }

    def getVariables(self):
        return PlotsBase.variables

    def addVariable(self,name,nbins,xmin,xmax,scut='l',uselog=True):
        assert name.isalnum()
        assert not name in self.histogramList
        if not name in PlotsBase.variables:
            PlotsBase.variables[name] = Variable(name,nbins,xmin,xmax,scut,uselog)
        h1d = PlotsBase.variables[name].createTH1()
        self.histogramList[name] = h1d
        setattr(self,"h"+name,h1d)


    def __init__(self,name,preselection=None,elist=None,elistBase="./elists"):
        self.name = name
        self.preselection = preselection
        self.elistBase = elistBase
        assert os.path.isdir(elistBase)
        self.timers = [ ]
        for i in range(10):
            self.timers.append(MyTimer())
        self.writeElist = False
        self.readElist = False
        if self.preselection!=None and elist!=None:
            self.preselName = self.preselection.__class__.__name__
            if elist.lower().startswith("w"):
                self.writeElist = True
            elif elist.lower().startswith("r"):
                self.readElist = True
        if self.writeElist or self.readElist:
            self.preselDirName = os.path.join(self.elistBase,self.preselName)
            if not os.path.isdir(self.preselDirName):
                os.mkdir(self.preselDirName,0744)
         
    def showTimers(self):
        line = ""
        for t in self.timers:
            line += "{0:14.2f}".format(1000000*t.meanTime())
#            line += " " + str(t.meanTime())
        print line

    def prepareElist(self,sample,subSampleName):
        elist = None
        elistFile = None
        if self.readElist or self.writeElist:
            elistFileName = os.path.join(self.preselDirName,subSampleName+"_elist.root")
            opt = "create" if self.writeElist else "read"
            elistFile = ROOT.TFile(elistFileName,opt)
            objarr = ROOT.TObjArray()
            if self.writeElist:
                objstr = ROOT.TObjString()
                objstr.SetString(sample.name)
                objarr.Add(objstr.Clone())
                objstr.SetString(subSampleName)
                objarr.Add(objstr.Clone())
                objstr.SetString(str(sample.downscale))
                objarr.Add(objstr.Clone())
                objarr.Write("file",ROOT.TObject.kSingleKey)
                elist = ROOT.TEventList("elist",self.preselName+" / "+sample.name+" / "+subSampleName)
            else:
                objarr = elistFile.Get("file")
                assert objarr[0].GetString().Data()==sample.name
                assert objarr[1].GetString().Data()==subSampleName
                assert objarr[2].GetString().Data()==str(sample.downscale)
                elist = elistFile.Get("elist")
        return ( elist, elistFile )

    def createGenerator(self,end,downscale=1):
        i = downscale - 1
        while i<end:
            yield i
            i += downscale


    def fillall(self,sample):
        for itree in range(len(sample.names)):
            tree = sample.getchain(itree)
            print sample.name,itree
            print tree.GetEntries()
            nentries = tree.GetEntries()
            downscale = sample.downscale
            iterator = self.createGenerator(tree.GetEntries(),sample.downscale)
            if self.readElist or self.writeElist:
                elist, elistFile = self.prepareElist(sample,sample.names[itree])
                if self.readElist:
                    iterator = self.createGenerator(elist.GetN())
            self.timers[6].start()
            eh = EventHelper(tree)
#        for iev in range(tree.GetEntries()):
            nall = 0
            nsel = 0
            for iev in iterator:
#            for iev in sample.getentries(tree):
#            if sample.downscale==1 or (iev%sample.downscale)==0:
                jev = iev if not self.readElist else elist.GetEntry(iev)
                eh.getEntry(jev)
                nall += 1
                if self.readElist or self.preselection==None or self.preselection.accept(eh):
                    self.fill(eh,sample.downscale)
                    if self.writeElist:
                        elist.Enter(iev)
                    nsel += 1
            print "Ntot for ",sample.name,sample.names[itree]," = ",nall,nsel
#        for ev in tree:
#            self.fill(ev)
            self.timers[6].stop()
            if self.writeElist:
                elist.Write()
            if self.writeElist or self.readElist:
                elistFile.Close()
        self.showTimers()
            
        