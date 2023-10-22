from minizinc import Instance, Model, Solver
import numpy as np
import json

from converter import convert, generate_mip_dzn
def mip_model(path_to_instance='./instances/inst01.dat'):
	datafile = 'mip_test.dzn'

	m, n, l, p, d = convert(path_to_instance)
	generate_mip_dzn(datafile, m, n, l, p, d)

	# quit(0)

	model = Model('mip.mzn')
	model.add_file(datafile)

	gecode = Solver.lookup('chuffed')

	instance = Instance(gecode, model)
	# instance['n'] = 4

	result = instance.solve()

	sol = [[] for _ in range(m)]
	x = np.array(result['x'])

	for courier in range(m):
    	# x of the single courier
		xc = x[:, :, courier]

		start_candidates = xc[-1, :]

		node = np.where(start_candidates == 1)[0][0] + 1
		sol[courier].append(int(node))
		
		while node != n + 1:
			node = np.where(xc[node - 1] == 1)[0][0] + 1
			sol[courier].append(int(node))

		sol[courier].pop()

	statistics = {}
	statistics['time'] = int(result.statistics['time'].seconds)
	statistics['optimal'] = statistics['time'] < 300
	statistics['obj'] = result.objective
	statistics['sol'] = sol

	stats = {'chuffed': statistics}

	json.dump(stats, open('mip_test.json', 'w'))
