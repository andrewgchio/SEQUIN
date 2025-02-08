# pm_model.jl
#
# The powermodels model for maximum loadability, under a specific generator 
# setpoint and generator ramping bound

function my_build_mld(pm::AbstractPowerModel, setpoints::Dict;
    percent_change=0.1, max_load=nothing)
    variable_bus_voltage(pm)
    variable_branch_power(pm)
    variable_dcline_power(pm)

    variable_gen_indicator(pm)
    variable_gen_power(pm, bounded=false)
    for (i, gen) in ref(pm, nw_id_default, :gen) # Set our own bounds
        pg = PowerModels.var(pm, nw_id_default)[:pg]
        if haskey(setpoints, i)
            # if setpoints[i] == 0 # Generator is turned off
            #     JuMP.set_lower_bound(pg[i], 0.0)
            #     JuMP.set_upper_bound(pg[i], 0.0)
            # else
                JuMP.set_lower_bound(pg[i], gen["pmin"])
                JuMP.set_upper_bound(pg[i], gen["pmax"])
            # end
        else # Setpoints not found
            JuMP.set_lower_bound(pg[i], 0.0)
            JuMP.set_upper_bound(pg[i], 0.0)
        end
    end

    variable_load_power_factor(pm, relax=true)
    variable_shunt_admittance_factor(pm, relax=true)

    if max_load === nothing
        objective_max_loadability(pm)
    else
        objective_min_fuel_cost(pm)
        my_constraint_max_loadability(pm, max_load)
    end

    constraint_model_voltage(pm)

    for i in ids(pm, :ref_buses)
        constraint_theta_ref(pm, i)
    end

    for i in ids(pm, :bus)
        constraint_power_balance_ls(pm, i)
    end

    for (i, gen) in ref(pm, nw_id_default, :gen) # custom bounds
        constraint_gen_power_on_off(pm, nw_id_default, i,
            max(gen["pmin"], setpoints[i] - percent_change * gen["pmax"]),
            min(gen["pmax"], setpoints[i] + percent_change * gen["pmax"]),
            gen["qmin"],
            gen["qmax"]
        )
    end

    for i in ids(pm, :branch)
        constraint_ohms_yt_from(pm, i)
        constraint_ohms_yt_to(pm, i)

        constraint_voltage_angle_difference(pm, i)

        constraint_thermal_limit_from(pm, i)
        constraint_thermal_limit_to(pm, i)
    end

    for i in ids(pm, :dcline)
        constraint_dcline_power_losses(pm, i)
    end
end

function my_constraint_max_loadability(pm::AbstractPowerModel, max_load::Float64)
    nws = nw_ids(pm)

    z_demand = Dict(n => var(pm, n, :z_demand) for n in nws)
    z_shunt = Dict(n => var(pm, n, :z_shunt) for n in nws)
    time_elapsed = Dict(n => get(ref(pm, n), :time_elapsed, 1) for n in nws)

    load_weight = Dict(n => Dict(i => get(load, "weight", 1.0)
                                 for (i, load) in ref(pm, n, :load))
                       for n in nws)

    # Convert objective to constraint
    JuMP.@constraint(pm.model,
        sum(
            (
                time_elapsed[n] * (
                    sum(z_shunt[n][i] for (i, shunt) in ref(pm, n, :shunt)) +
                    sum(load_weight[n][i] * abs(load["pd"]) * z_demand[n][i] for (i, load) in ref(pm, n, :load))
                )
            )
            for n in nws)
        >=
        max_load
    )
end
