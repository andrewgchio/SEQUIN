using ArgParse

function parse_commandline()
    s = ArgParseSettings()

    project_base = chop(Base.active_project(), tail=length("Project.toml"))

    @add_arg_table s begin
        "--case", "-c"
        help = "case file"
        arg_type = String
        default = "pglib_opf_case14_ieee.m"
        # default = "pglib_opf_case240_pserc.m"

        "--data_path", "-p"
        help = "data directory path"
        arg_type = String
        default = "$(project_base)data/"

        "--filetype", "-f"
        help = "type of file"
        arg_type = String
        default = "matpower"

        "--output_path"
        help = "output directory path"
        arg_type = String
        default = "$(project_base)output/"

        "--problem"
        help = "problem selection - traditional/permutation/enumeration"
        arg_type = String
        default = "permutation"

        "--timeout", "-t"
        help = "time limit for the run in seconds"
        arg_type = Int
        default = 86400

        "--optimality_gap", "-o"
        help = "relative optimality gap in % (termination criteria)"
        arg_type = Float64
        default = 1e-2

        "--budget", "-k"
        help = "budget for interdiction"
        arg_type = Int
        default = 2

        "--use_separate_budgets"
        help = "use separate line and generator budgets - keep to true"
        action = :store_true

        "--line_budget", "-l"
        help = "budget for lines"
        arg_type = Int
        default = 2

        "--generator_budget", "-g"
        help = "budget for generators"
        arg_type = Int
        default = 0

        "--generator_ramping_bounds"
        help = "generation ramping bounds"
        arg_type = Float64
        default = 0.1

        # This is only valid for the permutation N-k
        "--iterline_budget", "-m"
        help = "line budget for an iteration of the permutation N-k"
        arg_type = Int
        default = 1

        "--failed"
        help = "set specific lines to fail, separated by commas"
        arg_type = String
        default = ""

        "--inner_solver"
        help = "cplex/gurobi"
        arg_type = String
        default = "gurobi"
        # default = "cplex"

        "--rerun"
        help = "re-run even if result file already exists"
        action = :store_true
        default = true # Added

        "--log"
        help = "log file for saving intermediate states of the network"
        arg_type = String
        default = "log.log" # nothing

        "--do_perturb_loads"
        help = "true if loads should be perturbed"
        action = :store_true
        default = true # Added

        # This is only for experiments
        "--cache"
        help = "Cache file for an experiment"
        arg_type = String
        default = nothing

        "--no_enum"
        help = "Do not run ENUM experiments"
        action = :store_true
        default = false # Added

        "--exp_repeat"
        help = "Number of times to repeat experiments"
        arg_type = Int
        default = 1
        
    end

    return parse_args(s)
end

function validate_parameters(params)
    mkpath(params["data_path"])
    mkpath(params["output_path"])

    mkpath(params["output_path"] * "/log")
    mkpath(params["output_path"] * "/cache")
    mkpath(params["output_path"] * "/figures")

    case_file = params["data_path"] * params["filetype"] * "/" * params["case"]
    if !isfile(case_file)
        @error "$case_file does not exist, quitting."
        exit()
    end

    k, g, l = params["budget"], params["generator_budget"], params["line_budget"]
    if params["use_separate_budgets"] && k != g + l
        @error "line budget ($l) + generator budget ($g) != budget ($k)"
        exit()
    end

    m = params["iterline_budget"]
    if params["problem"] == "permutation" && m > l
        @error "iteration line budget ($m) is greater than line budget $(l)"
        exit()
    end
end

function get_filenames_with_paths(params)
    mp_file = params["data_path"] * params["filetype"] * "/" * params["case"]
    return (mp_file=mp_file,)
end
