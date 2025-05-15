# model.py

import re
import random
from copy import deepcopy
from pathlib import Path
from collections import defaultdict

import networkx as nx

from utils import Singleton

# Import julia and make sure everything needed is resolved
import juliapkg
juliapkg.resolve()
from juliacall import Main as jl, convert, VectorValue

jl.seval("using PowerModels")
jl.seval("using JuMP")
jl.seval("using Gurobi")
jl.seval("using Combinatorics")

jl.include("src/utils/cliparser.jl")
jl.include("src/utils/types.jl")

jl.include("src/utils/utils.jl")
jl.include("src/utils/ioutils.jl")
jl.include("src/utils/datautils.jl")
jl.include("src/utils/optimizationutils.jl")

jl.include("src/outer/traditional.jl")
jl.include("src/outer/permutation.jl")
jl.include("src/outer/enumeration.jl")

jl.include("src/outer/greedy-criticality.jl")
jl.include("src/outer/greedy-flow.jl")
jl.include("src/outer/greedy-impact.jl")
jl.include("src/outer/ours.jl")

jl.include("src/inner/pm_model.jl")
jl.include("src/inner/dc-ls-traditional.jl")
jl.include("src/inner/dc-ls-permutation.jl")

# Network properties
jl.include("src/network_properties/network-properties.jl")

# Variables used inside the julia code
jl.seval('DEBUG = false')

