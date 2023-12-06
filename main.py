import sys
import os
import json

print("Python version:", sys.version, '\n')
module_path = os.path.dirname(os.path.realpath(__file__))

from CP.cp import cp_model
from SAT.sat import sat_model
from SMT.smt import smt_model
from MIP.mip import mip_model
from instance_builder import generate_instances

models = {
    'CP': (cp_model, ['gecode', 'chuffed']),
    'SAT': (sat_model, ['z3']),
    'SMT': (smt_model, ['z3', 'msat']),
    'MIP': (mip_model, ['highs', 'scip'])
}


def solve_instances(model_function: callable, instances: list[str], solvers: list[str], time_limit: int, res_folder: str):
    # Infer model name
    model_name = model_function.__name__.split('_')[0].upper()
    assert model_name in ['CP', 'SAT', 'SMT', 'MIP'] and model_function.__name__.endswith('_model')

    for instance in instances:
        if model_name == 'CP':
            instance_file = os.path.join(module_path, f'CP/instances/cp_inst{instance}.dzn')
        elif model_name == 'SAT' or model_name == 'SMT':
            instance_file = os.path.join(module_path, f'instances/inst{instance}.dat')
        elif model_name == 'MIP':
            instance_file = os.path.join(module_path, f'MIP/instances/mip_inst{instance}.dat')

        statistics = dict()
        for solver in solvers:
            sym_break_solve, temp_text1 = False, 'without'
            for _ in range(2):
                print(f'Solving {instance_file} - {model_name} model {temp_text1} symmetry breaking - {solver} ...')
                stats_entry_name = solver + '_' + temp_text1 + '_symbreak'

                stats = model_function(instance_file, solver, time_limit, sym_break=sym_break_solve)
                if stats is None:
                    print(f'Solver not started. No solution found.')
                    continue
                if not sym_break_solve:
                    sym_break_solve, temp_text1 = True, 'with'

                try:
                    is_optimal, time = stats['optimal'], stats['time']
                except:
                    is_optimal, time = False, -1
                temp_text2 = 'was' if is_optimal else 'was not'
                print(f'Solver stopped. An optimal solution {temp_text2} found after {time} seconds.')

                statistics[stats_entry_name] = stats

        json_file = os.path.join(module_path,
                                 f'{res_folder}/{model_name}/{instance if instance[0] != "0" else instance[1]}.json')
        os.makedirs(os.path.dirname(json_file), exist_ok=True)
        try:
            json.dump(statistics, open(json_file, 'w+'))
        except:
            pass


if __name__ == '__main__':
    generate_instances()

    # TODO: write some info text about how to use the program
    info_text = \
        "\nCDMO-project (Bellatreccia, Fusa, Quarta)\n\n" \
        "TODO: write info text\n\n" \
        "Make a choice:\n" \
        "1. Run a single instance on a single model\n" \
        "2. Run multiple instances on a single model\n" \
        "3. Run all instances on all models\n"

    print(info_text)

    choice = input("Choice (1, 2 or 3): ")
    choice = int(choice)

    if choice == 1:
        # Choose instance
        instance = input("Make a choice for the instance (from 1 to 21): ")
        instance = int(instance)
        if not (1 <= instance <= 21):
            raise ValueError("Invalid choice")
        instance = str(instance) if instance >= 10 else '0' + str(instance)

        # Choose model
        info_text = \
            "\nMake a choice for the model:\n" \
            "1. CP\n" \
            "2. SAT\n" \
            "3. SMT\n" \
            "4. MIP\n"

        model_map = {1: 'CP', 2: 'SAT', 3: 'SMT', 4: 'MIP'}

        print(info_text)
        model_choice = input("Choice (1, 2, 3 or 4): ")
        model_choice = int(model_choice)
        if not (1 <= model_choice <= 4):
            raise ValueError("Invalid choice")

        model_function, solvers = models[model_map[model_choice]]
        solve_instances(model_function, [instance], solvers, 300, 'res_single')

    elif choice == 2:
        # Choose multiple instances
        info_text = \
            "\nMake a choice for the instances (from 1 to 21 separated by spaces).\n" \
            "Input example: 1 3 11 21 (for instances 1, 3, 11 and 21).\n" \
            "Make a choice: "
        instances = input(info_text)
        instances = instances.split(' ')
        try:
            instances = [int(x) for x in instances]
        except ValueError:
            raise ValueError("Invalid choice")
        for i in instances:
            if not (1 <= i <= 21):
                raise ValueError("Invalid choice")
        instances = [str(i) if i >= 10 else '0' + str(i) for i in instances]

        # Choose model
        info_text = \
            "\nMake a choice for the model:\n" \
            "1. CP\n" \
            "2. SAT\n" \
            "3. SMT\n" \
            "4. MIP\n"

        model_map = {1: 'CP', 2: 'SAT', 3: 'SMT', 4: 'MIP'}

        print(info_text)
        model_choice = input("Choice (1, 2, 3 or 4): ")
        model_choice = int(model_choice)
        if not (1 <= model_choice <= 4):
            raise ValueError("Invalid choice")

        model_function, solvers = models[model_map[model_choice]]

        solve_instances(model_function, instances, solvers, 300, 'res_multiple')

    elif choice == 3:
        # TODO: implement
        raise NotImplementedError("Not implemented yet")
    else:
        raise ValueError("Invalid choice")
