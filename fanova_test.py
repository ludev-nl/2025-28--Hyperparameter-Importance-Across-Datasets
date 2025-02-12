from fanova import fANOVA
import csv
import numpy as np 
import os 

path = os.path.dirname(os.path.realpath(__file__))
X = np.loadtxt(path + '/examples/example_data/online_lda/online_lda_features.csv', delimiter=",") #add corresponding path to csv files inside the fanova folder from github
Y = np.loadtxt(path + '/examples/example_data/online_lda/online_lda_responses.csv', delimiter=",")
f = fANOVA(X,Y)

ant = f.quantify_importance((0, )) #variable just to print results 

print(ant)  