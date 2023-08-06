from minizinc import Instance, Model, Solver
import numpy as np

model = Model('cp.mzn')
model.add_file('cp.dzn')

gecode = Solver.lookup("gecode")

instance = Instance(gecode, model)
#instance["n"] = 4

result = instance.solve()
x = np.array(result["x"])
y = np.array(result["y"])
u = np.array(result["u"])
print(result)
