import sys,os
import subprocess
from optparse import OptionParser
import glob

from limitTools import *


##
#python run_splitCardIntoBins.py "../../data/cards/13TeV/Reload_IsrWeight/Full/T2*.txt" /afs/hephy.at/user/n/nrad/CMSSW/fork/CMSSW_7_4_12_patch4/src/Workspace/DegenerateStopAnalysis/plotsNavid/data/cards/13TeV/Reload_IsrWeight/Bins_v2/
#python run_splitCardIntoBins.py "../cutbased/cards/8TeV/Full/T2DegStop_*.txt" /afs/hephy.at/user/n/nrad/CMSSW/fork/CMSSW_7_4_12_patch4/src/Workspace/DegenerateStopAnalysis/plotsNavid/data/cards/8TeV/Bins_v2



##



call_script = "splitCardIntoBins.py"


#
# any options needed for this script?
#
parser = OptionParser()
(options,args) = parser.parse_args()
#
# parse input files
#

# the systs will be read from these cards
input_cards = glob.glob(args[0])


if not input_cards:
    raise Exception("no cards found: %s"%cards_with_sys)


#
# outdir
#
output_dir = args[1]






for card in input_cards:
    command = ["python",call_script, card ,output_dir]
    subprocess.call(command)
    
    
