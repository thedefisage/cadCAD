from datetime import datetime, timedelta
from decimal import Decimal
from fn.func import curried
import pandas as pd
from pathos.threading import ThreadPool

from SimCAD.utils import groupByKey

class TensorFieldReport:
    def __init__(self, config_proc):
        self.config_proc = config_proc

    # ??? dont for-loop to apply exo_procs, use exo_proc struct
    def create_tensor_field(self, mechanisms, exo_proc, keys=['behaviors', 'states']):
        dfs = [self.config_proc.create_matrix_field(mechanisms, k) for k in keys]
        df = pd.concat(dfs, axis=1)
        for es, i in zip(exo_proc, range(len(exo_proc))):
            df['es' + str(i + 1)] = es
        df['m'] = df.index + 1
        return df


# def s_update(y, x):
#     return lambda step, sL, s, _input: (y, x)
#
#
def state_update(y, x):
    return lambda step, sL, s, _input: (y, x)


def bound_norm_random(rng, low, high):
    # Add RNG Seed
    res = rng.normal((high+low)/2,(high-low)/6)
    if (res<low or res>high):
        res = bound_norm_random(rng, low, high)
    return Decimal(res)


@curried
def proc_trigger(trigger_step, update_f, step):
    if step == trigger_step:
        return update_f
    else:
        return lambda x: x


# accept timedelta instead of timedelta params
t_delta = timedelta(days=0, minutes=0, seconds=30)
def time_step(dt_str, dt_format='%Y-%m-%d %H:%M:%S', _timedelta = t_delta):
    dt = datetime.strptime(dt_str, dt_format)
    t = dt + _timedelta
    return t.strftime(dt_format)


# accept timedelta instead of timedelta params
t_delta = timedelta(days=0, minutes=0, seconds=1)
def ep_time_step(s, dt_str, fromat_str='%Y-%m-%d %H:%M:%S', _timedelta = t_delta):
    if s['mech_step'] == 0:
        return time_step(dt_str, fromat_str, _timedelta)
    else:
        return dt_str


def exo_update_per_ts(ep):
    @curried
    def ep_decorator(fs, y, step, sL, s, _input):
        # print(s)
        if s['mech_step'] + 1 == 1:  # inside f body to reduce performance costs
            if isinstance(fs, list):
                pool = ThreadPool(nodes=len(fs))
                fx = pool.map(lambda f: f(step, sL, s, _input), fs)
                return groupByKey(fx)
            else:
                return fs(step, sL, s, _input)
        else:
            return (y, s[y])
    return {es: ep_decorator(f, es) for es, f in ep.items()}
