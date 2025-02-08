# ioutils.jl
#
# Contains utility functions for dealing with IO

""" generate config_data dictionary to write to file from cli-args """
function get_config_data(cliargs::Dict)
    config_data = Dict(
        "case" => cliargs["case"],
        "problem" => cliargs["problem"],
        "budget" => cliargs["budget"],
        "separate_budgets" => cliargs["use_separate_budgets"]
    )
    if cliargs["use_separate_budgets"]
        config_data["line_budget"] = cliargs["line_budget"]
        config_data["generator_budget"] = cliargs["generator_budget"]
    else
        config_data["line_budget"] = NaN
        config_data["generator_budget"] = NaN
    end
    return config_data
end

""" generate output file name from the config_data dictionary """
function get_outfile_name(cd::Dict; ext="json")
    c = replace(first(split(cd["case"], ".")), "_" => "-")
    p = cd["problem"][1:3]
    k = "k" * string(cd["budget"])
    lgk = if cd["separate_budgets"]
        "lk" * string(cd["line_budget"]) * "gk" * string(cd["generator_budget"])
    else
        ""
    end
    (p == "det") && (return join(filter(!=(""), [c, p, k, lgk]), "--") * ".$(ext)")
    return join(filter(!=(""), [c, p, k, lgk]), "--") * ".$(ext)"
end

""" generate run info dictionary to write to file """
function get_run_data(results::Results)
    return Dict(
        "time_ended" => string(now()),
        "objective" => round(results.objective_value * 100.0; digits=4),
        "bound" => round(results.bound * 100.0; digits=4),
        "run_time" => round(results.run_time_in_seconds; digits=2),
        "relative_gap" => round(results.optimality_gap; digits=2),
        "lines" => results.solution.lines,
        "generators" => results.solution.generators
    )
end
