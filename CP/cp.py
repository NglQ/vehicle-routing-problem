from minizinc import Instance, Model, Solver
import numpy as np
import json
import datetime

from converter import convert, generate_cp_dzn

def cp_model(path_to_instance='./instances/inst02.dat'):
	datafile = 'cp_test.dzn'
	
	time_limit = datetime.timedelta(seconds=60)#(seconds=5*60)
	
	m, n, l, p, d = convert(path_to_instance)
	indexes = generate_cp_dzn(datafile, m, n, l, p, d)

	# quit(0)

	model = Model('cp.mzn')
	model.add_file(datafile)

	gecode = Solver.lookup('gecode')

	instance = Instance(gecode, model)
	# instance["n"] = 4

	result = instance.solve(timeout=time_limit, intermediate_solutions=True)
	#result = instance.solve()#timeout=time_limit, intermediate_solutions=True)
	
	#print(result)
	print(result.status)
	print(result[-1].K)
	print(result[-1].u)
	#print(result['K'])
	#print(result['u'])

	#es = np.array(result['es'])
	es = np.array(result[-1].es)
	print(es)
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
	statistics['obj'] = max(result[-1].K)
	statistics['sol'] = sol

	stats = {'gecode': statistics}
	print(stats)

	json.dump(stats, open('cp_test.json', 'w'))
