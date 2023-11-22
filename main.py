import sys
import os

print("python version: ", sys.version)

sys.path.insert(0, './MIP')
sys.path.insert(0, './CP')
sys.path.insert(0, './SAT')
sys.path.insert(0, './SMT')

from instance_builder import generate_instances
from cp import cp_model
from mip import mip_model
from sat import sat_model
from smt import smt_model

if not(os.path.exists('./MIP/instances')) or not(os.path.exists('./CP/instances')):
    generate_instances()

choice = {'cp': cp_model, 'mip': mip_model, 'sat': sat_model, 'smt': smt_model, 'exit': exit}
actual_choice = input('choose a model:\n\tcp\n\tmip\n\tsat\n\tsmt\n\n\t')
choice.get(actual_choice, lambda: print('Choice not available!!!'))()