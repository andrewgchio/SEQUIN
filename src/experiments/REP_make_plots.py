# make_plots.py
# 
# Used to generate plots for the experiments. Utilizes cache files in 
# output/cache to quickly produce plots

import sys
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.ticker import PercentFormatter

TITLE_FONTSIZE = 14
AXIS_FONTSIZE = 14
LEGEND_FONTSIZE = 12

EXP1_CASES = [
    "pglib_opf_case14_ieee__api.m",
    "pglib_opf_case39_epri__api.m",
    "pglib_opf_case60_c.m",
    "pglib_opf_case118_ieee__api.m",
    "pglib_opf_case162_ieee_dtc.m",
    "pglib_opf_case240_pserc.m",
]

EXP2_CASES = [
    "pglib_opf_case14_ieee__api.m",
    "pglib_opf_case39_epri__api.m",
    "pglib_opf_case60_c.m",
    "pglib_opf_case118_ieee__api.m",
    "pglib_opf_case162_ieee_dtc.m",
    "pglib_opf_case240_pserc.m",
]

EXP3_CASES = [
    "pglib_opf_case39_epri__api.m",
    "pglib_opf_case118_ieee__api.m",
]

################################################################################
# General Utils 
################################################################################

def setup_pandas():
    pd.set_option('display.max_rows',    5000)
    pd.set_option('display.max_columns', 1000)
    pd.set_option('display.width',       1500)

def get_percent_change(old,new):
    return ((new-old) / old ) * 100

def get_percent_difference(a,b):
    return abs(a-b) / ((a+b)/2)

def export_legend(legend, fname="legend.png"):
    fig  = legend.figure
    fig.canvas.draw()
    bbox = legend.get_window_extent().transformed(fig.dpi_scale_trans.inverted())
    fig.savefig(fname, bbox_inches=bbox)

################################################################################
# I/O 
################################################################################

def get_fcache_exp0(case, cache_dir='cache'):
    return f'./output/{cache_dir}/{case.split(".")[0]}_exp0.csv'
def get_fcache_exp1(case, cache_dir='cache'):
    return f'./output/{cache_dir}/{case.split(".")[0]}_exp1.csv'
def get_fcache_exp2(case, k=4, cache_dir='cache'):
    return f'./output/{cache_dir}/{case.split(".")[0]}_exp2_k{k}.csv'
def get_fcache_exp3(case, cache_dir='cache'):
    return f'./output/{cache_dir}/{case.split(".")[0]}_exp3.csv'

def get_fplot_exp0(case, format='png'):
    return f'./output/figures/{case.split(".")[0]}_exp0.{format}'
def get_fplot_exp1(case, format='png'):
    return f'./output/figures/{case.split(".")[0]}_exp1.{format}'
def get_fplot_exp2(case, k, format='png'):
    return f'./output/figures/{case.split(".")[0]}_exp2_k{k}.{format}'

def get_fplot_exp1_legend(format='png'):
    return f'./output/figures/exp1_legend.{format}'
def get_fplot_exp2_legend(format='png'):
    return f'./output/figures/exp2_legend.{format}'

def save_to_file(fname, fig):
    fig.savefig(fname, bbox_inches='tight')

################################################################################
# Plotting
################################################################################

