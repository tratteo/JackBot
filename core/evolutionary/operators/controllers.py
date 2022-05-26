import csv
import json
import os
import shutil

from core.bot.evaluation import dataset_evaluator
from core.bot.logic.wallet_handler import TestWallet
from core.evolutionary.operators.evaluators import calculate_fitness
from core.utils import lib
from core.utils.lib import ProgressBar


def try_initialize(args):
    if not args.get("initialized", False):
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

        args["validation_set_counter"] = 0
        args["validation_set_fitness"] = 0
        args["initialized"] = True


def strategy_generator(random, args):
    """Generate the population"""
    try_initialize(args)
    genome = args.get("genome")
    individual_genome = []
    for i, (k, v) in enumerate(genome.items()):
        individual_genome.append(random.uniform(v["lower_bound"], v["upper_bound"]))
    return individual_genome


def validation_terminator(population, num_generations, num_evaluations, args):
    validation_set = args.get("validation_set")
    validation_set_frequency = args.get("validation_set_frequency")
    if len(validation_set) > 0 and (num_generations + 1) % validation_set_frequency == 0:
        validation_set_fitness = args.get("validation_set_fitness")
        validation_set_counter_threshold = args.get("validation_set_counter_threshold")
        general_params = args.get("general_params")
        timeframe = args.get("timeframe")
        file = args.get("reports_path") + "generation" + str(num_generations) + "champ.json"

        with open(file, "r") as file:
            gen_champion = json.loads(file.read())
        initial_balance = 1000
        strategy_class = args.get("strategy_class")
        progress = ProgressBar(sum(len(x) for x in validation_set))
        print("Evaluating generation champion on validation set...")
        results = []
        simulations = {"genome": gen_champion["data"]["genome"]}
        for i, val_set in enumerate(validation_set):
            ind = strategy_class(TestWallet.factory(initial_balance), gen_champion["data"]["genome"], **general_params)
            result, _, _ = dataset_evaluator.evaluate(ind, initial_balance, val_set,
                                                      timeframe = timeframe,
                                                      progress_reporter_span = 1440,
                                                      progress_delegate = progress.step)
            dic = vars(result)
            simulations[str(i)] = dic
            results.append(result)
        progress.dispose()
        fit = calculate_fitness(results)
        if fit < validation_set_fitness:
            args["validation_set_counter"] += 1
            print("Negative performance on validation set: {0}\nVSC: {1}\nValidation fitness: {2}".format(fit, args["validation_set_counter"], validation_set_fitness))
        else:
            args["validation_set_fitness"] = fit
            args["validation_set_counter"] = 0
            print("Positive performance on validation set\nVSC: {0}\nValidation fitness: {1}".format(args["validation_set_counter"], fit))
            val_champ_file = args.get("reports_path") + "validation_champ.json"
            with open(val_champ_file, "w") as file:
                file.write(json.dumps(simulations, indent = 4))
        if args["validation_set_counter"] >= validation_set_counter_threshold:
            return True
    print("\n")
    print("-" * 100)
    print("Starting generation {0}".format(num_generations + 1))
    print("Evaluating...")
    return False


def strategy_observer(population, num_generations, num_evaluations, args):
    """Observe the population evolving"""
    print("\nCurrent pop N: {0}".format(len(population)))

    cache_path = args.get("cache_path")
    results = []
    onlyfiles = [f for f in os.listdir(cache_path) if f.endswith(".JSON") or f.endswith(".json")]

    # Read all results
    for f in onlyfiles:
        path = cache_path + f
        with open(path, "r") as file:
            x = json.loads(file.read())
            results.append(x)

    print("{0} on {1}".format(args.get("strategy_class"), lib.get_flag_from_minutes(args.get("timeframe"))))
    print('Generation {0}, {1} evaluations'.format(num_generations, num_evaluations))

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

    # Append fitness reports
    fitness_report_file = args.get("fitness_report_file")
    with open(reports_path + fitness_report_file, 'a+', newline = "") as f:
        writer = csv.writer(f, delimiter = ";")
        row = [float(sum(fitnesses)) / len(fitnesses), generation_champ_fitness, float(results[-1]["data"]["fitness"])]
        writer.writerow(row)

    # Prepare for the next Gen
    args.get("unique_progress").dispose()


def strategy_genome_bounder(candidate, args):
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
