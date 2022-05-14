import json
import math
import os
import shutil
from os import listdir

import numpy
from colorama import Fore

from core import lib
from core.bot import dataset_evaluator
from core.bot.dataset_evaluator import TestResult
from core.bot.wallet_handler import TestWallet
from core.lib import ProgressBar


def __retrieve_dataset(args, num_generations) -> (int, numpy.ndarray, ProgressBar):
    dataset_epochs = args.get("dataset_epochs")
    datasets = args.get("datasets")
    progresses = args.get("progresses")
    dataset_index = math.floor(num_generations / dataset_epochs) % (len(datasets))
    return dataset_index, datasets[dataset_index], progresses[dataset_index]


def generator(random, args):
    """Generate the population"""
    initialized = args.get("initialized", False)
    parameters = args.get("parameters")
    if not initialized:
        cache_path = args.get("cache_path")

        if os.path.exists(cache_path):
            shutil.rmtree(cache_path)
        lib.create_folders_in_path(args.get("cache_path"))
        lib.create_folders_in_path(args.get("cache_path") + "champion/")

        onlyfiles = [f for f in listdir(cache_path) if f.endswith(".JSON") or f.endswith(".json")]
        for f in onlyfiles:
            os.remove(os.path.join(cache_path, f))

        # _, _, progress = __retrieve_dataset(args)
        # progress.render()
        args["initialized"] = True

    genome = []
    for b in parameters:
        genome.append(random.uniform(b["lower_bound"], b["upper_bound"]))
    return genome


def calculate_fitness(test_result: TestResult) -> float:
    """Calculate the fitness of a strategy TestResult"""
    a = 2
    b = 1
    c = 0.005

    fitness = test_result.result_percentage
    # fitness = math.log(math.exp(a * test_result.win_ratio + b * test_result.average_result_percentage) + c * test_result.closed_positions)
    return fitness


def iteration_report(val, progress, iteration_progress):
    iteration_progress.value += val
    progress.set_step(iteration_progress.value)
    pass


def evaluator(candidates, args):
    """Evaluate the candidates"""
    initial_balance = 1000
    fitnesses = []

    cache_path = args.get("cache_path")
    parameters = args.get("parameters")
    current_generation = args.get("current_generation")

    index, evaluate_data, progress = __retrieve_dataset(args, current_generation.value)
    timeframe = args.get("timeframe")
    strategy_class = args.get("strategy_class")
    job_index = args.get("job_index")
    iteration_progress = args.get("iteration_progress")
    lock = args.get("lock")

    # Safe since the evaluation is parallel
    for i, c in enumerate(candidates):
        strategy = strategy_class(TestWallet.factory(initial_balance), **dict([(p[1]["name"], p[0]) for p in zip(c, parameters)]))

        result, _, _ = dataset_evaluator.evaluate(strategy, initial_balance, evaluate_data, timeframe = timeframe, progress_delegate = lambda val: iteration_report(val, progress, iteration_progress))
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
            # progress.set_step(job_index.value)
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

    lock = args.get("lock")
    index, dataset, progress = __retrieve_dataset(args, num_generations)
    max_fitness = args.get("max_fitness", 0)

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

    print("Dataset index {0}".format(index))
    print("Evaluating {0} test results".format(len(results)))

    results.sort(key = lambda elem: float(elem["fitness"]), reverse = True)
    generation_champ_fit = float(results[0]["fitness"])
    champion = json.dumps(results[0], indent = 4)
    if generation_champ_fit > max_fitness:
        args["max_fitness"] = generation_champ_fit
        with open(cache_path + "champion/champ.json", "w") as file:
            file.write(champion)

    print('{0}Champion: \n{1}'.format(Fore.GREEN, champion))
    with open(cache_path + "champion/generation" + str(num_generations) + "champ.json", "w") as file:
        file.write(champion)
    args.get("job_index").value = 0
    args.get("iteration_progress").value = 0
    args.get("current_generation").value = num_generations
    print(Fore.RESET)

    # Prepare for new generation
    print("\nStarting generation {0}".format(num_generations + 1))
    next_index, next_dataset, next_progress = __retrieve_dataset(args, num_generations + 1)
    next_progress.render()


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
