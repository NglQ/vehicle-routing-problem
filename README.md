# vehicle-routing-problem

Bellatreccia Chiara, chiara.bellatreccia@studio.unibo.it

Fusa Edoardo, edoardo.fusa@studio.unibo.it

Quarta Angelo, angelo.quarta@studio.unibo.it

## Introduction

This report is meant to describe the process and the results of solving the Multiple Couriers Planning (MCP) problem. Since this problem is a particular instance of a more general set of problems called **Vehicle Routing Problems** (**VRP**), we found that the **Integer Linear Programming** (**ILP**) formulation is the most natural approach for this kind of problem.

In order to achieve solver independence, a solution based on python has been put in place. Said solution is organized in a modular fashion to call all the APIs of the employed solvers and modeling languages. So, we defined a pipeline that makes the user choose how many instances to run and which ones. At the end
of the execution, each model returns the JSON file formatted in the required fashion as output.

The modeling phase of the process has been carried out by the group in its entirety. However, the development workload has been split among the members: Edoardo and Angelo worked mainly on **Constraint Programming** (**CP**) and **Mixed Integer Programming** (**MIP**) models as well as the aspects related to software engineering. Chiara took care of **SATISFIABILITY** (**SAT**) an **Satisfiability Modulo Theories** (**SMT**) models.

The development process posed several challenges. One of the major difficulties was the lack of documentation in some open-source tools we employed, such as pySMT. Furthermore, that same library does not support a native timeout, therefore, we had to implement from scratch a way to stop the execution. The same issues was reported on SAT as well.

Overall those issues got an heavy impact on the time spent developing during the period right before handing the project. Concerning the developing time, it was stretched out on three months in which we did not consistently work on this particular project.

## Project installation
To build the docker image, run the following command in the root directory of the project:
```
docker compose build
```

To run the docker image, first run the following command in the root directory of the project:
```
docker compose up
```

Then, in a new terminal, keeping the previous one running, run the following command in the root directory of the project:
```
docker exec -it cdmo-container /bin/bash
```
