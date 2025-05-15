# view.py
#
# Controls the view of the SEQUIN toolkit

import tkinter as tk
import customtkinter as ctk

# For colormap 
import matplotlib as mpl
from matplotlib import colormaps
from matplotlib.colors import rgb2hex

# For plots
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from widgets.nxCanvas import nxCanvas
from widgets.AttackSequenceFrame import AttackSequenceFrame
from widgets.AnimationSlider import AnimationSlider

from utils import get_atk_eid

import model
import controller

# MVC Utility functions
Model = lambda : model.Model()
Controller = lambda : controller.Controller()

from utils import Singleton

# customtkinter options
ctk.set_appearance_mode("light")

class View(Singleton):

    HEADER_FONT = ('TkDefaultFont', 12, 'bold')

    def __init__(self):
        self.app = ctk.CTk()

        # window
        self.app.title('SEQUIN Toolkit')
        self.app.geometry('950x700+200+200')

        # layout
        self.app.columnconfigure(0, weight=0, minsize=125)
        self.app.columnconfigure(1, weight=1)

        # sidebar
        self.sidebar = Sidebar(self.app)
        self.sidebar.grid(row=0, column=0, sticky=tk.NSEW)

        # network canvas
        self.network_canvas = NetworkCanvas(self.app)
        self.network_canvas.grid(row=0, column=1, sticky=tk.NSEW)

    def start(self):
        self.app.mainloop()
    
    def get_sidebar(self):
        return self.sidebar
    
    def get_canvas(self):
        return self.network_canvas
    
    def make_plot(self, lines, title=None, xlabel=None, ylabel=None):
        fig = Figure(figsize=(6, 4))
        ax = fig.add_subplot()
        
        for x,y,label in lines:
            ax.plot(x,y, label=label)
            ax.set_xticks(x)

        ax.legend()
        ax.set_title(title)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        
        toplevel = ctk.CTkToplevel(self.app)
        toplevel.title('Plot')
        toplevel.geometry('400x300+400+400')

        canvas_fig = FigureCanvasTkAgg(fig, master=toplevel)
        canvas_fig.draw()

        canvas_fig.get_tk_widget().pack()

    @staticmethod
    def choose_file():
        return tk.filedialog.askopenfilename()

