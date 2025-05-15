# main.jl

using PowerModels
using JuMP
using Gurobi
using PrettyTables
using Logging

using Combinatorics

include("utils/cliparser.jl")
include("utils/types.jl")

include("utils/utils.jl")
include("utils/ioutils.jl")
include("utils/datautils.jl")
include("utils/optimizationutils.jl")

include("outer/traditional.jl")
include("outer/permutation.jl")
include("outer/enumeration.jl")

include("outer/greedy-criticality.jl")
include("outer/greedy-flow.jl")
include("outer/greedy-impact.jl")
include("outer/ours.jl")

include("inner/pm_model.jl")
include("inner/dc-ls-traditional.jl")
include("inner/dc-ls-permutation.jl")

# "Deterministic" version; for testing
include("outer/run.jl")
include("inner/dc-ls.jl")

# Network properties
include("network_properties/network-properties.jl")

# Experiments
# include("experiments/experiment0.jl")
# include("experiments/experiment1.jl")
# include("experiments/experiment2.jl")
# include("experiments/experiment3.jl")

const GRB_ENV = Gurobi.Env()

PowerModels.silence()

# ConsoleLogger to stderr that accepts messages with level >= Logging.Debug
debug_logger = ConsoleLogger(stderr, Logging.Debug)
global_logger(debug_logger)

# For simple debugging
const DEBUG = true

function main()
    cliargs = parse_commandline()

    # print input parameters
    pretty_table(cliargs,
        title="CLI Parameters",
        title_alignment=:c,
        title_same_width_as_table=true,
        show_header=false)

    validate_parameters(cliargs)
    files = get_filenames_with_paths(cliargs)
    run(cliargs, files)
    return
end

function run(cliargs, files)
    mp_file = files.mp_file

    if !cliargs["rerun"]
        config_data = get_config_data(cliargs)
        outfile = get_outfile_name(config_data)
        file = "$(cliargs["output_path"])$(config_data["problem"])/$(outfile)"
        if isfile(file)
            @info "run already completed, result file exists at $file"
            @info "to re-run, use the --rerun flag"
            return
        end
    end

    if cliargs["problem"] == "traditional"
        results = run_traditional(cliargs, mp_file)
        # write_results(cliargs, results)
        println(results.solution)
        return
    end

    if cliargs["problem"] == "permutation"
        results = run_permutation(cliargs, mp_file)
        write_results(cliargs, results)
        println(results)
        return
    end

    if cliargs["problem"] == "enumeration"
        results = run_enumeration(cliargs, mp_file)
        write_results(cliargs, results)
        println(results)
        return
    end

    # "Baseline" approaches
    if cliargs["problem"] == "criticality"
        results = run_greedy_criticality(cliargs, mp_file)
        write_results(cliargs, results)
        println(results)
        return
    end

    if cliargs["problem"] == "flow"
        results = run_greedy_flow(cliargs, mp_file)
        write_results(cliargs, results)
        println(results)
        return
    end

    if cliargs["problem"] == "impact"
        results = run_greedy_impact(cliargs, mp_file)
        write_results(cliargs, results)
        println(results)
        return
    end

    if cliargs["problem"] == "SEQUIN"
        results = run_approach(cliargs, mp_file)
        write_results(cliargs, results)
        println(results)
        return
    end

    if cliargs["problem"] == "test_network_properties"
        test_network_properties(cliargs, mp_file)
        return
    end

    if cliargs["problem"] == "visualization"
        run_visualization(cliargs, mp_file)
        return
    end

    if cliargs["problem"] == "cache_netprops"
        cache_network_properties(cliargs, mp_file)
        return
    end

    # if cliargs["problem"] == "cache_experiment0"
    #     cache_experiment0(cliargs, mp_file)
    #     return
    # end

    # if cliargs["problem"] == "cache_experiment1"
    #     cache_experiment1(cliargs, mp_file)
    #     return
    # end

    # if cliargs["problem"] == "cache_experiment2"
    #     cache_experiment2(cliargs, mp_file)
    #     return
    # end

    # if cliargs["problem"] == "cache_experiment3"
    #     cache_experiment3(cliargs, mp_file)
    #     return
    # end

    throw("Problem $(cliargs["problem"]) is not defined")

end

main()
