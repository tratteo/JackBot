import math

from colorama import Fore

from core import lib
from core.bot import dataset_evaluator
from core.bot.dataset_evaluator import TestResult
from core.bot.wallet_handler import TestWallet


def generator(random, args):
    """Generate the population"""
    parameters = args.get("parameters")
    genome = []
    for b in parameters:
        genome.append(random.uniform(b["lower_bound"], b["upper_bound"]))
    return genome


def calculate_fitness(test_result: TestResult) -> float:
    """Calculate the fitness of a strategy TestResult"""
    a = 1
    b = 1
    c = 0.5

    s = 0
    for p in test_result.closed_positions:
        s += p.result_percentage
    s /= len(test_result.closed_positions)
    # print("S: {0}", s)
    fitness = math.log(math.exp(a * test_result.win_ratio + b * test_result.total_profit) + c * len(test_result.closed_positions))
    return fitness


def evaluator(candidates, args):
    """Evaluate the candidates"""
    initial_balance = 1000
    fitnesses = []
    num_generations = args.get("num_generations")
    if num_generations is None:
        num_generations = 0
    cache_path = args.get("cache_path")
    parameters = args.get("parameters")
    dataset_epochs = args.get("dataset_epochs")
    datasets = args.get("datasets")
    dataset_index = math.ceil(num_generations / dataset_epochs) % dataset_epochs
    evaluate_data = datasets[dataset_index]
    timeframe = args.get("timeframe")
    strategy_class = args.get("strategy_class")
    job_index = args.get("job_index")

    for i, c in enumerate(candidates):
        strategy = strategy_class(TestWallet.factory(initial_balance), **dict([(p[1]["name"], p[0]) for p in zip(c, parameters)]))
        result, _, _ = dataset_evaluator.evaluate(strategy, initial_balance, evaluate_data, timeframe = timeframe)
        if result is None:
            fitnesses.append(0)
            continue
        fit = calculate_fitness(result)
        fitnesses.append(fit)
        # TODO append test results
        # mp_manager_list.append(result)
        path = cache_path + str(job_index.value) + ".json"
        lib.create_folders_in_path(path)
        with open(path, "w") as file:
            # Writing data to a file
            file.write(result.to_json())
        job_index.value += 1
    return fitnesses


def gaussian_adj_mutator(random, candidates, args):
    """Apply the mutation operator on all candidates"""
    bound = args.get("_ec").bounder
    parameters = args.get("parameters")
    mutation_rate = args.get("mutation_rate")
    for i, cs in enumerate(candidates):
        for j, g in enumerate(cs):
            if random.random() > mutation_rate:
                continue
            mean = (parameters[j]["upper_bound"] - parameters[j]["lower_bound"]) / 2
            stdv = (parameters[j]["upper_bound"] - parameters[j]["lower_bound"]) / 14
            g += random.gauss(mean, stdv)
            candidates[i][j] = g
        candidates[i] = bound(candidates[i], args)
    return candidates


def observer(population, num_generations, num_evaluations, args):
    """Observe the population evolving"""
    print("\nCurrent pop N: {0}".format(len(population)))
    strategy_class = args.get("strategy_class")
    timeframe = args.get("timeframe")

    # TODO read test results
    job_index = args.get("job_index")
    job_index.value = 0
    # mp_manager_list = args.get("mp_manager_list")
    # print("Current tests N: {0}".format(len(mp_manager_list)))
    # best = max(mp_manager_list, key = lambda x: calculate_fitness(x))
    # if best is not None:
    #     print("Best test:\n{0}".format(str(best)))
    # if num_evaluations > 0:
    #     mp_manager_list[:] = []
    #
    print("{0} on {1}".format(strategy_class, lib.get_flag_from_minutes(timeframe)))
    print('Generation {0}, {1} evaluations'.format(num_generations, num_evaluations))
    parameters = args.get("parameters")
    zipped = zip(population[0].candidate, parameters)
    print('Champion: {0}'.format(population[0].fitness))
    for i, z in enumerate(zipped):
        print('{0}[{1}: {2:.2F}]'.format(Fore.GREEN, z[1]["name"], z[0]), end = "")
        if i < len(parameters) - 1:
            print(' | ', end = "")
    print(Fore.RESET)


def bounder(candidate, args):
    """Bound the candidate genome with respect to the strategy parameters"""
    parameters = args.get("parameters")
    for i, g in enumerate(candidate):
        lower = parameters[i]["lower_bound"]
        upper = parameters[i]["upper_bound"]
        g = g if g > lower else lower
        g = g if g < upper else upper
        candidate[i] = g
    return candidate
