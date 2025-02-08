""" Get load shed and power flow solution on interdictable components"""
function get_permutation_inner_solution(data, ref,
    generators::Vector, lines::Vector, it_data::IterData;
    percent_change=0.1, solver="cplex")::NamedTuple

    # Turn off lines/generators and propagate topology
    case = interdict_components(data, generators, lines; make_deepcopy=true)

    lp_optimizer = get_lp_optimizer(solver)

    setpoints = it_data.prev_gen_setpoints
    loads = it_data.prev_loads

    # Ensure that you cannot recover lost load
    modify_loads!(case, loads)

    # Solve once to get max load shed
    pm = instantiate_model(deepcopy(case), DCPPowerModel,
        (pm) -> my_build_mld(pm, setpoints; percent_change=percent_change))
    result = optimize_model!(pm, optimizer=lp_optimizer)

    # Solve again to get min fuel cost, given solutions with max load shed
    # load_served = sum(load["pd"] for (_, load) in result["solution"]["load"])
    # load_shed = data["total_load"] - load_served
    # objective_value = JuMP.objective_value(pm.model)
    # pm = instantiate_model(case, DCPPowerModel,
    #     (pm) -> my_build_mld(pm, setpoints;
    #         percent_change=percent_change, max_load=objective_value))
    # result = optimize_model!(pm, optimizer=lp_optimizer)

    loads = Dict(i => load["pd"] for (i, load) in result["solution"]["load"])
    load_shed = data["total_load"] - sum(values(loads))

    pg = Dict(i => result["solution"]["gen"][string(i)]["pg"]
              for i in keys(ref[:gen])
              if haskey(result["solution"]["gen"], string(i))
    )

    p = Dict(i => max(
        abs(result["solution"]["branch"][string(i)]["pf"]),
        abs(result["solution"]["branch"][string(i)]["pt"]))
             for i in keys(ref[:branch])
             if haskey(result["solution"]["branch"], string(i))
    )

    return (load_shed=load_shed, loads=loads, pg=pg, p=p)
end