def make_experiment0_plots(save=False, show=False, cache_dir='cache'):

    # General parameters
    figsize = (5,2.25)

    ############################################################################
    # Case 39 EPRI API
    ############################################################################
    case = "pglib_opf_case39_epri__api.m"
    print(f'Case {case}')
    X = pd.read_csv(get_fcache_exp0(case, cache_dir=cache_dir))

    fig,ax = plt.subplots(1,1, figsize=figsize)
    ax.set_xlabel('Load Shed (per unit)', fontsize=AXIS_FONTSIZE)
    ax.set_ylabel('Frequency', fontsize=AXIS_FONTSIZE)
    ax.set_title(case, fontsize=TITLE_FONTSIZE)

    bins = np.linspace(0, 40, 100)
    loads = list(range(0, 41, 10))
    freqs = list(range(0,5))

    # Plot enumeration cases histogram
    Xenum = X[X['problem'] == 'enumeration']
    enum_ls = Xenum['load_shed']
    weights=np.ones_like(enum_ls)*100 / len(enum_ls)
    ax.hist(enum_ls, bins=bins, weights=weights, color='blue', label='ENUM')

    # Plot permutation cases histogram
    Xperm = X[X['problem'] == 'permutation']
    perm_ls = Xperm['load_shed'] # But this is only one value though
    ax.axvline(x=perm_ls.max(), color='blue', label="PERM", ls='--')

    # Plot standard case as vertical line
    Xdet = X[X['problem'] == 'standard']
    det_ls = next(iter(Xdet['load_shed']))
    ax.axvline(x=det_ls, color='red', label="STD")

    ax.set_xticks(loads)
    ax.set_yticks(freqs)
    ax.set_xticklabels(ax.get_xticks(), rotation=45, fontdict={'fontsize':AXIS_FONTSIZE})
    ax.set_yticklabels(ax.get_yticks(), fontdict={'fontsize':AXIS_FONTSIZE})
    ax.yaxis.set_major_formatter(PercentFormatter(decimals=0))

    ax.legend(fontsize=LEGEND_FONTSIZE, loc='upper right')

    if save:
        save_to_file(get_fplot_exp0(case), fig)

    if show:
        plt.show()
    
    ############################################################################
    # Case 118 IEEE API
    ############################################################################
    case = "pglib_opf_case118_ieee__api.m"
    print(f'Case {case}')
    X = pd.read_csv(get_fcache_exp0(case, cache_dir=cache_dir))

    fig,ax = plt.subplots(1,1, figsize=figsize)
    ax.set_xlabel('Load Shed (per unit)', fontsize=AXIS_FONTSIZE)
    ax.set_ylabel('Frequency', fontsize=AXIS_FONTSIZE)
    ax.set_title(case, fontsize=TITLE_FONTSIZE)

    bins = np.linspace(25, 45, 100)
    loads = list(np.arange(25,46,5))
    freqs = list(range(0,6))

    # Plot permutation cases histogram
    Xperm = X[X['problem'] == 'permutation']
    perm_ls = Xperm['load_shed']
    weights=np.ones_like(perm_ls)*100 / len(perm_ls)
    ax.hist(perm_ls, bins=bins, weights=weights, color='blue', label="PERM")

    # Plot standard case as vertical line
    Xdet = X[X['problem'] == 'standard']
    det_ls = next(iter(Xdet['load_shed']))
    ax.axvline(x=det_ls, color='red', label="STD")

    ax.set_xticks(loads)
    ax.set_yticks(freqs)
    ax.set_xticklabels(ax.get_xticks(), rotation=45, fontdict={'fontsize':AXIS_FONTSIZE})
    ax.set_yticklabels(ax.get_yticks(), fontdict={'fontsize':AXIS_FONTSIZE})
    ax.yaxis.set_major_formatter(PercentFormatter(decimals=0))

    ax.legend(fontsize=LEGEND_FONTSIZE, loc='upper right')

    if save:
        save_to_file(get_fplot_exp0(case), fig)

    if show:
        plt.show()

