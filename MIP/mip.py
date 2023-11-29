import time

from amplpy import AMPL, add_to_path
import json
import os

module_path = os.path.dirname(os.path.realpath(__file__))

# TODO: add_to_path() is only useful to run the code from the local machine, not from the container
add_to_path('/home/edo/ampl')


def mip_model(instance_file: str, solver: str, time_limit: int, sym_break: bool) -> dict:
	# TODO: add symmetry breaking constraints
	# TODO: email pacco!!!

	ampl_solver = AMPL()
	ampl_solver.eval(f"reset data;")
	ampl_solver.set_option("gentimes", 0)
	ampl_solver.set_option("times", 0)

	ampl_solver.read(os.path.join(module_path, "mip.mod"))
	ampl_solver.read_data(instance_file)
	ampl_solver.set_option("solver", solver)

	# Each solver has its own way to set time limit example:
	# ampl_solver.set_option('highs_options', f'time_limit={1}')
	ampl_solver.set_option(f'{solver}_options', f'time_limit={time_limit}')

	start_time = time.time()
	ampl_solver.solve()
	elapsed_time = time.time() - start_time

	total_cost = ampl_solver.get_objective("cost_function").to_list()[0]  # get objective function
	# print("Objective is:", total_cost.value())                          # print cost function
	# cost = ampl_solver.get_parameter("cost")                            # get parameters

	x = ampl_solver.get_variable("x")  # get variables
	# y = ampl_solver.get_variable("y")
	# u = ampl_solver.get_variable("u")
	# ampl_solver.get_data("{j in FOOD} 100*Buy[j]/Buy[j].ub")            # get data
	n = ampl_solver.get_parameter("N").to_list()[0]
	m = ampl_solver.get_parameter("K").to_list()[0]

	x_dict = x.to_dict()
	full_path = []
	for i in range(1, m + 1):
		path = [k for k, v in x_dict.items() if v == 1 and k[2] == i]
		start = n + 1
		sub_path = []
		while len(sub_path) < len(path) - 1:
			next_step = list(filter(lambda e: e[0] == start, path))[0]
			start = next_step[1]
			sub_path.append(start)
		full_path.append(sub_path)

	# print(full_path)

	# print(x.getValues())
	# print(y.getValues())
	# print(u.getValues())

	statistics = dict()
	elapsed_time = int(elapsed_time)
	statistics['time'] = elapsed_time
	# TODO: here "solved" means optimal???
	if ampl_solver.solve_result == "solved":
		if elapsed_time >= time_limit:
			statistics['time'] = time_limit - 1
		else:
			statistics['time'] = elapsed_time
		statistics['optimal'] = True
	else:
		statistics['time'] = time_limit
		statistics['optimal'] = False

	statistics['obj'] = total_cost
	statistics['sol'] = full_path

	print(instance_file, solver, statistics)
	return statistics
