import minizinc
from minizinc import Instance, Model, Solver
import numpy as np
import json
import datetime
import os

print(minizinc.__version__)


def cp_model():

	# TODO
	#  Hard time to use time limit with chuffed solver:
	# 		minizinc.error.MiniZincError:
	# 		WARNING: the --time-out flag has recently been changed.
	# 		The time-out is now provided in milliseconds instead of seconds
	#  Check the cost function
	#  add a model without symmetry breaking constraints

	path_to_cp_instances = './CP/instances'
	solvers = ['chuffed']  # , 'chuffed']  # 'gecode', 'findmus'
	# instance_files = os.listdir(path_to_cp_instances)
	instance_files = list(filter(lambda x: x == 'cp_inst10.dzn' or x == 'cp_inst01.dzn', os.listdir(path_to_cp_instances)))

	for i, ins_file in enumerate(instance_files):
		stats = dict()
		for solver in solvers:
			# time_limit = datetime.timedelta(seconds=300)
			time_limit = datetime.timedelta(milliseconds=300*1000)
			model = Model('./CP/cp.mzn')
			model.add_file(f'{path_to_cp_instances}/{ins_file[:ins_file.find(".")]}.dzn', parse_data=True)
			solver_ins = Solver.lookup(solver)
			instance = Instance(solver_ins, model)

			n = model['N']

			result = instance.solve(timeout=time_limit, intermediate_solutions=True)

			# print('result: ', result)
			# print(result.status)
			# print(result[-1].K)
			# print(result[-1].u)

			es = np.array(result[-1].es)
			# print(es)

			indexes = [(i, j) for i in [n-1] + list(range(1, n-1)) for j in range(1, n+1) if i != j and j != n-1 and (i, j) != (n-1, n)]
			# print(indexes, '\n\n')

			idxs = np.array(indexes)  # TODO check if that's the case
			# print(idxs, '\n\n')

			sol = [[] for _ in range(es.shape[0])]

			for courier in range(es.shape[0]):
				e = es[courier]
				start = e[:n]
				start = np.where(start == True)[0][0]

				node = idxs[start][1]
				sol[courier].append(int(node))

				while node != n:
					# print("node: ", node)
					candidates = np.where(idxs[:, 0] == node)[0]
					edge_idx = np.where(e[candidates] == True)[0][0] + candidates[0]
					node = idxs[edge_idx][1]
					sol[courier].append(int(node))

				sol[courier].pop()

			statistics = dict()
			statistics['time'] = int(result.statistics['time'].seconds)
			statistics['optimal'] = statistics['time'] < 300
			statistics['obj'] = max(result[-1].K)
			statistics['sol'] = sol

			print(statistics)

			stats[solver] = statistics

		print(stats)

		json_name = ins_file[ins_file.find('.') - 2:ins_file.find('.')]
		json_name = json_name if json_name[0] != '0' else json_name[-1]

		json.dump(stats, open(f'./res/CP/{json_name}.json', 'w+' if i == 0 else 'a+'))
