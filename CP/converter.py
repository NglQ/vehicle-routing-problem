import numpy as np

with open('inst01.txt', 'r') as f:
    matrix = ''
    for i, line in enumerate(f):
        match i:
            case 0:
                m = int(line)
            case 1:
                n = int(line)
            case 2:
                l = [int(x) for x in line.split(' ')]
            case 3:
                p = [int(x) for x in line.split(' ')]

        if i > 3:
            matrix += line[:-1] + '; '

d = np.matrix(matrix[:-2]).tolist()
