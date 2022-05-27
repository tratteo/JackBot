import json
import math

from core.bot.evaluation import dataset_evaluator
from core.bot.evaluation.dataset_evaluator import EvaluationResult
from core.bot.logic.wallet_handler import TestWallet


def calculate_fitness(results: list[EvaluationResult]) -> float:
    """Calculate the fitness of a strategy TestResult"""
    a = 0.65
    g = 3.75
    d = 1.75
    fitness = 0
    for i, result in enumerate(results):
        r = result.result_ratio
        wr = result.win_ratio
        penalizing_factor = 1
        wr_penalize = 1
        if r < 1:
            penalizing_factor = math.pow(r, g)
        if wr < 0.5:
            wr_penalize = math.pow(wr + 0.5, d)
        fac2 = penalizing_factor * math.pow(r + 1, a)
        fac3 = wr_penalize * math.pow(wr + 1, 1 - a)
        result_fit = fac2 + fac3
        fitness += 365 * result_fit / result.days
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

    minutes = int(len(data) / 3)
    strategy = strategy_class(TestWallet.factory(initial_balance), params, **general_params)
    result, _, _ = dataset_evaluator.evaluate(strategy, initial_balance, data,
                                              timeframe = timeframe,
                                              progress_reporter_span = minutes,
                                              progress_delegate = None,
                                              report_residual = False,
                                              progress_delegate_args = args)

    return result


def strategy_evaluator(candidates, args):
    """Evaluate the candidates"""

    cache_path = args.get("cache_path")
    genome = args.get("genome")
    datasets = args.get("datasets")
    job_index = args.get("job_index")
    lock = args.get("lock")
    fitnesses = []

    for i, c in enumerate(candidates):
        simulations = {}
        results = []
        for _, (k, v) in enumerate(datasets.items()):
            res = evaluate_single(args, v, c)

            results.append(res)
            simulations[k] = res
        fit = calculate_fitness(results)
        fitnesses.append(fit)
        with lock:
            val = job_index.value
            job_index.value = val + 1
        path = cache_path + str(val) + ".json"
        dics = {}
        for _, (k, v) in enumerate(simulations.items()):
            sim_dic = vars(v)
            dics[k] = sim_dic
        dic = {"fitness": fit, "index": val, "genome": dict([(p[1], p[0]) for p in zip(c, genome)])}
        dics["data"] = dic
        with open(path, "w") as file:
            file.write(json.dumps(dics, default = lambda x: None, indent = 4))

    return fitnesses
