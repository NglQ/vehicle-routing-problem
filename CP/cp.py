import os
import time
import datetime

import numpy as np
import minizinc
from minizinc import Instance, Model, Solver, Status

from converter import convert
from bounds_generator import generate_lowerbound, generate_upperbound

print("Minizinc Python API version:", minizinc.__version__, '\n')
module_path = os.path.dirname(os.path.realpath(__file__))


def cp_model(instance_file: str, instance_number: str, solver: str, time_limit: int, sym_break: bool) -> dict:
    # TODO: Check what happens to the `result` variable when no intermediate solutions is found

    # Calculate lower and upper bounds
    m, n, l, p, d = convert(os.path.join(module_path, f'./../instances/inst{instance_number}.dat'))
    lower_bound = generate_lowerbound(n, d)
    upper_bound = generate_upperbound(n, m, d)

    model = Model(os.path.join(module_path, 'cp.mzn'))
    model.add_file(instance_file, parse_data=True)
    model.add_string(
        f"""
        constraint objective >= {lower_bound};
        constraint objective <= {upper_bound};
        """
    )
    if sym_break:
        model.add_string(
            """
            constraint forall(i in 1..M, j in 1..M where (i < j /\ max(u[i], u[j]) <= min(l[j], l[i])))(lex_lesseq(row(es, i), row(es, j)));
            """
        )

    solver_ins = Solver.lookup(solver)
    instance = Instance(solver_ins, model)

    n = model['N']

    time_limit_mzn = datetime.timedelta(seconds=time_limit)
    start_time = time.time()
    result = instance.solve(timeout=time_limit_mzn, intermediate_solutions=True)
    elapsed_time = time.time() - start_time

    # Get the result in the proper way based on `intermediate_solutions` parameter
    try:
        # intermediate_solutions = True
        solution = result[-1]
    except TypeError:
        # intermediate_solutions = False
        solution = result.solution

    es = np.array(solution.es)

    # Same indexes calculated in the convert.py module
    indexes = [(i, j) for i in [n - 1] + list(range(1, n - 1)) for j in range(1, n + 1)
               if i != j and j != n - 1 and (i, j) != (n - 1, n)]
    idxs = np.array(indexes)
    sol = [[] for _ in range(es.shape[0])]

    # Build path covered by couriers
    for courier in range(es.shape[0]):
        e = es[courier]
        start = e[:n]
        start = np.where(start == True)[0][0]

        node = idxs[start][1]
        sol[courier].append(int(node))

        while node != n:
            candidates = np.where(idxs[:, 0] == node)[0]
            edge_idx = np.where(e[candidates] == True)[0][0] + candidates[0]
            node = idxs[edge_idx][1]
            sol[courier].append(int(node))

        sol[courier].pop()

    statistics = dict()
    elapsed_time = int(elapsed_time)
    if result.status == Status.OPTIMAL_SOLUTION:
        if elapsed_time >= time_limit:
            statistics['time'] = time_limit - 1
        else:
            statistics['time'] = elapsed_time
        statistics['optimal'] = True
    else:
        statistics['time'] = time_limit
        statistics['optimal'] = False

    statistics['obj'] = solution.objective
    statistics['sol'] = sol

    return statistics
