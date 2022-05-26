def gaussian_adj_mutator(random, candidates, args):
    """Apply the mutation operator on all candidates"""
    bound = args.get("_ec").bounder
    genome = args.get("genome")
    mutation_rate = args.get("mutation_rate")
    values = list(genome.values())
    for i, cs in enumerate(candidates):
        for j, g in enumerate(cs):
            if random.random() > mutation_rate:
                continue
            mean = g
            stdv = (values[j]["upper_bound"] - values[j]["lower_bound"]) / 6
            g = random.gauss(mean, stdv)
            candidates[i][j] = g
        candidates[i] = bound(candidates[i], args)
    return candidates


def random_mutator(random, candidates, args):
    """Apply the mutation operator on all candidates"""
    bound = args.get("_ec").bounder
    genome = args.get("genome")
    mutation_rate = args.get("mutation_rate")
    values = list(genome.values())
    for i, cs in enumerate(candidates):
        for j, g in enumerate(cs):
            if random.random() > mutation_rate:
                continue
            g = random.uniform(values[j]["lower_bound"], values[j]["upper_bound"])
            candidates[i][j] = g
        candidates[i] = bound(candidates[i], args)
    return candidates