def make_experiment1_plots(save=False, show=False, 
                           show_legend=False, save_legend=True, 
                           cache_dir='cache', mode='max'):
    ############################################################################
    # General Parameters
    ############################################################################

    figsize = (4,2.5)

    ks = list(range(2,7))

    SEQUIN_KWARGS = { 'label' : 'SEQUIN', 'marker' : 'v', 'markersize' : 6, 'color': 'black'}
    STD_KWARGS = { 'label' : 'STD', 'marker' : '*', 'markersize' : 6, 'color': 'orange'}
    ENUM_KWARGS = { 'label' : 'ENUM', 'marker' : 's', 'markersize' : 6, 'color': 'blue'}
    PERM_KWARGS = { 'label' : 'PERM', 'marker' : '.', 'markersize' : 6, 'color': 'green'}
    FLOW_KWARGS = { 'label' : 'Greedy-FLOW', 'marker' : '.', 'markersize' : 6, 'color' : 'purple'}
    SHED_KWARGS = { 'label' : 'Greedy-SHED', 'marker' : '.', 'markersize' : 6, 'color' : 'red'}
    CRIT_KWARGS = { 'label' : 'Greedy-CRIT', 'marker' : '.', 'markersize' : 6, 'color' : 'grey'}

    ############################################################################
    # Collect values for percent difference
    ############################################################################

    # a list of each network evaluated. each list is another list of k=2..8
    SEQUIN_VALS = []
    STD_VALS = []
    PERM_VALS = []
    FLOW_VALS = []
    SHED_VALS = []
    CRIT_VALS = []

    ############################################################################
    # Generate plots
    ############################################################################

    for case in EXP1_CASES:
        print(f'Case {case}')
        # All data in exp 2 files...
        X = pd.read_csv(get_fcache_exp1(case, cache_dir=cache_dir))

        # Limit to k > 1 and percent_change = 0.1, and sort
        X = X[(X['k'] > 1) & (X['percent_change'] == 0.1)]
        X.sort_values('k', inplace=True)

        fig,ax = plt.subplots(1,1, figsize=figsize)
        ax.set_xlabel('k', fontsize=AXIS_FONTSIZE)
        ax.set_ylabel('Load Shed (per unit)', fontsize=AXIS_FONTSIZE)
        ax.set_title(case, fontsize=TITLE_FONTSIZE)

        # Plot enumeration case
        Xenum = X[X['problem'] == 'enumeration']
        if Xenum.shape[0] > 0:
            Xenum = Xenum.groupby('k') \
                        .agg({'load_shed' : lambda x : list(x)}) \
                        .reset_index()
            if mode == 'max':
                Xenum['max_load_shed'] = Xenum['load_shed'].apply(max)
                ax.plot(Xenum['k'], Xenum['max_load_shed'], **ENUM_KWARGS)
            elif mode == 'range':
                Xenum['avg_load_shed'] = Xenum['load_shed'].apply(lambda x : np.mean(x))
                Xenum['lower_load_shed'] = Xenum['load_shed'].apply(lambda x : round(np.mean(x) - np.min(x), 5))
                Xenum['upper_load_shed'] = Xenum['load_shed'].apply(lambda x : round(np.max(x) - np.mean(x), 5))
                ax.errorbar(Xenum['k'], Xenum['avg_load_shed'], yerr=[Xenum['lower_load_shed'], Xenum['upper_load_shed']], \
                            capsize=4, fmt="r--o", ecolor = "black", **ENUM_KWARGS)

        # Plot standard case
        Xdet = X[X['problem'] == 'standard']
        ax.plot(Xdet['k'], Xdet['load_shed'], **STD_KWARGS)
        STD_VALS.append(max(Xdet['load_shed']))

        # Plot enumeration case
        Xperm = X[X['problem'] == 'permutation']
        Xperm = Xperm.groupby('k') \
                    .agg({'load_shed' : lambda x : list(x)}) \
                    .reset_index()
        PERM_VALS.append(Xperm['load_shed'].apply(max).to_list())
        if mode == 'max':
            Xperm['max_load_shed'] = Xperm['load_shed'].apply(max)
            ax.plot(Xperm['k'], Xperm['max_load_shed'], **PERM_KWARGS)
        elif mode == 'range':
            Xperm['avg_load_shed'] = Xperm['load_shed'].apply(lambda x : np.mean(x))
            Xperm['lower_load_shed'] = Xperm['load_shed'].apply(lambda x : round(np.mean(x) - np.min(x), 5))
            Xperm['upper_load_shed'] = Xperm['load_shed'].apply(lambda x : round(np.max(x) - np.mean(x), 5))
            ax.errorbar(Xperm['k'], Xperm['avg_load_shed'], yerr=[Xperm['lower_load_shed'], Xperm['upper_load_shed']], \
                        capsize=4, fmt="r--o", ecolor = "black", **PERM_KWARGS)

        # Plot greedy flow load shed
        Xflow = X[X['problem'] == 'greedy_flow']
        Xflow = Xflow.groupby('k') \
                .agg({'load_shed':lambda x : list(x)}) \
                .reset_index()
        FLOW_VALS.append(Xflow['load_shed'].apply(max).to_list())
        if mode == 'max':
            Xflow['max_load_shed'] = Xflow['load_shed'].apply(max)
            ax.plot(Xflow['k'], Xflow['max_load_shed'], **FLOW_KWARGS)
        elif mode == 'range':
            Xflow['avg_load_shed'] = Xflow['load_shed'].apply(lambda x : np.mean(x))
            Xflow['min_load_shed'] = Xflow['load_shed'].apply(lambda x : round(np.mean(x) - np.min(x), 5))
            Xflow['max_load_shed'] = Xflow['load_shed'].apply(lambda x : round(np.max(x) - np.mean(x), 5))
            ax.errorbar(Xflow['k'], Xflow['avg_load_shed'], yerr=[Xflow['min_load_shed'], Xflow['max_load_shed']], \
                        capsize=4, fmt="r--o", ecolor = "black", **FLOW_KWARGS)
        
        # Plot greedy load shed 
        Ximp = X[X['problem'] == 'greedy_impt']
        Ximp = Ximp.groupby('k') \
                .agg({'load_shed':lambda x : list(x)}) \
                .reset_index()
        SHED_VALS.append(Ximp['load_shed'].apply(max).to_list())
        if mode == 'max':
            Ximp['max_load_shed'] = Ximp['load_shed'].apply(max)
            ax.plot(Ximp['k'], Ximp['max_load_shed'], **SHED_KWARGS)
        elif mode == 'range':
            Ximp['avg_load_shed'] = Ximp['load_shed'].apply(lambda x : np.mean(x))
            Ximp['min_load_shed'] = Ximp['load_shed'].apply(lambda x : round(np.mean(x) - np.min(x), 5))
            Ximp['max_load_shed'] = Ximp['load_shed'].apply(lambda x : round(np.max(x) - np.mean(x), 5))
            ax.errorbar(Ximp['k'], Ximp['avg_load_shed'], yerr=[Ximp['min_load_shed'], Ximp['max_load_shed']], \
                        capsize=4, fmt="r--o", ecolor = "black", **SHED_KWARGS)
        
        # Plot greedy load shed 
        Xcrit = X[X['problem'] == 'greedy_crit']
        Xcrit = Xcrit.groupby('k') \
                .agg({'load_shed':lambda x : list(x)}) \
                .reset_index()
        CRIT_VALS.append(Xcrit['load_shed'].apply(max).to_list())
        if mode == 'max':
            Xcrit['max_load_shed'] = Xcrit['load_shed'].apply(max)
            ax.plot(Xcrit['k'], Xcrit['max_load_shed'], **CRIT_KWARGS)
        elif mode == 'range':
            Xcrit['avg_load_shed'] = Xcrit['load_shed'].apply(lambda x : np.mean(x))
            Xcrit['min_load_shed'] = Xcrit['load_shed'].apply(lambda x : round(np.mean(x) - np.min(x), 5))
            Xcrit['max_load_shed'] = Xcrit['load_shed'].apply(lambda x : round(np.max(x) - np.mean(x), 5))
            ax.errorbar(Xcrit['k'], Xcrit['avg_load_shed'], yerr=[Xcrit['min_load_shed'], Xcrit['max_load_shed']], \
                        capsize=4, fmt="r--o", ecolor = "black", **CRIT_KWARGS)

        # Plot SEQUIN
        Xsequin = X[X['problem'] == 'sequin']
        Xsequin = Xsequin.groupby('k') \
                .agg({'load_shed':lambda x : list(x)}) \
                .reset_index()
        SEQUIN_VALS.append(Xsequin['load_shed'].apply(max).to_list())
        if mode == 'max':
            Xsequin['max_load_shed'] = Xsequin['load_shed'].apply(max)
            ax.plot(Xsequin['k'], Xsequin['max_load_shed'], **SEQUIN_KWARGS)
        elif mode == 'range':
            Xsequin['avg_load_shed'] = Xsequin['load_shed'].apply(lambda x : np.mean(x))
            Xsequin['min_load_shed'] = Xsequin['load_shed'].apply(lambda x : round(np.mean(x) - np.min(x), 5))
            Xsequin['max_load_shed'] = Xsequin['load_shed'].apply(lambda x : round(np.max(x) - np.mean(x), 5))
            ax.errorbar(Xsequin['k'], Xsequin['avg_load_shed'], yerr=[Xsequin['min_load_shed'], Ximp['max_load_shed']], \
                        capsize=4, fmt="r--o", ecolor = "black", **SEQUIN_KWARGS)
            
        ax.tick_params(axis='both', which='major', labelsize=AXIS_FONTSIZE)

        if show_legend:
            ax.legend(fontsize=LEGEND_FONTSIZE)

        if save:
            save_to_file(get_fplot_exp1(case), fig)

        if show:
            plt.show()

    # create a new figure and save its legend
    if save_legend:
        fig, ax = plt.subplots(1,1)

        ax.plot([1],[1], **SEQUIN_KWARGS)
        ax.plot([1],[1], **STD_KWARGS)
        ax.plot([1],[1], **ENUM_KWARGS)
        ax.plot([1],[1], **PERM_KWARGS)
        ax.plot([1],[1], **FLOW_KWARGS)
        ax.plot([1],[1], **SHED_KWARGS)
        ax.plot([1],[1], **CRIT_KWARGS)

        lines_labels = [fig.axes[0].get_legend_handles_labels()]
        lines, labels = [sum(lol, []) for lol in zip(*lines_labels)]
        legend = fig.legend(lines, labels, 
                                fontsize=LEGEND_FONTSIZE, loc='right', 
                                bbox_to_anchor = (1.5, 0.5))
        export_legend(legend, fname=get_fplot_exp1_legend())
        plt.close()
    
