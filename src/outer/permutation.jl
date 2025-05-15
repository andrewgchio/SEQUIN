# permutation.jl

""" run algorithm for permutation N-k """
function run_permutation(cliargs::Dict, mp_file::String)::PermutationResults
    data, ref = init_models_data_ref(
        mp_file; 
        do_perturb_loads=cliargs["do_perturb_loads"])
    return solve_permutation(cliargs, data, ref)
end

""" solve with lazy constraint callback """
function solve_permutation(cliargs::Dict, data::Dict, ref::Dict)
    # Cache the generator setpoints and loads at equilibrium
    setpoints = Dict(i => gen["pg"] for (i, gen) in ref[:gen])
    loads = Dict(i => load["pd"] for (i, load) in ref[:load])
    pf = Dict(i => br["pf"] for (i,br) in ref[:branch])

    # Heuristic: solve the regular N-k problem to find the k lines to cut
    nk_solution = solve_traditional(cliargs, data, ref)
    lines = nk_solution.solution.lines

    solutions = Dict()
    for porder in permutations(lines)
        permutation = []
        it_data = IterData(loads, setpoints, pf)

        for iter_lines in take_n_items(porder, cliargs["iterline_budget"])
            push!(permutation, iter_lines)
            it_data.lines = collect(Iterators.flatten(permutation))

            DEBUG && println("Solving with k (subset) lines=$(it_data.lines)")
            solve_partial_interdiction(cliargs, data, ref, it_data)
        end

        # Save the solution at the end of all rounds
        solutions[permutation] = Solution(
            permutation,
            [],
            it_data.solution.load_shed,
            it_data.solution.stats
        )
    end

    return pack_permutation_solution(solutions)
end

function pack_permutation_solution(solutions)
    iterations = 0
    objective_value = 0 # TODO
    bound = 0 # TODO
    run_time = 0 # TODO
    rel_gap = 0 # TODO

    lo_porder, hi_porder = nothing, nothing
    for (p, s) in solutions
        if lo_porder === nothing || solutions[lo_porder].load_shed < s.load_shed
            lo_porder = p
        end
        if hi_porder === nothing || solutions[hi_porder].load_shed > s.load_shed
            hi_porder = p
        end
    end
    incumbent = PermutationSolution(hi_porder, lo_porder, solutions)

    return PermutationResults(
        iterations, objective_value, bound, run_time, rel_gap, incumbent
    )
end

""" solve the interdiction problem with part of the lines cut """
function solve_partial_interdiction(cliargs::Dict, data::Dict, ref::Dict,
    it_data::IterData)

    model = direct_model(Gurobi.Optimizer(Gurobi.Env()))

    attributes_outer_model(model, cliargs)

    variable_outer_interdiction(model, ref)

    # Set interdicted lines 
    constraint_outer_partial_budget(model, cliargs, length(it_data.lines))
    constraint_outer_failed_lines(model, it_data.lines)

    objective_outer_load_shed(model)

    # Create a lazy callback for the inner problem; update it_data in callback
    MOI.set(model, MOI.LazyConstraintCallback(),
        (cb_data) -> cb_permutation_inner_problem(
            cb_data, model, data, ref, it_data, cliargs["inner_solver"];
            percent_change=cliargs["generator_ramping_bounds"])
    )

    JuMP.optimize!(model)

    # Get the latest pg and load shed after optimization (and save it in prev)
    it_data.prev_gen_setpoints = it_data.next_gen_setpoints
    it_data.prev_loads = it_data.next_loads
    it_data.prev_br_pf = it_data.next_br_pf

    curr_lines = collect_values(model[:x_line], keys(ref[:branch]))
    curr_gens = collect_values(model[:x_gen], keys(ref[:gen]))
    objective_value = JuMP.objective_value(model)
    # objective_value = recompute_objective_value(data, ref,
    #     curr_lines, curr_gens, setpoints, cliargs)
    it_data.solution = Solution(curr_lines, curr_gens, objective_value, Dict())

    return model
end

function cb_permutation_inner_problem(cb_data, model, data, ref, it_data,
    solver; percent_change=0.1)
    status = callback_node_status(cb_data, model)
    (status != MOI.CALLBACK_NODE_STATUS_INTEGER) && (return)

    x_line, x_gen = model[:x_line], model[:x_gen]
    curr_lines = collect_values(x_line, keys(ref[:branch]); cb_data=cb_data)
    curr_gens = collect_values(x_gen, keys(ref[:gen]); cb_data=cb_data)

    cut_info = get_permutation_inner_solution(
        data, ref, curr_gens, curr_lines, it_data;
        percent_change=percent_change, solver=solver
    )

    # Cache next gen setpoints, loads 
    it_data.next_gen_setpoints = cut_info.pg
    it_data.next_loads = cut_info.loads
    it_data.next_br_pf = cut_info.p

    woods_cut = @build_constraint(
        model[:eta] 
        <= 
        round(cut_info.load_shed; digits=4) +
        # sum([cut_info.pg[i] * x_gen[i] for i in keys(cut_info.pg)]) +
        sum([cut_info.p[i] * x_line[i] for i in keys(cut_info.p)]))

    MOI.submit(model, MOI.LazyConstraint(cb_data), woods_cut)
end
