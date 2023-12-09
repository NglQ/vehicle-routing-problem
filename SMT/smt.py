import time
import signal

from pysmt.shortcuts import Symbol, Solver, And, GE, LE, Plus, Equals, Int, Store, Select, Minus, Times, ExactlyOne, Max, Implies, Or, LT, Min
from pysmt.typing import INT, ArrayType

from converter import convert
import bounds_generator as bds_gen
from _thread import interrupt_main
import threading as thr


def timeout_handler():
    interrupt_main()


def smt_model(instance_file: str, instance_number: str, solver: str, time_limit: int, sym_break: bool) -> dict:

    alarm = thr.Timer(time_limit, timeout_handler)
    alarm.start()
    intermediate_sol_found = False
    start_time = time.time()

    try:
        m, n, l, p, d = convert(instance_file)
        p += [0]

        N = n + 1

        x = Symbol("X", ArrayType(INT, ArrayType(INT, ArrayType(INT, INT))))
        y = Symbol("Y", ArrayType(INT, ArrayType(INT, INT)))
        u = Symbol("U", ArrayType(INT, INT))

        H = Symbol("H", ArrayType(INT, INT))
        H_max = Symbol("H_max", INT)

        with Solver(name=solver) as s:
            if solver == 'z3':
                # s.z3.set('timeout', 10000)
                pass

            for k in range(m):
                sum_distances = Int(0)
                for i in range(N):
                    for j in range(N):
                        sum_distances = Plus(sum_distances,
                                             Times(Select(Select(Select(x, Int(i)), Int(j)), Int(k)), Int(d[i][j])))
                H = Store(H, Int(k), sum_distances)

            H_max = Max([Select(H, Int(k)) for k in range(m)])

            # __0.0__ boolean x and y
            for i in range(N):
                for j in range(N):
                    for k in range(m):
                        s.add_assertion(Or(Equals(Select(Select(Select(x, Int(i)), Int(j)), Int(k)), Int(0)), Equals(Select(Select(Select(x, Int(i)), Int(j)), Int(k)), Int(1))))

            for i in range(N):
                for k in range(m):
                    s.add_assertion(Or(Equals(Select(Select(y, Int(i)), Int(k)), Int(0)), Equals(Select(Select(y, Int(i)), Int(k)), Int(1))))

            # __0__ self loops
            for i in range(N):
                for k in range(m):
                    s.add_assertion(Equals(Select(Select(Select(x, Int(i)), Int(i)), Int(k)), Int(0)))

            # __1__ y[i, k] = 1 for all i in N, k in M
            for i in range(n):
                vals = []
                for k in range(m):
                    vals.append(Select(Select(y, Int(i)), Int(k)))
                s.add_assertion(ExactlyOne([Equals(v, Int(1)) for v in vals]))

            # __2__ y[n, k] = 1 for all k in M
            for k in range(m):
                s.add_assertion(Equals(Select(Select(y, Int(n)), Int(k)), Int(1)))

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
                    s.add_assertion(Implies(Equals(y_val, Int(1)), ExactlyOne([Equals(v, Int(1)) for v in rws])))
                    s.add_assertion(Implies(Equals(y_val, Int(1)), ExactlyOne([Equals(v, Int(1)) for v in cls])))

            # __4__ sum(items) <= capacities
            for k in range(m):
                weights = [Symbol(f'w_{i}{k}', INT) for i in range(N)]
                for i in range(N):
                    s.add_assertion(Implies(Equals(Select(Select(y, Int(i)), Int(k)), Int(1)), Equals(weights[i], Int(p[i]))))
                    s.add_assertion(Implies(Equals(Select(Select(y, Int(i)), Int(k)), Int(0)), Equals(weights[i], Int(0))))
                s.add_assertion(LE(Plus(weights), Int(l[k])))

            # __5__ u[i] - u[j] + n * x[i, j, k] <= n - 1 for all i, j in N, k in M
            for i in range(n):
                for j in range(n):
                    for k in range(m):
                        x_elem = Select(Select(Select(x, Int(i)), Int(j)), Int(k))
                        s.add_assertion(Implies(Equals(x_elem, Int(0)), LE(Minus(Select(u, Int(i)), Select(u, Int(j))), Int(n-1))))
                        s.add_assertion(Implies(Equals(x_elem, Int(1)), LE(Minus(Select(u, Int(i)), Select(u, Int(j))), Int(-1))))

            # __6__ lower bound
            lw_bnd = bds_gen.generate_lowerbound(n, d)
            s.add_assertion(GE(H_max, Int(lw_bnd)))

            # __7__ upper bound
            up_bnd = bds_gen.generate_upperbound(n, m, d)
            s.add_assertion(LE(H_max, Int(int(up_bnd))))

            # __8__ symmetry breaking constraint
            if sym_break:
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
            s.push()
            optimal_solution = False
            res = s.solve()
            intermediate_sol_found = True

            print(s.check_sat())
            while s.check_sat():
                sol = s.get_model()
                H_current = s.get_value(H_max)
                s.add_assertion(LT(H_max, H_current))
                s.push()
                if s.check_sat():
                    s.solve()
                # final_sol = s.get_model() if s.check_sat() else sol
            optimal_solution = True
    except:
        alarm.cancel()
        if not intermediate_sol_found:
            print(f'No solution found for instance {instance_number} with solver {solver} with sym_break = {sym_break}.')
            return {'time': time_limit, 'optimal': False, 'obj': 0, 'sol': []}

    alarm.cancel()

    elapsed_time = time.time() - start_time
    print('elapsed_time: '+str(elapsed_time))

    objective = sol.get_value(H_max)


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

    return {'time': elapsed_time, 'optimal': optimal_solution, 'obj': objective, 'sol': full_path}


if __name__ == '__main__':
    print(smt_model('../instances/inst03.dat', '03', 'z3', 300, False))
