# greedy-criticality.jl

""" run algorithm for greedy criticality N-k """
function run_greedy_criticality(cliargs::Dict, mp_file::String)::PermutationResults
    data, ref = init_models_data_ref(mp_file;
                                    do_perturb_loads=cliargs["do_perturb_loads"])
    return solve_greedy_criticality(cliargs, data, ref)
end

""" solve with lazy constraint callback """
function solve_greedy_criticality(cliargs::Dict, data::Dict, ref::Dict)
    # Cache the generator setpoints and loads at equilibrium
    setpoints = Dict(i => gen["pg"] for (i, gen) in ref[:gen])
    loads = Dict(i => load["pd"] for (i, load) in ref[:load])

    init_it_data = IterData([], loads, Dict(), setpoints, Dict(), Solution())
    p0 = get_top_criticality(data, ref, init_it_data, cliargs["inner_solver"];
                percent_change=cliargs["generator_ramping_bounds"])[1]
    
    solutions = Dict()

    # Reset the setpoints, loads
    setpoints = Dict(i => gen["pg"] for (i, gen) in ref[:gen])
    loads = Dict(i => load["pd"] for (i, load) in ref[:load])

    permutation = [[p0]]
    it_data = IterData([p0], loads, Dict(), setpoints, Dict(), Solution())

    for _ in 2:cliargs["line_budget"]
        iter_lines = get_top_criticality(data, ref, it_data, 
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

""" return the next component to cut (the line with the impact on criticality)"""
function get_top_criticality(data, ref, it_data, solver; n=1, percent_change=0.1)
    crits = Dict()

    for (i,br) in ref[:branch]
        in(i, it_data.lines) && continue

        cut_info = get_permutation_inner_solution(
            data, ref, [], [it_data.lines..., i], it_data;
            percent_change=percent_change, solver=solver
        )

        crits[i] = criticality(ref, cut_info.p, cut_info.pg, percent_change)
    end

    return map(first, sort(collect(crits), by=x -> x[2])[1:n])
end