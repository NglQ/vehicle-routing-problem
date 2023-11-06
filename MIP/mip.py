import time

from amplpy import AMPL, add_to_path
import json
from converter import convert, generate_mip_dat
import os
add_to_path("./ampl.linux64")


def mip_model(path_to_instance='./instances/inst01.dat'):
	
	m, n, l, p, d = convert(path_to_instance)
	generate_mip_dat('./inst01_mip.dat', m, n, l, p, d)
	
	ampl_solver = AMPL()
	
	solver = 'scip'
	ampl_solver.set_option("solver", solver)
	ampl_solver.set_option('scip_options', f'time_limit={300}')  # Each solver has its own way to set time limit example:
															# ampl_solver.set_option('highs_options', f'time_limit={1}')
	ampl_solver.set_option("gentimes", 0)
	ampl_solver.set_option("times", 1)

	ampl_solver.read(os.path.join('.', "mip.mod"))
	ampl_solver.read_data(os.path.join('.', "mip.dat"))
	start_time = time.time()
	ampl_solver.solve()
	elapsed_time = time.time() - start_time

	# assert ampl_solver.solve_result == "solved"
	total_cost = ampl_solver.get_objective("cost_function").to_list()[0]  # get objective function
	# print("Objective is:", total_cost.value()) # print cost function
	# cost = ampl_solver.get_parameter("cost") #get parameters
	x = ampl_solver.get_variable("x") # get variables
	# y = ampl_solver.get_variable("y")
	# u = ampl_solver.get_variable("u")
	# ampl_solver.get_data("{j in FOOD} 100*Buy[j]/Buy[j].ub") # get data
	x_dict = x.to_dict()
	full_path = []
	for i in range(1, m+1):
		path = [k for k, v in x_dict.items() if v == 1 and k[2] == i]
		start = n+1
		sub_path = []
		while len(sub_path) < len(path)-1:
			next_step = list(filter(lambda e: e[0] == start, path))[0]
			start = next_step[1]
			sub_path.append(start)
		full_path.append(sub_path)

	# print(full_path)

	# print(x.getValues())
	# print(y.getValues())
	# print(u.getValues())
	statistics = dict()
	statistics['time'] = elapsed_time
	statistics['optimal'] = ampl_solver.solve_result == "solved"
	statistics['obj'] = total_cost
	statistics['sol'] = full_path

	stats = {'cplex': statistics}
	print(stats)
	json.dump(stats, open('mip_test.json', 'w'))
