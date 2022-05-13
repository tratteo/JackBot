import json
import math
import os
from os import listdir

from colorama import Fore

from core import lib
from core.bot import dataset_evaluator
from core.bot.dataset_evaluator import TestResult
from core.bot.wallet_handler import TestWallet


def generator(random, args):
    """Generate the population"""
    parameters = args.get("parameters")
    cache_path = args.get("cache_path")
    onlyfiles = [f for f in listdir(cache_path) if f.endswith(".JSON") or f.endswith(".json")]
    for f in onlyfiles:
        os.remove(os.path.join(cache_path, f))
    genome = []
    lib.create_folders_in_path(args.get("cache_path"))
    lib.create_folders_in_path(args.get("cache_path") + "champion/")
    for b in parameters:
        genome.append(random.uniform(b["lower_bound"], b["upper_bound"]))
    args.get("progress").render()
    return genome


def calculate_fitness(test_result: TestResult) -> float:
    """Calculate the fitness of a strategy TestResult"""
    a = 1
    b = 1
    c = 0.5

    # print("S: {0}", s)
    fitness = math.log(math.exp(a * test_result.win_ratio + b * test_result.average_result_percentage) + c * test_result.closed_positions)
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
    lock = args.get("lock")
    progress = args.get("progress")
    # Safe since the evaluation is parallel
    for i, c in enumerate(candidates):
        strategy = strategy_class(TestWallet.factory(initial_balance), **dict([(p[1]["name"], p[0]) for p in zip(c, parameters)]))
        result, _, _ = dataset_evaluator.evaluate(strategy, initial_balance, evaluate_data, timeframe = timeframe)
        fit = 0 if result is None else calculate_fitness(result)
        fitnesses.append(fit)
        lock.acquire()
        path = cache_path + str(job_index.value) + ".json"
        try:
            with open(path, "w") as file:
                # Writing data to a file
                dic = result.get_dic()
                dic["fitness"] = fit
                dic["index"] = job_index.value
                dic["genome"] = dict([(p[1]["name"], p[0]) for p in zip(c, parameters)])
                file.write(json.dumps(dic, default = lambda x: None, indent = 4))
        finally:
            # print("Worker {0} completed".format(job_index.value), end = "\r")
            job_index.value += 1
            progress.set_step(job_index.value)
            lock.release()
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
    cache_path = args.get("cache_path")
    job_index = args.get("job_index")
    lock = args.get("lock")
    progress = args.get("progress")
    progress.dispose()
    results = []
    onlyfiles = [f for f in listdir(cache_path) if f.endswith(".JSON") or f.endswith(".json")]
    lock.acquire()
    for f in onlyfiles:
        path = cache_path + f
        with open(path, "r") as file:
            x = json.loads(file.read())
            results.append(x)
    lock.release()
    print("{0} on {1}".format(strategy_class, lib.get_flag_from_minutes(timeframe)))
    print('Generation {0}, {1} evaluations'.format(num_generations, num_evaluations))

    print("Evaluating {0} test results".format(len(results)))
    results.sort(key = lambda elem: float(elem["fitness"]), reverse = True)
    champion = json.dumps(results[0], indent = 4)
    print('{0}Champion: \n{1}'.format(Fore.GREEN, champion))
    with open(cache_path + "champion/champion.json", "w") as file:
        file.write(champion)
    job_index.value = 0
    print(Fore.RESET)
    print("\nStarting generation {0}".format(num_generations + 1))
    progress.render()


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
