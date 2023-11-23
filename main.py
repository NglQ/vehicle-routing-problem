import sys
import os

print("Python version:", sys.version, '\n')
module_path = os.path.dirname(os.path.realpath(__file__))

from CP.cp import cp_model
from instance_builder import generate_instances


if __name__ == '__main__':
    generate_instances()

    info_text = \
        "\nCDMO-project (Bellatreccia, Fusa, Quarta)\n\n" \
        "TODO: write info text\n\n" \
        "Make a choice:\n" \
        "1. Run a single instance on a single model\n" \
        "2. Run all instances on all models\n"

    print(info_text)

    choice = input("Choice (1 or 2): ")
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
            "2. MIP\n" \
            "3. SAT\n" \
            "4. SMT\n"

        print(info_text)
        model_choice = input("Choice (1, 2, 3 or 4): ")
        model_choice = int(model_choice)

        if model_choice == 1:
            instance_file = os.path.join(module_path, f'CP/instances/cp_inst{instance}.dzn')
            solvers = ['gecode', 'chuffed']
            time_limit = 300
            statistics = dict()
            for solver in solvers:
                sym_break_solve, temp_text1 = False, 'without'
                for _ in range(2):
                    print(f'Solving {instance_file} - CP model {temp_text1} symmetry breaking - {solver} ...')

                    stats = cp_model(instance_file, solver, time_limit, sym_break=sym_break_solve)
                    if not sym_break_solve:
                        sym_break_solve, temp_text1 = True, 'with'

                    is_optimal, time = stats['optimal'], stats['time']
                    temp_text2 = 'was' if is_optimal else 'was not'
                    print(f'Solver stopped. An optimal solution {temp_text2} found after {time} seconds.')

                # TODO: Save statistics
                # stats[solver] = statistics
                #
                # json_name = ins_file[ins_file.find('.') - 2:ins_file.find('.')]
                # json_name = json_name if json_name[0] != '0' else json_name[-1]
                #
                # json.dump(stats, open(f'./res/CP/{json_name}.json', 'w+' if i == 0 else 'a+'))
        elif model_choice == 2:
            # TODO: implement
            raise NotImplementedError("MIP not implemented yet")
        elif model_choice == 3:
            # TODO: implement
            raise NotImplementedError("SAT not implemented yet")
        elif model_choice == 4:
            # TODO: implement
            raise NotImplementedError("SMT not implemented yet")
        else:
            raise ValueError("Invalid choice")

    elif choice == 2:
        # TODO: implement
        raise NotImplementedError("Not implemented yet")
    else:
        raise ValueError("Invalid choice")
