from WMCore.Configuration import Configuration
config = Configuration()

#config.section_("<section-name>")
#config.<section-name>.<parameter-name> = <parameter-value>

config.section_("General")
config.General.requestName = "miniAODTuple"
#config.General.workArea = "" #full or relative path to working directory
config.General.transferOutput = True #whether to transfer
config.General.saveLogs = False #1MB still available
#config.General.failureLimit =  #0.1 or 10% (which?) fraction of tolerated failures

config.section_("JobType")
config.JobType.pluginName = 'Analysis'
config.JobType.psetName   = 'defaultMINIAODTupelizer_cfg.py'
#config.JobType.pyCfgParams   = [ 'xyz', 'xyz']

config.section_("Data")
config.Data.inputDataset   = '/TTJets_MSDecaysCKM_central_Tune4C_13TeV-madgraph-tauola/Spring14miniaod-PU20bx25_POSTLS170_V5-v2/MINIAODSIM'
config.Data.splitting   = 'FileBased'
config.Data.unitsPerJob = 2
#config.Data.totalUnits = 

config.section_("Site")
config.Site.storageSite = 'T2_AT_Legarno'


