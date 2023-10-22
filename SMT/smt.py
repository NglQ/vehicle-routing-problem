import z3
import numpy as np

def smt_model(path_to_instance='./instances/inst01.dat'):
	solver = z3.Solver()
