% Parameters
int: n;                             % number of customers
int: m;                             % number of couriers
int: N = n + 1;                     % number of customers + depot
array[1..m] of int: l;              % couriers max load
array[1..n] of int: w;              % items weight
array[1..N] of int: W = w ++ [0];   % items weight + depot
array[1..N, 1..N] of int: D;        % distance matrix

% Variables
array[1..N, 1..N, 1..m] of var 0..1: x;  % edges matrix
array[1..N, 1..m] of var 0..1: y;        % customers matrix
array[1..N, 1..m] of var int: u;         % cumulative load delivered by couriers

% Constraints

constraint forall (i in 1..N, k in 1..m) (x[i,i,k] == 0);

constraint forall (k in 1..m) (u[N,k] == 0);

% constraint forall (i in 1..n, j in 1..n, k in 1..m where i != j) (if w[i] + w[j] > l[k] then x[i,j,k] == 0 else true endif);

% each customer is visited exactly once
constraint forall (i in 1..n) (sum (k in 1..m) (y[i,k]) == 1);

% m vehicles leave the depot
constraint sum (k in 1..m) (y[N,k]) == m;

% the same vehicle enters and leaves a given customer
constraint forall (i in 1..N, k in 1..m) (
                        sum (j in 1..N) (x[i,j,k]) == sum (j in 1..N) (x[j,i,k]) /\
                        sum (j in 1..N) (x[j,i,k]) == y[i,k]
                  );

% subtour elimination constraint
% fix i and j iterators
constraint forall (i in 1..n, j in 1..n, k in 1..m where (i != j /\ y[i,k] == 1 /\ y[j,k] == 1)) (
                        u[i,k] - u[j,k] + l[k] * x[i,j,k] <= l[k] - w[j]
                  );

% `u` lower and upper bounds
constraint forall (i in 1..n, k in 1..m) (if y[i,k] == 1 then w[i] <= u[i,k] /\ u[i,k] <= l[k] else u[i,k] == 0 endif);
% constraint forall (i in 1..n, k in 1..m) (w[i] <= u[i,k] /\ u[i,k] <= l[k]);


solve minimize max (k in 1..m) (sum (i in 1..N, j in 1..N) (D[i,j] * x[i,j,k]));

