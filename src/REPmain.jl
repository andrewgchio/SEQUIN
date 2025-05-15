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

# Used to execute the REP
include("experiments/REP.jl")

# include("visualization/cache_network_properties.jl")

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

    ############################################################################
    # Repeatability Evaluation Package Scripts
    ############################################################################

    if cliargs["problem"] == "REP_cache_fig4a"
        # Add convenient config options 
        cliargs["rerun"] = true
        cliargs["use_separate_budgets"] = true

        cliargs["case"] = "pglib_opf_case39_epri__api.m" 
        mp_file = "data/matpower/$(cliargs["case"])"
        cliargs["budget"] = 3
        cliargs["line_budget"] = 3
        cliargs["generator_ramping_bounds"] = 0.1
        REP_cache_fig4(cliargs, mp_file)

        return
    end

    if cliargs["problem"] == "REP_cache_fig4b"
        # Add convenient config options 
        cliargs["rerun"] = true
        cliargs["use_separate_budgets"] = true

        # For Fig. 4b
        cliargs["case"] = "pglib_opf_case118_ieee__api.m"
        mp_file = "data/matpower/$(cliargs["case"])"
        cliargs["budget"] = 6
        cliargs["line_budget"] = 6
        cliargs["generator_ramping_bounds"] = 0.01
        REP_cache_fig4(cliargs, mp_file)

        return
    end


    if cliargs["problem"] == "REP_cache_fig5a"
        # Add convenient config options 
        cliargs["rerun"] = true
        cliargs["use_separate_budgets"] = true
        
        # Case 14
        cliargs["case"] = "pglib_opf_case14_ieee__api.m"
        mp_file = "data/matpower/$(cliargs["case"])"
        REP_cache_fig5(cliargs, mp_file; enum_bound=7, perm_bound=8)

        return
    end

    if cliargs["problem"] == "REP_cache_fig5b"
        # Add convenient config options 
        cliargs["rerun"] = true
        cliargs["use_separate_budgets"] = true

        # Case 39
        cliargs["case"] = "pglib_opf_case39_epri__api.m"
        mp_file = "data/matpower/$(cliargs["case"])"
        REP_cache_fig5(cliargs, mp_file; enum_bound=3, perm_bound=6)

        return
    end

    if cliargs["problem"] == "REP_cache_fig5c"
        # Add convenient config options 
        cliargs["rerun"] = true
        cliargs["use_separate_budgets"] = true

        # Case 60
        cliargs["case"] = "pglib_opf_case60_c.m"
        mp_file = "data/matpower/$(cliargs["case"])"
        REP_cache_fig5(cliargs, mp_file; enum_bound=2, perm_bound=6)

        return
    end

    if cliargs["problem"] == "REP_cache_fig5d"
        # Add convenient config options 
        cliargs["rerun"] = true
        cliargs["use_separate_budgets"] = true

        # Case 118
        cliargs["case"] = "pglib_opf_case118_ieee__api.m"
        mp_file = "data/matpower/$(cliargs["case"])"
        REP_cache_fig5(cliargs, mp_file; enum_bound=2, perm_bound=6)

        return
    end

    if cliargs["problem"] == "REP_cache_fig5e"
        # Add convenient config options 
        cliargs["rerun"] = true
        cliargs["use_separate_budgets"] = true
        
        # Case 162
        cliargs["case"] = "pglib_opf_case162_ieee_dtc.m"
        mp_file = "data/matpower/$(cliargs["case"])"
        REP_cache_fig5(cliargs, mp_file; enum_bound=2, perm_bound=1)
        
        return
    end

    if cliargs["problem"] == "REP_cache_fig5f"
        # Add convenient config options 
        cliargs["rerun"] = true
        cliargs["use_separate_budgets"] = true

        # Case 240
        cliargs["case"] = "pglib_opf_case240_pserc.m"
        mp_file= "data/matpower/$(cliargs["case"])"
        REP_cache_fig5(cliargs, mp_file; enum_bound=2, perm_bound=1)

        return
    end


    if cliargs["problem"] == "REP_cache_fig6a"
        # Add convenient config options 
        cliargs["rerun"] = true
        cliargs["use_separate_budgets"] = true

        # Setting
        cliargs["iterline_budget"] = 1
        cliargs["line_budget"] = 4
        cliargs["budget"] = 4
        
        # Case 14
        cliargs["case"] = "pglib_opf_case14_ieee__api.m"
        mp_file = "data/matpower/$(cliargs["case"])"
        REP_cache_fig6(cliargs, mp_file; run_enum=true, run_perm=true)

        return
    end

    if cliargs["problem"] == "REP_cache_fig6b"
        # Add convenient config options 
        cliargs["rerun"] = true
        cliargs["use_separate_budgets"] = true

        # Setting
        cliargs["iterline_budget"] = 1
        cliargs["line_budget"] = 4
        cliargs["budget"] = 4
        
        # Case 39
        cliargs["case"] = "pglib_opf_case39_epri__api.m"
        mp_file = "data/matpower/$(cliargs["case"])"
        REP_cache_fig6(cliargs, mp_file; run_enum=false, run_perm=true)

        return
    end

    if cliargs["problem"] == "REP_cache_fig6c"
        # Add convenient config options 
        cliargs["rerun"] = true
        cliargs["use_separate_budgets"] = true

        # Setting
        cliargs["iterline_budget"] = 1
        cliargs["line_budget"] = 4
        cliargs["budget"] = 4
        
        # Case 60
        cliargs["case"] = "pglib_opf_case60_c.m"
        mp_file = "data/matpower/$(cliargs["case"])"
        REP_cache_fig6(cliargs, mp_file; run_enum=false, run_perm=true)

        return
    end

    if cliargs["problem"] == "REP_cache_fig6d"
        # Add convenient config options 
        cliargs["rerun"] = true
        cliargs["use_separate_budgets"] = true

        # Setting
        cliargs["iterline_budget"] = 1
        cliargs["line_budget"] = 4
        cliargs["budget"] = 4
        
        # Case 118
        cliargs["case"] = "pglib_opf_case118_ieee__api.m"
        mp_file = "data/matpower/$(cliargs["case"])"
        REP_cache_fig6(cliargs, mp_file; run_enum=false, run_perm=true)

        return
    end

    if cliargs["problem"] == "REP_cache_fig6e"
        # Add convenient config options 
        cliargs["rerun"] = true
        cliargs["use_separate_budgets"] = true
        
        # Setting
        cliargs["iterline_budget"] = 1
        cliargs["line_budget"] = 4
        cliargs["budget"] = 4
        
        # Case 162
        cliargs["case"] = "pglib_opf_case162_ieee_dtc.m"
        mp_file = "data/matpower/$(cliargs["case"])"
        REP_cache_fig6(cliargs, mp_file; run_enum=false, run_perm=true)
        
        return
    end

    if cliargs["problem"] == "REP_cache_fig6f"
        # Add convenient config options 
        cliargs["rerun"] = true
        cliargs["use_separate_budgets"] = true

        # Setting
        cliargs["iterline_budget"] = 1
        cliargs["line_budget"] = 4
        cliargs["budget"] = 4
        
        # Case 240
        cliargs["case"] = "pglib_opf_case240_pserc.m"
        mp_file= "data/matpower/$(cliargs["case"])"
        REP_cache_fig6(cliargs, mp_file; run_enum=false, run_perm=true)

        return
    end


    # Note: we can re-use REP_cache_fig6 by just changing the budget
    if cliargs["problem"] == "REP_cache_fig7a"
        # Add convenient config options 
        cliargs["rerun"] = true
        cliargs["use_separate_budgets"] = true
        
        # Setting
        cliargs["iterline_budget"] = 1
        cliargs["line_budget"] = 2
        cliargs["budget"] = 2
        
        # Case 14
        cliargs["case"] = "pglib_opf_case14_ieee__api.m"
        mp_file = "data/matpower/$(cliargs["case"])"
        REP_cache_fig6(cliargs, mp_file; run_enum=true, run_perm=true)

        return
    end

    # Note: we can re-use REP_cache_fig6 by just changing the budget
    if cliargs["problem"] == "REP_cache_fig7b"
        # Add convenient config options 
        cliargs["rerun"] = true
        cliargs["use_separate_budgets"] = true

        # Setting
        cliargs["iterline_budget"] = 1
        cliargs["line_budget"] = 2
        cliargs["budget"] = 2
        
        # Case 39
        cliargs["case"] = "pglib_opf_case39_epri__api.m"
        mp_file = "data/matpower/$(cliargs["case"])"
        REP_cache_fig6(cliargs, mp_file; run_enum=true, run_perm=true)

        return
    end

    # Note: we can re-use REP_cache_fig6 by just changing the budget
    if cliargs["problem"] == "REP_cache_fig7c"
        # Add convenient config options 
        cliargs["rerun"] = true
        cliargs["use_separate_budgets"] = true

        # Setting
        cliargs["iterline_budget"] = 1
        cliargs["line_budget"] = 2
        cliargs["budget"] = 2
        
        # Case 60
        cliargs["case"] = "pglib_opf_case60_c.m"
        mp_file = "data/matpower/$(cliargs["case"])"
        REP_cache_fig6(cliargs, mp_file; run_enum=true, run_perm=true)

        return
    end

    # Note: we can re-use REP_cache_fig6 by just changing the budget
    if cliargs["problem"] == "REP_cache_fig7d"
        # Add convenient config options 
        cliargs["rerun"] = true
        cliargs["use_separate_budgets"] = true

        # Setting
        cliargs["iterline_budget"] = 1
        cliargs["line_budget"] = 2
        cliargs["budget"] = 2
        
        # Case 118
        cliargs["case"] = "pglib_opf_case118_ieee__api.m"
        mp_file = "data/matpower/$(cliargs["case"])"
        REP_cache_fig6(cliargs, mp_file; run_enum=true, run_perm=true)

        return
    end

    # Note: we can re-use REP_cache_fig6 by just changing the budget
    if cliargs["problem"] == "REP_cache_fig7e"
        # Add convenient config options 
        cliargs["rerun"] = true
        cliargs["use_separate_budgets"] = true
        
        # Setting
        cliargs["iterline_budget"] = 1
        cliargs["line_budget"] = 2
        cliargs["budget"] = 2
        
        # Case 162
        cliargs["case"] = "pglib_opf_case162_ieee_dtc.m"
        mp_file = "data/matpower/$(cliargs["case"])"
        REP_cache_fig6(cliargs, mp_file; run_enum=true, run_perm=true)
        
        return
    end

    # Note: we can re-use REP_cache_fig6 by just changing the budget
    if cliargs["problem"] == "REP_cache_fig7f"
        # Add convenient config options 
        cliargs["rerun"] = true
        cliargs["use_separate_budgets"] = true

        # Setting
        cliargs["iterline_budget"] = 1
        cliargs["line_budget"] = 2
        cliargs["budget"] = 2
        
        # Case 240
        cliargs["case"] = "pglib_opf_case240_pserc.m"
        mp_file= "data/matpower/$(cliargs["case"])"
        REP_cache_fig6(cliargs, mp_file; run_enum=false, run_perm=true)

        return
    end


    # Note: we can re-use REP_cache_fig6 by just changing the budget
    if cliargs["problem"] == "REP_cache_fig8a"
        # Add convenient config options 
        cliargs["rerun"] = true
        cliargs["use_separate_budgets"] = true
        
        # Setting
        cliargs["iterline_budget"] = 1
        cliargs["line_budget"] = 3
        cliargs["budget"] = 3
        
        # Case 14
        cliargs["case"] = "pglib_opf_case14_ieee__api.m"
        mp_file = "data/matpower/$(cliargs["case"])"
        REP_cache_fig6(cliargs, mp_file; run_enum=true, run_perm=true)

        return
    end

    # Note: we can re-use REP_cache_fig6 by just changing the budget
    if cliargs["problem"] == "REP_cache_fig8b"
        # Add convenient config options 
        cliargs["rerun"] = true
        cliargs["use_separate_budgets"] = true

        # Setting
        cliargs["iterline_budget"] = 1
        cliargs["line_budget"] = 3
        cliargs["budget"] = 3
        
        # Case 39
        cliargs["case"] = "pglib_opf_case39_epri__api.m"
        mp_file = "data/matpower/$(cliargs["case"])"
        REP_cache_fig6(cliargs, mp_file; run_enum=true, run_perm=true)

        return
    end

    # Note: we can re-use REP_cache_fig6 by just changing the budget
    if cliargs["problem"] == "REP_cache_fig8c"
        # Add convenient config options 
        cliargs["rerun"] = true
        cliargs["use_separate_budgets"] = true

        # Setting
        cliargs["iterline_budget"] = 1
        cliargs["line_budget"] = 3
        cliargs["budget"] = 3
        
        # Case 60
        cliargs["case"] = "pglib_opf_case60_c.m"
        mp_file = "data/matpower/$(cliargs["case"])"
        REP_cache_fig6(cliargs, mp_file; run_enum=false, run_perm=true)

        return
    end

    # Note: we can re-use REP_cache_fig6 by just changing the budget
    if cliargs["problem"] == "REP_cache_fig8d"
        # Add convenient config options 
        cliargs["rerun"] = true
        cliargs["use_separate_budgets"] = true

        # Setting
        cliargs["iterline_budget"] = 1
        cliargs["line_budget"] = 3
        cliargs["budget"] = 3
        
        # Case 118
        cliargs["case"] = "pglib_opf_case118_ieee__api.m"
        mp_file = "data/matpower/$(cliargs["case"])"
        REP_cache_fig6(cliargs, mp_file; run_enum=false, run_perm=true)

        return
    end

    # Note: we can re-use REP_cache_fig6 by just changing the budget
    if cliargs["problem"] == "REP_cache_fig8e"
        # Add convenient config options 
        cliargs["rerun"] = true
        cliargs["use_separate_budgets"] = true
        
        # Setting
        cliargs["iterline_budget"] = 1
        cliargs["line_budget"] = 3
        cliargs["budget"] = 3
        
        # Case 162
        cliargs["case"] = "pglib_opf_case162_ieee_dtc.m"
        mp_file = "data/matpower/$(cliargs["case"])"
        REP_cache_fig6(cliargs, mp_file; run_enum=false, run_perm=true)
        
        return
    end

    # Note: we can re-use REP_cache_fig6 by just changing the budget
    if cliargs["problem"] == "REP_cache_fig8f"
        # Add convenient config options 
        cliargs["rerun"] = true
        cliargs["use_separate_budgets"] = true

        # Setting
        cliargs["iterline_budget"] = 1
        cliargs["line_budget"] = 3
        cliargs["budget"] = 3
        
        # Case 240
        cliargs["case"] = "pglib_opf_case240_pserc.m"
        mp_file= "data/matpower/$(cliargs["case"])"
        REP_cache_fig6(cliargs, mp_file; run_enum=false, run_perm=true)

        return
    end

    throw("Problem $(cliargs["problem"]) is not defined")

end

main()
