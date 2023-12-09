import time
import signal
from _thread import interrupt_main
import threading as thr

import numpy as np
from z3 import *

from converter import convert
from bounds_generator import generate_lowerbound, generate_upperbound

module_path = os.path.dirname(os.path.realpath(__file__))


def at_least_one(bool_vars):
    return Or(bool_vars)


def at_least_one_seq(bool_vars):
    return at_least_one(bool_vars)


def at_most_one_seq(bool_vars, name):
    constraints = []
    n = len(bool_vars)
    s = [Bool(f"s_{name}_{i}") for i in range(n - 1)]
    constraints.append(Or(Not(bool_vars[0]), s[0]))
    constraints.append(Or(Not(bool_vars[n - 1]), Not(s[n - 2])))
    for i in range(1, n - 1):
        constraints.append(Or(Not(bool_vars[i]), s[i]))
        constraints.append(Or(Not(bool_vars[i]), Not(s[i - 1])))
        constraints.append(Or(Not(s[i - 1]), s[i]))
    return And(constraints)


def exactly_one_seq(bool_vars, name):
    return And(at_least_one_seq(bool_vars), at_most_one_seq(bool_vars, name))


def at_least_k_seq(bool_vars, k, name):
    return at_most_k_seq([Not(var) for var in bool_vars], len(bool_vars) - k, name)


def at_most_k_seq(bool_vars, k, name):
    constraints = []
    n = len(bool_vars)
    s = [[Bool(f"s_{name}_{i}_{j}") for j in range(k)] for i in range(n - 1)]
    constraints.append(Or(Not(bool_vars[0]), s[0][0]))
    constraints += [Not(s[0][j]) for j in range(1, k)]
    for i in range(1, n - 1):
        constraints.append(Or(Not(bool_vars[i]), s[i][0]))
        constraints.append(Or(Not(s[i - 1][0]), s[i][0]))
        constraints.append(Or(Not(bool_vars[i]), Not(s[i - 1][k - 1])))
        for j in range(1, k):
            constraints.append(Or(Not(bool_vars[i]), Not(s[i - 1][j - 1]), s[i][j]))
            constraints.append(Or(Not(s[i - 1][j]), s[i][j]))
    constraints.append(Or(Not(bool_vars[n - 1]), Not(s[n - 2][k - 1])))
    return And(constraints)


def exactly_k_seq(bool_vars, k, name):
    return And(at_most_k_seq(bool_vars, k, name), at_least_k_seq(bool_vars, k, name))

def bit_bound(upper_bound, n, l):
    max_value = max(upper_bound, n + 1, max(l))
    number_of_bits = math.ceil(math.log2(max_value))
    return number_of_bits

def toBinary(num, length):
    num_bin = bin(num).split("b")[-1]
    num_bin = "0" * (length - len(num_bin)) + num_bin
    return [bool(int(num_bin[i])) for i in range(len(num_bin))]


def toInt(num, length):
    num_int = 0
    for i in range(length):
        if num[i]:
            num_int += 2 ** (length - 1 - i)
    return num_int

def bin_add(name, d, a, b, length):  # d is the sum of a and b
    constraints = []
    C = [Bool(f'C_{name}_{i}') for i in range(length + 1)]

    constraints.append(And(Not(C[0]), Not(C[length])))
    for i in range(length):
        constraints.append(C[i] == Or(And(a[i], b[i]), And(a[i], C[i + 1]), And(b[i], C[i + 1])))

    for i in range(length):
        constraints.append(
            d[i] == Or(And(a[i], Not(b[i]), Not(C[i + 1])), And(b[i], Not(a[i]), Not(C[i + 1])), And(C[i + 1],
                                                                                                     Not(a[i]),
                                                                                                     Not(b[i])),
                       And(a[i], b[i], C[i + 1])))

    return And(constraints)

def bin_multiadd(name, d, *args, length): # d is the sum of the args
    constraints = []
    T = [[Bool(f'T_{name}_{i}_{j}') for j in range(length)] for i in range(len(args))]

    for i in range(len(args) - 1):
        constraints.append(bin_add(f'{name}_{i}', T[i + 1][:], T[i][:], args[i + 1][:], length=length))

    for i in range(length):
        constraints.append(T[0][i] == args[0][i])
        constraints.append(T[len(args) - 1][i] == d[i])
    return And(constraints)


