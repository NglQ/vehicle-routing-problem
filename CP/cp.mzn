% Use this editor as a MiniZinc scratch book
include "globals.mzn";

int: N;
int: M;
int: E;
array [1..E] of int: from;
array [1..E] of int: to;
array [1..E] of int: w;
array [1..M] of int: l;
array [1..N-2] of int: p; 

var int: s;
var int: t;
array [1..M, 1..N] of var bool: ns;
array [1..M, 1..E] of var bool: es;
array [1..M] of var int: K;

constraint s = 9;
constraint t = 10;
constraint forall(j in 1..M)(sum(i in 1..N-2)(ns[j,i]*p[i]) <= l[j]);
constraint forall(j in 1..M)(bounded_dpath(N, E, from, to, w, s, t, [ns[j,i] | i in 1..N], [es[j,i] | i in 1..E], K[j]));
constraint forall(i in 1..N-2)(sum(j in 1..M)(ns[j,i]) == 1);
constraint forall(i in 1..M, j in 1..M where (i < j /\ l[i] == l[j]))(es[i] == 1);

solve minimize max(K);

output [ show(ns), " ", show(es), " ", show(K), " ", show(s), " ", show(t) ];