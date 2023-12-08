from z3 import *
import numpy as np
import networkx as nx

import converter


def generate_lowerbound(n,D):
        distances = []
        for i in range(n):
            distances.append(D[i][n] + D[n][i])
        return max(distances)

def generate_upperbound(n, m, D):
    depot_to_cities = np.array(D[-1][:len(D) - 1])
    cities_to_depot = np.array([D[i][-1] for i in range(len(D) - 1)])
    depot_cities_depot = depot_to_cities + cities_to_depot
    distances_prov = np.sort(depot_cities_depot)
    distances = distances_prov[-m + 1:]
    indices_to_remove = np.argsort(depot_cities_depot)[-m + 1:]

    range_n = [i for i in range(n) if i not in indices_to_remove]
    idx = n
    visited = [idx]
    dist = 0
    while len(range_n) != 0:
        idx = np.argmin(np.array([val if i != idx and i in range_n else np.inf for i, val in enumerate(D[idx])]))
        dist += D[visited[-1]][idx]
        range_n.remove(idx)
        visited.append(idx)

    dist += D[visited[-1]][n]
    return max(np.append(distances, dist))

def toPath(M): # outputs the path of every courier
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

def max_of(H_max, H): # H_max is the maximum value of list H
  constraints = []
  constraints.append(Or([H_max == H[i] for i in range(len(H))]))
  for i in range(len(H)):
    constraints.append(H_max >= H[i])
  return And(constraints)

def smt_model(n, m, l, w, D, LB=None, UB=None, SB=False):
    N = n + 1

    # VARIABLES

    X = [[[Bool(f"X_{i}_{j}_{k}") for k in range(m)] for j in range(N)] for i in range(N)]
    Y = [[Bool(f"Y_{i}_{k}") for k in range(m)] for i in range(N)]
    U = [Int(f"U_{i}") for i in range(N)]
    H_max = Int('max_H')

    # SOLVER

    s = Optimize()

    # CONSTRAINTS

    # 1) Each courier cannot go from one location to the same location: X[i,i,k] == 0 for every i, k
    for i in range(N):
        for k in range(m):
            s.add(Not(X[i][i][k]))

    # 2) The same vehicle enters and leaves a given customer
    for i in range(N):
        for k in range(m):
            X_enter = []
            X_exit = []
            for j in range(N):
                X_enter += [X[i][j][k]]
                X_exit += [X[j][i][k]]

            s.add(Implies(Y[i][k], And(AtLeast(*X_enter, 1), AtMost(*X_enter, 1))))
            s.add(Implies(Y[i][k], And(AtLeast(*X_exit, 1), AtMost(*X_exit, 1))))
            s.add(Implies(Not(Y[i][k]), And(AtLeast(*X_enter, 0), AtMost(*X_enter, 0))))
            s.add(Implies(Not(Y[i][k]), And(AtLeast(*X_exit, 0), AtMost(*X_exit, 0))))

    # 3) Each customer is visited exactly once: for every i (except depot), the sum over k of Y must be 1
    for i in range(n):
        Y_sum = []
        for k in range(m):
            Y_sum += [Y[i][k]]
        s.add(And(AtLeast(*Y_sum, 1), AtMost(*Y_sum, 1)))

    # 4) All the vehicles leave the depot: Y[n][k] is True for every k
    for k in range(m):
        s.add(Y[n][k])

    # 5) Every entry of the U vector has a value between 0 and N-1
    for i in range(N):
        s.add(U[i] >= 0)
        s.add(U[i] <= N - 1)

    # 6) Anti-subtour constraint
    for i in range(n):
        for j in range(n):
            if i != j:
                for k in range(m):
                    s.add(Implies(X[i][j][k], U[i] - U[j] <= -1))

    # 7) Maximum load constraint
    loads = []
    for k in range(m):
        sum_w = 0
        for i in range(n):
          sum_w += w[i] * Y[i][k]
        loads.append(sum_w)
        s.add(sum_w <= l[k])

    # 8) H constraint: H is the vector of the distance covered by each courier
    H = []
    for k in range(m):
        H_sum = 0
        for i in range(N):
            for j in range(N):
                H_sum += X[i][j][k] * D[i][j]
        H.append(H_sum)

    # 9) H_max constraint: H_max is the maximum value of H.
    s.add(max_of(H_max, H))

    # OPTIONAL CONSTRAINTS: LB, UB, SB

    if LB is not None: # Lower-bound for the objective function
      s.add(H_max >= LB)

    if UB is not None: # Upper-bound for the objective function
      s.add(H_max <= UB)

    if SB: # symmetry-breaking constraint
      for i in range(m):
        for j in range(m):
          if i < j:
            max_value = Int(f'max_value_{i}_{j}')
            s.add(max_of(max_value, [loads[i], loads[j]]))
            for t in range(n):
              s.add(Implies(And(max_value <= min(l[i], l[j]), X[n][t][i]), And([Not(X[n][o][j]) for o in range(t)])))

    # OBJECTIVE FUNCTION: minimize H_max
    s.minimize(H_max)

    s.check()
    print(s.check())
    sol = s.model()

    x_dict = dict()
    for i in range(N):
        for j in range(N):
            for k in range(m):
                x_dict[(i, j, k)] = sol.evaluate(X[i][j][k])

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

    return {"obj": sol.evaluate(H_max), "sol": toPath([[[sol.evaluate(X[i][j][k]) for k in range(m)] for j in range(N)] for i in range(N)])}

