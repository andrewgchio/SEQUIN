# datautils.jl 
#
# Contains utility functions to process the data dict in PowerModels

""" set generation limits to zero when pmax/qmax are positive """
function modify_generation_limits!(case_data::Dict)
    for (_, gen) in get(case_data, "gen", [])
        (gen["pmax"] > 0.0) && (gen["pmin"] = 0.0)
        (gen["qmax"] > 0.0) && (gen["qmin"] = 0.0)
    end
end

""" modify phase angle bounds """
function modify_phase_angle_bounds!(case_data::Dict)
    for (_, branch) in get(case_data, "branch", [])
        branch["angmin"] = -pi / 2
        branch["angmax"] = pi / 2
    end
end

function modify_loads_zero!(case_data::Dict)
    for (i, load) in get(case_data, "load", [])
        if (load["pd"] < 0)
            println("setting load $(load["pd"]) at $(i) to 0")
            load["pd"] = 0
        end
    end
end

""" modify loads """
function modify_loads!(case_data::Dict, loads::Dict)
    for (i, load) in loads
        case_data["load"][string(i)]["pd"] = load
    end
end

""" add total load to case_data """
function add_total_load_info!(case_data::Dict)
    pd = sum([load["pd"] for (_, load) in case_data["load"]]; init=0.0)
    ps = sum([shunt["gs"] for (_, shunt) in case_data["shunt"]]; init=0.0)
    case_data["total_load"] = pd + ps
end

""" perturbs the loads at each node by `by` percent """
function perturb_loads!(data; by=0.01)
    for (i, load) in get(data, "load", [])
        load["pd"] = load["pd"] * (2*by*rand() + (1-by))
        if (load["pd"] < 0)
            load["pd"] = 0
        end
    end
end

""" solve the OPF solution for the data file and reset generation """
function put_system_at_equilibrium!(data, mp_file)
    lp_optimizer = JuMP.optimizer_with_attributes(
        () -> Gurobi.Optimizer(Gurobi.Env()), "LogToConsole" => 0
    )

    # Note, solve_opf turns qg into NaN since a DC model is used
    # result = solve_opf(mp_file, DCPPowerModel, lp_optimizer)
    result = solve_model(data, DCPPowerModel, lp_optimizer, build_opf)

    # Replace generator values to put power model in equilibrium
    for (i, gen) in result["solution"]["gen"]
        data["gen"][string(i)]["pg"] = gen["pg"]
        data["gen"][string(i)]["qg"] = gen["qg"]
    end

    # Also cache the power flows on each branch
    for (i, br) in result["solution"]["branch"]
        data["branch"][string(i)]["pf"] = br["pf"]
    end

    (DEBUG) && println("Put system in equilibrium")
end

""" deepcopy and turn-off interdicted components """
function interdict_components(case_data, generators::Vector, lines::Vector;
    make_deepcopy=true)
    case = make_deepcopy ? deepcopy(case_data) : case_data
    for i in generators
        case["gen"][string(i)]["gen_status"] = 0
    end
    for i in lines
        case["branch"][string(i)]["br_status"] = 0
    end
    PowerModels.propagate_topology_status!(case)
    return case
end
