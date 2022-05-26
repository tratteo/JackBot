import json
from multiprocessing.managers import SyncManager
from os import listdir
from random import Random
from time import time

import inspyred
from inspyred.ec import Individual

from core.evolutionary.operators.controllers import validation_terminator, strategy_observer, strategy_generator, strategy_genome_bounder
from core.evolutionary.operators.evaluators import strategy_evaluator
from core.evolutionary.operators.variators import gaussian_adj_mutator
from core.utils import lib
from core.utils.lib import ProgressBar


def evolve_parallel(parameters_json, dataset_path, **kwargs) -> Individual:
    pop_size = int(kwargs.get("pop_size"))
    generations = int(kwargs.get("generations", int(pop_size / 2)))
    mutation_rate = float(kwargs.get("mutation_rate"))
    validation_set_path = kwargs.get("validation_set_path", None)
    crossover_rate = float(kwargs.get("crossover_rate"))
    processes = int(kwargs.get("processes"))
    tournament_size = int(kwargs.get("tournament_size"))
    validation_set_counter_threshold = int(kwargs.get("validation_set_counter_threshold"))
    validation_set_frequency = int(kwargs.get("validation_set_frequency"))
    cache_path = kwargs.get("cache_path", ".cache/")
    reports_path = kwargs.get("reports_path", ".cache/reports/")
    fitness_report_file = kwargs.get("fitness_report_file", "fitness_report.csv")

    rand = Random()
    rand.seed(int(time()))
    onlyfiles = [f for f in listdir(dataset_path) if f.endswith(".CSV") or f.endswith(".csv")]
    print("Found {0} files in {1}".format(len(onlyfiles), dataset_path))
    datasets = {}
    total_length = 0

    for f in onlyfiles:
        print("Loading {0}...".format(f), flush = True)
        data = lib.dynamic_load_data(dataset_path + "//" + f)
        if len(data) > 1_000_000:
            print("O.O that was a big file")
        datasets[f] = data
        total_length += len(data)
    unique_progress = ProgressBar.create(total_length * pop_size).width(100).build()

    validation_set = []
    if validation_set_path is not None:
        onlyfiles = [f for f in listdir(validation_set_path) if f.endswith(".CSV") or f.endswith(".csv")]
        for f in onlyfiles:
            print("Loading validation {0}...".format(f), flush = True)
            data = lib.dynamic_load_data(validation_set_path + "//" + f)
            if len(data) > 1_000_000:
                print("O.O that was a big file")
            validation_set.append(data)

    # Create EA
    ec = inspyred.ec.EvolutionaryComputation(rand)
    ec.terminator = [inspyred.ec.terminators.generation_termination, validation_terminator]
    ec.variator = [gaussian_adj_mutator, inspyred.ec.variators.uniform_crossover]
    ec.selector = inspyred.ec.selectors.tournament_selection
    ec.replacer = inspyred.ec.replacers.plus_replacement
    ec.observer = strategy_observer

    with SyncManager() as sync_manager:
        # Evolve
        print("Starting evolutionary computation\nParameters: {0}\n".format(json.dumps(kwargs, indent = 4)), flush = True)

        final_pop = ec.evolve(
            # Inspyred
            evaluator = inspyred.ec.evaluators.parallel_evaluation_mp,
            generator = strategy_generator,
            bounder = strategy_genome_bounder,
            mp_evaluator = strategy_evaluator,
            mp_num_cpus = processes,
            maximize = True,
            pop_size = pop_size,
            max_generations = generations,
            # Variation
            mutation_rate = mutation_rate,
            crossover_rate = crossover_rate,
            # Selection
            num_selected = pop_size,
            tournament_size = tournament_size,
            # Synchronization
            iteration_progress = sync_manager.Value("I", 0),
            job_index = sync_manager.Value("I", 0),
            lock = sync_manager.Lock(),
            # Validation
            validation_set = validation_set,
            validation_set_counter_threshold = validation_set_counter_threshold,
            validation_set_frequency = validation_set_frequency,
            # Data and reports
            datasets = datasets,
            unique_progress = unique_progress,
            cache_path = cache_path,
            reports_path = reports_path,
            fitness_report_file = fitness_report_file,
            # Strategy
            strategy_class = lib.load_strategy_module(parameters_json["strategy"]),
            timeframe = lib.get_minutes_from_flag(parameters_json["timeframe"]),
            genome = parameters_json["genome"],
            general_params = parameters_json["parameters"])

    # Sort and print the best individual, who will be at index 0.
    final_pop.sort(reverse = True)
    print('Terminated due to {0}.'.format(ec.termination_cause))
    return final_pop[0]
