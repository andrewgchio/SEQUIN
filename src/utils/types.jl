################################################################################
# Traditional/Standard Problem
################################################################################

""" data class that holds a solution to the problem """
struct Solution
    lines::Vector
    generators::Vector
    load_shed::Float64
    stats::Dict{Symbol,Any}
end

Solution() = Solution([], [], NaN, Dict())

function Base.show(io::IO, solution::Solution)
    longest_field_name =
        maximum([
            length(string(fname)) for fname in fieldnames(Solution)
        ]) + 2
    printstyled(io, "\n************** Solution **************\n", color=:cyan)
    for name in fieldnames(Solution)
        sname = string(name)
        pname = sname * repeat(" ", longest_field_name - length(sname))
        if getfield(solution, name) === nothing
            println(io, pname, ": NA")
        else
            println(io, pname, ": ", getfield(solution, name))
        end
    end
    printstyled(io, "*************************************\n", color=:cyan)
end

""" data class that holds the results """
struct Results
    num_iterations::Int
    objective_value::Float64
    bound::Float64
    run_time_in_seconds::Float64
    optimality_gap::Float64
    solution::Solution
end

Results() = Results(0, NaN, NaN, NaN, NaN, Solution())

################################################################################
# Permutation Problem
################################################################################

""" data class that holds a permutation solution to the problem """
struct PermutationSolution
    best_permutation::Vector
    worst_permutation::Vector
    solutions::Dict{Vector,Solution}
end

PermutationSolution() = PermutationSolution([], [], Dict())

function Base.show(io::IO, psolution::PermutationSolution)
    solution_list = collect(values(psolution.solutions))
    sort!(solution_list, by=x -> -x.load_shed)

    for soln in solution_list
        println(io, soln)
    end

end

""" data class that holds the permutation results """
struct PermutationResults
    num_iterations::Int
    objective_value::Float64
    bound::Float64
    run_time_in_seconds::Float64
    optimality_gap::Float64
    solution::PermutationSolution
end

PermutationResults() = PermutationResults(0, NaN, NaN, NaN, NaN, Solution())

function write_results(cliargs, results)
    case = first(split(cliargs["case"], "."))
    prob = cliargs["problem"][1:4]
    k = cliargs["budget"]
    pc = cliargs["generator_ramping_bounds"]
    fname = cliargs["output_path"] * "log/$(case)_$(prob)_soln_k$(k)_pc$(pc).csv"

    open(fname, "w") do f
        write(f, "k,m,pc,load_shed,perm\n")
        for (perm, soln) in sort(collect(results.solution.solutions), by=x -> x[1])
            k = cliargs["line_budget"]
            m = cliargs["iterline_budget"]
            ls = round(soln.load_shed; digits=4)
            pstr = join((join(x, ";") for x in perm), "/")
            write(f, "$(k),$(m),$(pc),$(ls),$(pstr)\n")
        end
    end
end

""" data class that holds information between iterations """
mutable struct IterData
    lines::Vector{Int}
    prev_loads::Dict
    next_loads::Dict
    prev_gen_setpoints::Dict
    next_gen_setpoints::Dict
    prev_br_pf::Dict
    next_br_pf::Dict
    solution::Solution
end

IterData(loads, setpoints, pf) = 
    IterData([], loads, Dict(), setpoints, Dict(), pf, pf, Solution())