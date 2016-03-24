



isrWeight = lambda norm: '(1.+{norm}*GenPart_mass[stopIndex1]) *(1.*(stops_pt<120.)+0.95*(stops_pt>=120.&&stops_pt<150.)+0.9*(stops_pt>=150.&&stops_pt<250.)+0.8*(stops_pt>=250.))'.format(norm=norm)
isrw = isrWeight(9.5e-5)



isrWeight_8tev = "puWeight*wpts4X*(1.+7.5e-5*Max$(gpM*(gpPdg==1000006)))*(1.*(ptISR<120.)+0.95*(ptISR>=120.&&ptISR<150.)+0.9*(ptISR>=150.&&ptISR<250.)+0.8*(ptISR>=250.))"


wptweight_a = "((ptw<200)*1.+(ptw>200&&ptw<250)*1.008+(ptw>250&&ptw<350)*1.063+(ptw>350&&ptw<450)*0.992+(ptw>450&&ptw<650)*0.847+(ptw>650&&ptw<800)*0.726+(ptw>800)*0.649)"
wptweight_p = "((ptw<200)*1.+(ptw>200&&ptw<250)*1.016+(ptw>250&&ptw<350)*1.028+(ptw>350&&ptw<450)*0.991+(ptw>450&&ptw<650)*0.842+(ptw>650&&ptw<800)*0.749+(ptw>800)*0.704)"
wptweight_n = "((ptw<200)*1.+(ptw>200&&ptw<250)*0.997+(ptw>250&&ptw<350)*1.129+(ptw>350&&ptw<450)*1.003+(ptw>450&&ptw<650)*0.870+(ptw>650&&ptw<800)*0.687+(ptw>800)*0.522)"
ttptweight = "1.24*exp(0.156-0.5*0.00137*(gpPt[6]+gpPt[7]))"

weightDict={
             "w": {
                    "ptweight":{ 
                                "SR1":  wptweight_a  , 
                                "SR2":  wptweight_n  ,
                                }
                   },

             "tt": {
                    "ptweight": ttptweight
                   }

           }


"""
Branching Ratio reweight = 1.022  ,  
Pythia ignores the given SLHA BR for stop decay to leptons (vs taus) and uses equal BR of 10.8%.
The reweighting factor to come to 11.1% is 1.028 for one stop, and 1.022 for two stops.

"""

