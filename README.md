# SEQUIN

SEQUIN is a framework leveraging network science principles and physics-based constraint optimization to explore sequential failures in the electric power grid. 
This repository contains code and data for the corresponding ACM/IEEE ICCPS 2025 paper, "SEQUIN: A Network Science and Physics-based Approach to Identify Sequential N-k Attacks in Electric Power Grids". 

## Installation and Setup Instructions (General Use)<a id="installation-and-setup"></a> 

Most of the required software dependencies are included in a Docker image. Please install it [here](https://www.docker.com/) if you do not already have it. 

This project also utilizes the commercial [Gurobi Optimization](https://www.gurobi.com/) solver, and a license will need to be obtained prior to running. In particular, running Gurobi with docker requires a Web License Service (WLS) license. Please first follow the directions [here](https://hub.docker.com/r/gurobi/optimizer) to obtain a WLS license (which should result in a file, `gurobi.lic`). 

To set up the environment for general use, follow the instructions below. If you are interested in the ACM/IEEE ICCPS 2025 Repeatability Evaluation Package (REP), then please skip to [here](#REP) instead.

1. Pull the docker image:
```
docker pull andrewgchio/sequin:v1.0.0
```

2. Create the container without starting it. 
```
docker create -it \
              --name sequin \
              -e DISPLAY=host.docker.internal:0 \
              -v /tmp/.X11-unix:/tmp/.X11-unix 
              --net host \
              andrewgchio/sequin:v1.0.0
```

The `-e`, `-v`, and `--net` flags are needed for the SEQUIN GUI toolkit to be shown properly. Depending on the host machine, the `DISPLAY` variable may also need to modified. However, if you do not plan on using the SEQUIN GUI toolkit, then these flags can be omitted, i.e., 
```
docker create -it --name sequin andrewgchio/sequin:v1.0.0
```

3. Copy the `gurobi.lic` file into the docker container. 
```
docker cp /path/to/gurobi.lic sequin:/opt/gurobi 
```

Here, `/path/to/gurobi.lic` refers to the path that the `gurobi.lic` file is stored. 

4. Start the container. This should open a bash terminal that should be able to run everything.
```
docker start -i sequin
```

5. Clone this repository into the docker image, and move the working directory.
```
git clone https://github.com/andrewgchio/SEQUIN.git
cd SEQUIN
```

6. (Optional) Test that the CLI environment is set up correctly. 
```
julia --project=. src/main.jl --use_separate_budgets --rerun --case pglib_opf_case14_ieee.m --problem traditional -l 2 -k 2
```

The command should run an optimization using Gurobi on the IEEE Case 14 benchmark, and should not produce any errors. 

7. (Optional) Test that the GUI tool is set up correctly.
```
python3 src/visual/main.py
```

The command should open the GUI tool. If there are issues with opening the display, then there may be an issue with X11 forwarding on your system. 

## Command Line Options

This section provides a listing of the different command line options that are provided 

The above command illustrates the intended interface for running code from this project. There are a number of different command line options that are implemented. 

* `--case` This option is used to define a matpower case filename. The case `pglib_opf_case14_ieee.m` is the default. 

    Note: If additional power grid case studies are needed, the [PGLib-OPF](https://github.com/power-grid-lib/pglib-opf) contains a large public repository of benchmark grid case studies that can be downloaded and used. 

* `--data_path` This option defines the path to the data directory. The `data/` directory is the default. 

* `--filetype` This option defines the type of file. `matpower` is the default.

* `--output_path` This option defines the path to the output directory. The `output/` directory is the default. 

* `--problem` This option defines the type of problem that we wish to solve. There are mulitple possible options: <a id="flags-problem"></a> 

    * `SEQUIN` This runs the SEQUIN approach for identifying sequential failures. 

    * `traditional` This runs the standard N-k model, in which the `k` lines are assumed to fail simultaneously or near-simultaneously.
    
    * `permutation` This runs the permutation heuristic, which iterates over all possible permutations of the traditional solution. 

    * `enumeration` This runs an enumeration over all possible permutations of the edges of the given network. It is generally very expensive to use.

    * `criticality` This runs the greedy criticality heuristic, which identifies sequential failures by greedily selecting the line with the highest criticality. 

    * `flow`  This runs the greedy criticality heuristic, which identifies sequential failures by greedily selecting the line with the highest power flow. 

    * `impact` This runs the greedy criticality heuristic, which identifies sequential failures by greedily selecting the line with the highest load shed. 

* `--timeout` This sets a timeout for the optimizer

* `--optimality_gap` This sets the optimality gap for the optimizer

* `--budget`, `-k` This sets the total budget for the interdiction problem.

* `--line_budget` `-l` This sets the line budget for the interdiction problem. Currently, this must be set equal to `--budget`.

* `--use_separate_budgets` This option needs to be set to force separate budgets to be selected. Part of future work will be to extend the model to different types of component failures.

* `--generator_ramping_bounds` This option is a floating point number in [0,1] that determines the degree to which generators can deviate from their current setpoint. 

* `--iterline_budget`, `-m` This option is used to determine if more than one network component should fail at a time.

* `--failed` This is a comma-separated string that sets specific lines to fail. 

* `--rerun` This option needs to be set to allow the code to be re-run. 

* `--do_perturb_loads` This option is a boolean value determining whether loads in the network should first be perturbed before initializing equilibrium.

## GUI Toolkit

The SEQUIN toolkit also includes a GUI to explore the evolution of the grid under the sequential/simultaneous failure of components. The core functions of this toolkit are split into four logical modules. The toolkit in use can be seen in the screenshot below. 

<p align="center">
    <img src="https://github.com/user-attachments/assets/b142d5ae-0a63-4298-a40e-8ed31aa5e384" alt="SEQUIN GUI">
</p>

#### Network Module

The user selects the power grid network to analyze, and manages its layout in the tool. 

* `Load Case` will open a file dialog to load a power grid network file. This should be in the [Matpower](https://matpower.org/) specification, a standardized data format for power system models. This provides details about the network topology and physical attributes of its components. The selected power grid network will be visualized after selection (after a few seconds).

* `Load Layout` and `Save Layout` will allow the user to load/save the layout seen on screen. A case must be loaded previously.

#### Attack Module

This provides the guided exploration of sequential attacks on the grid, which are constructed algorithmically, e.g., using the SEQUIN approach, or fine-tuned manually.

* The `Attack Sequence Editor` lists the lines that fail in the network. The visualized graph will show interdicted (failed) lines with dotted lines (which will be briefly highlighted with red)

* The `Manual Interdiction` menu allows the user to fail particular line components, and modify the generator ramping bounds for the next failure. Various controls (`Reset`, `Undo`, and `Attack`) are also provided to reset, remove, and add line failures to the attack sequence editor. 

Note: Hovering over the buses/branchs in the visualized graph will display their component numbers. 

* The `Algorithmic Interdiction` menu allows the user to fail `k` line components according to a `Strategy`. Descriptions of each strategy are provided in the `--problem` flag of the command line arguments [here](#flags-problem).

* The `Attack Mode` allows the user to select whether the failures are sequential or simultaneous (for comparison purposes).

#### Visual Module

This attack can then be played out using the Visual module, showing the state of the network as the sequential failures occur. 

* The scrollbar (`Failed current failure count / # number of failures`) and controls (`Back`, `Step`, `Stop`, and `Run`) allows users to visualize the evolution of the grid as the sequence of failures occur. 

* The `Bus Node Properties` menu colors the nodes in the graph based on the selected property (listed below). The coloring can be done on an absolute (per unit) or relative (percent) scale. 
    * `Total Load`: colors the node based on the total load present at the node
    * `Load Shed`: colors the node based on the load that has been shed at the node 
    * `Power Generated`: colors the node based on the amount of power a generator co-located at the node produces
    * `Generator Criticality`: colors the node based on the *generator criticality*, a measure of how close the generator is to its production limits (*See more details in the main conference paper.*)
    * `Transmission width`: colors the node based on the *transmission width*, a measure of the degree of difficulty in disconnecting a load from the all other generators (*See more details in the main conference paper.*)

* The `Branch Edge Properties` menu colors the edges in the graph based on the selected property (listed below). The coloring can be done on an absolute (per unit) or relative (percent) scale. 
    * `Thermal Rating`: colors the edge based on the thermal rating limits of the line
    * `Power Flow`: colors the edge based on the power flow on the edge
    * `Branch Criticality`
    * `Branch Criticality`: colors the edge based on the *branch criticality*, a measure of how close the branch is to its thermal limits (*See more details in the main conference paper.*)
    * `Cut Impact`: colors the edge based on the *cut impact*, a measure of how much additional load shed would be incurred by failing the branch. (*See more details in the main conference paper.*) Note that this can take some time to compute. 

### Analysis Module 

This displays plots showing the impact of each failure in sequence on the network. 5 such plots can be created, which compare the sequential and simultaneous failures with respect to: 

* `Show load shed plot`: Plots the total load shed in the grid as the failures occur
* `Show load serviced plot`: Plots the total load that was served to consumers as the failures occur
* `Show generator criticality plot`: Plots the *generator criticality* metric as the failures occur
* `Show branch criticality plot`: Plots the *branch criticality* metric as the failures occur
* `Show total power flow plot`: Plots the total power flow in the grid as the failures occur

## ACM/IEEE ICCPS 2025 Repeatability Evaluation Package (REP)<a id="REP"></a>

A separate docker image is provided for the Repeatability Evaluation Package (REP) for ACM/IEEE ICCPS 2025. This section is meant for those who wish to repeat the experiments conducted in the corresponding ACM/IEEE ICCPS 2025 paper. If you wish to install the SEQUIN tool for general use, please follow the instructions [here](#installation-and-setup) instead.

The DOI generated by Zenodo for the REP release is: https://doi.org/10.5281/zenodo.14836525.

1. Pull the docker image:
```
$ docker pull andrewgchio/iccps-sequin:v1.0.3
```

2. Create the container:
```
docker create -it \
              --name sequin_rep \
              --entrypoint /bin/bash \
              andrewgchio/iccps-sequin:v1.0.3
```

3. Copy the `gurobi.lic` file into the docker container. 
```
docker cp /path/to/gurobi.lic sequin_rep:/opt/gurobi 
```

Here, `/path/to/gurobi.lic` refers to the path that the `gurobi.lic` file is stored.

4. Start the container. This should open a bash terminal that should be able to run everything.
```
docker start -i sequin_rep
```

6. (Optional) Test that the environment is set up correctly.

```
julia --project=. src/REPmain.jl \
      --use_separate_budgets \
      --rerun \
      --case pglib_opf_case14_ieee.m \
      --problem traditional \
      -l 2 -k 2
```

Note that this docker image comes with the source code (i.e., `git clone` is not needed), and that `REPmain.jl` should be used for running. 

7. Run experiments for repeatability. 

Specialized values can be provided as values for the `--problem` flag within the `REPmain.jl` script for the REP. This will run and collect the raw data needed for the main figures/tables in the paper. The output will be stored in the `output/cache` directory, and a separate script (written in Python) must be used to generate plots from the raw data.

The general form of the command is as follows: 
```
julia --project=. src/REPmain.jl --problem REP_cache_fig<num><letter> [--no-enum] [--exp_repeat N]
```

The `--problem` flag determines the which case and data to run. Its value should be in the form of `REP_cache_fig<num><letter>`. The reproducible figure numbers and letters are: `4{ab}`, `5{a-f}`, `6{a-f}`, `7{a-f}` , and `8{a-f}`. Note, for figures `6{a-f}`, `7{a-f}`, and `8{a-f}`, it is recommended to also pass the `--no_enum` flag to avoid running the enumeration case (which can take exponentially long to run).
e.g., for Figure 4a:
```
julia --project=. src/REPmain.jl --problem REP_cache_fig4a
```

The expected runtime of the scripts depends on the size of the network and the value of $k$ as described in the paper. At a high level, scripts that operate on a small networks and/or with small values of `k` will be able to run in < 1 hour. However, scripts that operate on larger networks and/or higher values of `k` can take on the order of a few hours to run. These times are based off of doing 1 run (see the `--exp_repeat` flag to modify this number). 

The `--no_enum` flag will avoid running the `ENUM` baseline, which exhaustively enumerates over all permutations of lines in the network. Running the REP without this command will allow the `ENUM` baseline in the figures to be shown, but it will increase the total runtime to the order of days. 
e.g., for Figure 6a:
```
julia --project=. src/REPmain.jl --problem REP_cache_fig6a --no_enum 
```

The `--exp_repeat N` flag will repeat all experiments N times. If `N` is set to 3, doing this will extend the runtime by a factor of 3. For convenience of running, the default number of runs is set to 1. 
e.g., for Figure 4a:
```
julia --project=. src/REPmain.jl --problem REP_cache_fig4a --exp_repeat 3
```

8. After the scripts to generate the cached data have finished running, the plots used in the paper can be generated with the following command: 
```
python src/experiments/REP_make_plots.py output/cache
```

Here, `output/cache` can be replaced with `output/cache-authors` to use our generated cache files. However, there will be some plots in the paper that may look slightly different than the generated plots. This will likely be most seen in the runs for Case 14. This is generally due to the small size of the benchmark case and the lack of multiple runs (for the REP). This creates a bit of non-determinism in the results, but the general trend still holds. The `GREEDY-Crit` baseline is also sensitive to such changes. Some results may vary. 

## Citations: <a id="citations"></a>

If you use this project, please cite the following papers:

Main conference paper:
```
@inproceedings{chio2025sequin,
  title={SEQUIN: A Network Science and Physics-based Approach to Identify Sequential Nk Attacks in Electric Power Grids},
  author={Chio, Andrew and Bent, Russell and Sundar, Kaarthik and Venkatasubramanian, Nalini},
  booktitle={Proceedings of the ACM/IEEE 16th International Conference on Cyber-Physical Systems (with CPS-IoT Week 2025)},
  pages={1--12},
  year={2025}
}
```

Demo paper:
```
@inproceedings{chio2025sequindemo,
  title={Demo Abstract: SEQUIN: A Network Science and Physics-based Approach to Identify Sequential Nk Attacks in Electric Power Grids},
  author={Chio, Andrew and Bent, Russell and Sundar, Kaarthik and Venkatasubramanian, Nalini},
  booktitle={Proceedings of the ACM/IEEE 16th International Conference on Cyber-Physical Systems (with CPS-IoT Week 2025)},
  pages={1--2},
  year={2025}
}
```
