""" Get load shed and power flow solution on interdictable components"""
function get_traditional_inner_solution(data, ref,
    generators::Vector, lines::Vector, setpoints::Dict;
    percent_change=0.1, solver="cplex")::NamedTuple

    # Turn off lines/generators and propagate topology
    case = interdict_components(data, generators, lines; make_deepcopy=true)

    lp_optimizer = get_lp_optimizer(solver)

    pm = instantiate_model(case, DCPPowerModel,
        (pm) -> my_build_mld(pm, setpoints; percent_change=percent_change))
    result = optimize_model!(pm, optimizer=lp_optimizer)

    pd = Dict(i => load["pd"] for (i, load) in result["solution"]["load"])
    load_shed = data["total_load"] - sum(values(pd))

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
    return (
        load_shed=load_shed, 
        all_loads=pd, 
        pg=pg, 
        p=p)
end

# Mainly for the SEQUIN GUI tool to access this function
get_traditional_inner_solution_PY(
    data,ref,lines::String,setpoints, percent_change, solver) = 
    get_traditional_inner_solution(
        data,ref,[],split(lines,","),setpoints; 
        percent_change=percent_change, solver=solver)
