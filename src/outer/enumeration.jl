# enumeration.jl 
# 
# Contains the functions needed to do the N-k interdiction through enumeration

""" run algorithm for enumeration N-k """
function run_enumeration(cliargs::Dict, mp_file::String)::PermutationResults
    data, ref = init_models_data_ref(
        mp_file; 
        do_perturb_loads=cliargs["do_perturb_loads"])
    return solve_enumeration(cliargs, data, ref)
end

""" solve with lazy constraint callback """
function solve_enumeration(cliargs::Dict, data::Dict, ref::Dict)
    # Cache the generator setpoints and loads at equilibrium
    setpoints = Dict(i => gen["pg"] for (i, gen) in ref[:gen])
    loads = Dict(i => load["pd"] for (i, load) in ref[:load])
    pf = Dict(i => br["pf"] for (i, br) in ref[:branch])

    solutions = Dict()

    for lines in combinations(collect(keys(ref[:branch])), cliargs["budget"])

        DEBUG && println("Set of lines = $(lines)")

        for porder in permutations(lines)
            permutation = []
            it_data = IterData(loads, setpoints, pf)

            for iter_lines in take_n_items(porder, cliargs["iterline_budget"])
                push!(permutation, iter_lines)
                it_data.lines = collect(Iterators.flatten(permutation))

                DEBUG && println("Solving with lines=$(it_data.lines)")
                try
                    solve_partial_interdiction(cliargs, data, ref, it_data)
                catch e
                    # Some ordering that caused an error
                    println("Error occurred", e)
                    println("Press enter to continue...")
                    readline()
                    continue
                end
            end

            # Save solution at the end of all rounds for porder
            solutions[permutation] = Solution(
                permutation,
                [],
                it_data.solution.load_shed,
                it_data.solution.stats
            )
        end
    end

    return pack_enumeration_solution(solutions)
end

function pack_enumeration_solution(solutions)
    iterations = 0
    objective_value = 0 # TODO
    bound = 0 # TODO
    run_time = 0 # TODO
    rel_gap = 0 # TODO

    lo_porder, hi_porder = Vector(), Vector()
    lo_ls, hi_ls = typemax(Float64), typemin(Float64)
    for (p, s) in solutions
        if lo_ls > s.load_shed
            lo_ls, lo_porder = s.load_shed, Vector([p])
        elseif lo_ls == s.load_shed
            push!(lo_porder, p)
        end

        if hi_ls < s.load_shed
            hi_ls, hi_porder = s.load_shed, Vector([p])
        elseif lo_ls == s.load_shed
            push!(hi_porder, p)
        end
    end

    hi_lo_solutions = Dict(
        (porder => solutions[porder] for porder in hi_porder)...,
        (porder => solutions[porder] for porder in lo_porder)...
    )
    incumbent = PermutationSolution(hi_porder, lo_porder, solutions)

    return PermutationResults(
        iterations, objective_value, bound, run_time, rel_gap, incumbent
    )
end
