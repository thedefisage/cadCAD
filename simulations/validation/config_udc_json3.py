from datetime import timedelta
from cadCAD.utils import UDC
from cadCAD.configuration import append_configs
from cadCAD.configuration.utils import ep_time_step, config_sim
from typing import Dict, List


# ToDo: Create member for past value
class MyClassA(object):
    def __init__(self, x):
        self.x = x
        print(f"Instance of MyClass (mem_id {hex(id(self))}) created with value {self.x}")

    def update(self):
        self.x += 1
        print(f"Instance of MyClass (mem_id {hex(id(self))}) has been updated, has now value {self.x}")
        # return self.x
        return self

    def getMemID(self):
        return str(hex(id(self)))

    # can be accessed after an update within the same substep and timestep
    # ToDo: id sensitive to lineage, rerepresent
    def __str__(self):
        # return f"{self.__class__.__name__} - {hex(id(self))} - {self.__dict__}"
        return f"{self.__dict__}"


# a is Correct, and classX's value is Incorrect
# Expected: a == classX's value
# b should be tracking classX's value and a:
#     b should be the same value as the previous classX value and the previous a value
# https://pymotw.com/2/multiprocessing/communication.html
# ccc = MyClassA
# udc = ccc(0)
# print(MyClassA(**udc.__dict__).__dict__)

g: Dict[str, List[MyClassA]] = {'udc': [MyClassA]}

# udcB = MyClassB()

# z = MyClass()
# pointer(z)
# separate thread/process for UCD with async calls to this thread/process

# genesis state
# udc_obj = MyClassA(0)
# hydra = UDC_Wrapper(udc, udc, current_functions=['update'])
# hydra = UDC_Wrapper(udc_obj, functions=['update'])
hydra = UDC(MyClassA(0))
hydra_members = hydra.get_object()

state_dict = {
    'a': 0,
    'b': 0,
    'j': 0,
    "hydra_members": hydra_members,
    'timestamp': '2019-01-01 00:00:00'
}

timestep_duration = timedelta(minutes=1) # In this example, a timestep has a duration of 1 minute.
ts_format = '%Y-%m-%d %H:%M:%S'
def time_model(_g, step, sL, s, _input):
    y = 'timestamp'
    x = ep_time_step(s, dt_str=s['timestamp'], fromat_str=ts_format, _timedelta=timestep_duration)
    return (y, x)


def HydraMembers(_g, step, sL, s, _input):
    y = 'hydra_members'
    obj = s['hydra_members'].obj
    obj.update()
    x = UDC(obj).get_object()
    return (y, x)


def A(_g, step, sL, s, _input):
    y = 'a'
    x = s['a'] + 1
    return (y, x)

def B(_g, step, sL, s, _input):
    y = 'b'
    # x = s['hydra_members']['x']
    x = s['hydra_members'].x
    # x = s['hydra_obj'].x
    return (y, x)


def J(_g, step, sL, s, _input):
    y = 'j'
    # x = s['hydra_members']['x']
    x = s['hydra_members'].x
    # x = s['hydra_obj'].x
    # x = s['hydra_view'].x
    return (y, x)


partial_state_update_blocks = {
    'PSUB1': {
        'behaviors': {
        },
        'states': {
            # 'ca': CA,
            'a': A,
            'b': B,
            # 'hydra': Hydra,
            'hydra_members': HydraMembers,
            # 'hydra_obj': HydraObj,
            # 'hydra_view': HydraView,
            # 'i': I,
            'j': J,
            # 'k': K,
            'timestamp': time_model,
        }
    },
    'PSUB2': {
        'behaviors': {
        },
        'states': {
            # 'ca': CA,
            'a': A,
            'b': B,
            # 'hydra': Hydra,
            'hydra_members': HydraMembers,
            # 'hydra_obj': HydraObj,
            # 'hydra_view': HydraView,
            # 'i': I,
            'j': J,
            # 'k': K,
        }
    },
    'PSUB3': {
        'behaviors': {
        },
        'states': {
            'a': A,
            'b': B,
            # 'hydra': Hydra,
            'hydra_members': HydraMembers,
            # 'hydra_obj': HydraObj,
            # 'hydra_view': HydraView,
            # 'i': I,
            'j': J,
            # 'k': K,
        }
    }
}

sim_config = config_sim({
    "N": 2,
    "T": range(4),
    "M": g
})

append_configs(sim_config, state_dict, {}, {}, {}, partial_state_update_blocks)