# optimizationutils.jl
# 
# Contains utility functions for the optimization problem
# 
# Also contains functions to extract model values

function get_lp_optimizer(solver)
    if solver == "cplex"
        return JuMP.optimizer_with_attributes(
            () -> CPLEX.Optimizer(), "CPX_PARAM_SCRIND" => 0
        )
    elseif solver == "gurobi"
        return JuMP.optimizer_with_attributes(
            () -> Gurobi.Optimizer(Gurobi.Env()), "LogToConsole" => 0
        )
    else
        @error "Unknown LP solver ($(solver)); must be one of [cplex|gurobi]"
        exit()
    end
end

function init_models_data_ref(mp_file::String; do_perturb_loads=false)
    data = PowerModels.parse_file(mp_file; validate=false)
    PowerModels.make_per_unit!(data)

    reset_all = true

    if do_perturb_loads
        for i in 1:10 # Try 10 times
            try
            perturb_loads!(data; by=0.05)

            add_total_load_info!(data)
            modify_generation_limits!(data)
            # modify_phase_angle_bounds!(data)
            put_system_at_equilibrium!(data, mp_file)
            reset_all = false
            break
            catch
                # Reset data and try again...
                data = PowerModels.parse_file(mp_file; validate=false)
                PowerModels.make_per_unit!(data)
            end
        end
    end

    # Reset all loads and ignore perturbation...
    if reset_all || !do_perturb_loads
        data = PowerModels.parse_file(mp_file; validate=false) 
        PowerModels.make_per_unit!(data)
        add_total_load_info!(data)
        modify_generation_limits!(data)
        # modify_phase_angle_bounds!(data)
        put_system_at_equilibrium!(data, mp_file)
    end

    # Print a summary of the data used for the run
    DEBUG && print_summary(data)

    ref = PowerModels.build_ref(data)[:it][:pm][:nw][0]
    return data, ref
end

function attributes_outer_model(model, cliargs)
    # set_attribute(model, "LogToConsole", 0)
    set_attribute(model, "TimeLimit", cliargs["timeout"])
    MOI.set(model, MOI.RelativeGapTolerance(), cliargs["optimality_gap"]/100.0)

    # Increase Number of threads used
    # MOI.set(model, MOI.NumberOfThreads(), 32)
end

function variable_outer_interdiction(model, ref)
    @variable(model, x_line[i in keys(ref[:branch])], Bin)
    @variable(model, x_gen[i in keys(ref[:gen])], Bin)
end

function constraint_outer_interdiction_budget(model, cliargs)
    x_line, x_gen = model[:x_line], model[:x_gen]
    @constraint(model, sum(x_line) + sum(x_gen) == cliargs["budget"])
    if cliargs["use_separate_budgets"]
        @constraint(model, sum(x_line) == cliargs["line_budget"])
        @constraint(model, sum(x_gen) == cliargs["generator_budget"])
    end
end

function constraint_outer_partial_budget(model, cliargs, partial_line_budget)
    x_line, x_gen = model[:x_line], model[:x_gen]
    @constraint(model, sum(x_line) + sum(x_gen) == partial_line_budget)
    if cliargs["use_separate_budgets"]
        @constraint(model, sum(x_line) == partial_line_budget)
        @constraint(model, sum(x_gen) == cliargs["generator_budget"])
    end
end

function constraint_outer_failed_lines(model, failed_lines_str::String)
    (failed_lines_str == "") && return
    failed_lines = map(x -> parse(Int, x), split(failed_lines_str, ","))
    constraint_outer_failed_lines(model, failed_lines)
end

function constraint_outer_failed_lines(model, failed_lines::Vector)
    for i_fail in failed_lines
        @constraint(model, model[:x_line][i_fail] == 1)
    end
end

function constraint_outer_failed_gens(model, failed_gens_str::String)
    (failed_gens_str == "") && return
    failed_gens = map(x => parse(Int, x), split(failed_gens_str, ","))
    constraint_outer_failed_gens(model, failed_gens)
end

function constraint_outer_failed_gens(model, failed_gens::Vector)
    for i_fail in failed_gens
        @constraint(model, model[:x_gen][i_fail] == 1)
    end
end

function objective_outer_load_shed(model)
    @variable(model, 0.0 <= eta <= 1E6) # @variable(model, 1E-6 <= eta <= 1E6)
    @objective(model, Max, eta)
end

function collect_values(x, x_keys; cb_data=nothing)
    get_value(xi) = cb_data === nothing ?
                    JuMP.value(xi) : JuMP.callback_value(cb_data, xi)

    values_dict = Dict(i => get_value(x[i]) for i in x_keys)
    values = filter!(z -> last(z) > 0.5, values_dict) |> keys |> collect
    return values
end

function recompute_objective_value(data, ref, lines, gens, setpoints, cliargs)
    cut_info = get_traditional_inner_solution(data, ref, gens, lines, setpoints;
        percent_change=cliargs["generator_ramping_bounds"], 
        solver=cliargs["inner_solver"])
    return cut_info.load_shed +
           sum([cut_info.pg[i] for i in keys(cut_info.pg) if in(i, gens)]) +
           sum([cut_info.p[i] for i in keys(cut_info.p) if in(i, lines)])
end