class Model(Singleton):

    SEQUENTIAL_ATK_MODE = 0
    SIMULTANEOUS_ATK_MODE = 1

    ############################################################################
    # Constructors
    ############################################################################

    def __init__(self):
        self.network = None
        self.network_name = None

        # Information about the attack
        self.atk_seq = []

        # Used for optimization in julia
        self.cliargs = jl.parse_commandline()
        self.cliargs['rerun'] = True
        self.cliargs['use_separate_budgets'] = True

        self.atk_mode = Model.SEQUENTIAL_ATK_MODE

        # Sequential Attack Cache
        self.it_data = []

        # Simultanous Attack Cache
        self.simu_atk_cache = []

    ############################################################################
    # Queries
    ############################################################################

    def get_atk_count(self):
        return len(self.atk_seq)

    def has_no_atk(self):
        return not self.atk_seq
    
    def get_uv_from_eid(self, eid):
        for uv in self.network.edges():
            if self.network.edges[uv]['eid'] == eid:
                return uv
        return None
    
    def get_eid_from_uv(self, uv):
        return self.network.edges[uv]['eid']
    
    def get_nodeids(self):
        return self.pm_ref["bus"].keys()

    def get_edgeids(self, make_sorted=False):
        if make_sorted:
            return sorted(self.pm_ref['branch'].keys())
        else:
            return self.pm_ref["branch"].keys()
    
    def get_edge_uv(self, make_sorted=False):
        if make_sorted:
            return sorted(self.network.edges(), key=self.get_eid_from_uv)
        else:
            return Model().network.edges()

    ############################################################################
    # Methods
    ############################################################################

    def set_case(self, mp_file):
        self.cliargs['mp_file'] = mp_file
        self.cliargs['case'] = Path(mp_file).name

        self.network = nx.Graph()
        self.pm_data, self.pm_ref = jl.init_models_data_ref(
            self.cliargs['mp_file'])
        for (i,bus) in self.pm_ref["bus"].items():
            self.network.add_node(i, nid=i, data=bus)
        for (i,br) in self.pm_ref["branch"].items():
            self.network.add_edge(br["f_bus"], br["t_bus"], eid=i, data=br)
        
        # Set initial it_data
        setpoints = {i : gen["pg"] for (i,gen) in self.pm_ref["gen"].items()}
        loads = {i : load["pd"] for (i,load) in self.pm_ref["load"].items()}
        # Cached pf in set_to_equilibrium
        pf = {i : pd["pf"] for (i,pd) in self.pm_ref["branch"].items()}
        next_it_data = jl.IterData(loads, setpoints, pf)
        self.it_data = [deepcopy(next_it_data)]

        # Also, add the same to the simu_atk_cache
        self.simu_atk_cache = [deepcopy({'loads':loads,'pg':setpoints,'p':pf})]

    def set_k(self, k):
        self.cliargs['budget'] = int(k)
        self.cliargs['line_budget'] = int(k)
    
    def set_generator_ramping_bounds(self, bounds):
        self.cliargs["generator_ramping_bounds"] = float(bounds)
    
    def set_atk_mode(self, atk_mode='Sequential'):
        if atk_mode == 'Sequential':
            self.atk_mode = Model.SEQUENTIAL_ATK_MODE
        elif atk_mode == 'Simultaneous':
            self.atk_mode = Model.SIMULTANEOUS_ATK_MODE
        else:
            raise f'Unknown attack mode {atk_mode} given'
    
    ############################################################################ 
    # Attack Sequence processing
    ############################################################################ 

    def reset_atk(self):
        self.atk_seq.clear()
        self.it_data = [self.it_data[0]] # keep initial state
        self.simu_atk_cache = [self.simu_atk_cache[0]] # keep initial state
    
    def check_atk(self, eid):
        return eid not in self.atk_seq

    def do_atk(self, eid):
        self.atk_seq.append(eid)

        # Sequential Attack
        prev_it_data = deepcopy(self.it_data[-1])
        prev_it_data.lines = deepcopy(self.atk_seq)
        jl.solve_partial_interdiction(self.cliargs, self.pm_data, self.pm_ref, prev_it_data)
        self.it_data.append(prev_it_data)

        # Simultaneous Attack
        cut_info = jl.get_traditional_inner_solution_PY(
            self.pm_data, self.pm_ref,
            ','.join(map(str, self.atk_seq)),
            self.it_data[0].prev_gen_setpoints,
            self.cliargs['generator_ramping_bounds'],
            self.cliargs['inner_solver'])
        self.simu_atk_cache.append(deepcopy(
            {'loads': cut_info[2],
            'pg':cut_info[3],
            'p' : cut_info[4]}))
    
    def undo_atk(self):
        if self.has_no_atk():
            return 

        eid = self.atk_seq.pop()
        self.it_data.pop()
        self.simu_atk_cache.pop()
        return eid

    def run_atk_strategy(self, atk_strategy):
        if atk_strategy == 'SEQUIN':
            return self.run_SEQUIN_atk()
        elif atk_strategy == 'Permutation':
            return self.run_permutation_atk()
        elif atk_strategy == 'Greedy-Flow':
            return self.run_greedy_flow_atk()
        elif atk_strategy == 'Greedy-Criticality':
            return self.run_greedy_criticality_atk()
        elif atk_strategy == 'Greedy-LoadShed':
            return self.run_greedy_loadshed_atk()
        elif atk_strategy == 'Random':
            return self.run_random_atk()
        
    def run_SEQUIN_atk(self):
        # No need to select anything if past line_budget
        if len(self.atk_seq) >= self.cliargs['line_budget']:
            return []

        self.cliargs['failed'] = ','.join(map(str,self.atk_seq))
        result = jl.solve_approach(self.cliargs, self.pm_data, self.pm_ref)

        return list(map(lambda x : x[0], 
            result.solution.best_permutation[len(self.atk_seq):]))

    def run_permutation_atk(self):
        # For permutation attack, no lines can be selected to be failed
        if self.atk_seq:
            return []

        # For permutation attack, line budget cannot be larger than 4
        if self.cliargs['line_budget'] > 4:
            return []

        self.cliargs['failed'] = ','.join(map(str,self.atk_seq))
        result = jl.solve_permutation(self.cliargs, self.pm_data, self.pm_ref)

        return list(map(lambda x : x[0], 
            result.solution.best_permutation[len(self.atk_seq):]))

    def run_greedy_flow_atk(self):
        # For greedy attack, select lines iteratively until line_budget
        if len(self.atk_seq) >= self.cliargs['line_budget']:
            return []
        
        self.cliargs['failed'] = ','.join(map(str,self.atk_seq))
        result = jl.solve_greedy_flow(self.cliargs, self.pm_data, self.pm_ref)

        return list(map(lambda x : x[0], 
            result.solution.best_permutation[len(self.atk_seq):]))
    
    def run_greedy_criticality_atk(self):
        # For greedy attack, select lines iteratively until line_budget
        if len(self.atk_seq) >= self.cliargs['line_budget']:
            return []
        
        self.cliargs['failed'] = ','.join(map(str,self.atk_seq))
        result = jl.solve_greedy_criticality(self.cliargs, self.pm_data, self.pm_ref)

        return list(map(lambda x : x[0], 
            result.solution.best_permutation[len(self.atk_seq):]))
    
    def run_greedy_loadshed_atk(self):
        # For greedy attack, select lines iteratively until line_budget
        if len(self.atk_seq) >= self.cliargs['line_budget']:
            return []
        
        self.cliargs['failed'] = ','.join(map(str,self.atk_seq))
        result = jl.solve_greedy_impact(self.cliargs, self.pm_data, self.pm_ref)
        return list(map(lambda x : x[0], 
            result.solution.best_permutation[len(self.atk_seq):]))
    
    def run_random_atk(self):
        # For random attack, select lines iteratively until line_budget
        if len(self.atk_seq) >= self.cliargs['line_budget']:
            return []
        
        k = self.cliargs['line_budget'] - len(self.atk_seq)
        eids = list(set(Model().get_edgeids()) - set(self.atk_seq))
        return random.sample(eids, k)
    
    ############################################################################ 
    # Network Properties
    ############################################################################ 

    def get_total_load(self, step=None, atk_mode=None):
        loads = defaultdict(float)
        for i,load in self.pm_ref['load'].items():
            loads[i] = load['pd']
        bounds = [0, max(loads.values())]
        return loads, bounds

    def get_load_shed(self, step, atk_mode=None):
        atk_mode = atk_mode or self.atk_mode
        if atk_mode == Model.SEQUENTIAL_ATK_MODE:
            load = {i : abs(x) for i,x in self.it_data[step].prev_loads.items()}
            all_loads = {abs(x) for data in self.it_data \
                        for x in data.prev_loads.values()}
            bounds = [0, max(all_loads)]
            return load, bounds
        elif atk_mode == Model.SIMULTANEOUS_ATK_MODE:
            load = {i : abs(x) for i,x in self.simu_atk_cache[step]['loads'].items()}
            all_loads = {abs(x) for data in self.simu_atk_cache \
                        for x in data['loads'].values()}
            bounds = [0, max(all_loads)]
            return load, bounds

    def get_power_gen(self, step, atk_mode=None):
        atk_mode = atk_mode or self.atk_mode
        if atk_mode == Model.SEQUENTIAL_ATK_MODE:
            gen = {i : abs(x) for i,x in self.it_data[step].prev_gen_setpoints.items()}
            all_gens = {abs(x) for data in self.it_data \
                        for x in data.prev_gen_setpoints.values()}
            bounds = [0, max(all_gens)]
            return gen, bounds
        elif atk_mode == Model.SIMULTANEOUS_ATK_MODE:
            gen = {i : abs(x) for i,x in self.simu_atk_cache[step]['pg'].items()}
            all_gens = [abs(x) for data in self.simu_atk_cache
                        for x in data['pg'].values()]
            bounds = [0, max(all_gens)]
            return gen, bounds

    def get_gen_crit(self, step, atk_mode=None):
        atk_mode = atk_mode or self.atk_mode
        if atk_mode == Model.SEQUENTIAL_ATK_MODE:
            gen_crit = jl.generator_criticality(
                self.pm_ref, 
                self.it_data[step].prev_br_pf, 
                self.cliargs['generator_ramping_bounds'])
            all_gen_crits = {x for data in self.it_data \
                        for x in jl.generator_criticality(
                            self.pm_ref, 
                            data.prev_br_pf, 
                            self.cliargs['generator_ramping_bounds']).values()}
            bounds = [min(all_gen_crits), max(all_gen_crits)]
            return gen_crit, bounds
        elif atk_mode == Model.SIMULTANEOUS_ATK_MODE:
            gen_crit = jl.generator_criticality(
                self.pm_ref, 
                self.simu_atk_cache[step]['pg'], 
                self.cliargs['generator_ramping_bounds'])
            all_gen_crits = {x for data in self.simu_atk_cache \
                        for x in jl.generator_criticality(
                            self.pm_ref, 
                            data['pg'], 
                            self.cliargs['generator_ramping_bounds']).values()}
            bounds = [min(all_gen_crits), max(all_gen_crits)]
            return gen_crit, bounds
    
    def get_trans_width(self, step=None, atk_mode=None):
        trans_width = jl.transmission_width(self.pm_ref)
        bounds = [min(trans_width), max(trans_width)]
        return trans_width, bounds

    def get_rate_a(self, step=None, atk_mode=None):
        br_rate_a = {i : br['rate_a'] for i,br in self.pm_ref['branch'].items()}
        bounds = [min(br_rate_a), max(br_rate_a)]
        return br_rate_a, bounds
    
    def get_power_flow(self, step, atk_mode=None):
        atk_mode = atk_mode or self.atk_mode
        step = int(step)
        if atk_mode == Model.SEQUENTIAL_ATK_MODE:
            br_pf = {i : abs(x) for i,x in self.it_data[step].prev_br_pf.items()}
            all_pfs = {abs(x) for data in self.it_data for x in data.prev_br_pf.values()}
            bounds = [0, max(all_pfs)]
            return br_pf, bounds
        elif atk_mode == Model.SIMULTANEOUS_ATK_MODE:
            br_pf = {i : abs(x) for i,x in self.simu_atk_cache[step]['p'].items()}
            all_pfs = {abs(x) for data in self.simu_atk_cache for x in data['p'].values()}
            bounds = [0, max(all_pfs)]
            return br_pf, bounds

    def get_br_crit(self, step, atk_mode=None):
        atk_mode = atk_mode or self.atk_mode
        if atk_mode == Model.SEQUENTIAL_ATK_MODE:
            br_crit = jl.branch_criticality(self.pm_ref, self.it_data[step].prev_br_pf)
            all_br_crits = {x for data in self.it_data \
                        for x in jl.branch_criticality(self.pm_ref, data.prev_br_pf).values()}
            bounds = [min(all_br_crits), max(all_br_crits)]
            return br_crit, bounds
        elif atk_mode == Model.SIMULTANEOUS_ATK_MODE:
            br_crit = jl.branch_criticality(self.pm_ref, 
                                            self.simu_atk_cache[step]['p'])
            all_br_crits = {x for data in self.simu_atk_cache \
                        for x in jl.branch_criticality(self.pm_ref, data['p']).values()}
            bounds = [min(all_br_crits), max(all_br_crits)]
            return br_crit, bounds

    def get_cut_impt(self, step):
        if self.atk_mode == Model.SEQUENTIAL_ATK_MODE:
            lines = list(set(self.pm_ref['branch'].keys()) - set(self.atk_seq))
            cut_impt = jl.cut_impact(self.cliargs, self.cliargs['mp_file'], lines, self.atk_seq)
            bounds = [0, self.pm_data['total_load']]
            return cut_impt, bounds
