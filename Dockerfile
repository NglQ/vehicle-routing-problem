FROM ubuntu:22.04

# docker compose build --build-arg <varname>=<value>
# if build-arg is not specified, the default value below is used
ARG MINIZINC_VERSION=2.7.5

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

RUN mkdir cdmo

WORKDIR ./cdmo

# Install AMPL
RUN wget -O ampl.linux64.tgz https://portal.ampl.com/external/?url=https://portal.ampl.com/dl/amplce/ampl.linux64.tgz
RUN tar -xvf ampl.linux64.tgz
ENV PATH="${PATH}:/cdmo/ampl.linux-intel64"

# Install MiniZinc
RUN wget https://github.com/MiniZinc/MiniZincIDE/releases/download/$MINIZINC_VERSION/MiniZincIDE-$MINIZINC_VERSION-bundle-linux-x86_64.tgz
RUN tar -xvf MiniZincIDE-$MINIZINC_VERSION-bundle-linux-x86_64.tgz
ENV PATH="${PATH}:/cdmo/MiniZincIDE-$MINIZINC_VERSION-bundle-linux-x86_64/bin"
ENV LD_LIBRARY_PATH="${LD_LIBRARY_PATH}:/cdmo/MiniZincIDE-$MINIZINC_VERSION-bundle-linux-x86_64/lib"
ENV QT_PLUGIN_PATH="${QT_PLUGIN_PATH}:/cdmo/MiniZincIDE-$MINIZINC_VERSION-bundle-linux-x86_64/plugins"

# Add the project files to the image
ADD . .

# main.sh is deprecated
# RUN chmod +x main.sh

# Execute the main script when the container starts
RUN echo "python3.11 /cdmo/main.py" >> ~/.bashrc

CMD ["/bin/bash"]
