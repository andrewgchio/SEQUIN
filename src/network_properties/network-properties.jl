# network-properties.jl
# We implement each of these network properties in this file...

"""
Returns the cut impact for the set of lines `lines`, assuming that the lines in
`failed` have failed
"""
function cut_impact(cliargs, mp_file, lines, failed)
    ci = Dict()

    # Compute the load shed before the line is cut.
    cliargs["line_budget"] = 0
    cliargs["budget"] = 0
    cliargs["failed"] = ""
    nk_result = run_traditional(cliargs, mp_file)
    init_load_shed = nk_result.solution.load_shed

    for i in lines
        # Set the line to be disabled
        cliargs["line_budget"] = 1 + length(failed)
        cliargs["budget"] = 1 + length(failed)
        cliargs["failed"] = "$(join([i,failed...], ","))"

        # Compute the new load shed
        result = run_traditional(cliargs, mp_file)
        load_shed = result.solution.load_shed

        # Cache the cut impact
        ci[i] = load_shed - init_load_shed
    end

    return ci
end

"""
Returns the transmission width of each of the nodes in the network
Output: Dict(bus_index => transmission width)
"""
function transmission_width(ref)
    widths = Dict()

    # Iterate through each bus and compute the transmission width
    for i in keys(ref[:bus])
        width, rem = 0, Set()

        # Iterate through each generator and isolate the bus from it
        for gen in values(ref[:gen])
            # Get all paths from the generator to the bus and remove them
            while true
                p = _get_path(gen["index"], i, ref, rem)
                isempty(p) && break
                union!(rem, p)
                width += 1
            end
        end

        # Save width
        widths[i] = width
    end

    return widths
end

"""
Return a list of edges that represent a path to go from bus_i to bus_j
"""
function _get_path(bus_i, bus_j, ref, rem)
    # Run breadth first search
    Q = [bus_i]
    parents = Dict(bus_i => bus_i)
    while !isempty(Q)
        v = popfirst!(Q)

        # If goal node is found, break
        (v == bus_j) && break

        # Iterate through all edges 
        for br in values(ref[:branch])
            # Get adjacent node that is not explored or "removed"
            if br["f_bus"] == v
                w = br["t_bus"]
            elseif br["t_bus"] == v
                w = br["f_bus"]
            else
                continue
            end
            in(w, keys(parents)) && continue

            # Make sure that the branch is also not "removed"
            (in((v, w), rem) || in((w, v), rem)) && continue

            # Add w to parents
            parents[w] = v
            push!(Q, w)
        end
    end

    # At this point, we have should have either: found the goal node, or
    # found that no such path exists. Reconstruct the path only if it does.
    path = []
    w = bus_j
    while w != bus_i
        !in(w, keys(parents)) && return []
        v = parents[w]
        push!(path, (w, v))
        w = v
    end
    return path
end

"""
Returns the load density for each of the clusters provided
"""
function load_density(ref, bus_set)::Float64
    total_load = 0
    for load in values(ref[:load])
        if in(load["load_bus"], bus_set)
            total_load += load["pd"]
        end
    end
    return total_load
end

function load_density(ref)
    ld = Dict()
    for (i,bus) in ref[:bus]
        ld[i] = load_density(ref, Set([i]))
    end
    return ld
end

"""
The criticality is the degree of flexibility that the network has
Output: A single number quantifying the current criticality
"""
function criticality(ref, pf, pg, percent_change)
    br_crit = 0 # branch_criticality(ref, pf)
    gen_crit = generator_criticality(ref, pg, percent_change)
    return sum(values(br_crit)) + sum(values(gen_crit))
end

"""
Return a map of the criticality of each of the 
"""
function branch_criticality(ref, pf)
    br_crit = Dict()

    for (i, br) in ref[:branch]
        if in(i, keys(pf))
            br_crit[i] = abs(br["rate_a"] - pf[i])
        end
    end

    return br_crit
end

function generator_criticality(ref, pg, percent_change)
    gen_crit = Dict()

    for (i, gen) in ref[:gen]
        if in(i, keys(pg))
            gen_crit[i] = min(
                abs(gen["pmax"] - pg[i]),
                abs(percent_change * gen["pmax"])
            )
        end
    end

    return gen_crit
end

# A sort of "main" function with which to test whether implementations of 
# the network properties works...
function test_network_properties(cliargs, mp_file)
    data, ref = init_models_data_ref(mp_file)

    # Testing cut impact
    println("Testing cut impact")
    # println(cut_impact(cliargs, mp_file, 1:20, []))

    # Testing transmission width
    println("Testing transmission width")
    # println(transmission_width(ref))

    # Testing load density
    println("Testing load density")
    # println(load_density(ref, [1, 2, 3, 4]))

    # Testing criticality
    println("Testing criticality")
    # Criticality only makes sense after the network is in some state
    setpoints = Dict(i => gen["pg"] for (i, gen) in ref[:gen])
    curr_lines = []
    if cliargs["failed"] != ""
        curr_lines = [map(x -> parse(Int, x), split(cliargs["failed"], ","))...]
    end

    cut_info = get_traditional_inner_solution(
        data, ref, [], curr_lines, setpoints;
        percent_change=cliargs["generator_ramping_bounds"],
        solver=cliargs["inner_solver"]
    )
    println(criticality(ref, cut_info.p, cut_info.pg, cliargs["generator_ramping_bounds"]))

    println("Done tests")
end
