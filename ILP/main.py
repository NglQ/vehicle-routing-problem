from minizinc import Instance, Model, Solver
import numpy as np

model = Model('ilp.mzn')
model.add_file('ilp.dzn')

gecode = Solver.lookup("gecode")

instance = Instance(gecode, model)
# instance["n"] = 4

result = instance.solve()
x = np.array(result["x"])
y = np.array(result["y"])
u = np.array(result["u"])
print(result)