class Sidebar(ctk.CTkFrame):

    ############################################################################
    # Constructor
    ############################################################################

    def __init__(self, master):
        super().__init__(master)

        # Visual variables
        self.is_running = False

        # Initialize tabs
        self.tabs = ctk.CTkTabview(
            self, 
            height=700,
            command=Controller().make_last_ani_step)

        self.make_network_tab()
        self.make_attack_tab()
        self.make_visual_tab()
        self.make_analysis_tab()

        self.tabs.set('Case') # network
        self.tabs.pack(fill='both', expand=False, padx=10)
    
    def get_ramp_bound(self):
        return float(self.ramp_bound.get()[:-1])/100.0

    ############################################################################
    # Network / Case tab
    ############################################################################

    def make_network_tab(self):
        self.tabs.add('Case')
        self.network_tab = self.tabs.tab('Case')

        # load a case
        self._make_load_case_button(self.network_tab)

        # save/load layouts
        self._make_layout_buttons(self.network_tab)

        # network view options
        self._make_network_viewer_options(self.network_tab)

    def _make_load_case_button(self, master):
        self.load_case_button = ctk.CTkButton(
            master, 
            text='Load Case', 
            command=Controller().load_network)
        self.load_case_button.pack(pady=10)

    def _make_layout_buttons(self, master):
        block = ctk.CTkFrame(master, fg_color='transparent')

        self.save_layout_button = ctk.CTkButton(
            block,
            text='Load Layout',
            command=Controller().load_layout,
            width=90)
        self.save_layout_button.grid(row=0, column=0, padx=5, pady=5)
    
        self.load_layout_button = ctk.CTkButton(
            block,
            text='Save Layout',
            command=Controller().save_layout,
            width=90)
        self.load_layout_button.grid(row=0, column=1, padx=5, pady=5)

        block.pack(pady=10)
        
    def _make_network_viewer_options(self, master):
        block = ctk.CTkFrame(master)

        _label = ctk.CTkLabel(block, text='Visuals', font=View.HEADER_FONT)
        _label.grid(row=0, columnspan=2)

        _label = ctk.CTkLabel(block, text='Bus Width')
        _label.grid(row=1, column=0, padx=5, sticky=tk.W)

        self.case_node_width = ctk.CTkSlider(
            block,
            from_=0.0, to=10,
            width=130,
            command=Controller().update_node_width)
        self.case_node_width.grid(row=1, column=1)
        self.case_node_width.set(4)
        
        _label = ctk.CTkLabel(block, text='Branch Width')
        _label.grid(row=2, column=0, padx=5, sticky=tk.W)

        self.case_edge_width = ctk.CTkSlider(
            block,
            from_=1, to=8,
            width=130,
            command=Controller().update_edge_width)
        self.case_edge_width.grid(row=2, column=1)
        self.case_edge_width.set(4)

        block.pack()
     
    ############################################################################
    # Attack tab
    ############################################################################

    def make_attack_tab(self):
        self.tabs.add('Attack')
        self.attack_tab = self.tabs.tab('Attack')

        # show attack sequence
        self._make_atk_seq_editor_block(self.attack_tab)

        # attack controls
        self._make_manual_atk_controls(self.attack_tab)
        self._make_auto_atk_controls(self.attack_tab)

        # attack mode
        self._make_attack_mode_switch(self.attack_tab)
 
    def _make_atk_seq_editor_block(self, master):
        block = ctk.CTkFrame(master)

        self.atk_seq_editor = AttackSequenceFrame(
            block, 
            title='Attack Sequence Editor',
            titlefont=View.HEADER_FONT)
        self.atk_seq_editor.pack()

        block.pack(pady=5)
    
    def _make_manual_atk_controls(self, master):
        block = ctk.CTkFrame(master)

        _label = ctk.CTkLabel(
            block, 
            text="Manual Interdiction", 
            font=View.HEADER_FONT)
        _label.grid(row=0, columnspan=3)

        _label = ctk.CTkLabel(block, text='Component')
        _label.grid(row=1, column=0, columnspan=2, padx=10, sticky=tk.W)

        self.atk_entry = ctk.CTkOptionMenu(
            block, 
            values=[""], 
            width=120, 
            dynamic_resizing=False,
            state='disabled')
        self.atk_entry.grid(
            row=1, column=1, columnspan=2, 
            padx=10, pady=3, 
            sticky=tk.E)

        _label = ctk.CTkLabel(block, text='Gen. Ramping Bound')
        _label.grid(row=2, columnspan=3, padx=10, sticky=tk.W)
        
        self.ramp_bound = ctk.CTkOptionMenu(
            block, 
            values=[f'{i}%' for i in range(0,101,5)],
            width=70,
            dynamic_resizing=False)
        self.ramp_bound.grid(row=2, columnspan=3, padx=10, pady=3, sticky=tk.E)
        self.ramp_bound.set('10%')

        self.reset_atk_button = ctk.CTkButton(
            block,
            text='Reset',
            width=65,
            command=Controller().reset_atk)
        self.reset_atk_button.grid(row=3, column=0, padx=5, pady=3)

        self.undo_atk_button = ctk.CTkButton(
            block, 
            text='Undo', 
            width=65,
            command=Controller().undo_atk)
        self.undo_atk_button.grid(row=3, column=1, padx=5, pady=3)

        self.atk_button = ctk.CTkButton(
            block, 
            text='Attack', 
            width=65,
            command=lambda : Controller().do_atk(
                get_atk_eid(self.atk_entry.get())))
        self.atk_button.grid(row=3, column=2, padx=5, pady=3)
        
        block.pack(pady=5)

    def _make_auto_atk_controls(self, master):
        block = ctk.CTkFrame(master)

        _label = ctk.CTkLabel(
            block, 
            text="Algorithmic Interdiction", 
            font=View.HEADER_FONT)
        _label.grid(row=0, columnspan=2)

        _label = ctk.CTkLabel(block, text='Select k')
        _label.grid(row=1, column=0, padx=10, pady=3)

        self.k = ctk.CTkOptionMenu(
            block, 
            values=list(map(str,range(1, 20))),
            width=70)
        self.k.grid(row=1, columnspan=3, padx=10, pady=3, sticky=tk.E)

        _label = ctk.CTkLabel(block, text='Strategy')
        _label.grid(row=2, column=0, padx=10, pady=3)

        self.atk_strategy = ctk.CTkOptionMenu(
            block, 
            values=[
                'SEQUIN', 
                'Permutation', 
                'Greedy-Flow', 
                'Greedy-Criticality',
                'Greedy-LoadShed',
                'Random'],
            width=130)
        self.atk_strategy.grid(row=2, column=1, padx=10, pady=3)

        self.gen_atk_button = ctk.CTkButton(
            block,
            text='Generate Attack',
            command=lambda : Controller().gen_atk(
                int(self.k.get()), 
                float(self.ramp_bound.get()[:-1])/100,
                self.atk_strategy.get()))
        self.gen_atk_button.grid(row=3, columnspan=2, pady=3)

        block.pack(pady=5)

    def _make_attack_mode_switch(self, master):
        block = ctk.CTkFrame(master, width=200)

        _label = ctk.CTkLabel(block, text='Attack Mode', font=View.HEADER_FONT)
        _label.grid(row=0)

        self.atk_mode_button = ctk.CTkSegmentedButton(
            block, 
            values=["Sequential", "Simultaneous"], 
            command=Controller().set_atk_mode,
            corner_radius=10,
            border_width=5)
        self.atk_mode_button.set('Sequential')
        self.atk_mode_button.grid(row=1, padx=15, pady=5)

        block.pack(pady=5)

    ############################################################################
    # Visual tab
    ############################################################################

    def make_visual_tab(self):
        self.tabs.add('Visual')
        self.visual_tab = self.tabs.tab('Visual')

        # show attack sequence
        self._make_atk_seq_status_block(self.visual_tab)

        # animation controls
        self._make_animation_controls(self.visual_tab)

        # view selection
        self._make_network_property_selection(self.visual_tab)

    def _make_atk_seq_status_block(self, master):
        block = ctk.CTkFrame(master)

        self.atk_mode_status = tk.StringVar(value='Sequential Attack Status')
        self.atk_seq_status = AttackSequenceFrame(
            block, 
            title=self.atk_mode_status,
            titlefont=View.HEADER_FONT)
        self.atk_seq_status.pack()

        block.pack(pady=5)

    def _make_animation_controls(self, master):
        block = ctk.CTkFrame(master)

        self.slider = AnimationSlider(block)
        self.slider.grid(row=0, columnspan=4, pady=3)

        self.back_ani_button = ctk.CTkButton(
            block,
            text='Back',
            width=50,
            command=Controller().back_ani)
        self.back_ani_button.grid(row=1, column=0, padx=3, pady=3)

        self.step_ani_button = ctk.CTkButton(
            block, 
            text='Step', 
            width=50,
            command=Controller().step_ani)
        self.step_ani_button.grid(row=1, column=1, padx=3, pady=3)

        self.stop_ani_button = ctk.CTkButton(
            block,
            text='Stop',
            width=50,
            command=Controller().stop_ani)
        self.stop_ani_button.grid(row=1, column=2, padx=3, pady=3)

        self.run_ani_button = ctk.CTkButton(
            block, 
            text='Run', 
            width=50,
            command=lambda : Controller().run_ani(first=True))
        self.run_ani_button.grid(row=1, column=3, padx=3, pady=3)

        block.pack(pady=5)
    
    def _make_network_property_selection(self, master):
        node_block = ctk.CTkFrame(master)

        # For buses
        _label = ctk.CTkLabel(
            node_block, 
            text='Bus Node Properties', 
            font=View.HEADER_FONT)
        _label.grid(row=0, columnspan=2)

        _label = ctk.CTkLabel(node_block, text='Property')
        _label.grid(row=1, column=0, padx=5)

        self.node_property_menu = ctk.CTkOptionMenu(
            node_block,
            values=[
                'None',
                'Total Load',
                'Load Shed',
                'Power Generated',
                'Generator Criticality',
                'Transmission Width'
            ],
            width=150,
            dynamic_resizing=False,
            command=Controller().apply_bus_property)
        self.node_property_menu.grid(row=1, column=1, padx=5, pady=3)

        _label = ctk.CTkLabel(node_block, text='Unit')
        _label.grid(row=2, column=0)

        self.node_property_unit = ctk.CTkSegmentedButton(
            node_block, 
            values=["Per Unit", "Percent"], 
            command=lambda x: Controller().apply_bus_property(unit=x),
            corner_radius=10,
            border_width=5)
        self.node_property_unit.set('Per Unit')
        self.node_property_unit.grid(row=2, column=1, padx=5, pady=3)

        self.show_node_legend = tk.BooleanVar(value=False)
        self.show_node_legend_button = ctk.CTkCheckBox(
            node_block, 
            text="Show bus legend", 
            variable=self.show_node_legend, 
            onvalue=True, offvalue=False,
            command=Controller().apply_legends,
            corner_radius=5,
            checkbox_width=20, checkbox_height=20)
        self.show_node_legend_button.grid(row=3, columnspan=2, pady=3)

        node_block.pack(pady=5)

        # For branches
        edge_block = ctk.CTkFrame(master)

        _label = ctk.CTkLabel(
            edge_block, 
            text='Branch Edge Properties', 
            font=View.HEADER_FONT)
        _label.grid(row=0, columnspan=2)

        _label = ctk.CTkLabel(edge_block, text='Property')
        _label.grid(row=1, column=0, padx=5)

        self.edge_property_menu = ctk.CTkOptionMenu(
            edge_block,
            values=[
                'None',
                'Thermal Rating',
                'Power Flow',
                'Branch Criticality',
                'Cut Impact'
            ],
            width=150,
            dynamic_resizing=False,
            command=Controller().apply_branch_property)
        self.edge_property_menu.grid(row=1, column=1, padx=5, pady=3)

        _label = ctk.CTkLabel(edge_block, text='Unit')
        _label.grid(row=2, column=0)

        self.edge_property_unit = ctk.CTkSegmentedButton(
            edge_block, 
            values=["Per Unit", "Percent"], 
            command=lambda x: Controller().apply_branch_property(unit=x),
            corner_radius=10,
            border_width=5)
        self.edge_property_unit.set('Per Unit')
        self.edge_property_unit.grid(row=2, column=1, padx=5, pady=3)

        self.show_edge_legend = tk.BooleanVar(value=False)
        self.show_edge_legend_button = ctk.CTkCheckBox(
            edge_block, 
            text="Show branch legend", 
            variable=self.show_edge_legend, 
            onvalue=True, offvalue=False,
            command=Controller().apply_legends,
            corner_radius=5,
            checkbox_width=20, checkbox_height=20)
        self.show_edge_legend_button.grid(row=3, columnspan=2, pady=3)

        edge_block.pack(pady=5)
    
    ############################################################################
    # Analysis tab
    ############################################################################

    def make_analysis_tab(self):
        self.tabs.add('Analysis')
        self.analysis_tab = self.tabs.tab('Analysis')

        self._make_statistics_block(self.analysis_tab)

        self._make_plots_block(self.analysis_tab)

    def _make_statistics_block(self, master):
        pass

    def _make_plots_block(self, master): 
        block = ctk.CTkFrame(master)

        _label = ctk.CTkLabel(block, text='Results', font=View.HEADER_FONT)
        _label.pack()

        self.show_load_shed_plot_button = ctk.CTkButton(
            block,
            text='Show load shed plot',
            command=Controller().show_load_shed_plot,
            width=200)
        self.show_load_shed_plot_button.pack(padx=5, pady=10)

        self.show_load_serviced_plot_button = ctk.CTkButton(
            block,
            text='Show load serviced plot',
            command=Controller().show_load_serviced_plot,
            width=200)
        self.show_load_serviced_plot_button.pack(padx=5, pady=10)

        self.show_gen_crit_plot_button = ctk.CTkButton(
            block,
            text='Show generator criticality plot',
            command=Controller().show_gen_crit_plot,
            width=200)
        self.show_gen_crit_plot_button.pack(padx=5, pady=10)

        self.show_br_crit_plot_button = ctk.CTkButton(
            block,
            text='Show branch criticality plot',
            command=Controller().show_br_crit_plot,
            width=200)
        self.show_br_crit_plot_button.pack(padx=5, pady=10)

        self.show_power_flow_plot_button = ctk.CTkButton(
            block,
            text='Show total power flow plot',
            command=Controller().show_power_flow_plot,
            width=200)
        self.show_power_flow_plot_button.pack(padx=5, pady=10)

        self.show_power_gen_plot_button = ctk.CTkButton(
            block,
            text='Show total power generated plot',
            command=Controller().show_power_flow_plot,
            width=200)
        self.show_power_flow_plot_button.pack(padx=5, pady=10)

        block.pack()
    
