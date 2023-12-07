from z3 import *
import networkx as nx
import numpy as np
import math
from converter import convert


def at_least_one(bool_vars):
    return Or(bool_vars)


def at_least_one_seq(bool_vars):
    return at_least_one(bool_vars)


def at_most_one_seq(bool_vars, name):
    constraints = []
    n = len(bool_vars)
    s = [Bool(f"s_{name}_{i}") for i in range(n - 1)]
    constraints.append(Or(Not(bool_vars[0]), s[0]))
    constraints.append(Or(Not(bool_vars[n-1]), Not(s[n-2])))
    for i in range(1, n - 1):
        constraints.append(Or(Not(bool_vars[i]), s[i]))
        constraints.append(Or(Not(bool_vars[i]), Not(s[i-1])))
        constraints.append(Or(Not(s[i-1]), s[i]))
    return And(constraints)


def exactly_one_seq(bool_vars, name):
    return And(at_least_one_seq(bool_vars), at_most_one_seq(bool_vars, name))


def at_least_k_seq(bool_vars, k, name):
    return at_most_k_seq([Not(var) for var in bool_vars], len(bool_vars)-k, name)


def at_most_k_seq(bool_vars, k, name):
    constraints = []
    n = len(bool_vars)
    s = [[Bool(f"s_{name}_{i}_{j}") for j in range(k)] for i in range(n - 1)]
    constraints.append(Or(Not(bool_vars[0]), s[0][0]))
    constraints += [Not(s[0][j]) for j in range(1, k)]
    for i in range(1, n-1):
        constraints.append(Or(Not(bool_vars[i]), s[i][0]))
        constraints.append(Or(Not(s[i-1][0]), s[i][0]))
        constraints.append(Or(Not(bool_vars[i]), Not(s[i-1][k-1])))
        for j in range(1, k):
            constraints.append(Or(Not(bool_vars[i]), Not(s[i-1][j-1]), s[i][j]))
            constraints.append(Or(Not(s[i-1][j]), s[i][j]))
    constraints.append(Or(Not(bool_vars[n-1]), Not(s[n-2][k-1])))
    return And(constraints)


def exactly_k_seq(bool_vars, k, name):
    return And(at_most_k_seq(bool_vars, k, name), at_least_k_seq(bool_vars, k, name))


# binary addition in SAT. a and b are boolean vectors of length 16. s is the solver.
def add1(name, d, a, b, length): # d is the sum of the args
    constraints = []
    #global C
    # carry matrix
    C = [Bool(f'C_{name}_{i}') for i in range(length+1)]

    constraints.append(And(Not(C[0]), Not(C[length])))
    for i in range(length):
        constraints.append(C[i] == Or(And(a[i], b[i]), And(a[i], C[i+1]), And(b[i], C[i+1])))

    for i in range(length):
        #constraints.append((a[i] == b[i]) == (C[i] == d[i]))
        constraints.append(d[i] == Or(And(a[i], Not(b[i]), Not(C[i+1])), And(b[i], Not(a[i]), Not(C[i+1])), And(C[i+1],
        Not(a[i]), Not(b[i])), And(a[i], b[i], C[i+1])))

    return And(constraints)


# convert a number to binary
def toBinary(num, length):
    num_bin = bin(num).split("b")[-1]
    num_bin = "0"*(length - len(num_bin)) + num_bin
    return [bool(int(num_bin[i])) for i in range(len(num_bin))]


def toInt(num, length):
    num_int = 0
    for i in range(length):
      if num[i]:
        num_int += 2**(length-1-i)
    return num_int


def add2(name, d, *args, length):
    constraints = []
    #global T
    T = [[Bool(f'T_{name}_{i}_{j}') for j in range(length)] for i in range(len(args))]

    for i in range(len(args)-1):
        constraints.append(add1(f'{name}_{i}', T[i+1][:], T[i][:], args[i+1][:], length=length))
        #pass

    for i in range(length):
        constraints.append(T[0][i] == args[0][i])
        constraints.append(T[len(args)-1][i] == d[i])
        #pass
    return And(constraints)


def greater_than(name, a, b, length): # a is greater than b.
    constraints = []
    found_diff = [Bool(f'found_diff_{name}_{i}') for i in range(length)]
    for i in range(length):
        #s.add(Or(And(a[i], b[i]), And(Not(a[i]), Not(b[i]))) == Not(found_diff[i]))
        constraints.append(Or(And(a[i], Not(b[i])), And(Not(a[i]), b[i])) == found_diff[i])
        constraints.append(Implies(And([Not(found_diff[j]) for j in range(i)]), Or(Not(found_diff[i]), And(a[i], Not(b[i])))))
    return And(constraints)


def strictly_greater_than(name, a, b, length): # a is greater than b.
    constraints = []
    constraints.append(greater_than(name, a, b, length=length))
    constraints.append(Or([And(a[i], Not(b[i])) for i in range(length)]))
    return And(constraints)


