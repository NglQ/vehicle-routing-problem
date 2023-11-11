from converter import convert, generate_cp_dzn, generate_mip_dat
import os


def generate_instances(path_to_instances_folder='./instances'):
    if not(os.path.exists('./CP/instances')):
        os.mkdir('./CP/instances')
    if not(os.path.exists('./MIP/instances')):
        os.mkdir('./MIP/instances')
    instance_files = os.listdir(path_to_instances_folder)
    for ins_file in instance_files:
        m, n, l, p, d = convert(f'{path_to_instances_folder}/{ins_file}')
        generate_cp_dzn(f'./CP/instances/cp_{ins_file[:ins_file.find(".")]}.dzn', m, n, l, p, d)
        generate_mip_dat(f'./MIP/instances/mip_{ins_file}', m, n, l, p, d)
