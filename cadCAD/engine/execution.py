import threading
from pprint import pprint
from typing import Callable, Dict, List, Any, Tuple
from pathos.multiprocessing import ThreadPool as TPool
# from pathos.multiprocessing import ProcessPool as PPool
import pathos.multiprocessing as mp
from collections import Counter

from cadCAD.utils import flatten

VarDictType = Dict[str, List[Any]]
StatesListsType = List[Dict[str, Any]]
ConfigsType = List[Tuple[List[Callable], List[Callable]]]
EnvProcessesType = Dict[str, Callable]


def single_proc_exec(
    simulation_execs: List[Callable],
    var_dict_list: List[VarDictType],
    states_lists: List[StatesListsType],
    configs_structs: List[ConfigsType],
    env_processes_list: List[EnvProcessesType],
    Ts: List[range],
    SimIDs,
    Ns: List[int],
    ExpIDs: List[int],
    SubsetIDs,
    SubsetWindows,
    configured_n
):
    print(f'Execution Mode: single_threaded')
    params = [
        simulation_execs, states_lists, configs_structs, env_processes_list,
        Ts, SimIDs, Ns, SubsetIDs, SubsetWindows
    ]
    simulation_exec, states_list, config, env_processes, T, sim_id, N, subset_id, subset_window = list(
        map(lambda x: x.pop(), params)
    )
    result = simulation_exec(
        var_dict_list, states_list, config, env_processes, T, sim_id, N, subset_id, subset_window, configured_n
    )
    return flatten(result)


def parallelize_simulations(
    simulation_execs: List[Callable],
    var_dict_list: List[VarDictType],
    states_lists: List[StatesListsType],
    configs_structs: List[ConfigsType],
    env_processes_list: List[EnvProcessesType],
    Ts: List[range],
    SimIDs,
    Ns: List[int],
    ExpIDs: List[int],
    SubsetIDs,
    SubsetWindows,
    configured_n
):

    print(f'Execution Mode: parallelized')
    params = list(
        zip(
            simulation_execs, var_dict_list, states_lists, configs_structs, env_processes_list,
            Ts, SimIDs, Ns, SubsetIDs, SubsetWindows
        )
    )

    len_configs_structs = len(configs_structs)

    unique_runs = Counter(SimIDs)
    sim_count = max(unique_runs.values())
    highest_divisor = int(len_configs_structs / sim_count)

    new_configs_structs, new_params = [], []
    for count in range(len(params)):
        if count == 0:
            new_params.append(
                params[count: highest_divisor]
            )
            new_configs_structs.append(
                configs_structs[count: highest_divisor]
            )
        elif count > 0:
            new_params.append(
                params[count * highest_divisor: (count + 1) * highest_divisor]
            )
            new_configs_structs.append(
                configs_structs[count * highest_divisor: (count + 1) * highest_divisor]
            )

    # new_params = list(filter(None, new_params))
    # for param in list(filter(lambda x: x, new_params)):
    #     print(param)
    # exit()

    def threaded_executor(params):
        # print(len(params))
        # print(params)
        if len_configs_structs > 1:
            # procs = mp.cpu_count()
            # print(len_configs_structs)
            tp = TPool(processes=len_configs_structs)
            results = tp.map(
                lambda t: t[0](t[1], t[2], t[3], t[4], t[5], t[6], t[7], t[8], t[9], configured_n), params
            )
            tp.close()
        else:
            t = params[0]
            results = t[0](t[1], t[2], t[3], t[4], t[5], t[6], t[7], t[8], t[9], configured_n)
        return results

    results = flatten(list(map(lambda params: threaded_executor(params), new_params)))

    # pp = PPool()
    # results = flatten(list(pp.map(lambda params: threaded_executor(params), new_params)))
    results = flatten(list(map(lambda params: threaded_executor(params), new_params)))
    # pp.close()
    # pp.join()
    # pp.clear()
    # pp.restart()

    # def threaded_executor(params):
    #     pprint(len(params))
    #     if len_configs_structs > 1:
    #         def pop_execute(T):
    #             t = T[0]
    #             return [t[0](t[1], t[2], t[3], t[4], t[5], t[6], t[7], t[8], t[9], configured_n)]
    #         tp = TPool()
    #         results = tp.map(lambda T: pop_execute(T), params)
    #         tp.close()
    #     else:
    #         t = params[0]
    #         results = t[0](t[1], t[2], t[3], t[4], t[5], t[6], t[7], t[8], t[9], configured_n)
    #     return results
    #
    # results = flatten(list(threaded_executor(new_params)))

    return results


def local_simulations(
        simulation_execs: List[Callable],
        var_dict_list: List[VarDictType],
        states_lists: List[StatesListsType],
        configs_structs: List[ConfigsType],
        env_processes_list: List[EnvProcessesType],
        Ts: List[range],
        SimIDs,
        Ns: List[int],
        ExpIDs: List[int],
        SubsetIDs,
        SubsetWindows,
        configured_n
    ):
    print(f'SimIDs   : {SimIDs}')
    print(f'SubsetIDs: {SubsetIDs}')
    print(f'Ns       : {Ns}')
    print(f'ExpIDs   : {ExpIDs}')
    config_amt = len(configs_structs)

    try:
        _params = None
        if config_amt == 1: # and configured_n != 1
            _params = var_dict_list[0]
            return single_proc_exec(
                simulation_execs, _params, states_lists, configs_structs, env_processes_list,
                Ts, SimIDs, Ns, ExpIDs, SubsetIDs, SubsetWindows, configured_n
            )
        elif config_amt > 1: # and configured_n != 1 # and config_amt < remote_threshold
            _params = var_dict_list
            return parallelize_simulations(
                simulation_execs, _params, states_lists, configs_structs, env_processes_list,
                Ts, SimIDs, Ns, ExpIDs, SubsetIDs, SubsetWindows, configured_n
            )
        # elif config_amt > 1 and configured_n == 1:
    except ValueError:
        raise ValueError("\'sim_configs\' N must > 0")
