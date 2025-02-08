"""
 * Implements the cutting plane algorithm in the paper
 *
 * Worst-Case Interdiction Analysis of Large-Scale Electric Power Grids 
 * DOI: 10.1109/TPWRS.2008.2004825
"""

""" run algorithm for traditional N-k """
function run_traditional(cliargs::Dict, mp_file::String)::Results
    data, ref = init_models_data_ref(mp_file; 
                    do_perturb_loads=cliargs["do_perturb_loads"])
    return solve_traditional(cliargs, data, ref)
end

""" solve with lazy constraint callback """
function solve_traditional(cliargs::Dict, data::Dict, ref::Dict)
    # Cache the generator setpoints at equilibrium
    setpoints = Dict(i => gen["pg"] for (i, gen) in ref[:gen])

    model = direct_model(Gurobi.Optimizer(Gurobi.Env()))

    attributes_outer_model(model, cliargs)

    variable_outer_interdiction(model, ref)
    constraint_outer_interdiction_budget(model, cliargs)

    # Set failed lines if given
    constraint_outer_failed_lines(model, cliargs["failed"])

    objective_outer_load_shed(model)

    # Create a lazy callback for the inner problem
    MOI.set(model, MOI.LazyConstraintCallback(),
        (cb_data) -> cb_traditional_inner_problem(
            cb_data, model, data, ref, setpoints, cliargs["inner_solver"];
            percent_change=cliargs["generator_ramping_bounds"])
    )

    JuMP.optimize!(model)

    return pack_solution(model, data, ref, setpoints, cliargs)
end

function pack_solution(model, data, ref, setpoints, cliargs)
    iterations = 0
    run_time = JuMP.solve_time(model)
    # objective_value = JuMP.objective_value(model)
    bound = JuMP.objective_bound(model)
    rel_gap = JuMP.relative_gap(model)

    curr_lines = collect_values(model[:x_line], keys(ref[:branch]))
    curr_gens = collect_values(model[:x_gen], keys(ref[:gen]))

    objective_value = recompute_objective_value(data, ref,
        curr_lines, curr_gens, setpoints, cliargs)

    incumbent = Solution(curr_lines, curr_gens, objective_value, Dict())

    return Results(
        iterations, objective_value, bound, run_time, rel_gap, incumbent
    )
end

function cb_traditional_inner_problem(cb_data, model, data, ref, setpoints,
    solver; percent_change=0.1)
    status = callback_node_status(cb_data, model)
    (status != MOI.CALLBACK_NODE_STATUS_INTEGER) && (return)

    x_line, x_gen = model[:x_line], model[:x_gen]
    curr_lines = collect_values(x_line, keys(ref[:branch]); cb_data=cb_data)
    curr_gens = collect_values(x_gen, keys(ref[:gen]); cb_data=cb_data)

    cut_info = get_traditional_inner_solution(
        data, ref, curr_gens, curr_lines, setpoints;
        percent_change=percent_change, solver=solver
    )

    # println("Looking at line = $(curr_lines), with load shed = $(cut_info.load_shed)")

    woods_cut = @build_constraint(
        model[:eta] <= round(cut_info.load_shed; digits=4) +
                       sum([cut_info.pg[i] * x_gen[i] for i in keys(cut_info.pg)]) +
                       sum([cut_info.p[i] * x_line[i] for i in keys(cut_info.p)]))
    MOI.submit(model, MOI.LazyConstraint(cb_data), woods_cut)
end
