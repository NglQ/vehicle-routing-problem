FROM ubuntu:22.04

RUN apt-get update
RUN apt-get install -y software-properties-common
RUN apt-get install -y keyboard-configuration
RUN apt-get install -y libgl1-mesa-dev
RUN apt-add-repository ppa:deadsnakes/ppa
RUN apt-get update

ENV TZ=Europe/Rome
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

RUN apt-get install -y tzdata
RUN apt-get install -y python3.11-dev

RUN apt-get install -y python3-pip

RUN apt-get install -y wget

RUN python3.11 -m pip install minizinc
RUN python3.11 -m pip install minizinc[dzn]
RUN python3.11 -m pip install numpy
RUN python3.11 -m pip install z3-solver

RUN python3.11 -m pip install amplpy
RUN python3.11 -m pip install pysmt
RUN python3.11 -m pip install swig

RUN pysmt-install --confirm-agreement --picosat
RUN pysmt-install --confirm-agreement --bdd

RUN mkdir cdmo-test

WORKDIR ./cdmo-test

RUN mkdir -p ./res/MIP ./res/CP ./res/SAT ./res/SMT

RUN wget -O ampl.linux64.tgz https://portal.ampl.com/external/?url=https://portal.ampl.com/dl/amplce/ampl.linux64.tgz
RUN tar -xvf ampl.linux64.tgz

COPY ampl.lic ./ampl.linux-intel64

RUN wget https://github.com/MiniZinc/MiniZincIDE/releases/download/2.7.5/MiniZincIDE-2.7.5-bundle-linux-x86_64.tgz
RUN tar -xvf MiniZincIDE-2.7.5-bundle-linux-x86_64.tgz

COPY main.sh \
     main.py ./

COPY converter.py ./
COPY instance_builder.py ./

RUN chmod +x main.sh

RUN mkdir CP MIP SAT SMT

COPY instances ./instances/

COPY CP/instances ./CP/instances/
COPY CP/cp.py ./CP
COPY CP/cp.mzn ./CP
COPY CP/cp.dzn ./CP

COPY MIP/instances ./MIP/instances/
COPY MIP/mip.py MIP/
COPY MIP/mip.dat ./MIP
COPY MIP/mip.mod ./MIP

COPY SAT/sat.py SAT/

COPY SMT/smt.py SMT/

# CMD ["./main.sh","main.py", "CP/cp.py", "MIP/mip.py", "SAT/sat.py"] # "/bin/bash",
CMD ["/bin/bash"]
