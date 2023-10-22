import z3

def sat_model(path_to_instance='./instances/inst01.dat'):

	# Create a solver instance
	solver = z3.Solver()

	# Create variables

