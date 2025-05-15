# controller.py

import re
from collections import defaultdict

import model
import view

from utils import Singleton, get_atk_str

# MVC Utility functions
View = lambda : view.View()
Model = lambda : model.Model()

class Controller(Singleton):

    ############################################################################
    # Network Module
    ############################################################################

    def load_network(self, fname=None):
        case = fname or View().choose_file()

        # Update Model
        Model().set_case(case)

        # Update View
        View().get_sidebar().atk_entry.configure(
            state='normal',
            values=[get_atk_str(uv, Model()) 
                    for uv in Model().get_edge_uv(make_sorted=True)])
        View().get_sidebar().atk_entry.set("")
        
        View().get_canvas().canvas.set_network(
            Model().network, 
            Model().cliargs['case'])

        # Reset any attack, if one exists
        self.reset_atk()

        self.slider_move(0, do_highlight=False)

        View().get_canvas().draw()

    def save_layout(self):
        pass

    def load_layout(self):
        pass

    def update_node_width(self, x):
        for vid in Model().get_nodeids():
            ns = View().get_canvas().canvas.node_state['style'][vid]
            ns.update_normal_style(width=x)
            ns.update_marked_style(width=x)
            ns.update_normal_style(width=x)
        View().get_canvas().draw()

    def update_edge_width(self, x):
        for eid in Model().get_edgeids():
            es = View().get_canvas().canvas.edge_state['style'][eid]
            es.update_normal_style(width=x)
            es.update_marked_style(width=x)
            es.update_normal_style(width=x)
        View().get_canvas().draw()

    ############################################################################
    # Attack Module
    ############################################################################

    def reset_atk(self):
        # Update View
        for eid in Model().atk_seq:
            View().get_canvas().unmark_edge(eid)
        View().get_sidebar().atk_seq_editor.clear()
        View().get_sidebar().atk_seq_status.clear()

        # Update Model
        Model().reset_atk()

        # Update the slider
        View().get_sidebar().slider.update(value=0, to=0)
        self.slider_move(0, do_highlight=False)

        View().get_canvas().draw()

    def undo_atk(self):
        eid = Model().undo_atk()
        if eid is None: # no attack exists
            return

        # Update View
        View().get_sidebar().atk_seq_editor.remove_entry()
        View().get_sidebar().atk_seq_status.remove_entry()

        View().get_sidebar().slider.update(
            value=len(Model().atk_seq), 
            to=len(Model().atk_seq))
        self.slider_move(len(Model().atk_seq), do_highlight=False)

        View().get_canvas().unmark_edge(eid)
        View().get_canvas().draw()

    def do_atk(self, eid, grb=None):
        # Check if attack on eid is allowed
        if not Model().check_atk(eid):
            return
        
        # Set next generator ramping bound
        grb = grb or View().get_sidebar().get_ramp_bound()
        Model().set_generator_ramping_bounds(grb)

        # Update Model
        Model().do_atk(eid)

        # Update View
        View().get_sidebar().atk_seq_editor.add_entry(eid)
        View().get_sidebar().atk_seq_status.add_entry(eid)

        View().get_sidebar().slider.update(
            value=Model().get_atk_count(), 
            to=Model().get_atk_count())
        self.slider_move(Model().get_atk_count(), do_highlight=False)

        View().get_canvas().mark_edge(eid, do_highlight=True)

        View().get_canvas().draw()

    def gen_atk(self, k, grb, strategy):
        Model().set_k(k)
        Model().set_generator_ramping_bounds(grb)

        for eid in Model().run_atk_strategy(strategy):
            self.do_atk(eid, grb)
    
    def set_atk_mode(self, mode):
        Model().set_atk_mode(mode)

        View().get_sidebar().atk_mode_status.set(f'{mode} Attack Status')

        self.update_network_view(up_to=View().get_sidebar().slider.get())
    
    ############################################################################
    # Visual Module
    ############################################################################

    def slider_move(self, x, move_right=True, do_highlight=True):
        if x > Model().get_atk_count():
            return

        View().get_sidebar().is_running = False

        # Update status
        View().get_sidebar().slider.update(value=x)
        for i,(*_,st) in enumerate(View().get_sidebar().atk_seq_status):
            if i < x:
                st.configure(text=' - failed -', text_color='red')
            else:
                st.configure(text=' -   OK   -', text_color='black')

        # Update network
        self.update_network_view(
            up_to=x, 
            hl=x-move_right if do_highlight else None)

    def update_network_view(self, up_to=None, hl=None):

        # Determine which lines should be marked/unmarked
        for i,eid in enumerate(Model().atk_seq):
            if up_to is None or i < up_to:
                View().get_canvas().mark_edge(eid, do_highlight=False)
            else:
                View().get_canvas().unmark_edge(eid, do_highlight=False)
            
            if i == hl:
                View().get_canvas().highlight_edge(eid)
        
        # Determine bus/branch properties to display
        self.apply_bus_property(step=up_to)
        self.apply_branch_property(step=up_to)
        
        View().get_canvas().draw()

    def make_last_ani_step(self):
        self.slider_move(Model().get_atk_count(), do_highlight=False)

    def back_ani(self):
        self.slider_move(View().get_sidebar().slider.get()-1, move_right=False)

    def step_ani(self):
        self.slider_move(View().get_sidebar().slider.get()+1, move_right=True)

    def stop_ani(self):
        View().get_sidebar().is_running = False

    def run_ani(self, first=False):
        if first and View().get_sidebar().slider.get() == Model().get_atk_count():
            self.slider_move(0,move_right=False, do_highlight=False)
            View().get_sidebar().is_running = True
            View().app.after(1000, self.run_ani)

        elif first or View().get_sidebar().is_running and \
            View().get_sidebar().slider.get() < Model().get_atk_count():
                self.step_ani()
                View().get_sidebar().is_running = True
                View().app.after(1000, self.run_ani)
    
    def apply_bus_property(self, property=None, unit=None, step=None):
        property = property or View().get_sidebar().node_property_menu.get()
        unit = unit or View().get_sidebar().node_property_unit.get()
        step = step or View().get_sidebar().slider.get()

        if property == 'None':
            View().get_canvas().reset_node_styles()
            self.apply_legends()
            return
        
        elif property == 'Total Load':
            load, bounds = Model().get_total_load(step)
            if unit == 'Percent':
                load = {i : x/bounds[1] for i,x in load.items()}
                bounds[1] = 1
            View().get_canvas().update_node_styles(load, bounds)
            View().get_canvas().node_title = 'Total Load'
        
        elif property == 'Load Shed':
            load_shed, bounds = Model().get_load_shed(step)
            if unit == 'Percent':
                loads = defaultdict(float)
                for i,ld in Model().pm_ref['load'].items():
                    loads[i] = ld['pd']
                load_shed = {i : (x/loads[i] if loads[i] != 0 else 0) \
                             for i,x in load_shed.items()}
                bounds[1] = 1
            View().get_canvas().update_node_styles(load_shed, bounds)
            View().get_canvas().node_title = 'Load Shed'
        
        elif property == 'Power Generated':
            power_gen, bounds = Model().get_power_gen(step)
            if unit == 'Percent':
                maxpower = Model().pm_ref['gen']
                power_gen = {i : x/(maxpower[i]['pmax'] or 1) \
                             for i,x in power_gen.items()}
                bounds[1] = 1
            View().get_canvas().update_node_styles(power_gen, bounds)
            View().get_canvas().node_title = 'Power Gen.'
        
        elif property == 'Generator Criticality':
            gen_crit, bounds = Model().get_gen_crit(step)
            if unit == 'Percent':
                gen_crit = {i : x/bounds[1] for i,x in gen_crit.items()}
                bounds[1] = 1
            View().get_canvas().update_node_styles(gen_crit, bounds)
            View().get_canvas().node_title = 'Gen. Crit.'
        
        elif property == 'Transmission Width':
            trans_width, bounds = Model().get_trans_width(step)
            View().get_canvas().update_node_styles(trans_width, bounds)
            View().get_canvas().node_title = 'Trans. Width'
        
        self.apply_legends()

        View().get_canvas().draw()

    def apply_branch_property(self, property=None, unit=None, step=None):
        property = property or View().get_sidebar().edge_property_menu.get()
        unit = unit or View().get_sidebar().edge_property_unit.get()
        step = step or View().get_sidebar().slider.get()

        if property == 'None':
            # All styles should be set to 0
            View().get_canvas().reset_edge_styles()
            self.apply_legends()

        elif property == 'Thermal Rating':
            rate_a, bounds = Model().get_rate_a(step)
            if unit == 'Percent':
                rate_a = {i : x/bounds[1] for i,x in rate_a.items()}
                bounds[1] = 1
            View().get_canvas().update_edge_styles(rate_a, bounds)
            View().get_canvas().edge_title = 'Rate A'
            
        elif property == 'Power Flow':
            pfs, bounds = Model().get_power_flow(step)
            if unit == 'Percent':
                rate_a = Model().get_rate_a(step)[0]
                pfs = {i : x/rate_a[i] for i,x in pfs.items()}
                bounds[1] = 1
            View().get_canvas().update_edge_styles(pfs, bounds)
            View().get_canvas().edge_title = 'Power Flow'
        
        elif property == 'Branch Criticality':
            br_crit, bounds = Model().get_br_crit(step)
            if unit == 'Percent':
                br_crit = {i : x/bounds[1] for i,x in br_crit.items()}
                bounds[1] = 1
            View().get_canvas().update_edge_styles(br_crit, bounds)
            View().get_canvas().edge_title = 'Branch Crit.'
    
        elif property == 'Cut Impact':
            cut_impt, bounds = Model().get_cut_impt(step)
            if unit == 'Percent':
                cut_impt = {i : x/bounds[1] for i,x in cut_impt.items()}
                bounds[1] = 1
            View().get_canvas().update_edge_styles(cut_impt, bounds)
            View().get_canvas().edge_title = 'Cut Impt.'
        
        self.apply_legends()

        View().get_canvas().draw()

    def apply_legends(self):
        show_node_legend = \
            View().get_sidebar().node_property_menu.get() != 'None' and \
            View().get_sidebar().show_node_legend.get()
        
        show_edge_legend = \
            View().get_sidebar().edge_property_menu.get() != 'None' and \
            View().get_sidebar().show_edge_legend.get()

        if show_node_legend and show_edge_legend:
            View().get_canvas().canvas.show_legend1 = True
            View().get_canvas().canvas.show_legend2 = True

            View().get_canvas().canvas.set_colormap_legend1(
                View().get_canvas().node_cmap,
                *View().get_canvas().node_bounds,
                title=View().get_canvas().node_title)
            View().get_canvas().canvas.set_colormap_legend2(
                View().get_canvas().edge_cmap,
                *View().get_canvas().edge_bounds,
                title=View().get_canvas().edge_title)
        
        elif show_node_legend and not show_edge_legend:
            View().get_canvas().canvas.show_legend1 = True
            View().get_canvas().canvas.show_legend2 = False

            View().get_canvas().canvas.set_colormap_legend1(
                View().get_canvas().node_cmap,
                *View().get_canvas().node_bounds,
                title=View().get_canvas().node_title)
        
        elif not show_node_legend and show_edge_legend:
            View().get_canvas().canvas.show_legend1 = True
            View().get_canvas().canvas.show_legend2 = False

            View().get_canvas().canvas.set_colormap_legend1(
                View().get_canvas().edge_cmap,
                *View().get_canvas().edge_bounds,
                title=View().get_canvas().edge_title)
        
        else:
            View().get_canvas().canvas.show_legend1 = False
            View().get_canvas().canvas.show_legend2 = False

        View().get_canvas().draw()


    ############################################################################
    # Analysis Module
    ############################################################################

    def show_load_shed_plot(self):
        ks = range(1,Model().get_atk_count()+1)

        seq_ys, simu_ys = [], []
        for k in ks:
            seq_ys.append(Model().pm_data['total_load'] - sum(Model().it_data[k].prev_loads.values()))
            simu_ys.append(Model().pm_data['total_load'] - sum(Model().simu_atk_cache[k]['loads'].values()))

        View().make_plot(
            [(ks,seq_ys,'Load Shed (Sequential)'), 
             (ks,simu_ys,'Load Shed (Simultaneous)')], 
            'Load Shed', 
            xlabel='k', ylabel='Load Shed (p.u.)')

    def show_load_serviced_plot(self):
        ks = range(1,Model().get_atk_count()+1)

        seq_ys, simu_ys = [], []
        for k in ks:
            seq_ys.append(sum(Model().it_data[k].prev_loads.values()))
            simu_ys.append(sum(Model().simu_atk_cache[k]['loads'].values()))

        View().make_plot(
            [(ks,seq_ys,'Load Serviced (Sequential)'),
             (ks,simu_ys,'Load Serviced (Simultaneous)')], 
            'Load Serviced', 
            xlabel='k', ylabel='Load Serviced (p.u.)')

    def show_gen_crit_plot(self):
        ks = range(1,Model().get_atk_count()+1)

        seq_ys, simu_ys = [], []
        for k in ks:
            seq_ys.append(sum(Model().get_gen_crit(k, atk_mode=Model().SEQUENTIAL_ATK_MODE)[0].values()))
            simu_ys.append(sum(Model().get_gen_crit(k, atk_mode=Model().SIMULTANEOUS_ATK_MODE)[0].values()))

        View().make_plot(
            [(ks,seq_ys,'Generator Criticality (Sequential)'),
             (ks,simu_ys,'Generator Criticality (Simultanous)')], 
            'Generator Criticality', 
            xlabel='k', ylabel='Generator Criticality')

    def show_br_crit_plot(self):
        ks = range(1,Model().get_atk_count()+1)

        seq_ys, simu_ys = [], []
        for k in ks:
            seq_ys.append(sum(Model().get_br_crit(k, atk_mode=Model().SEQUENTIAL_ATK_MODE)[0].values()))
            simu_ys.append(sum(Model().get_br_crit(k, atk_mode=Model().SIMULTANEOUS_ATK_MODE)[0].values()))

        View().make_plot(
            [(ks,seq_ys,'Branch Criticality (Sequential)'),
             (ks,simu_ys,'Branch Criticality (Simultanous)')], 
            'Branch Criticality', 
            xlabel='k', ylabel='Branch Criticality')

    def show_power_flow_plot(self):
        ks = range(1,Model().get_atk_count()+1)

        seq_ys, simu_ys = [], []
        for k in ks:
            seq_ys.append(sum(Model().get_power_flow(k, atk_mode=Model().SEQUENTIAL_ATK_MODE)[0].values()))
            simu_ys.append(sum(Model().get_power_flow(k, atk_mode=Model().SIMULTANEOUS_ATK_MODE)[0].values()))

        View().make_plot(
            [(ks,seq_ys,'Power Flow (Sequential)'),
             (ks,simu_ys,'Power Flow (Simultanous)')], 
            'Power Flow', 
            xlabel='k', ylabel='Power Flow (p.u.)')

    def show_power_gen_plot(self):
        ks = range(1,Model().get_atk_count()+1)

        seq_ys, simu_ys = [], []
        for k in ks:
            seq_ys.append(sum(Model().get_power_gen(k, atk_mode=Model().SEQUENTIAL_ATK_MODE)[0].values()))
            simu_ys.append(sum(Model().get_power_gen(k, atk_mode=Model().SIMULTANEOUS_ATK_MODE)[0].values()))

        View().make_plot(
            [(ks,seq_ys,'Power Generated (Sequential)'),
             (ks,simu_ys,'Power Generated (Simultanous)')], 
            'Power Generated', 
            xlabel='k', ylabel='Power Generated (p.u.)')

