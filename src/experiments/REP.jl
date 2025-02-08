# REP.jl
# 
# This code is used to reconstruct figures, etc. 

# using CairoMakie
# using CSV, DataFrames
using BenchmarkTools

function REP_cache_fig4(cliargs::Dict, mp_file::String)
    fcache = cliargs["output_path"] * "cache/" * first(split(cliargs["case"], ".")) * "_exp0.csv"
    open(fcache, "w") do f
        # Write header
        write(f, "k,percent_change,problem,load_shed,permutation\n")

        k = cliargs["budget"]
        pc = cliargs["generator_ramping_bounds"]

        # Get traditional solution (simultaneous)
        trad_soln = run_traditional(cliargs, mp_file)
        ls = trad_soln.solution.load_shed
        l_str = join(trad_soln.solution.lines, ";")
        write(f, "$(k),$(pc),standard,$(ls),$(l_str)\n")
        flush(f)

        # Get permutation solutions - with the same traditional solution
        cliargs["failed"] = join(trad_soln.solution.lines, ",")
        perm_soln = run_permutation(cliargs, mp_file)
        for (po, s) in perm_soln.solution.solutions
            ls = s.load_shed
            porder_str = join([join(o, "/") for o in po], ";")
            write(f, "$(k),$(pc),permutation,$(ls),$(porder_str)\n")
            flush(f)
        end
        cliargs["failed"] = ""

        # Get enumeration solution only if k <= 3
        if cliargs["budget"] <= 3
            enum_soln = run_enumeration(cliargs, mp_file)
            for (po, s) in enum_soln.solution.solutions
                ls = s.load_shed
                porder_str = join([join(o, "/") for o in po], ";")
                write(f, "$(k),$(pc),enumeration,$(ls),$(porder_str)\n")
                flush(f)
            end
        end

    end

end

function REP_cache_fig5(cliargs::Dict, mp_file::String; enum_bound=1,perm_bound=1)
    ks = [2,3,4,5,6,7,8]
    pc = 0.1

    fcache = cliargs["output_path"] * "cache/" * first(split(cliargs["case"], ".")) * "_exp1.csv"
    open(fcache, "w") do f
        # Write header
        write(f, "k,percent_change,problem,load_shed,permutation\n")

        for k in ks
            # Set budget 
            cliargs["iterline_budget"] = 1
            cliargs["line_budget"] = k
            cliargs["budget"] = k

            # Get traditional solution
            for _ in 1:cliargs["exp_repeat"]
                trad_soln = run_traditional(cliargs, mp_file)
                ls = trad_soln.solution.load_shed
                l_str = join(trad_soln.solution.lines, ";")
                write(f, "$(k),$(pc),standard,$(ls),$(l_str)\n")
                flush(f)
            end

            # Get permutation solutions - with the same traditional solution
            if k <= perm_bound
                for _ in 1:cliargs["exp_repeat"]
                    trad_soln = run_traditional(cliargs, mp_file)
                    cliargs["failed"] = join(trad_soln.solution.lines, ",")
                    perm_soln = run_permutation(cliargs, mp_file)
                    for (po, s) in perm_soln.solution.solutions
                        ls = s.load_shed
                        porder_str = join([join(o, "/") for o in po], ";")
                        write(f, "$(k),$(pc),permutation,$(ls),$(porder_str)\n")
                        flush(f)
                    end
                    cliargs["failed"] = ""
                end
            end
            
            # Get enumeration solutions
            if k <= enum_bound && !cliargs["no_enum"]
                for _ in 1:cliargs["exp_repeat"]
                    enum_soln = run_enumeration(cliargs, mp_file)
                    for (po, s) in enum_soln.solution.solutions
                        ls = s.load_shed
                        porder_str = join([join(o, "/") for o in po], ";")
                        write(f, "$(k),$(pc),enumeration,$(ls),$(porder_str)\n")
                        flush(f)
                    end
                end
            end

            # Get the greedy flow solution
            for _ in 1:cliargs["exp_repeat"]
                try
                    flow_soln = run_greedy_flow(cliargs, mp_file)
                    for (po,s) in flow_soln.solution.solutions
                        ls = s.load_shed
                        porder_str = join([join(o, "/") for o in po], ";")
                        write(f, "$(k),$(pc),greedy_flow,$(ls),$(porder_str)\n")
                        flush(f)
                    end
                catch
                end
            end

            # Get the greedy load shed solution
            for _ in 1:cliargs["exp_repeat"]
                try
                imp_soln = run_greedy_impact(cliargs, mp_file)
                for (po,s) in imp_soln.solution.solutions
                    ls = s.load_shed
                    porder_str = join([join(o, "/") for o in po], ";")
                    write(f, "$(k),$(pc),greedy_impt,$(ls),$(porder_str)\n")
                    flush(f)
                end
                catch 
                end
            end

            # Get the greedy criticality solution
            for _ in 1:cliargs["exp_repeat"]
                try
                crit_soln = run_greedy_criticality(cliargs, mp_file)
                for (po,s) in crit_soln.solution.solutions
                    ls = s.load_shed
                    porder_str = join([join(o, "/") for o in po], ";")
                    write(f, "$(k),$(pc),greedy_crit,$(ls),$(porder_str)\n")
                    flush(f)
                end
                catch 
                end
            end

            # Get our solution
            for _ in 1:cliargs["exp_repeat"]
                sequin_soln = run_approach(cliargs, mp_file)
                for (po,s) in sequin_soln.solution.solutions
                    ls = s.load_shed
                    porder_str = join([join(o, "/") for o in po], ";")
                    write(f, "$(k),$(pc),sequin,$(ls),$(porder_str)\n")
                    flush(f)
                end
            end

        end
    end
