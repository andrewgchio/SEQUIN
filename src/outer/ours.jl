# ours.jl

""" run algorithm for our N-k """
function run_approach(cliargs::Dict, mp_file::String)::PermutationResults
    data, ref = init_models_data_ref(mp_file;
                                    do_perturb_loads=cliargs["do_perturb_loads"])
    return solve_approach(cliargs, data, ref)
end

""" solve with lazy constraint callback """
function solve_approach(cliargs::Dict, data::Dict, ref::Dict)
    # Cache the generator setpoints and loads at equilibrium
    setpoints = Dict(i => gen["pg"] for (i, gen) in ref[:gen])
    loads = Dict(i => load["pd"] for (i, load) in ref[:load])

    init_it_data = IterData([], loads, Dict(), setpoints, Dict(), Solution())

    # This is only possible since we cache values in put_system_at_equilibrium
    pfs = get_top_pfs(data, ref, init_it_data, cliargs["inner_solver"];
            init=true,
            n=10,
            # n=div(length(ref[:branch]), 10),
            percent_change=cliargs["generator_ramping_bounds"])

    # crits = get_top_criticality(data, ref, init_it_data, cliargs["inner_solver"];
    #             n=10,
    #             percent_change=cliargs["generator_ramping_bounds"])

    # Doesn't work too well
    # init_it_data = IterData([], loads, Dict(), setpoints, Dict(), Solution())
    # ldtw = get_ldtw(ref, init_it_data; n=10)

    solutions = Dict()
    for p0 in pfs

        # Reset the setpoints, loads
        setpoints = Dict(i => gen["pg"] for (i, gen) in ref[:gen])
        loads = Dict(i => load["pd"] for (i, load) in ref[:load])

        permutation = []
        it_data = IterData([], loads, Dict(), setpoints, Dict(), Solution())

        branches = nothing

        for i in 1:cliargs["line_budget"]
            iter_lines = i == 1 ? [p0] : get_top_impacts(data, ref, it_data, 
                cliargs["inner_solver"]; 
                branches=branches,
                percent_change=cliargs["generator_ramping_bounds"])
            push!(permutation, iter_lines)
            it_data.lines = collect(Iterators.flatten(permutation))

            DEBUG && println("Solving with k (subset) lines=$(it_data.lines)")
            solve_partial_interdiction(cliargs, data, ref, it_data)

            # Get branches with high pf 
            branches = get_top_pfs(data, ref, it_data, cliargs["inner_solver"]; 
                    init=false,
                    n=10,
                    # n=div(length(ref[:branch]), 10),
                    percent_change=cliargs["generator_ramping_bounds"])

            println("branches ", branches)

        end

        # Last step should always be cut impact
        # iter_lines = get_top_impacts(data, ref, it_data, 
        #         cliargs["inner_solver"]; 
        #         percent_change=cliargs["generator_ramping_bounds"])
        # push!(permutation, iter_lines)
        # it_data.lines = collect(Iterators.flatten(permutation))
        # DEBUG && println("Solving with k (subset) lines=$(it_data.lines)")
        # solve_partial_interdiction(cliargs, data, ref, it_data)

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

function get_top_pfs(data, ref, it_data, solver; init=false, n=1, percent_change=0.1)
    if init
        pf = Dict(i => abs(br["pf"]) for (i, br) in ref[:branch])
    else
        cut_info = get_permutation_inner_solution(
            data, ref, [], it_data.lines, it_data;
            percent_change=percent_change, solver=solver
        )
        pf = cut_info.p
    end
    pfs = sort(collect(pf), by=x -> (-x[2],x[1]))
    return map(first, pfs[1:n])
end

""" return the next component to cut (the line with the most impact)"""
function get_top_impacts(data, ref, it_data, solver; branches=nothing, n=1, percent_change=0.1)
    impacts = Dict()

    println("Branches = $(branches)")
    (branches == nothing) && (branches = keys(ref[:branch]))

    for i in branches
        br = ref[:branch][i]
        in(i, it_data.lines) && continue

        cut_info = get_permutation_inner_solution(
            data, ref, [], [it_data.lines..., i], it_data;
            percent_change=percent_change, solver=solver
        )

        impacts[i] = cut_info.load_shed
    end

    return map(first, sort(collect(impacts), by=x -> -x[2])[1:n])
end

""" return the component that would push the criticality up the most """
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
    println("Criticality = $(crits)")

    return map(first, sort(collect(crits), by=x -> -x[2])[1:n])
end

function get_ldtw(ref, it_data; n=1)
    tw = transmission_width(ref)
    ld = load_density(ref)

    ldtw = Dict()

    for (i,br) in ref[:branch]
        in(i, it_data.lines) && continue

        f_bus = br["f_bus"]
        t_bus = br["t_bus"]

        ldtw[i] = ld[f_bus]/tw[f_bus] + ld[t_bus]/tw[t_bus]
    end
    
    return map(first, sort(collect(ldtw), by=x -> -x[2])[1:n])
end