class NetworkCanvas(ctk.CTkFrame):

    def __init__(self, master):
        super().__init__(master)

        # legend info
        self.node_title, self.edge_title = None, None
        self.node_cmap, self.node_bounds = None, None
        self.edge_cmap, self.edge_bounds = None, None

        # The canvas that draws everything
        self.canvas = nxCanvas(self)
        self.canvas.pack(fill='both', expand=True)
    
    def draw(self):
        self.canvas.draw()

    def mark_edge(self, eid, do_highlight=True):
        self.canvas.mark_edge(eid)
        self.canvas.draw()

        if do_highlight:
            self.highlight_edge(eid)
    
    def unmark_edge(self, eid, do_highlight=True):
        self.canvas.unmark_edge(eid)
        self.canvas.draw()

        if do_highlight:
            self.highlight_edge(eid)
    
    def highlight_edge(self, eid):
        self.canvas.highlight_edge(eid)
    
    def reset_node_styles(self):
        for style in self.canvas.node_state['style'].values():
            style.reset_normal_style()

    def reset_edge_styles(self):
        for style in self.canvas.edge_state['style'].values():
            style.reset_normal_style()
    
    def update_node_styles(self, node_values, bounds):
        self.node_cmap = colormaps['magma']
        self.node_bounds = bounds
        norm = mpl.colors.Normalize(vmin=bounds[0], vmax=bounds[1])
        for i,x in node_values.items():
            color = rgb2hex(self.node_cmap(norm(x)))
            new_style = {'fill' : color, 'outline' : color}
            self.canvas.node_state['style'][i].update_normal_style(**new_style)
        self.canvas.draw()

    def update_edge_styles(self, edge_values, bounds):
        self.edge_cmap = colormaps['plasma']
        self.edge_bounds = bounds
        norm = mpl.colors.Normalize(vmin=bounds[0], vmax=bounds[1])
        for i,x in edge_values.items():
            new_style = {'fill' : rgb2hex(self.edge_cmap(norm(x)))}
            self.canvas.edge_state['style'][i].update_normal_style(**new_style)
        self.canvas.draw()
    