end

function REP_cache_fig6(cliargs::Dict, mp_file::String; run_enum=true,run_perm=true)
    k = cliargs["budget"]
    percent_changes = 1.0:-0.05:0.0

    fcache = cliargs["output_path"] * "cache/" * first(split(cliargs["case"], ".")) * "_exp2_k$(k).csv"
    open(fcache, "w") do f
        # Write header
        write(f, "k,percent_change,problem,load_shed,permutation\n")

        for pc in percent_changes
            # Set budget 
            cliargs["iterline_budget"] = 1
            cliargs["line_budget"] = k
            cliargs["budget"] = k

            cliargs["generator_ramping_bounds"] = pc

            # Get traditional solution
            for _ in 1:cliargs["exp_repeat"]
                trad_soln = run_traditional(cliargs, mp_file)
                ls = trad_soln.solution.load_shed
                l_str = join(trad_soln.solution.lines, ";")
                write(f, "$(k),$(pc),standard,$(ls),$(l_str)\n")
                flush(f)
            end

            # Get permutation solutions - with the same traditional solution
            if run_perm
                for _ in 1:cliargs["exp_repeat"]
                    trad_soln = run_traditional(cliargs, mp_file)
                    cliargs["failed"] = join(trad_soln.solution.lines, ",")
                    perm_soln = run_permutation(cliargs, mp_file)
                    for (po, s) in perm_soln.solution.solutions
                        ls = s.load_shed
                        porder_str = join([join(o, "/") for o in po], ";")
                        write(f, "$(k),$(pc),permutation,$(ls),$(porder_str)\n")
                        flush(f)
                    end
                    cliargs["failed"] = ""
                end
            end

            # Get enumeration solutions
            if run_enum && !cliargs["no_enum"]
                for _ in 1:cliargs["exp_repeat"]
                    enum_soln = run_enumeration(cliargs, mp_file)
                    for (po, s) in enum_soln.solution.solutions
                        ls = s.load_shed
                        porder_str = join([join(o, "/") for o in po], ";")
                        write(f, "$(k),$(pc),enumeration,$(ls),$(porder_str)\n")
                        flush(f)
                    end
                end
            end

            # Get the greedy flow solution
            for _ in 1:cliargs["exp_repeat"]
                try
                    flow_soln = run_greedy_flow(cliargs, mp_file)
                    for (po,s) in flow_soln.solution.solutions
                        ls = s.load_shed
                        porder_str = join([join(o, "/") for o in po], ";")
                        write(f, "$(k),$(pc),greedy_flow,$(ls),$(porder_str)\n")
                        flush(f)
                    end
                catch
                end
            end

            # Get the greedy load shed solution
            for _ in 1:cliargs["exp_repeat"]
                try
                imp_soln = run_greedy_impact(cliargs, mp_file)
                for (po,s) in imp_soln.solution.solutions
                    ls = s.load_shed
                    porder_str = join([join(o, "/") for o in po], ";")
                    write(f, "$(k),$(pc),greedy_impt,$(ls),$(porder_str)\n")
                    flush(f)
                end
                catch 
                end
            end

            # Get the greedy criticality solution
            for _ in 1:cliargs["exp_repeat"]
                try
                crit_soln = run_greedy_criticality(cliargs, mp_file)
                for (po,s) in crit_soln.solution.solutions
                    ls = s.load_shed
                    porder_str = join([join(o, "/") for o in po], ";")
                    write(f, "$(k),$(pc),greedy_crit,$(ls),$(porder_str)\n")
                    flush(f)
                end
                catch 
                end
            end

            # Get our solution
            for _ in 1:cliargs["exp_repeat"]
                sequin_soln = run_approach(cliargs, mp_file)
                for (po,s) in sequin_soln.solution.solutions
                    ls = s.load_shed
                    porder_str = join([join(o, "/") for o in po], ";")
                    write(f, "$(k),$(pc),sequin,$(ls),$(porder_str)\n")
                    flush(f)
                end
            end


        end

    end

