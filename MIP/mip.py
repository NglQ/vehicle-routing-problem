import time
import os

import numpy as np
from amplpy import AMPL, add_to_path

from bounds_generator import generate_lowerbound, generate_upperbound
from converter import convert

module_path = os.path.dirname(os.path.realpath(__file__))

# INFO: add_to_path() is only useful to run the code from the local machine, not from the container
# add_to_path('/home/edo/ampl')


def mip_model(instance_file: str, instance_number: str, solver: str, time_limit: int, sym_break: bool) -> dict:

	# Calculate lower and upper bounds
	m, n, l, p, d = convert(os.path.join(module_path, f'./../instances/inst{instance_number}.dat'))
	lb = generate_lowerbound(n, d)
	ub = generate_upperbound(n, m, d)

	ampl_solver = AMPL()
	ampl_solver.eval(f'reset data;')

	ampl_solver.set_option('gentimes', 0)
	ampl_solver.set_option('times', 0)

	ampl_solver.read(os.path.join(module_path, "mip.mod"))
	if sym_break:
		ampl_solver.eval(
			's.t. sym_break {k in COURIERS, m in COURIERS, j in NODES: k<m}: max(sum{i in NODES} y[i,k]*L[i], '
			'sum{i in NODES} y[i,m]*L[i]) <= min(C[k], C[m]) ==> ((x[N+1, j, k] == 1) ==> sum{l in {1..j}} x[N+1, l, m] == 0);'
		)
	ampl_solver.eval('s.t. lower_bound: max{k in COURIERS} sum {i in NODES_1, j in NODES_1} D[i,j]*x[i,j,k] >='+str(lb)+';')
	ampl_solver.eval('s.t. upper_bound: max{k in COURIERS} sum {i in NODES_1, j in NODES_1} D[i,j]*x[i,j,k] <='+str(ub)+';')

	ampl_solver.read_data(instance_file)
	ampl_solver.set_option('solver', solver)

	# Each solver has its own way to set time limit example:
	# ampl_solver.set_option('highs_options', f'time_limit={1}')
	if solver in ['highs']:
		ampl_solver.set_option(f'{solver}_options', f'time_limit={time_limit}')
	elif solver in ['gurobi', 'cbc', 'xpress', 'copt', 'mosek']:
		ampl_solver.set_option(f'{solver}_options', f'TimeLimit={time_limit}')
	else:
		raise NotImplementedError(f'Solver {solver} not implemented.')

	start_time = time.time()
	ampl_solver.solve()
	elapsed_time = time.time() - start_time

	total_cost = ampl_solver.get_objective('cost_function').to_list()[0]  # get objective function
	if total_cost == 0:
		print(f'No solution found for instance {instance_number} with solver {solver} with sym_break = {sym_break}.')
		return {'time': time_limit, 'optimal': False, 'obj': total_cost, 'sol': []}

	x = ampl_solver.get_variable('x')  # get variables
	n = ampl_solver.get_parameter('N').to_list()[0]
	m = ampl_solver.get_parameter('K').to_list()[0]

	x_dict = x.to_dict()

	full_path = []
	for i in range(1, m + 1):
		path = [k for k, v in x_dict.items() if np.allclose(v, 1) and k[2] == i]
		start = n + 1
		sub_path = []
		while len(sub_path) < len(path) - 1:
			next_step = list(filter(lambda e: e[0] == start, path))[0]
			start = next_step[1]
			sub_path.append(start)
		full_path.append(sub_path)

	statistics = dict()
	elapsed_time = int(elapsed_time)
	statistics['time'] = elapsed_time
	if ampl_solver.solve_result == 'solved':
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

	return statistics