def toPath(M):
    a = np.array(M)
    b = a.swapaxes(0,2)
    c = b.swapaxes(1,2)

    allpaths = []
    for i in range(a.shape[2]):
        G = nx.from_edgelist(zip(*np.nonzero(c[i])), create_using = nx.DiGraph())
        path = nx.tournament.hamiltonian_path(G)
        path.remove(a.shape[0]-1)
        path = list(map(lambda x: x+1, path))
        allpaths.append(path)

    return allpaths


def bit_bound(upper_bound, n, l):
  # se ci sono n nodi e m corrieri, visto che m corrieri lasciano il depot
  # (esplorando almeno un nodo) il corriere con distanza maggiore passa al massimo
  # per n - m nodi, percorrendo quindi n - m + 1 edges (contando anche gli edge
  # dei depot). Quindi prendo gli n-m+1 valori maggiori di D e li sommo.
  # Data la loro somma, il num di bit max sarà il log in base 2.
  # I valori che potrebbero essere più grandi di questa somma sono n+1 ed l.
  #number_of_max_values = len(D) - m
  max_value = max(upper_bound, n+1, max(l))
  number_of_bits = math.ceil(math.log2(max_value))
  return number_of_bits    

def max_of(name, H_max, H, length): # H_max is the maximum of H
  constraints = []
  constraints.append(Or([And([H_max[j] == H[i][j] for j in range(length)]) for i in range(len(H))]))  # v is an element in x)
  for i in range(len(H)):
      constraints.append(greater_than(f'h_{name}_{i}', H_max, H[i], length=length))  # and it's the greatest
  return And(constraints)

