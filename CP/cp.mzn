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
array [1..M] of var int: u;

constraint forall(j in 1..M)(u[j] = sum(i in 1..N-2)(ns[j,i]*p[i]));

constraint s = N - 1;
constraint t = N;
constraint forall(j in 1..M)(u[j] <= l[j]);
constraint forall(j in 1..M)(bounded_dpath(N, E, from, to, w, s, t, row(ns, j), row(es, j), K[j]));
constraint forall(i in 1..N-2)(sum(j in 1..M)(ns[j,i]) == 1);

%constraint forall(i in 1..M, j in 1..M where (i < j /\ l[i] == l[j]))(lex_lesseq(row(es, i), row(es, j)));
constraint forall(i in 1..M, j in 1..M where (i < j /\ max(u[i], u[j]) <= min(l[j], l[i])))(lex_lesseq(row(es, i), row(es, j)));

% implicit constraints 


solve minimize max(K);

output [ show(ns), " ", show(es), " ", show(K), " ", show(s), " ", show(t) ];
