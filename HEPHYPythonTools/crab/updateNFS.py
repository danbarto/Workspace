import subprocess
import os

from optparse import OptionParser

parser = OptionParser()
parser.add_option("--userNameDPM", dest="userNameDPM", default="schoef", type="string", action="store", help="username of DPM User")
parser.add_option("--userNameNFS", dest="userNameNFS", default="schoef", type="string", action="store", help="username on NFS disk /data/")
parser.add_option("--source", dest="source", default="pat_130418/8TeV-T1tttt-test", type="string", action="store", help="source directory in users dpm folder")
parser.add_option("--target", dest="target", default="pat_130501/8TeV-T1tttt", type="string", action="store", help="target directory in users NFS folder")
parser.add_option("--histName", dest="histName", default="histo", type="string", action="store", help="histogram name")
parser.add_option("--postFix", dest="postFix", default=".root", type="string", action="store", help="postFix of file")
(options, args) = parser.parse_args()

dpmDir = '/dpm/oeaw.ac.at/home/cms/store/user/'+options.userNameDPM+'/'+options.source
oDir = '/data/'+options.userNameNFS+'/'+options.target
hName = options.histName
hNameLen= len(hName)
pFix = options.postFix
pFixLen = len(pFix)

if not os.path.isdir(oDir):
  print "Creating ",oDir
  os.system("mkdir -p "+oDir)

lsNFS = os.listdir(oDir)
print oDir


p = subprocess.Popen(["dpns-ls -l "+ dpmDir], shell = True , stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
for line in p.stdout.readlines():
    line = line[:-1]
    print line
    filename = line.split(" ")[-1]
    size = int(line.split(" ")[-5]) 
    if  filename[:hNameLen+1] == "%s_"%hName and filename[-5:]==".root":
    #if (filename[:hNameLen+1] == "%s_"%hName and filename[-pFixLen:]==pFix) :
      sf = filename.split("_")
      print sf
      #tf = sf[0]+"_"+sf[1]+"_"
      tf = sf[0]+"_"+sf[1]+"_"
      found = False
      for f in lsNFS:
        #print "debug ", f
        if f.count(tf): 
          print "Found ", f, "when looking for", tf,"(copying", filename,")"
          found = True
          break
      if found: continue
      else: 
        if not size> 1000:
          print "Skipping because file is too small (",filename, "size:", size,")"
          continue
        print "Copying", dpmDir+"/"+filename, "to", oDir+"/"+filename
        #os.system("$LCG_LOCATION/bin/dpm/rfcp "+dpmDir+"/"+filename+" "+oDir+"/"+filename)
        print "debug"
        #print "lcg-cp rm://hephyse.oeaw.ac.at/"+dpmDir+"/"+filename+" "+oDir+"/"+filename 
        os.system("lcg-cp srm://hephyse.oeaw.ac.at/"+dpmDir+"/"+filename+" "+oDir+"/"+filename)
    
retval = p.wait()

