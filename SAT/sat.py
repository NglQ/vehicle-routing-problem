from itertools import chain, combinations
from z3 import *
from utils import *

from converter import convert

# Useful constraints
def at_least_one(bool_vars):
    return Or(bool_vars)

def at_most_one(bool_vars):
    return [Not(And(pair[0], pair[1])) for pair in combinations(bool_vars, 2)]

def exactly_one(bool_vars):
    return at_most_one(bool_vars) + [at_least_one(bool_vars)]

# Advanced constraints
def at_least_k_np(bool_vars, k):
    #print("at_least")
    return at_most_k_np([Not(var) for var in bool_vars], len(bool_vars)-k)

def at_most_k_np(bool_vars, k):
    #print("at_most")
    return And([Or([Not(x) for x in X]) for X in combinations(bool_vars, k + 1)])

def exactly_k_np(bool_vars, k):
    #print("excactly")
    return And(at_most_k_np(bool_vars, k), at_least_k_np(bool_vars, k))

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
def add1(name, d, a, b): # d is the sum of the args    
    constraints = []
    #global C
    # carry matrix
    C = [Bool(f'C_{name}_{i}') for i in range(17)]

    constraints.append(And(Not(C[0]), Not(C[16])))
    for i in range(16):
        constraints.append(C[i] == Or(And(a[i], b[i]), And(a[i], C[i+1]), And(b[i], C[i+1])))        

    for i in range(16):
        #constraints.append((a[i] == b[i]) == (C[i] == d[i]))
        constraints.append(d[i] == Or(And(a[i], Not(b[i]), Not(C[i+1])), And(b[i], Not(a[i]), Not(C[i+1])), And(C[i+1], 
        Not(a[i]), Not(b[i])), And(a[i], b[i], C[i+1])))
        
    return And(constraints)

# convert a number to binary
def toBinary(num, length=16):
    num_bin = bin(num).split("b")[-1]
    num_bin = "0"*(length - len(num_bin)) + num_bin
    return [bool(int(num_bin[i])) for i in range(len(num_bin))]
        

def add2(name, d, *args):
    constraints = []
    #global T
    T = [[Bool(f'T_{name}_{i}_{j}') for j in range(16)] for i in range(len(args))]
    
    for i in range(len(args)-1):
        constraints.append(add1(f'{name}_{i}', T[i+1][:], T[i][:], args[i+1][:]))
        #pass
        
    for i in range(16):
        constraints.append(T[0][i] == args[0][i])
        constraints.append(T[len(args)-1][i] == d[i])
        #pass
    return And(constraints)
    
# binary multiplication in SAT. a and b are boolean vectors of length 16. s is the solver.
def multiply(name, a, b, prod): # prod is the product of a and b
    # define the subsum matrix
    #global SUM
    constraints = []
    S = [[Bool(f'S_{name}_{i}_{j}') for j in range(16)] for i in range(16)]
    for i in range(16):
        if i != 0:
            for k in range(i):
                constraints.append(Not(S[i][15-k]))
        for j in range(16):
            if j+i <= 15:
                constraints.append(S[i][15-j-i] == And(a[15-j], b[15-i]))
            if j+i > 15:
                constraints.append(Not(And(a[15-j], b[15-i])))
    #print(*[SUM[i][:] for i in range(16)])      
    # sum every row of the matrix
    constraints.append(add2(name, prod, *[S[i][:] for i in range(16)]))
    return And(constraints)

def greater_than(name, a, b): # a is greater than b.
    constraints = []
    found_diff = [Bool(f'found_diff_{name}_{i}') for i in range(16)]
    for i in range(16):
        #s.add(Or(And(a[i], b[i]), And(Not(a[i]), Not(b[i]))) == Not(found_diff[i]))
        constraints.append(Or(And(a[i], Not(b[i])), And(Not(a[i]), b[i])) == found_diff[i])
        constraints.append(Implies(And([Not(found_diff[j]) for j in range(i)]), Or(Not(found_diff[i]), And(a[i], Not(b[i])))))
    return And(constraints)

def strictly_greater_than(name, a, b): # a is greater than b.
    constraints = []
    constraints.append(greater_than(name, a, b))
    constraints.append(Or([And(a[i], Not(b[i])) for i in range(16)]))
    return And(constraints)    