def make_experiment2_plots(save=False, show=False, 
                           show_legend=False, save_legend=True,
                           cache_dir='cache', mode='max', k=4):
    ############################################################################
    # General Parameters
    ############################################################################
    figsize = (4,2.5)

    grb = list(np.arange(0, 101, 5)/100)

    SEQUIN_KWARGS = { 'label' : 'SEQUIN', 'marker' : 'v', 'markersize' : 6, 'color': 'black'}
    STD_KWARGS  = { 'label' : 'STD', 'marker' : '*', 'markersize' : 6, 'color': 'orange'}
    ENUM_KWARGS = { 'label' : 'ENUM', 'marker' : 's', 'markersize' : 6, 'color': 'blue'}
    PERM_KWARGS = { 'label' : 'PERM', 'marker' : '.', 'markersize' : 5, 'color': 'green'}
    FLOW_KWARGS = { 'label' : 'Greedy-FLOW', 'marker' : '.', 'markersize' : 4, 'color' : 'purple'}
    SHED_KWARGS = { 'label' : 'Greedy-SHED', 'marker' : '.', 'markersize' : 3, 'color' : 'red'}
    CRIT_KWARGS = { 'label' : 'Greedy-CRIT', 'marker' : '.', 'markersize' : 2, 'color' : 'grey'}

    SEQUIN_VALS = []
    STD_VALS = []
    PERM_VALS = []
    FLOW_VALS = []
    SHED_VALS = []
    CRIT_VALS = []

    ############################################################################
    # Generate plots
    ############################################################################

    for case in EXP2_CASES:
        print(f'Case {case}')
        X = pd.read_csv(get_fcache_exp2(case, k=k, cache_dir=cache_dir), 
                        dtype={
                            'k': 'int', 
                            'percent_change':'float', 
                            'problem': 'str', 
                            'load_shed':'float', 
                            'permutation':'str'
                        }
        )

        # We only care about k=4, but let's generate all of them anyways
        for k,Xk in X.groupby('k'):
            if k == 1:
                continue 

            print(f"k = {k}")
            Xk.sort_values(['percent_change', 'load_shed'], inplace=True)

            # Note: for now, ignore the actual permutation
            fig,ax = plt.subplots(1,1, figsize=figsize)
            ax.set_xlabel('Generator Ramping Bounds', fontsize=AXIS_FONTSIZE)
            ax.set_ylabel('Load Shed (per unit)', fontsize=AXIS_FONTSIZE)
            ax.set_title(case, fontsize=TITLE_FONTSIZE)

            # Plot enumeration case if exists
            Xenum = Xk[Xk['problem'] == 'enumeration']
            if Xenum.shape[0] > 0: 
                Xenum = Xenum.groupby(['k', 'percent_change']) \
                        .agg({'load_shed':lambda x : list(x)}) \
                        .reset_index()
                if mode == 'max':
                    Xenum['max_load_shed'] = Xenum['load_shed'].apply(max)
                    ax.plot(Xenum['percent_change'], Xenum['max_load_shed'], **ENUM_KWARGS)
                elif mode == 'range':
                    Xenum['avg_load_shed'] = Xenum['load_shed'].apply(lambda x : np.mean(x))
                    Xenum['lower_load_shed'] = Xenum['load_shed'].apply(lambda x : round(np.mean(x) - np.min(x), 5))
                    Xenum['upper_load_shed'] = Xenum['load_shed'].apply(lambda x : round(np.max(x) - np.mean(x), 5))
                    ax.errorbar(Xenum['percent_change'], Xenum['avg_load_shed'], yerr=[Xenum['lower_load_shed'], Xenum['upper_load_shed']], \
                                capsize=4, fmt="b--o", ecolor = "black", **ENUM_KWARGS)

            # Plot standard case
            Xdet = Xk[Xk['problem'] == 'standard']
            ax.plot(Xdet['percent_change'], Xdet['load_shed'], **STD_KWARGS)

            # Plot permutation load shed
            Xperm = Xk[Xk['problem'] == 'permutation']
            Xperm = Xperm.groupby(['k', 'percent_change']) \
                    .agg({'load_shed':lambda x : list(x)}) \
                    .reset_index()
            PERM_VALS.append(Xperm['load_shed'].apply(max).to_list())
            if mode == 'max':
                Xperm['max_load_shed'] = Xperm['load_shed'].apply(max)
                ax.plot(Xperm['percent_change'], Xperm['max_load_shed'], **PERM_KWARGS)
            elif mode == 'range':
                Xperm['avg_load_shed'] = Xperm['load_shed'].apply(lambda x : np.mean(x))
                Xperm['lower_load_shed'] = Xperm['load_shed'].apply(lambda x : round(np.mean(x) - np.min(x), 5))
                Xperm['upper_load_shed'] = Xperm['load_shed'].apply(lambda x : round(np.max(x) - np.mean(x), 5))
                ax.errorbar(Xperm['percent_change'], Xperm['avg_load_shed'], yerr=[Xperm['lower_load_shed'], Xperm['upper_load_shed']], \
                            capsize=4, fmt="g--o", ecolor = "green", **PERM_KWARGS)
            
            # Plot greedy flow load shed
            Xflow = Xk[Xk['problem'] == 'greedy_flow']
            Xflow = Xflow.groupby(['k', 'percent_change']) \
                    .agg({'load_shed':lambda x : list(x)}) \
                    .reset_index()
            FLOW_VALS.append(Xflow['load_shed'].apply(max).to_list())
            if mode == 'max':
                Xflow['max_load_shed'] = Xflow['load_shed'].apply(max)
                ax.plot(Xflow['percent_change'], Xflow['max_load_shed'], **FLOW_KWARGS)
            elif mode == 'range':
                Xflow['avg_load_shed'] = Xflow['load_shed'].apply(lambda x : np.mean(x))
                Xflow['lower_load_shed'] = Xflow['load_shed'].apply(lambda x : round(np.mean(x) - np.min(x), 5))
                Xflow['upper_load_shed'] = Xflow['load_shed'].apply(lambda x : round(np.max(x) - np.mean(x), 5))
                ax.errorbar(Xflow['percent_change'], Xflow['avg_load_shed'], yerr=[Xflow['lower_load_shed'], Xflow['upper_load_shed']], \
                            capsize=4, fmt="o", markerfacecolor='blue',markeredgecolor='blue', color = "blue", **FLOW_KWARGS)
            
            # Plot greedy load shed 
            Ximp = Xk[Xk['problem'] == 'greedy_impt']
            Ximp = Ximp.groupby(['k', 'percent_change']) \
                    .agg({'load_shed':lambda x : list(x)}) \
                    .reset_index()
            SHED_VALS.append(Ximp['load_shed'].apply(max).to_list())
            if mode == 'max':
                Ximp['max_load_shed'] = Ximp['load_shed'].apply(max)
                ax.plot(Ximp['percent_change'], Ximp['max_load_shed'], **SHED_KWARGS)
            elif mode == 'range':
                Ximp['avg_load_shed'] = Ximp['load_shed'].apply(lambda x : np.mean(x))
                Ximp['lower_load_shed'] = Ximp['load_shed'].apply(lambda x : round(np.mean(x) - np.min(x), 5))
                Ximp['upper_load_shed'] = Ximp['load_shed'].apply(lambda x : round(np.max(x) - np.mean(x), 5))
                ax.errorbar(Ximp['percent_change'], Ximp['avg_load_shed'], yerr=[Ximp['lower_load_shed'], Ximp['upper_load_shed']], \
                            capsize=4, fmt="o", markerfacecolor='green', markeredgecolor='green', ecolor = "green", **SHED_KWARGS)
            
            # Plot greedy load shed 
            Xcrit = Xk[Xk['problem'] == 'greedy_crit']
            Xcrit = Xcrit.groupby(['k', 'percent_change']) \
                    .agg({'load_shed':lambda x : list(x)}) \
                    .reset_index()
            CRIT_VALS.append(Xcrit['load_shed'].apply(max).to_list())
            if mode == 'max':
                Xcrit['max_load_shed'] = Xcrit['load_shed'].apply(max)
                ax.plot(Xcrit['percent_change'], Xcrit['max_load_shed'], **CRIT_KWARGS)
            elif mode == 'range':
                Xcrit['avg_load_shed'] = Xcrit['load_shed'].apply(lambda x : np.mean(x))
                Xcrit['lower_load_shed'] = Xcrit['load_shed'].apply(lambda x : round(np.mean(x) - np.min(x), 5))
                Xcrit['upper_load_shed'] = Xcrit['load_shed'].apply(lambda x : round(np.max(x) - np.mean(x), 5))
                ax.errorbar(Xcrit['percent_change'], Xcrit['avg_load_shed'], yerr=[Xcrit['lower_load_shed'], Xcrit['upper_load_shed']], \
                            capsize=4, fmt="o", markerfacecolor='purple', markeredgecolor='purple', ecolor = "purple", **CRIT_KWARGS)
            
            # Plot SEQUIN
            Xsequin = Xk[Xk['problem'] == 'sequin']
            Xsequin = Xsequin.groupby(['k', 'percent_change']) \
                    .agg({'load_shed':lambda x : list(x)}) \
                    .reset_index()
            SEQUIN_VALS.append(Xsequin['load_shed'].apply(max).to_list())
            if mode == 'max':
                Xsequin['max_load_shed'] = Xsequin['load_shed'].apply(max)
                ax.plot(Xsequin['percent_change'], Xsequin['max_load_shed'], **SEQUIN_KWARGS)
            elif mode == 'range':
                Xsequin['avg_load_shed'] = Xsequin['load_shed'].apply(lambda x : np.mean(x))
                Xsequin['lower_load_shed'] = Xsequin['load_shed'].apply(lambda x : round(np.mean(x) - np.min(x), 5))
                Xsequin['upper_load_shed'] = Xsequin['load_shed'].apply(lambda x : round(np.max(x) - np.mean(x), 5))
                ax.errorbar(Xsequin['percent_change'], Xcrit['avg_load_shed'], yerr=[Xsequin['lower_load_shed'], Xsequin['upper_load_shed']], \
                            capsize=4, fmt="o", markerfacecolor='purple', markeredgecolor='purple', ecolor = "purple", **SEQUIN_KWARGS)

            ax.tick_params(axis='both', which='major', labelsize=AXIS_FONTSIZE)

            if show_legend: 
                ax.legend(fontsize=LEGEND_FONTSIZE)
            
            if save:
                save_to_file(get_fplot_exp2(case, k), fig)

            if show:
                plt.show()

            plt.close()

    # create a new figure and save its legend
    if save_legend:
        fig, ax = plt.subplots(1,1)

        ax.plot([1],[1], **SEQUIN_KWARGS)
        ax.plot([1],[1], **STD_KWARGS)
        ax.plot([1],[1], **ENUM_KWARGS)
        ax.plot([1],[1], **PERM_KWARGS)
        ax.plot([1],[1], **FLOW_KWARGS)
        ax.plot([1],[1], **SHED_KWARGS)
        ax.plot([1],[1], **CRIT_KWARGS)

        lines_labels = [fig.axes[0].get_legend_handles_labels()]
        lines, labels = [sum(lol, []) for lol in zip(*lines_labels)]
        legend = fig.legend(lines, labels, 
                                fontsize=LEGEND_FONTSIZE, loc='right', 
                                bbox_to_anchor = (1.5, 0.5))
        export_legend(legend, fname=get_fplot_exp2_legend())
        plt.close()
            
if __name__ == '__main__':

    if len(sys.argv) != 2:
        print('Usage: python src/experiments/REP_make_plots.py <cache_dir>')
        print('  <cache_dir> should be set to `cache` or `cache-authors`')
        exit()

    cache_dir = sys.argv[1]

    setup_pandas()

    make_experiment0_plots(save=True, show=True, cache_dir=cache_dir)

    make_experiment1_plots(save=True, show=True, cache_dir=cache_dir)

    make_experiment2_plots(save=True, show=True, k=4, cache_dir=cache_dir)
    make_experiment2_plots(save=True, show=True, k=2, cache_dir=cache_dir)
    make_experiment2_plots(save=True, show=True, k=3, cache_dir=cache_dir)
