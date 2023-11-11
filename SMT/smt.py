from pysmt.shortcuts import Symbol, get_env, Solver, Not, And, GE, LT, Plus, Equals, Int, get_model
from pysmt.logics import QF_UFLRA
from pysmt.typing import INT


def smt_model():
    name = "z3"  # Note: The API version is called 'msat'

    x, y = Symbol("x"), Symbol("y")
    f = x.Implies(y)
# Path to the solver. The solver needs to take the smtlib file from
# stdin. This might require creating a tiny shell script to set the
# solver options.
# path = ["/tmp/mathsat"]
    logics = [QF_UFLRA,]    # List of the supported logics

# Add the solver to the environment
# env = get_env()
# env.factory.add_generic_solver(name, path, logics)

# The solver name of the SMT-LIB solver can be now used anywhere
# where pySMT would accept an API solver name
    with Solver(name=name, logic="QF_UFLRA") as s:
        s.add_assertion(f)
        s.push()
        s.add_assertion(x)
        res = s.solve()
        v_y = s.get_value(y)
        print(v_y)  # TRUE

        s.pop()
        s.add_assertion(Not(y))
        res = s.solve()
        v_x = s.get_value(x)
        print(v_x)  # FALSE