def greater_than(name, a, b, length):  # a is greater than b
    constraints = []
    found_diff = [Bool(f'found_diff_{name}_{i}') for i in range(length)]
    for i in range(length):
        constraints.append(Or(And(a[i], Not(b[i])), And(Not(a[i]), b[i])) == found_diff[i])
        constraints.append(
            Implies(And([Not(found_diff[j]) for j in range(i)]), Or(Not(found_diff[i]), And(a[i], Not(b[i])))))
    return And(constraints)


def strictly_greater_than(name, a, b, length):  # a is strictly greater than b
    constraints = []
    constraints.append(greater_than(name, a, b, length=length))
    constraints.append(Or([And(a[i], Not(b[i])) for i in range(length)]))
    return And(constraints)

def max_of(name, H_max, H, length):  # H_max is the maximum of H
    constraints = []
    constraints.append(
        Or([And([H_max[j] == H[i][j] for j in range(length)]) for i in range(len(H))]))  # v is an element in x)
    for i in range(len(H)):
        constraints.append(greater_than(f'h_{name}_{i}', H_max, H[i], length=length))  # and it's the greatest
    return And(constraints)


def timeout_handler():
    interrupt_main()


def sat_model(instance_file: str, instance_number: str, solver: str, time_limit: int, sym_break: bool) -> dict:

    alarm = thr.Timer(time_limit, timeout_handler)
    alarm.start()
    intermediate_sol_found = False
    stopped = False
    start_time = time.time()

    try:
        # Compute lower and upper bounds
        m, n, l, w, D = convert(os.path.join(module_path, f'./../instances/inst{instance_number}.dat'))
        N = toBinary(n + 1, length=length)
        lower_bound = generate_lowerbound(n, D)
        upper_bound = generate_upperbound(n, m, D)

        trial_number = 0
        length = bit_bound(upper_bound, m, l)

        # VARIABLES

        X = [[[Bool(f"X_{i}_{j}_{k}") for k in range(m)] for j in range(n + 1)] for i in range(n + 1)]
        Y = [[Bool(f"Y_{i}_{k}") for k in range(m)] for i in range(n + 1)]
        U = [[Bool(f"U_{i}_{j}") for j in range(length)] for i in range(n + 1)]
        H_max = [Bool(f'H_max_{i}') for i in range(length)]

        # SOLVER

        s = Solver()

        # 1) Each courier cannot go from one location to the same location: X[i,i,k] == 0 for every i, k
        for i in range(n + 1):
            for k in range(m):
                s.add(Not(X[i][i][k]))

        # 2) The same vehicle enters and leaves a given customer
        for i in range(n + 1):
            for k in range(m):
                # defining the sum
                X_enter = []
                X_exit = []
                for j in range(n + 1):
                    X_enter += [X[i][j][k]]
                    X_exit += [X[j][i][k]]

                s.add(Implies(Y[i][k], And(exactly_one_seq(X_enter, f'n_{i}{k}'))))
                s.add(Implies(Y[i][k], And(exactly_one_seq(X_exit, f'o_{i}{k}'))))
                s.add(Implies(Not(Y[i][k]), And([Not(i) for i in X_enter])))
                s.add(Implies(Not(Y[i][k]), And([Not(i) for i in X_exit])))

        # 3) Each customer is visited exactly once: for every i (except depot), the sum over k of Y must be 1
        for i in range(n):
            Y_sum = []
            for k in range(m):
                Y_sum += [Y[i][k]]
            s.add(exactly_one_seq(Y_sum, f'l_{i}'))

        # 4) All the vehicles leave the depot: Y[n][k] is True for every k
        s.add(And([Y[n][k] for k in range(m)]))

        # 5) Every entry of the U vector has a value between 0 and N-1
        for i in range(n + 1):
            s.add(greater_than(f'a_{i}', U[i][:], toBinary(0, length=length), length=length))
            s.add(greater_than(f'b_{i}', toBinary(n, length=length), U[i][:], length=length))

        # 6) Anti-subtour constraint
        for i in range(n):
            var = [Bool(f'var2_{i}_{l}') for l in range(length)]
            s.add(bin_add(f'c_{i}', var, U[i][:], toBinary(1, length=length), length=length))
            for j in range(n):
                if i != j:
                    for k in range(m):
                        s.add(Implies(X[i][j][k], greater_than(f'd_{i}{j}', U[j][:], var, length=length)))

        # 7) Maximum load constraint
        loads = []
        for k in range(m):
            sum_w = [Bool(f'sum_w_{k}_{i}') for i in range(length)]
            sum_w_list = []
            for i in range(n + 1):
                sum_w_list_i = [Bool(f'sum_w_list_i_{k}{i}_{l}') for l in range(length)]
                s.add(Implies(Y[i][k], And([sum_w_list_i[l] == toBinary(w[i], length=length)[l] for l in range(length)])))
                s.add(Implies(Not(Y[i][k]), And([Not(sum_w_list_i[l]) for l in range(length)])))
                sum_w_list.append(sum_w_list_i)
            s.add(bin_multiadd(f'e_{k}', sum_w, *sum_w_list, length=length))
            s.add(greater_than(f'f_{k}', toBinary(l[k], length=length), sum_w, length=length))
            loads.append(sum_w)

        # 8) H constraint: H is the vector of the distance covered by each courier
        H = [[Bool(f'H_{i}_{k}') for i in range(length)] for k in range(m)]
        for k in range(m):
            H_list = []
            for i in range(n + 1):
                for j in range(n + 1):
                    H_list_i = [Bool(f'H_list_i_{k}{i}{j}_{l}') for l in range(length)]
                    s.add(Implies(X[i][j][k],
                                  And([H_list_i[l] == toBinary(D[i][j], length=length)[l] for l in range(length)])))
                    s.add(Implies(Not(X[i][j][k]), And([Not(H_list_i[l]) for l in range(length)])))
                    H_list.append(H_list_i)
            s.add(bin_multiadd(f'g_{k}', H[k][:], *H_list, length=length))

        # 9) H_max constraint: H_max is the maximum value of H.
        s.add(max_of('k', H_max, H, length=length))

        # 10) Bound constraints
        s.add(greater_than('i', H_max, toBinary(lower_bound, length=length), length=length))
        s.add(greater_than('j', toBinary(upper_bound, length=length), H_max, length=length))

        # 11) symmetry breaking constraint (OPTIONAL)
        if sym_break:
            for i in range(m):
                for j in range(m):
                    if i < j:
                        max_value = [Bool(f'max_value_{i}_{j}_{k}') for k in range(length)]
                        s.add(max_of(f'p_{i}_{j}', max_value, [loads[i], loads[j]], length=length))
                        for t in range(n):
                            s.add(Implies(
                                And(greater_than(f'q_{i}_{j}_{t}', toBinary(min(l[i], l[j]), length=length), max_value,
                                                 length=length), X[n][t][i]), And([Not(X[n][o][j]) for o in range(t)])))

        print('Model built. Starting solver...')

        optimal_solution = False
        while s.check() == sat:
            sol = s.model()
            intermediate_sol_found = True
            if time.time() - start_time <= time_limit:
                before_time_limit_sol = sol

            H_current = [sol.evaluate(H_max[j]) for j in range(length)]
            s.add(strictly_greater_than(f'l_{trial_number}', H_current, H_max, length=length))
            trial_number += 1
            if s.check() == sat:
                sol = s.model()
                if time.time() - start_time <= time_limit:
                    before_time_limit_sol = sol
            else:
                optimal_solution = True
                print('Optimal solution found.')
    except:
        alarm.cancel()
        stopped = True
        print('Timeout reached.')
        if not intermediate_sol_found:
            print(f'No solution found for instance {instance_number} with solver {solver} with sym_break = {sym_break}.')
            return {'time': time_limit, 'optimal': False, 'obj': 0, 'sol': []}

    alarm.cancel()
    elapsed_time = time.time() - start_time
    if stopped:
        sol = before_time_limit_sol

    x_dict = dict()
    for i in range(n+1):
        for j in range(n+1):
            for k in range(m):
                x_dict[(i, j, k)] = int(bool(sol.evaluate(X[i][j][k])))

    full_path = []
    for i in range(m):
        path = [k for k, v in x_dict.items() if v == 1 and k[2] == i]
        start = n
        sub_path = []
        while len(sub_path) < len(path) - 1:
            next_step = list(filter(lambda e: e[0] == start, path))[0]
            start = next_step[1]
            sub_path.append(start + 1)
        full_path.append(sub_path)

    objective = toInt([sol.evaluate(H_max[i]) for i in range(length)], length=length)

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

    return statistics
