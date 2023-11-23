import numpy as np


def convert(filename: str) -> tuple:
    print('Parsing ' + filename + '...')
    with open(filename, 'r') as f:
        matrix = ''
        for i, line in enumerate(f):
            if i == 0:
                m = int(line)
            elif i == 1:
                n = int(line)
            elif i == 2:
                l = [int(x) for x in line.split(' ')]
            elif i == 3:
                p = [int(x) for x in line.split(' ')]
            else:
                matrix += line[:-1] + '; '

    d = np.matrix(matrix[:-2]).tolist()

    return m, n, l, p, d


def generate_cp_dzn(output_filename: str, m: int, n: int, l: list, p: list, d: list):
    n_nodes = len(p)
    e = n_nodes * (n_nodes + 1)
    depot_1 = n_nodes + 1    # outgoing edges
    depot_2 = n_nodes + 2    # incoming edges

    indexes = [(i, j) for i in [depot_1] + list(range(1, depot_1))
               for j in range(1, n_nodes + 3) if i != j and j != depot_1 and (i, j) != (depot_1, depot_2)]

    w = [d[i-1][j-1] for i, j in map(lambda x: x if x[1] != depot_2 else (x[0], depot_1), indexes)]
    _from = [i for i, j in indexes]
    _to = [j for i, j in indexes]

    assert len(w) == e

    with open(output_filename, 'w') as f:
        f.write('M = %d;\n' % m)
        f.write('N = %d;\n' % (n_nodes + 2))
        f.write('E = %d;\n' % e)
        f.write('l = %s;\n' % str(l))
        f.write('p = %s;\n' % str(p))

        f.write('from = %s;\n' % str(_from))
        f.write('to = %s;\n' % str(_to))
        f.write('w = %s;\n' % str(w))

    return indexes


def generate_mip_dzn(output_filename: str, m: int, n: int, l: list, p: list, d: list):
    with open(output_filename, 'w') as f:
        f.write('m = %d;\n' % m)
        f.write('n = %d;\n' % n)
        f.write('l = %s;\n' % str(l))
        f.write('w = %s;\n' % str(p))

        matrix = '[|\n'
        for i in range(n + 1):
            matrix += '\t' + str(d[i])[1:-1] + ' |\n'
        matrix = matrix[:-1] + ']'

        f.write('D = %s;\n' % matrix)
        

def generate_mip_dat(output_filename: str, m: int, n: int, l: list, p: list, d: list):
    with open(output_filename, 'w') as f:
        f.write('data;\n')
        f.write('param K := %d;\n' % m)
        f.write('param N := %d;\n' % n)
        f.write('param C := \n\t%s;\n' % '\n\t'.join([f'{i+1} {j}' for i,j in enumerate(l)]))
        f.write('param L := \n\t%s;\n' % '\n\t'.join([f'{i+1} {j}' for i,j in enumerate(p)]))
        f.write(f'param D:  {"  ".join(map(str,range(1,n+2)))} :=\n')

        for i in range(n + 1):
            f.write(f'\t{i+1} {str(d[i])[1:-1].replace(",", " ")}\n')
        f.write(';')
