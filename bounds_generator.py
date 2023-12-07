import numpy as np


def generate_lowerbound(n, D):
        distances = []
        for i in range(n):
            distances.append(D[i][n] + D[n][i])
        return max(distances)


def generate_upperbound(n, m, D):
    depot_to_cities = np.array(D[-1][:len(D) - 1])
    cities_to_depot = np.array([D[i][-1] for i in range(len(D) - 1)])
    depot_cities_depot = depot_to_cities + cities_to_depot
    distances_prov = np.sort(depot_cities_depot)
    distances = distances_prov[-m + 1:]
    indices_to_remove = np.argsort(depot_cities_depot)[-m + 1:]

    range_n = [i for i in range(n) if i not in indices_to_remove]
    idx = n
    visited = [idx]
    dist = 0
    while len(range_n) != 0:
        idx = np.argmin(np.array([val if i != idx and i in range_n else np.inf for i, val in enumerate(D[idx])]))
        dist += D[visited[-1]][idx]
        range_n.remove(idx)
        visited.append(idx)

    dist += D[visited[-1]][n]
    return int(max(np.append(distances, dist)))
