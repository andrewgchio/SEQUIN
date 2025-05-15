# greedy-impact.jl

""" run algorithm for greedy impact N-k """
function run_greedy_impact(cliargs::Dict, mp_file::String)::PermutationResults
    data, ref = init_models_data_ref(
        mp_file; 
        do_perturb_loads=cliargs["do_perturb_loads"])
    return solve_greedy_impact(cliargs, data, ref)
end

""" solve with lazy constraint callback """
function solve_greedy_impact(cliargs::Dict, data::Dict, ref::Dict)
    # Cache the generator setpoints and loads at equilibrium
    setpoints = Dict(i => gen["pg"] for (i, gen) in ref[:gen])
    loads = Dict(i => load["pd"] for (i, load) in ref[:load])
    pf = Dict(i => br["pf"] for (i,br) in ref[:branch])

    init_it_data = IterData(loads, setpoints, pf)
    p0 = get_top_impacts(data, ref, init_it_data, cliargs["inner_solver"];
                percent_change=cliargs["generator_ramping_bounds"])[1]
    
    solutions = Dict()

    # Reset the setpoints, loads
    setpoints = Dict(i => gen["pg"] for (i, gen) in ref[:gen])
    loads = Dict(i => load["pd"] for (i, load) in ref[:load])
    pf = Dict(i => br["pf"] for (i,br) in ref[:branch])

    permutation = []
    it_data = IterData(loads, setpoints, pf)

    for i in 1:cliargs["line_budget"]
        iter_lines = i == 1 ? [p0] : get_top_impacts(data, ref, it_data, 
            cliargs["inner_solver"]; 
            percent_change=cliargs["generator_ramping_bounds"])
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

    return pack_permutation_solution(solutions)
end

""" return the next component to cut (the line with the most flow)"""
function get_top_impacts(data, ref, it_data, solver; n=1, percent_change=0.1)
    impacts = Dict()

    for (i,br) in ref[:branch]
        in(i, it_data.lines) && continue

        cut_info = get_permutation_inner_solution(
            data, ref, [], [it_data.lines..., i], it_data;
            percent_change=percent_change, solver=solver
        )

        impacts[i] = cut_info.load_shed
    end

    return map(first, sort(collect(impacts), by=x -> -x[2])[1:n])
end