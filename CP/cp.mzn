include "globals.mzn";

int: N;                     % number of nodes (including the two special nodes to represent the depot)
int: M;                     % number of couriers
int: E;                     % number of edges
array [1..E] of int: from;  % from[i] is the node where edge i starts
array [1..E] of int: to;    % to[i] is the node where edge i ends
array [1..E] of int: w;     % w[i] is the distance/length of edge i
array [1..M] of int: l;     % l[i] is the capacity of courier i
array [1..N-2] of int: p;   % p[i] is the weight of node i

var int: s;
var int: t;
var int: objective;
array [1..M, 1..N] of var bool: ns;
array [1..M, 1..E] of var bool: es;
array [1..M] of var int: K;
array [1..M] of var int: u;

constraint s = N - 1;
constraint t = N;
constraint objective = max(K);
constraint forall(j in 1..M)(u[j] = sum(i in 1..N-2)(ns[j,i]*p[i]));
constraint forall(j in 1..M)(u[j] <= l[j]);
constraint forall(j in 1..M)(bounded_dpath(N, E, from, to, w, s, t, row(ns, j), row(es, j), K[j]));
constraint forall(i in 1..N-2)(sum(j in 1..M)(ns[j,i]) == 1);

% Symmetry breaking constraints
% constraint forall(i in 1..M, j in 1..M where (i < j /\ max(u[i], u[j]) <= min(l[j], l[i])))(lex_lesseq(row(es, i), row(es, j)));

solve minimize objective;

output [ show(ns), " ", show(es), " ", show(K), " ", show(u), " ", show(s), " ", show(t) ];
