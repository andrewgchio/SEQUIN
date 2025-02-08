"""
 * Implements the cutting plane algorithm in the paper
 *
 * Worst-Case Interdiction Analysis of Large-Scale Electric Power Grids 
 * DOI: 10.1109/TPWRS.2008.2004825
"""

""" run algorithm for determinsitic N-k """
function run_deterministic(cliargs::Dict, mp_file::String)::Results
    data = PowerModels.parse_file(mp_file; validate=false)
    PowerModels.make_per_unit!(data)
    add_total_load_info!(data)

    # modify_loads_zero!(data) # EDIT: Added
    modify_generation_limits!(data) # EDIT: Added

    put_system_at_equilibrium!(data, mp_file)

    ref = PowerModels.build_ref(data)[:it][:pm][:nw][0]

    print_summary(data)

    return solve_deterministic(cliargs, data, ref)
end

""" solve with lazy constraint callback """
function solve_deterministic(cliargs::Dict, data::Dict, ref::Dict)::Results
    model = direct_model(Gurobi.Optimizer(Gurobi.Env()))
    # set_attribute(model, "LogToConsole", 0)
    set_attribute(model, "TimeLimit", cliargs["timeout"])
    MOI.set(model, MOI.RelativeGapTolerance(), cliargs["optimality_gap"] / 100.0)

    # Turn off presolve
    set_optimizer_attribute(model, "Presolve", 0)

    # eta represents the min load shed 
    @variable(model, 0 <= eta <= 2000) # EDIT: 1E-6 to 0
    # interdiction variables
    @variable(model, x_line[i in keys(ref[:branch])], Bin)
    @variable(model, x_gen[i in keys(ref[:gen])], Bin)

    # budget constraints 
    @constraint(model, sum(x_line) + sum(x_gen) == cliargs["budget"])
    if cliargs["use_separate_budgets"]
        @constraint(model, sum(x_line) == cliargs["line_budget"])
        @constraint(model, sum(x_gen) == cliargs["generator_budget"])
    end

    constraint_outer_failed_lines(model, cliargs["failed"]) # EDIT: added

    # objective 
    @objective(model, Max, eta)
    TOL = 0.5 # EDIT: modified here

    function inner_problem(cb_data)
        status = callback_node_status(cb_data, model)
        (status != MOI.CALLBACK_NODE_STATUS_INTEGER) && (return)
        current_x_line = Dict(i => JuMP.callback_value(cb_data, x_line[i])
                              for i in keys(ref[:branch]))
        current_x_gen = Dict(i => JuMP.callback_value(cb_data, x_gen[i])
                             for i in keys(ref[:gen]))
        current_lines = filter!(z -> last(z) > TOL,
                            current_x_line) |> keys |> collect
        current_gens = filter!(z -> last(z) > TOL,
                           current_x_gen) |> keys |> collect
        cut_info = get_inner_solution(data, ref, current_gens, current_lines; solver=cliargs["inner_solver"])
        println(cut_info)
        woods_cut = @build_constraint(
            eta <= round(cut_info.load_shed; digits=4) + # EDIT
                   sum([cut_info.pg[i] * x_gen[i] for i in keys(cut_info.pg)]) +
                   sum([cut_info.p[i] * x_line[i] for i in keys(cut_info.p)]))
        MOI.submit(model, MOI.LazyConstraint(cb_data), woods_cut)
    end

    MOI.set(model, MOI.LazyConstraintCallback(), inner_problem)
    JuMP.optimize!(model)

    println("Termination Status: $(termination_status(model))")
    println("Primal Status: $(primal_status(model))")
    println("Dual Status: $(dual_status(model))")

    iterations = 0
    run_time = JuMP.solve_time(model)
    objective_value = JuMP.objective_value(model)
    bound = JuMP.objective_bound(model)
    rel_gap = JuMP.relative_gap(model)
    current_x_line = Dict(i => JuMP.value(x_line[i]) for i in keys(ref[:branch]))
    current_x_gen = Dict(i => JuMP.value(x_gen[i]) for i in keys(ref[:gen]))
    current_lines = filter!(z -> last(z) > TOL, current_x_line) |> keys |> collect
    current_gens = filter!(z -> last(z) > TOL, current_x_gen) |> keys |> collect
    incumbent = Solution(current_lines, current_gens, objective_value, Dict())

    return Results(
        iterations, objective_value, bound, run_time, rel_gap, incumbent
    )
end