import csv
import json
import math
import os
import shutil
from os import listdir

from colorama import Fore

from core.bot.evaluation import dataset_evaluator
from core.bot.evaluation.dataset_evaluator import EvaluationResult
from core.bot.logic.wallet_handler import TestWallet
from core.utils import lib


def try_initialize(args):
    initialized = args.get("initialized", False)
    if not initialized:
        cache_path = args.get("cache_path")
        if os.path.exists(cache_path):
            shutil.rmtree(cache_path)
        reports_path = args.get("reports_path")
        if os.path.exists(reports_path):
            shutil.rmtree(reports_path)

        lib.create_folders_in_path(reports_path)
        lib.create_folders_in_path(cache_path)

        fitness_report_file = args.get("fitness_report_file")

        with open(reports_path + fitness_report_file, 'a+', newline = "") as f:
            writer = csv.writer(f, delimiter = ";")
            row = ["Average", "Best", "Worst"]
            writer.writerow(row)

        args["initialized"] = True


def generator(random, args):
    """Generate the population"""
    try_initialize(args)
    genome = args.get("genome")
    individual_genome = []
    for i, (k, v) in enumerate(genome.items()):
        individual_genome.append(random.uniform(v["lower_bound"], v["upper_bound"]))
    return individual_genome


def calculate_fitness(result: EvaluationResult) -> float:
    """Calculate the fitness of a strategy TestResult"""
    a = 0.35
    g = 2.5
    r = result.initial_balance / result.final_balance
    wr = result.win_ratio
    penalizing_factor = 1
    # Penalizes negative values
    if r < 1:
        penalizing_factor = math.pow(r, g)
    fac2 = math.pow((penalizing_factor * r) + 1, a)
    fac3 = math.pow(wr + 1, 1 - a)
    result_fit = fac2 * fac3
    fitness = result_fit
    return fitness


def iteration_report(val, args):
    unique_progress = args.get("unique_progress")
    iteration_progress = args.get("iteration_progress")
    lock = args.get("lock")
    with lock:
        new_val = iteration_progress.value + val
        iteration_progress.value += val
        unique_progress.set_step(new_val)


def evaluate_single(args, data, c) -> EvaluationResult:
    initial_balance = 1000
    strategy_class = args.get("strategy_class")
    timeframe = args.get("timeframe")
    genome = args.get("genome")
    general_params = args.get("general_params")

    params = {}
    for i, (k, v) in enumerate(genome.items()):
        params[k] = c[i]

    strategy = strategy_class(TestWallet.factory(initial_balance), params, **general_params)
    result, _, _ = dataset_evaluator.evaluate(strategy, initial_balance, data,
                                              timeframe = timeframe,
                                              progress_reporter_span = 172800,
                                              progress_delegate = iteration_report,
                                              progress_delegate_args = args)

    return result


def evaluator(candidates, args):
    """Evaluate the candidates"""

    cache_path = args.get("cache_path")
    genome = args.get("genome")
    datasets = args.get("datasets")
    job_index = args.get("job_index")
    lock = args.get("lock")
    fitnesses = []

    for i, c in enumerate(candidates):
        simulations = {}
        fitness = 0
        for _, (k, v) in enumerate(datasets.items()):
            res = evaluate_single(args, v, c)
            fit = calculate_fitness(res)
            fitness += fit
            simulations[k] = [res, fit]
        fitnesses.append(fitness)
        with lock:
            val = job_index.value
            job_index.value = val + 1
        path = cache_path + str(val) + ".json"
        dics = {}
        for _, (k, v) in enumerate(simulations.items()):
            sim_dic = vars(v[0])
            sim_dic["simulation_fitness"] = v[1]
            dics[k] = sim_dic
        dic = {"fitness": fitness, "index": val, "genome": dict([(p[1], p[0]) for p in zip(c, genome)])}
        dics["data"] = dic
        with open(path, "w") as file:
            file.write(json.dumps(dics, default = lambda x: None, indent = 4))

    return fitnesses


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
            # Set the stdev so that the
            stdv = (values[j]["upper_bound"] - values[j]["lower_bound"]) / 6
            g = random.gauss(mean, stdv)
            candidates[i][j] = g
        candidates[i] = bound(candidates[i], args)
    return candidates


def observer(population, num_generations, num_evaluations, args):
    """Observe the population evolving"""
    print("\nCurrent pop N: {0}".format(len(population)))

    cache_path = args.get("cache_path")
    results = []
    onlyfiles = [f for f in listdir(cache_path) if f.endswith(".JSON") or f.endswith(".json")]

    # Read all results
    for f in onlyfiles:
        path = cache_path + f
        with open(path, "r") as file:
            x = json.loads(file.read())
            results.append(x)

    print("{0} on {1}".format(args.get("strategy_class"), lib.get_flag_from_minutes(args.get("timeframe"))))
    print('Generation {0}, {1} evaluations'.format(num_generations, num_evaluations))
    print("Evaluating {0} test results".format(len(results)))

    results.sort(key = lambda elem: float(elem["data"]["fitness"]), reverse = True)
    fitnesses = [e["data"]["fitness"] for e in results]
    generation_champ_fitness = float(results[0]["data"]["fitness"])
    champion_json = json.dumps(results[0], indent = 4)
    reports_path = args.get("reports_path")

    # Save the fittest
    if generation_champ_fitness > args.get("max_fitness", 0):
        args["max_fitness"] = generation_champ_fitness
        with open(args.get("reports_path") + "champ.json", "w") as file:
            file.write(champion_json)

    # Log the generation champ
    with open(reports_path + "generation" + str(num_generations) + "champ.json", "w") as file:
        file.write(champion_json)
    args.get("job_index").value = 0
    args.get("iteration_progress").value = 0
    print(Fore.RESET)

    # Append fitness reports
    fitness_report_file = args.get("fitness_report_file")
    with open(reports_path + fitness_report_file, 'a+', newline = "") as f:
        writer = csv.writer(f, delimiter = ";")
        row = [float(sum(fitnesses)) / len(fitnesses), generation_champ_fitness, float(results[-1]["data"]["fitness"])]
        writer.writerow(row)

    # Prepare for the next Gen
    args.get("unique_progress").dispose()
    print("-" * 100)
    print("Starting generation {0}".format(num_generations + 1))
    print("Evaluating...")


def bounder(candidate, args):
    """Bound the candidate genome with respect to the strategy genome"""
    genome = args.get("genome")
    values = list(genome.values())
    for i, g in enumerate(candidate):
        lower = values[i]["lower_bound"]
        upper = values[i]["upper_bound"]
        g = g if g > lower else lower
        g = g if g < upper else upper
        candidate[i] = g
    return candidate
