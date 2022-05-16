import json
import os
import shutil
from os import listdir

from colorama import Fore

from core.bot.evaluation import dataset_evaluator
from core.bot.evaluation.dataset_evaluator import EvaluationResult
from core.bot.logic.wallet_handler import TestWallet
from core.utils import lib


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

        args["initialized"] = True

    genome = []
    for i, (k, v) in enumerate(parameters.items()):
        genome.append(random.uniform(v["lower_bound"], v["upper_bound"]))
    return genome


def calculate_fitness(test_results: [EvaluationResult]) -> float:
    """Calculate the fitness of a strategy TestResult"""
    a = 1
    b = 1
    c = 2
    fitness = 0
    for t in test_results:
        if t is not None:
            fitness += a * t.result_percentage + b * t.estimated_apy + c * t.win_ratio * 100
    return fitness


def iteration_report(val, progress, iteration_progress, lock):
    iteration_progress.value += val
    progress.set_step(iteration_progress.value)
    pass


def evaluate_single(args, data, c) -> EvaluationResult:
    initial_balance = 1000
    strategy_class = args.get("strategy_class")
    timeframe = args.get("timeframe")
    parameters = args.get("parameters")
    unique_progress = args.get("unique_progress")
    iteration_progress = args.get("iteration_progress")
    lock = args.get("lock")

    params = {}
    for i, (k, v) in enumerate(parameters.items()):
        params[k] = c[i]

    strategy = strategy_class(TestWallet.factory(initial_balance), **params)
    result, _, _ = dataset_evaluator.evaluate(strategy, initial_balance, data,
                                              timeframe = timeframe,
                                              progress_reporter_span = 8640,
                                              progress_delegate = lambda val: iteration_report(val, unique_progress, iteration_progress, lock))
    return result


def evaluator(candidates, args):
    """Evaluate the candidates"""

    cache_path = args.get("cache_path")
    parameters = args.get("parameters")
    datasets = args.get("datasets")
    job_index = args.get("job_index")
    lock = args.get("lock")
    fitnesses = []
    results = []

    for i, c in enumerate(candidates):
        # with concurrent.futures.ThreadPoolExecutor() as executor:
        #     num = len(datasets)
        #     thread_results = executor.map(evaluate_single, itertools.repeat(args, num), datasets, itertools.repeat(c, num))
        #     for r in thread_results:
        #         results.append(r)
        for d in datasets:
            results.append(evaluate_single(args, d, c))

        fit = calculate_fitness(results)
        fitnesses.append(fit)
        lock.acquire()
        path = cache_path + str(job_index.value) + ".json"
        try:
            dics = {str(i): vars(r) for i, r in enumerate(results)}
            dic = {"fitness": fit, "index": job_index.value, "genome": dict([(p[1], p[0]) for p in zip(c, parameters)])}
            dics["data"] = dic
            with open(path, "w") as file:
                file.write(json.dumps(dics, default = lambda x: None, indent = 4))
        finally:
            job_index.value += 1
            lock.release()
    return fitnesses


def gaussian_adj_mutator(random, candidates, args):
    """Apply the mutation operator on all candidates"""
    bound = args.get("_ec").bounder
    parameters = args.get("parameters")
    mutation_rate = args.get("mutation_rate")
    values = list(parameters.values())
    for i, cs in enumerate(candidates):
        for j, g in enumerate(cs):
            if random.random() > mutation_rate:
                continue
            mean = (values[j]["upper_bound"] - values[j]["lower_bound"]) / 2
            stdv = (values[j]["upper_bound"] - values[j]["lower_bound"]) / 14
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
    max_fitness = args.get("max_fitness", 0)
    unique_progress = args.get("unique_progress")
    unique_progress.dispose()
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

    results.sort(key = lambda elem: float(elem["data"]["fitness"]), reverse = True)
    generation_champ_fit = float(results[0]["data"]["fitness"])
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
    print(Fore.RESET)

    # Prepare for new generation
    print("\nStarting generation {0}".format(num_generations + 1))


def bounder(candidate, args):
    """Bound the candidate genome with respect to the strategy parameters"""
    parameters = args.get("parameters")
    values = list(parameters.values())
    for i, g in enumerate(candidate):
        lower = values[i]["lower_bound"]
        upper = values[i]["upper_bound"]
        g = g if g > lower else lower
        g = g if g < upper else upper
        candidate[i] = g
    return candidate
