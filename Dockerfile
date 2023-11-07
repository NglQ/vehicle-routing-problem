FROM ubuntu:22.04

RUN apt-get update
RUN apt-get install -y software-properties-common && apt-get install -y keyboard-configuration
RUN apt-get install -y python3.11

RUN apt-get install -y python3-pip


RUN apt-get install -y libgl1-mesa-dev

RUN apt-get install -y wget

RUN pip3 install minizinc
RUN pip3 install numpy && pip3 install z3-solver

RUN pip3 install amplpy

RUN mkdir cdmo-test

WORKDIR ./cdmo-test

RUN wget -O ampl.linux64.tgz https://portal.ampl.com/external/?url=https://portal.ampl.com/dl/amplce/ampl.linux64.tgz
RUN tar -xvf ampl.linux64.tgz

RUN wget https://github.com/MiniZinc/MiniZincIDE/releases/download/2.7.6/MiniZincIDE-2.7.6-bundle-linux-x86_64.tgz
RUN tar -xvf MiniZincIDE-2.7.6-bundle-linux-x86_64.tgz

COPY main.sh \
     main.py ./

COPY converter.py ./

RUN chmod +x main.sh

RUN mkdir CP MIP SAT SMT

COPY instances ./instances/

COPY CP/cp.py CP/
COPY CP/cp.mzn ./
COPY CP/cp.dzn ./

COPY MIP/mip.py MIP/
COPY MIP/mip.dat ./
COPY MIP/mip.mod ./

COPY SAT/sat.py SAT/

COPY SMT/smt.py SMT/

CMD ["./main.sh","main.py", "CP/cp.py", "MIP/mip.py", "SAT/sat.py"] # "/bin/bash",
# CMD ["/bin/bash"]

#TODO: docker installs python version 3.12 but it employes python 3.8 for some reason => Understand what's going on
