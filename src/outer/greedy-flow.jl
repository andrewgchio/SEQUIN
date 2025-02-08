# greedy-flow.jl

""" run algorithm for greedy flow N-k """
function run_greedy_flow(cliargs::Dict, mp_file::String)::PermutationResults
    data, ref = init_models_data_ref(mp_file;
                                    do_perturb_loads=cliargs["do_perturb_loads"])
    return solve_greedy_flow(cliargs, data, ref)
end

""" solve with lazy constraint callback """
function solve_greedy_flow(cliargs::Dict, data::Dict, ref::Dict)
    # Cache the generator setpoints and loads at equilibrium
    setpoints = Dict(i => gen["pg"] for (i, gen) in ref[:gen])
    loads = Dict(i => load["pd"] for (i, load) in ref[:load])

    # This is only possible since we cache values in put_system_at_equilibrium
    pf = Dict(i => br["pf"] for (i, br) in ref[:branch])
    p0 = maximum(x -> (x[2],x[1]), pf)[2]

    solutions = Dict()

    # Reset the setpoints, loads
    setpoints = Dict(i => gen["pg"] for (i, gen) in ref[:gen])
    loads = Dict(i => load["pd"] for (i, load) in ref[:load])

    permutation = []
    it_data = IterData([], loads, Dict(), setpoints, Dict(), Solution())

    for i in 1:cliargs["line_budget"]
        iter_lines = i == 1 ? [p0] : get_next_pf(data, ref, it_data, 
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
function get_next_pf(data, ref, it_data, solver; percent_change=0.1)
    cut_info = get_permutation_inner_solution(
        data, ref, [], it_data.lines, it_data;
        percent_change=percent_change, solver=solver
    )

    # Return value of the max pair
    return [maximum(x -> (x[2],x[1]), cut_info.p)[2]]
end