def sat_model(n, m, l, w, D, lower_bound, upper_bound, symbreak=False):
    w += [0]
    trial_number = 0
    length = bit_bound(upper_bound, m, l)
    #print(length)

    # Building the M matrix: a NxNxm matrix where M_ijk == 1 iff courier k goes from i to j. This will be the solution.
    N = toBinary(n + 1, length=length)  # add depot
    M = [[[Bool(f"M_{i}_{j}_{k}") for k in range(m)] for j in range(n+1)] for i in range(n+1)]

    # Building the C matrix (customer matrix): a Nxk matrix where C_ik == 1 iff courier k visits customer i
    C = [[Bool(f"C_{i}_{k}") for k in range(m)] for i in range(n+1)]

    # Building cumulative weight matrix
    U = [[Bool(f"U_{i}_{j}") for j in range(length)] for i in range(n+1)]

    # create solver
    s = Solver()

    # 1) In M, each courier cannot go from one location to the same location: M[i,i,k] == 0 for every i, k
    for i in range(n+1):
        for k in range(m):
            s.add(Not(M[i][i][k]))

    # 2) Each customer is visited exactly once: for every i (except depot), the sum over the k of C must be 1
    for i in range(n):
        # defining the sum
        C_sum = []
        for k in range(m):
            C_sum += [C[i][k]]

        # constraints for the sum: exactly_one
        s.add(exactly_one_seq(C_sum, f'l_{i}'))

    # 3) m vehicles leave the depot: C[N-1][k] == 1 for every k
    s.add(And([C[n][k] for k in range(m)]))

    # 4) the same vehicle enters and leaves a given customer
    # the == operator means double implication and is supported by Z3
    for i in range(n+1):
        for k in range(m):
            # defining the sum
            M_enter_sum = []
            M_exit_sum = []
            for j in range(n+1):
                M_enter_sum += [M[i][j][k]]
                M_exit_sum += [M[j][i][k]]

            # s.add(And(exactly_one(M_enter_sum)) == And(exactly_one(M_exit_sum)))
            s.add(Implies(C[i][k], And(exactly_one_seq(M_enter_sum, f'n_{i}{k}'))))
            s.add(Implies(C[i][k], And(exactly_one_seq(M_exit_sum, f'o_{i}{k}'))))
            s.add(Implies(Not(C[i][k]), And([Not(i) for i in M_enter_sum])))
            s.add(Implies(Not(C[i][k]), And([Not(i) for i in M_exit_sum])))

    # 5) First constraint on U matrix: for every courier, the N-th element of the matrix must be 0.
    for i in range(n+1):
        s.add(greater_than(f'a_{i}', U[i][:], toBinary(0, length=length), length=length))
        s.add(greater_than(f'b_{i}', toBinary(n, length=length), U[i][:], length=length))

    for i in range(n):
        var2 = [Bool(f'var2_{i}_{l}') for l in range(length)]
        s.add(add1(f'c_{i}', var2, U[i][:], toBinary(1, length=length), length=length))
        for j in range(n):
            #M_ij_sum = []
            if i != j:
                for k in range(m):
                    #M_ij_sum += [M[i][j][k]]
                    #s.add(Implies(And(AtLeast(*M_ij_sum,1), AtMost(*M_ij_sum,1)), greater_than('f', U[j][:], var2)))
                    s.add(Implies(M[i][j][k], greater_than(f'd_{i}{j}', U[j][:], var2, length=length)))

    # Constraint sui pesi
    loads = []
    for k in range(m):
        sum_w = [Bool(f'sum_w_{k}_{i}') for i in range(length)]
        sum_w_list = []
        for i in range(n+1):
            sum_w_list_i = [Bool(f'sum_w_list_i_{k}{i}_{l}') for l in range(length)]
            s.add(Implies(C[i][k], And([sum_w_list_i[l] == toBinary(w[i], length=length)[l] for l in range(length)])))
            s.add(Implies(Not(C[i][k]), And([Not(sum_w_list_i[l]) for l in range(length)])))
            sum_w_list.append(sum_w_list_i)
        s.add(add2(f'e_{k}', sum_w, *sum_w_list, length=length))
        s.add(greater_than(f'f_{k}', toBinary(l[k], length=length), sum_w, length=length))
        loads.append(sum_w)

    if symbreak:
      # symmetry breaking constraint
      #constraint forall(i in 1..M, j in 1..M where (i < j /\ max(u[i], u[j]) <= min(l[j], l[i])))(lex_lesseq(row(es, i), row(es, j)))
      # row(es, i) = M[:][:][i] flattened
      for i in range(m):
        for j in range(m):
          if i < j:
            max_value = [Bool(f'max_value_{i}_{j}_{k}') for k in range(length)]
            s.add(max_of(f'p_{i}_{j}', max_value, [loads[i], loads[j]], length=length)) 
            for t in range(n):
              #s.add(Implies(And(greater_than(f'q_{i}_{j}_{t}', toBinary(min(l[i], l[j]), length=length), max_value, length=length), M[n][t][i]), And([Not(M[n][o][j]) for o in range(t)])))
              s.add(Implies(And(greater_than(f'q_{i}_{j}_{t}', toBinary(min(l[i], l[j]), length=length), max_value, length=length), M[n][t][i]), And([Not(M[n][o][j]) for o in range(t)])))
            #s.add(Implies(max_value <= min(l[i], l[j]), precedes(M[n][:][i], M[n][:][j])))

    # Building the H vector: a vector which contains the distance covered for each courier
    H = [[Bool(f'H_{i}_{k}') for i in range(length)] for k in range(m)]
    for k in range(m):
        H_list = []
        for i in range(n+1):
            for j in range(n+1):
                H_list_i = [Bool(f'H_list_i_{k}{i}{j}_{l}') for l in range(length)]
                s.add(Implies(M[i][j][k], And([H_list_i[l] == toBinary(D[i][j], length=length)[l] for l in range(length)])))
                s.add(Implies(Not(M[i][j][k]), And([Not(H_list_i[l]) for l in range(length)])))
                H_list.append(H_list_i)
        #print(H_sum)
        s.add(add2(f'g_{k}', H[k][:], *H_list, length=length))

    # Variable which symbolizes the maximum of H
    H_max = [Bool(f'H_max_{i}') for i in range(length)]

    # 8) H_max constraint: H_max is the maximum value of H.
    # print(maximum(H))
    s.add(Or([And([H_max[j] == H[i][j] for j in range(length)]) for i in range(len(H))]))  # v is an element in x)
    for i in range(len(H)):
        s.add(greater_than(f'h_{i}', H_max, H[i], length=length))  # and it's the greatest

    distances = []
    for i in range(n):
        distances.append(D[i][n] + D[n][i])

    s.add(greater_than('i', H_max, toBinary(lower_bound, length=length), length=length))
    s.add(greater_than('j', toBinary(upper_bound, length=length), H_max, length=length))

    # symmetry breaking constraints
    #  constraint forall(i in 1..M, j in 1..M where (i < j /\ max(u[i], u[j]) <= min(l[j], l[i])))(lex_lesseq(row(es, i), row(es, j)));


    # timeout
    #s.set("timeout", 150000)
    print(s.check())

    while s.check() == sat:
        sol = s.model()
        H_current = [sol.evaluate(H_max[j]) for j in range(length)]
        print(s.check(), f'trial_number: {trial_number}, H_current: {toInt(H_current, length=length)}')
        s.add(strictly_greater_than(f'l_{trial_number}', H_current, H_max, length=length))
        print(s.check())
        trial_number += 1
        if s.check() == sat:
            final_sol = s.model()
        else:
            final_sol = sol

    return toPath([[[final_sol.evaluate(M[i][j][k]) for k in range(m)] for j in range(n+1)] for i in range(n+1)]), toInt([final_sol.evaluate(H_max[i]) for i in range(length)], length=length)
