from minizinc import Instance, Model, Solver
import numpy as np

from converter import convert, generate_dzn

m, n, l, p, d = convert('inst01.txt')
generate_dzn('cp_test.dzn', m, n, l, p, d)

quit(0)

# model = Model('cp.mzn')
# model.add_file('cp.dzn')
#
# gecode = Solver.lookup("gecode")
#
# instance = Instance(gecode, model)
# # instance["n"] = 4
#
# result = instance.solve()
# x = np.array(result["x"])
# y = np.array(result["y"])
# u = np.array(result["u"])
# print(result)
