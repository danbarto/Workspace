cmsDriver.py Configuration/GenProduction/python/SUS-RunIISpring15FSPremix-00002-fragment.py --filein root://hephyse.oeaw.ac.at//dpm/oeaw.ac.at/home/cms/store/user/nrad/lhe/merged/T2DegStop2j_300_270_merged.lhe --pileup_input dbs:/Neutrino_E-10_gun/RunIISpring15PrePremix-MCRUN2_74_V9-v1/GEN-SIM-DIGI-RAW --mc --eventcontent AODSIM --fast --customise SLHCUpgradeSimulations/Configuration/postLS1CustomsPreMixing.customisePostLS1 --datatier AODSIM --conditions MCRUN2_74_V9 --beamspot NominalCollision2015 --step GEN,SIM,RECOBEFMIX,DIGIPREMIX_S2:pdigi_valid,DATAMIX,L1,L1Reco,RECO,HLT:@frozen25ns --magField 38T_PostLS1 --datamix PreMix --no_exec --python_filename fastSim_cfg.py -n 1500000 --fileout T2DegStop_300_270_FastSim_full.root
