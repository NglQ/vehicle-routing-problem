from minizinc import Instance, Model, Solver
import numpy as np
import json

from converter import convert, generate_cp_dzn

def cp_model(path_to_instance='./instances/inst01.dat'):
	datafile = 'cp_test.dzn'

	m, n, l, p, d = convert(path_to_instance)
	indexes = generate_cp_dzn(datafile, m, n, l, p, d)

	# quit(0)

	model = Model('cp.mzn')
	model.add_file(datafile)

	gecode = Solver.lookup('gecode')

	instance = Instance(gecode, model)
	# instance["n"] = 4

	result = instance.solve()
	print(result['K'])
	print(result['u'])

	es = np.array(result['es'])
	idxs = np.array(indexes)
	sol = [[] for _ in range(es.shape[0])]

	for courier in range(es.shape[0]):
		e = es[courier]
		start = e[:n]
		start = np.where(start == True)[0][0]

		node = idxs[start][1]
		sol[courier].append(int(node))

		while node != n + 2:
			candidates = np.where(idxs[:, 0] == node)[0]
			edge_idx = np.where(e[candidates] == True)[0][0] + candidates[0]
			node = idxs[edge_idx][1]
			sol[courier].append(int(node))

		sol[courier].pop()

	statistics = {}
	statistics['time'] = int(result.statistics['time'].seconds)
	statistics['optimal'] = statistics['time'] < 300
	statistics['obj'] = max(result['K'])
	statistics['sol'] = sol

	stats = {'gecode': statistics}

	json.dump(stats, open('cp_test.json', 'w'))