def sat_model(instance_file: str, solver: str, time_limit: int, sym_break: bool):
    if sym_break:
        print('Symmetry breaking constraints not implemented for SAT model yet.')
        return None
    if solver != 'z3':
        print('Only z3 solver is supported for SAT model.')
        return None

    m, n, l, w, D = convert(instance_file)
    w += [0]

    trial_number = 0
    
    # Building the M matrix: a NxNxm matrix where M_ijk == 1 iff courier k goes from i to j. This will be the solution.
    N = toBinary(n + 1)  # add depot
    M = [[[Bool(f"M_{i}_{j}_{k}") for k in range(m)] for j in range(n+1)] for i in range(n+1)]

    # Building the C matrix (customer matrix): a Nxk matrix where C_ik == 1 iff courier k visits customer i
    C = [[Bool(f"C_{i}_{k}") for k in range(m)] for i in range(n+1)]

    # Building cumulative weight matrix
    U = [[Bool(f"U_{i}_{j}") for j in range(16)] for i in range(n+1)]
    
    # create solver
    s = Solver()

    # timeout
    timeout = time_limit / 2 * 1000
    # s.set("timeout", timeout)
 
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
        s.add(greater_than(f'a_{i}', U[i][:], toBinary(0)))
        s.add(greater_than(f'b_{i}', toBinary(n), U[i][:]))
        
    for i in range(n):
        var2 = [Bool(f'var2_{i}_{l}') for l in range(16)]
        s.add(add1(f'c_{i}', var2, U[i][:], toBinary(1)))
        for j in range(n):
            #M_ij_sum = []
            if i != j:
                for k in range(m):
                    #M_ij_sum += [M[i][j][k]]
                    #s.add(Implies(And(AtLeast(*M_ij_sum,1), AtMost(*M_ij_sum,1)), greater_than('f', U[j][:], var2)))
                    s.add(Implies(M[i][j][k], greater_than(f'd_{i}{j}', U[j][:], var2)))
                    
    # Constraint sui pesi
    for k in range(m):
        sum_w = [Bool(f'sum_w_{k}_{i}') for i in range(16)]
        sum_w_list = []
        for i in range(n+1):
            sum_w_list_i = [Bool(f'sum_w_list_i_{k}{i}_{l}') for l in range(16)]
            s.add(Implies(C[i][k], And([sum_w_list_i[l] == toBinary(w[i])[l] for l in range(16)])))
            s.add(Implies(Not(C[i][k]), And([Not(sum_w_list_i[l]) for l in range(16)])))
            sum_w_list.append(sum_w_list_i)
        s.add(add2(f'e_{k}', sum_w, *sum_w_list))
        s.add(greater_than(f'f_{k}', toBinary(l[k]), sum_w))

    # Building the H vector: a vector which contains the distance covered for each courier
    H = [[Bool(f'H_{i}_{k}') for i in range(16)] for k in range(m)]
    for k in range(m):
        H_list = []
        for i in range(n+1):
            for j in range(n+1):
                H_list_i = [Bool(f'H_list_i_{k}{i}{j}_{l}') for l in range(16)]
                s.add(Implies(M[i][j][k], And([H_list_i[l] == toBinary(D[i][j])[l] for l in range(16)])))
                s.add(Implies(Not(M[i][j][k]), And([Not(H_list_i[l]) for l in range(16)])))
                H_list.append(H_list_i)
        #print(H_sum)
        s.add(add2(f'g_{k}', H[k][:], *H_list))    
        
    # Variable which symbolizes the maximum of H
    H_max = [Bool(f'H_max_{i}') for i in range(16)]
    
    # 8) H_max constraint: H_max is the maximum value of H.
    # print(maximum(H))
    s.add(Or([And([H_max[j] == H[i][j] for j in range(16)]) for i in range(len(H))]))  # v is an element in x)
    for i in range(len(H)):
        s.add(greater_than(f'h_{i}', H_max, H[i]))  # and it's the greatest
    
    distances = []
    for i in range(n):
        distances.append(D[i][n] + D[n][i])

    print(distances)
    s.add(greater_than('i', H_max, toBinary(max(distances))))

    # Objective function: minimize H_max
    #s.minimize(H_max)
    
    s.add(greater_than('j', toBinary(250), H_max))

    while s.check() == sat:
        sol = s.model()
        H_current = [sol.evaluate(H_max[j]) for j in range(16)]
        print(s.check(), f'trial_number: {trial_number}, H_current: {H_current}')
        s.add(strictly_greater_than(f'l_{trial_number}', H_current, H_max))
        print(s.check())
        trial_number += 1
        if s.check() == sat:
            final_sol = s.model()
        else:
            final_sol = sol
    
    #s.check()
    #print(s.check())
    #sol = s.model()
    
    return [[[final_sol.evaluate(M[i][j][k]) for k in range(m)] for j in range(n+1)] for i in range(n+1)], [
        [final_sol.evaluate(C[i][k]) for k in range(m)] for i in range(n+1)], [[final_sol.evaluate(U[i][j]) for j in range(16)] for i in range(n+1)], [[final_sol.evaluate(H[i][j]) for j in range(16)]for i in range(m)], [
        final_sol.evaluate(H_max[i]) for i in range(16)]