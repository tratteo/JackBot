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

    fitness = math.log(math.exp(a * test_result.win_ratio + b * s) + 1) + math.log(c * len(test_result.closed_positions))
    return fitness


def evaluator(candidates, args):
    """Evaluate the candidates"""
    initial_balance = 1000
    fitnesses = []
    parameters = args.get("parameters")
    evaluate_data = args.get("dataset")
    timeframe = args.get("timeframe")
    strategy_class = args.get("strategy_class")
    for c in candidates:
        strategy = strategy_class(TestWallet.factory(initial_balance), **dict([(p[1]["name"], p[0]) for p in zip(c, parameters)]))
        res = dataset_evaluator.evaluate(strategy, initial_balance, evaluate_data, timeframe = timeframe)
        result, balance, index = res
        fitnesses.append(calculate_fitness(result))
    return fitnesses


def mutator(random, candidates, args):
    """Apply the mutation operator on all candidates"""
    bound = args.get("_ec").bounder
    mutation_rate = args.get("mutation_rate")
    for i, cs in enumerate(candidates):
        for j, g in enumerate(cs):
            if random.random() < mutation_rate:
                g += random.uniform(-1, 1)
                candidates[i][j] = g
        candidates[i] = bound(candidates[i], args)
    return candidates


def observer(population, num_generations, num_evaluations, args):
    """Observe the population evolving"""
    strategy_class = args.get("strategy_class")
    timeframe = args.get("timeframe")
    print("\n{0} on {1}".format(strategy_class, lib.get_flag_from_minutes(timeframe)))
    print('Generation {0}, {1} evaluations'.format(num_generations, num_evaluations))
    parameters = args.get("parameters")
    zipped = zip(population[0].candidate, parameters)
    print('Champion: {0}'.format(population[0].fitness))
    for i, z in enumerate(zipped):
        print('{0}[{1}: {2:.2F}]'.format(Fore.GREEN, z[1]["name"], z[0]), end = "")
        if i < len(parameters) - 1:
            print(' | ', end = "")
    print(Fore.RESET)
    pass


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
