#! /usr/bin/env python
import sys, os, subprocess

from optparse import OptionParser

parser = OptionParser()
#parser.add_option("--mode", dest="mode", default="dpm", type="string", action="store", help="'dpm' or 'nfs'")
#parser.add_option("--dirname", dest="dirname", default="/dpm/oeaw.ac.at/home/cms/store/user/schoef/MET_050214/", type="string", action="store", help="username on NFS disk ir DPM")
parser.add_option("--mode", dest="mode", default="nfs", type="string", action="store", help="'dpm' or 'nfs'")
parser.add_option("--delete", dest="delete", default=0, type="int", action="store", help="whether or not to delete")
parser.add_option("--dirname", dest="dirname", default="/data/schoef/pat_131021/", type="string", action="store", help="username on NFS disk ir DPM")
(options, args) = parser.parse_args()

print "Looking at",options.mode,options.dirname
if options.mode=="dpm":
  subdirnames = []
  p = subprocess.Popen(["dpns-ls "+ options.dirname], shell = True , stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
  for line in p.stdout.readlines():
    line = line[:-1]
    if not line.count('joined'):
      subdirnames.append(line)

if options.mode=="nfs":
  subdirnames = os.listdir(options.dirname) 

toBeRemovedGlobal=[]
print "Going through:", subdirnames

def diff(a, b):
  b = set(b)
  return [aa for aa in a if aa not in b]

def readFileSize(f):
  p = subprocess.Popen(["dpns-ls -l "+ f], shell = True , stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
  line=""
  for line in p.stdout.readlines():
    line = line[:-1]
  return int(line.split()[4])
onlyOnNameServer=[]
for subdir in subdirnames:
  subdirname = options.dirname+"/"+subdir+"/"
  print  "At subdir ", subdirname
  filenames = []
  if options.mode=='nfs':
    filenames = os.listdir(subdirname)
  if options.mode=='dpm':
    filenamesNameServer = []
    p = subprocess.Popen(["dpns-ls -l "+ subdirname], shell = True , stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    for line in p.stdout.readlines():
      line = line[:-1].split()[-1]
      filenames.append(line)
#      if line.count('_1429_'):print 'l', line
    p = subprocess.Popen(["dpns-ls "+ subdirname], shell = True , stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    for line in p.stdout.readlines():
      line = line[:-1].split()[-1]
      filenamesNameServer.append(line)
    for file in diff(filenamesNameServer , filenames):
      print "Only on name server:", file  
      onlyOnNameServer.append(subdirname+file)
  numbers=[]
  for file in filenames:
    sstring = file.split("_")
    if len(sstring)>1:
      numbers.append(int(sstring[1]))
  if len(numbers)>0:
    maxFileNumber = max(numbers)
  else:
    continue
  filesPerNumber={}
  for i in range(1,maxFileNumber+1):
    filesPerNumber[str(i)]=[]
    for file in filenames:
      if file.count("histo_"+str(i)+"_")>0:
#        if i==1429:print file
        filesPerNumber[str(i)].append(file)
  for i in range(1,maxFileNumber+1):
    if len(filesPerNumber[str(i)])>1:
      toBeRemoved=[]
      for file in filesPerNumber[str(i)]:
        toBeRemoved.append(subdirname+"/"+file)
      print "Found duplicate Files!"
      toBeKept = ""
      maxSize = 0
      for file in filesPerNumber[str(i)]:
        filename = subdirname+"/"+file
        if options.mode=="nfs":
          size = os.path.getsize(filename)
        else:
          print filename, filesPerNumber[str(i)]
          size = readFileSize(filename)
        print filename, "size", size
        if size>=maxSize:
          toBeKept = filename
          maxSize = size
      toBeRemoved.remove(toBeKept)
      print "Keep:", toBeKept, "Remove:", toBeRemoved
      toBeRemovedGlobal.extend(toBeRemoved)


for f in toBeRemovedGlobal:
  if options.delete:
    print "Removing",f
    if options.mode=='nfs':
      os.system('rm '+f)
    else:
      os.system('$LCG_LOCATION/bin/rfrm '+f)
#      os.system('dpns-rm '+f)
  else:
    print "Would remove",f

for f in onlyOnNameServer:
  if not options.mode=='nfs':
    print "Entry only in name server:",f,'--> Remove from db'
    if options.delete:
      os.system('dpns-rm -f '+f)