end

function REP_cache_tab2(cliargs::Dict, mp_file::String)
    ks = [3,4]
    percent_changes = 1.0:-0.05:0.0

    fcache = cliargs["output_path"] * "cache/" * first(split(cliargs["case"], ".")) * "_exp3.csv"
    open(fcache, "w") do f
        # Write header
        write(f, "k,percent_change,problem,time\n")

        for k in ks
            for pc in percent_changes
                # Set budget 
                cliargs["iterline_budget"] = 1
                cliargs["line_budget"] = k
                cliargs["budget"] = k

                # Set percent change
                cliargs["generator_ramping_bounds"] = pc

                # Get traditional solution
                for _ in 1:cliargs["exp_repeat"]
                    time_std = @belapsed run_traditional($cliargs, $mp_file)
                    write(f, "$(k),$(pc),standard,$(time_std)\n")
                    flush(f)
                end

                # Get permutation solutions - with the same traditional solution
                for _ in 1:cliargs["exp_repeat"]
                    trad_soln = run_traditional(cliargs, mp_file)
                    cliargs["failed"] = join(trad_soln.solution.lines, ",")
                    time_perm = @belapsed run_permutation($cliargs, $mp_file)
                    write(f, "$(k),$(pc),permutation,$(time_perm)\n")
                    flush(f)
                    cliargs["failed"] = ""
                end

                # Get the greedy flow solution
                for _ in 1:cliargs["exp_repeat"]
                    try
                        time_flow = @belapsed run_greedy_flow($cliargs, $mp_file)
                        write(f, "$(k),$(pc),greedy_flow,$(time_flow)\n")
                        flush(f)
                    catch end
                end

                # Get the greedy load shed solution
                for _ in 1:cliargs["exp_repeat"]
                    try
                        time_imp = @belapsed run_greedy_impact($cliargs, $mp_file)
                        write(f, "$(k),$(pc),greedy_impt,$(time_imp)\n")
                        flush(f)
                    catch end
                end

                # Get the greedy criticality solution
                for _ in 1:cliargs["exp_repeat"]
                    try
                        time_crit = @belapsed run_greedy_criticality($cliargs, $mp_file)
                        write(f, "$(k),$(pc),greedy_crit,$(time_crit)\n")
                        flush(f)
                    catch end
                end

                for _ in 1:cliargs["exp_repeat"]
                    time_sequin = @belapsed run_approach($cliargs, $mp_file)
                    write(f, "$(k),$(pc),sequin,$(time_sequin)\n")
                    flush(f)
                end

            end
        end
    end

end