param N integer >= 0; # Number of customers
param K integer >= 0; # Number of couriers

set NODES := {1..N}; 
set NODES_1 := {1..N+1};
set COURIERS := {1..K};

param C{COURIERS} integer >= 0; # capacity of vehicles
param L{NODES} integer >= 0; # loads of items
param D{NODES_1, NODES_1} integer >= 0; # weights of the arcs

param lb integer >= 0; # lower bound for the objective function
param ub integer >= 0; # upper bound for the objective function

var x{NODES_1, NODES_1, COURIERS} in {0..1}; # Edges tensor
var y{NODES_1, COURIERS} in {0..1}; # customers matrix
# var u{NODES_1, COURIERS} integer >= 0; # Cumulative load delivered by couriers
var u{NODES} integer >= 0; # Cumulative load delivered by couriers
var objective integer >= 0; # Objective function

# minimize cost_function : max{k in COURIERS} sum {i in NODES_1, j in NODES_1} D[i,j]*x[i,j,k];
minimize cost_function: objective;
subject to bounds: lb <= objective <= ub;

s.t. objective_assignement: objective == max{k in COURIERS} sum {i in NODES_1, j in NODES_1} D[i,j]*x[i,j,k];
s.t. self_loops{i in NODES_1, k in COURIERS}: x[i,i,k] == 0;
s.t. exactly_once {i in NODES}: sum {k in COURIERS} y[i,k] == 1;
s.t. depot_k: sum {k in COURIERS} y[N+1, k] == K;
s.t. enter_quit_1 {i in NODES_1, k in COURIERS}: sum {j in NODES_1} x[j,i,k] == sum {j in NODES_1} x[i,j,k];
s.t. enter_quit_2 {i in NODES_1, k in COURIERS}: sum {j in NODES_1} x[i,j,k] == y[i,k];
s.t. load_cap {k in COURIERS}: sum {i in NODES} L[i]*y[i,k] <= C[k];
s.t. subtour_elimination {i in NODES, j in NODES, k in COURIERS}: u[i] - u[j] + N*x[i,j,k] <= N-1;
