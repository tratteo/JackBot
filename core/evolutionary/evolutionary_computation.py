from multiprocessing.managers import SyncManager
from random import Random
from time import time

import inspyred
from inspyred.ec import Individual
from numpy import genfromtxt

from core.evolutionary.operators import *
from core.utils.lib import ProgressBar


def evolve_parallel(parameters_json, dataset_path, **kwargs) -> Individual:
    pop_size = int(kwargs.get("pop_size"))
    generations = int(kwargs.get("generations", int(pop_size / 2)))
    mutation_rate = float(kwargs.get("mutation_rate"))
    crossover_rate = float(kwargs.get("crossover_rate"))
    processes = int(kwargs.get("processes"))

    rand = Random()
    rand.seed(int(time()))
    onlyfiles = [f for f in listdir(dataset_path) if f.endswith(".CSV") or f.endswith(".csv")]
    print("Found {0} files in {1}".format(len(onlyfiles), dataset_path))
    datasets = {}
    total_length = 0
    delimiter = lib.get_delimiter(dataset_path + "//" + onlyfiles[0])
    for f in onlyfiles:
        # datasets.append(genfromtxt(dataset_path + "//" + f, delimiter = config.DEFAULT_DELIMITER))
        print("Loading {0}...".format(f), flush = True)
        data = genfromtxt(dataset_path + "//" + f, delimiter = delimiter)
        if len(data) > 1_000_000:
            print("O.O that was a big file")
        datasets[f] = data
        total_length += len(data)
    unique_progress = ProgressBar.create(total_length * pop_size).width(100).build()

    # Create EA
    ec = inspyred.ec.EvolutionaryComputation(rand)
    ec.terminator = [inspyred.ec.terminators.generation_termination]
    ec.variator = [gaussian_adj_mutator, inspyred.ec.variators.uniform_crossover]
    ec.selector = inspyred.ec.selectors.tournament_selection
    ec.replacer = inspyred.ec.replacers.plus_replacement
    ec.observer = observer

    with SyncManager() as sync_manager:
        # Evolve
        print("Starting evolutionary computation\nParameters: {0}\n".format(kwargs), flush = True)

        final_pop = ec.evolve(
            # Operators
            evaluator = inspyred.ec.evaluators.parallel_evaluation_mp,
            generator = generator,
            bounder = bounder,
            mp_evaluator = evaluator,
            mp_num_cpus = processes,
            # Parameters
            maximize = True,
            pop_size = pop_size,
            max_generations = generations,
            # Variation
            mutation_rate = mutation_rate,
            crossover_rate = crossover_rate,
            # Selection
            num_selected = pop_size,
            tournament_size = int(8),
            # Synchronization
            iteration_progress = sync_manager.Value("I", 0),
            job_index = sync_manager.Value("I", 0),
            lock = sync_manager.Lock(),
            # Data and reports
            datasets = datasets,
            unique_progress = unique_progress,
            cache_path = ".cache/",
            reports_path = ".cache/reports/",
            fitness_report_file = "fitness_report.csv",
            # Strategy
            strategy_class = lib.load_strategy_module(parameters_json["strategy"]),
            timeframe = lib.get_minutes_from_flag(parameters_json["timeframe"]),
            genome = parameters_json["genome"],
            general_params = parameters_json["parameters"])

    # Sort and print the best individual, who will be at index 0.
    final_pop.sort(reverse = True)
    print('Terminated due to {0}.'.format(ec.termination_cause))
    return final_pop[0]
