import time

from pysmt.shortcuts import Symbol, Solver, And, GE, LE, Plus, Equals, Int, Store, Select, Minus, Times, ExactlyOne, Max, Implies, Or, LT, Min
from pysmt.typing import INT, ArrayType

from converter import convert
import bounds_generator as bds_gen

from timeout import stopped, timeout_handler, check_timeout


def smt_model(instance_file: str, instance_number: str, solver: str, time_limit: int, sym_break: bool) -> dict:

    stopped_key = instance_number + '_smt_' + solver + '_' + ('with' if sym_break else 'without') + '_symbreak'
    intermediate_sol_found = False
    start_time = time.time()
    stopped[stopped_key] = (False, start_time)

    try:
        m, n, l, p, d = convert(instance_file)
        p += [0]

        N = n + 1

        x = Symbol('X', ArrayType(INT, ArrayType(INT, ArrayType(INT, INT))))
        y = Symbol('Y', ArrayType(INT, ArrayType(INT, INT)))
        u = Symbol('U', ArrayType(INT, INT))

        H = Symbol('H', ArrayType(INT, INT))
        H_max = Symbol('H_max', INT)

        with Solver(name=solver) as s:
            for k in range(m):
                sum_distances = Int(0)
                for i in range(N):
                    for j in range(N):
                        sum_distances = Plus(sum_distances,
                                             Times(Select(Select(Select(x, Int(i)), Int(j)), Int(k)), Int(d[i][j])))
                        if check_timeout(time_limit):
                            return {'time': time_limit, 'optimal': False, 'obj': 0, 'sol': []}
                H = Store(H, Int(k), sum_distances)

            H_max = Max([Select(H, Int(k)) for k in range(m)])

            print('Building model part 0.0...')
            # __0.0__ boolean x and y
            for i in range(N):
                for j in range(N):
                    for k in range(m):
                        s.add_assertion(Or(Equals(Select(Select(Select(x, Int(i)), Int(j)), Int(k)), Int(0)), Equals(Select(Select(Select(x, Int(i)), Int(j)), Int(k)), Int(1))))
                        if check_timeout(time_limit):
                            return {'time': time_limit, 'optimal': False, 'obj': 0, 'sol': []}

            for i in range(N):
                for k in range(m):
                    s.add_assertion(Or(Equals(Select(Select(y, Int(i)), Int(k)), Int(0)), Equals(Select(Select(y, Int(i)), Int(k)), Int(1))))

            print('Building model part 0...')
            # __0__ self loops
            for i in range(N):
                for k in range(m):
                    s.add_assertion(Equals(Select(Select(Select(x, Int(i)), Int(i)), Int(k)), Int(0)))

            print('Building model part 1...')
            # __1__ y[i, k] = 1 for all i in N, k in M
            for i in range(n):
                vals = []
                for k in range(m):
                    vals.append(Select(Select(y, Int(i)), Int(k)))
                s.add_assertion(ExactlyOne([Equals(v, Int(1)) for v in vals]))

            print('Building model part 2...')
            # __2__ y[n, k] = 1 for all k in M
            for k in range(m):
                s.add_assertion(Equals(Select(Select(y, Int(n)), Int(k)), Int(1)))
                if check_timeout(time_limit):
                    return {'time': time_limit, 'optimal': False, 'obj': 0, 'sol': []}

            print('Building model part 3...')
            # __3__ one entering edge and one exiting edge admissible
            for k in range(m):
                for i in range(N):
                    rws = []
                    cls = []
                    y_val = Select(Select(y, Int(i)), Int(k))
                    for j in range(N):
                        x_val_r = Select(Select(Select(x, Int(i)), Int(j)), Int(k))
                        x_val_c = Select(Select(Select(x, Int(j)), Int(i)), Int(k))
                        rws.append(x_val_r)
                        cls.append(x_val_c)
                        s.add_assertion(Implies(Equals(y_val, Int(0)), And(Equals(x_val_r, Int(0)), Equals(x_val_c, Int(0)))))
                        if check_timeout(time_limit):
                            return {'time': time_limit, 'optimal': False, 'obj': 0, 'sol': []}
                    s.add_assertion(Implies(Equals(y_val, Int(1)), ExactlyOne([Equals(v, Int(1)) for v in rws])))
                    if check_timeout(time_limit):
                        return {'time': time_limit, 'optimal': False, 'obj': 0, 'sol': []}
                    s.add_assertion(Implies(Equals(y_val, Int(1)), ExactlyOne([Equals(v, Int(1)) for v in cls])))
                    if check_timeout(time_limit):
                        return {'time': time_limit, 'optimal': False, 'obj': 0, 'sol': []}

            print('Building model part 4...')
            # __4__ sum(items) <= capacities
            for k in range(m):
                weights = [Symbol(f'w_{i}{k}', INT) for i in range(N)]
                for i in range(N):
                    s.add_assertion(Implies(Equals(Select(Select(y, Int(i)), Int(k)), Int(1)), Equals(weights[i], Int(p[i]))))
                    s.add_assertion(Implies(Equals(Select(Select(y, Int(i)), Int(k)), Int(0)), Equals(weights[i], Int(0))))
                    if check_timeout(time_limit):
                        return {'time': time_limit, 'optimal': False, 'obj': 0, 'sol': []}
                s.add_assertion(LE(Plus(weights), Int(l[k])))

            print('Building model part 5...')
            # __5__ u[i] - u[j] + n * x[i, j, k] <= n - 1 for all i, j in N, k in M
            for i in range(n):
                for j in range(n):
                    for k in range(m):
                        x_elem = Select(Select(Select(x, Int(i)), Int(j)), Int(k))
                        s.add_assertion(Implies(Equals(x_elem, Int(0)), LE(Minus(Select(u, Int(i)), Select(u, Int(j))), Int(n-1))))
                        s.add_assertion(Implies(Equals(x_elem, Int(1)), LE(Minus(Select(u, Int(i)), Select(u, Int(j))), Int(-1))))
                        if check_timeout(time_limit):
                            return {'time': time_limit, 'optimal': False, 'obj': 0, 'sol': []}

            print('Building model part 6...')
            # __6__ lower bound
            lw_bnd = bds_gen.generate_lowerbound(n, d)
            s.add_assertion(GE(H_max, Int(lw_bnd)))
            if check_timeout(time_limit):
                return {'time': time_limit, 'optimal': False, 'obj': 0, 'sol': []}

            print('Building model part 7...')
            # __7__ upper bound
            up_bnd = bds_gen.generate_upperbound(n, m, d)
            s.add_assertion(LE(H_max, Int(up_bnd)))

            # __8__ symmetry breaking constraint
            if sym_break:
                print('Building model part 8...')
                for i in range(m):
                    for j in range(m):
                        if i < j:
                            pass
                            sum_i = Plus(
                                [Times(Select(Select(y, Int(line)), Int(i)), Int(p[line])) for line in range(n)])
                            sum_j = Plus(
                                [Times(Select(Select(y, Int(line)), Int(j)), Int(p[line])) for line in range(n)])
                            max_sum = Max(sum_i, sum_j)
                            for t in range(n):
                                s.add_assertion(Implies(And(max_sum <= Min(Int(l[i]), Int(l[j])),
                                                            Equals(Select(Select(Select(x, Int(n)), Int(t)), Int(i)),
                                                                   Int(1))), And([Equals(
                                    Select(Select(Select(x, Int(n)), Int(o)), Int(i)), Int(0)) for o in range(t)])))
                                if check_timeout(time_limit):
                                    return {'time': time_limit, 'optimal': False, 'obj': 0, 'sol': []}

            print('Pushing assertions...')
            s.push()

            if check_timeout(time_limit):
                return {'time': time_limit, 'optimal': False, 'obj': 0, 'sol': []}

            print('Model built. Starting solver...')

            optimal_solution = False
            res = s.solve()

            if check_timeout(time_limit):
                return {'time': time_limit, 'optimal': False, 'obj': 0, 'sol': []}

            while s.check_sat():
                sol = s.get_model()
                if time.time() - start_time <= time_limit:
                    before_time_limit_sol = sol
                intermediate_sol_found = True
                if check_timeout(time_limit):
                    raise Exception

                H_current = s.get_value(H_max)
                s.add_assertion(LT(H_max, H_current))
                s.push()
                if check_timeout(time_limit):
                    raise Exception
                if s.check_sat():
                    s.solve()
                    if check_timeout(time_limit):
                        raise Exception
            optimal_solution = True
            print('Optimal solution found.')
    except Exception as e:
        # Print with traceback
        print(e)
        stopped[stopped_key] = (True, start_time)
        print('Timeout reached.')
        if not intermediate_sol_found:
            print(f'No solution found for instance {instance_number} with solver {solver} with sym_break = {sym_break}.')
            return {'time': time_limit, 'optimal': False, 'obj': 0, 'sol': []}

    elapsed_time = time.time() - start_time
    if stopped[stopped_key][0]:
        sol = before_time_limit_sol

    objective = sol.get_value(H_max)._content.payload

    x_dict = dict()
    for i in range(N):
        for j in range(N):
            for k in range(m):
                x_dict[(i, j, k)] = int(str(sol.get_value(Select(Select(Select(x, Int(i)), Int(j)), Int(k)))))

    full_path = []
    for i in range(m):
        path = [k for k, v in x_dict.items() if v == 1 and k[2] == i]
        start = n
        sub_path = []
        while len(sub_path) < len(path) - 1:
            next_step = list(filter(lambda e: e[0] == start, path))[0]
            start = next_step[1]
            sub_path.append(start+1)
        full_path.append(sub_path)

    statistics = dict()
    elapsed_time = int(elapsed_time)
    if optimal_solution:
        if elapsed_time >= time_limit:
            statistics['time'] = time_limit - 1
        else:
            statistics['time'] = elapsed_time
        statistics['optimal'] = True
    else:
        statistics['time'] = time_limit
        statistics['optimal'] = False

    statistics['obj'] = objective
    statistics['sol'] = full_path

    stopped[stopped_key] = (True, start_time)
    return statistics
