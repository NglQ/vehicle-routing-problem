from z3 import *
import numpy as np
import networkx as nx

def max_of(a, l): # a is the maximum value of list l
  constraints = []
  constraints.append(Or([a == l[i] for i in range(len(l))]))
  for i in range(len(l)):
    constraints.append(a >= l[i])
  return And(constraints)

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

def smt_model(n, m, l, w, D, lower_bound, upper_bound, symbreak=False):
    w += [0]
    # Building the M matrix: a NxNxm matrix where M_ijk == 1 iff courier k goes from i to j. This will be the solution.
    N = n + 1  # add depot
    M = [[[Bool(f"M_{i}_{j}_{k}") for k in range(m)] for j in range(N)] for i in range(N)]

    # Building the C matrix (customer matrix): a Nxk matrix where C_ik == 1 iff courier k visits customer i
    C = [[Bool(f"C_{i}_{k}") for k in range(m)] for i in range(N)]

    # Building cumulative weight matrix
    U = [Int(f"U_{i}") for i in range(N)]

    # Building the H vector: a vector which contains the distance covered for each courier
    H = []
    for k in range(m):
        H_sum = 0
        for i in range(N):
            for j in range(N):
                H_sum += M[i][j][k] * D[i][j]
                # print(H_sum)

        H.append(H_sum)

    # Variable which symbolizes the maximum of H
    H_max = Int('max_H')

    # create solver
    s = Optimize()

    # CONSTRAINTS

    # 1) In M, each courier cannot go from one location to the same location: M[i,i,k] == 0 for every i, k
    for i in range(N):
        for k in range(m):
            s.add(Not(M[i][i][k]))

    # 2) Each customer is visited exactly once: for every i (except depot), the sum over the k of C must be 1
    for i in range(n):
        # defining the sum
        C_sum = []
        for k in range(m):
            C_sum += [C[i][k]]

        # constraints for the sum: exactly_one
        s.add(And(AtLeast(*C_sum, 1), AtMost(*C_sum, 1)))

    # 3) m vehicles leave the depot: sum over k of C[N-1][k] == m
    # defining the sum
    C_N_sum = []
    for k in range(m):
        # defining the sum
        C_N_sum += [C[N - 1][k]]
        # print(at_most_k_np(C_N_sum, m))

    s.add(And(AtLeast(*C_N_sum, m), AtMost(*C_N_sum, m)))

    # 4) the same vehicle enters and leaves a given customer
    # the == operator means double implication and is supported by Z3
    for i in range(N):
        for k in range(m):
            # defining the sum
            M_enter_sum = []
            M_exit_sum = []
            for j in range(N):
                M_enter_sum += [M[i][j][k]]
                M_exit_sum += [M[j][i][k]]

            # s.add(And(exactly_one(M_enter_sum)) == And(exactly_one(M_exit_sum)))
            s.add(Implies(C[i][k], And(AtLeast(*M_enter_sum, 1), AtMost(*M_enter_sum, 1))))
            s.add(Implies(C[i][k], And(AtLeast(*M_exit_sum, 1), AtMost(*M_exit_sum, 1))))
            s.add(Implies(Not(C[i][k]), And(AtLeast(*M_enter_sum, 0), AtMost(*M_enter_sum, 0))))
            s.add(Implies(Not(C[i][k]), And(AtLeast(*M_exit_sum, 0), AtMost(*M_exit_sum, 0))))

    # 5) First constraint on U matrix: for every courier, the N-th element of the matrix must be 0.
    for i in range(N):
        s.add(U[i] >= 0)
        s.add(U[i] <= N - 1)
        # pass

    # 6) subtour elimination constraint
    for i in range(N):
        for j in range(N):
            for k in range(m):
                if i != j:  # fix meeeeeeeeeeeeeeeee
                    pass
                    # s.add(Implies(And([C[i][k], C[j][k], M[i][j][k]]), U[i][k] - U[j][k] + l[k] <= l[k] - w[j]))
                    # s.add(Implies(And([C[i][k], C[j][k], Not(M[i][j][k])]), U[i][k] - U[j][k] <= l[k] - w[j]))

    # 7) U lower and upper bounds
    # chiedi: perché nel modello ILP non definiamo U direttamente come somma cumulata dei pesi, ma mettiamo
    # solo i constraint?
    for k in range(m):
        for i in range(N):
            # s.add(Implies(C[i][k], And(w[i] <= U[i][k], U[i][k] <= l[k])))
            # s.add(Implies(Not(C[i][k]), U[i][k] == 0))
            pass

    for i in range(N - 1):
        for j in range(N - 1):
            M_ij_sum = []
            if i != j:
                for k in range(m):
                    M_ij_sum += [M[i][j][k]]
                    # s.add(Implies(And(AtLeast(*M_ij_sum,1), AtMost(*M_ij_sum,1)), U[i] - U[j] <= -1))
                    s.add(Implies(M[i][j][k], U[i] - U[j] <= -1))

    # MTZ constraint
    # for k in range(m):
    # for i in range(N-1):
    # for j in range(N-1):
    # s.add(Implies(M[i][j][k], U[j][k] > U[i][k]))
    # pass

    # Constraint sui pesi e vettore dei pesi
    loads = []
    for k in range(m):
        sum_w = 0
        for i in range(N):
            sum_w += w[i] * C[i][k]
        loads.append(sum_w)
        s.add(sum_w <= l[k])
    
    if symbreak:
      # symmetry breaking constraint
      #constraint forall(i in 1..M, j in 1..M where (i < j /\ max(u[i], u[j]) <= min(l[j], l[i])))(lex_lesseq(row(es, i), row(es, j)))
      # row(es, i) = M[:][:][i] flattened
      for i in range(m):
        for j in range(m):
          if i < j:
            max_value = Int(f'max_value_{i}_{j}')
            s.add(max_of(max_value, [loads[i], loads[j]])) 
            for t in range(n):
              s.add(Implies(And(max_value <= min(l[i], l[j]), M[n][t][i]), And([Not(M[n][o][j]) for o in range(t)])))
            #s.add(Implies(max_value <= min(l[i], l[j]), precedes(M[n][:][i], M[n][:][j])))


    # 8) H_max constraint: H_max is the maximum value of H.
    # print(maximum(H))
    s.add(Or([H_max == H[i] for i in range(len(H))]))  # v is an element in x)
    for i in range(len(H)):
        s.add(H_max >= H[i])  # and it's the greatest

    # Lower and upper bound
    s.add(H_max <= upper_bound)
    s.add(H_max >= lower_bound)

    # 9) H_max lower bound: H_max is higher than the maximum distance between the distances starting from depot
    # D_max = max(D[n][:])
    # s.add(H_max >= 436)
    # s.add(H_max <= 1000)

    # Objective function: minimize H_max
    s.minimize(H_max)

    # timeout
    #s.set("timeout", 150000)

    s.check()
    print(s.check())
    sol = s.model()

    return toPath([[[sol.evaluate(M[i][j][k]) for k in range(m)] for j in range(N)] for i in range(N)]), sol.evaluate(H_max)