# nxCanvas.py

import tkinter as tk
from collections import defaultdict

import numpy as np
import matplotlib as mpl
from matplotlib import colormaps
from matplotlib.colors import rgb2hex

import networkx as nx

try:
    from widgets.CanvasTooltip import CanvasTooltip
except: # if running from this file directly for testing...
    from CanvasTooltip import CanvasTooltip

class nxCanvas(tk.Canvas):

    def __init__(self, master, **kwargs):
        super().__init__(master, bg='white', **kwargs)

        # Network
        self.network_name = None
        self.network = None
        self.layout = None

        # nodes and edges drawn on the canvas
        self.nodes = {}
        self.edges = {}

        # any persistent state for nodes / edges
        self.node_state = {'style' : defaultdict(NodeStyle)}
        self.edge_state = {'style' : defaultdict(EdgeStyle)}

        # legends
        self.show_legend1, self.show_legend2 = False, False
        self.legend1_kwargs, self.legend2_kwargs = {}, {}

    def set_network(self, network, name=None, layout=None):
        self.network = network
        self.network_name = name

        if layout is None:
            scale = (0.9 * min(self.winfo_width(), self.winfo_height())) // 2
            center = (self.winfo_width()//2, self.winfo_height()//2)
            layout = nx.spring_layout(network, scale=scale, center=center) 
        self.layout = layout
    
    ############################################################################
    # Drawing Utils
    ############################################################################

    def draw(self):
        self.delete_all()

        # Write network name at top
        self.create_text(
            20, 15, 
            text=self.network_name, 
            fill='black', 
            anchor=tk.NW)

        # Initialize all nodes and edges first
        for (uid,vid) in self.network.edges():
            eid = self.network.edges[uid,vid]['eid']
            e = nxCanvasEdge(uid,vid, eid)
            e.set_style(self.edge_state['style'][eid])
            e.set_tooltip_text(f'Edge {eid}({uid}-{vid})')
            self.edges[eid] = e

        for vid in self.network.nodes():
            v = nxCanvasNode(*self.layout[vid], vid)
            v.set_style(self.node_state['style'][vid])
            v.set_tooltip_text(f'Node {vid}')
            self.nodes[vid] = v
        
        # Plot edges first, then nodes
        for e in self.edges.values():
            e.draw(self)
        for v in self.nodes.values():
            v.draw(self)
        
        # Show legends
        if self.show_legend1:
            self.colormap_legend(**self.legend1_kwargs)
        if self.show_legend2:
            self.colormap_legend(**self.legend2_kwargs)
    
    def delete_all(self):
        self.delete('all')
        self.nodes.clear()
        self.edges.clear()
    
    def delete_node(self, vid):
        self.delete(self.nodes[vid].canvas_id)
        del self.nodes[vid]

    def delete_edge(self, eid):
        self.delete(self.edges[eid].canvas_id)
        del self.edges[eid]
    
    def mark_edge(self, eid):
        self.edge_state['style'][eid].set(GraphStyle.MARKED)
    
    def unmark_edge(self, eid):
        self.edge_state['style'][eid].set(GraphStyle.NORMAL)
    
    def highlight_edge(self, eid):
        if self.edge_state['style'][eid] != GraphStyle.HIGHLIGHT:
            self.edge_state['style'][eid].set(GraphStyle.HIGHLIGHT)
            self.edge_state['style'][eid].step_highlight(self)
    
    def set_colormap_legend1(self, cmap, vmin, vmax, title, **kwargs):
        self.legend1_kwargs = {
            'cmap':cmap, 
            'vmin':vmin, 
            'vmax':vmax, 
            'title':title, 
            'x0':10, 'y0':40,
            **kwargs
        }
    
    def set_colormap_legend2(self, cmap, vmin, vmax, title, **kwargs):
        self.legend2_kwargs = {
            'cmap':cmap, 
            'vmin':vmin, 
            'vmax':vmax, 
            'title':title, 
            'x0':10, 'y0':220,
            **kwargs
        }

    def colormap_legend(self, cmap, vmin, vmax,
                        x0, y0, colorbar_width=20, colorbar_iterheight=1.3,
                        legend_width=100, legend_height=170,
                        margin=10,
                        title=None):

        self.create_rectangle(
            x0, y0, 
            x0 + legend_width, y0 + legend_height,
            fill='white', outline='black')

        self.create_text(
            x0 + legend_width/2,
            y0 + margin,
            text=title, fill='black')

        norm = mpl.colors.Normalize(vmin=vmin, vmax=vmax)
        for i,x in enumerate(np.linspace(vmin, vmax, 101)):
            self.create_rectangle(
                x0 + margin,
                y0 + 2.5*margin + colorbar_iterheight*i,
                x0 + margin + colorbar_width,
                y0 + 2.5*margin + colorbar_iterheight*(i+1),
                fill=rgb2hex(cmap(norm(x))),
                outline=rgb2hex(cmap(norm(x))))

            if i % 25 == 0:
                self.create_text(
                    x0 + 3.5*margin,
                    y0 + 2.5*margin + colorbar_iterheight*i,
                    text=f'{round(x,2)}', fill='black', anchor=tk.W)

class nxCanvasNode:

    DEFAULT_NODE_TOOLTIP_STYLE = { 'bg' : '#FFFF00' }

    def __init__(self, x,y, nid):
        self.x, self.y = x,y
        self.nid = nid 
        self.canvas_id = None # Set only after it is drawn

        # drawing styles
        self.style = None

        # tooltip
        self.tooltip = None
        self.tooltip_text = None
        self.tooltip_style = nxCanvasNode.DEFAULT_NODE_TOOLTIP_STYLE.copy()

    ############################################################################ 
    # Node Drawing
    ############################################################################ 

    def draw(self, canvas):
        width = self.style.get()['width']
        self.canvas_id = canvas.create_oval(
            self.x-width, self.y-width,
            self.x+width, self.y+width,
            **self.style.get())
        
        self.tooltip = CanvasTooltip(
            canvas, self.canvas_id, 
            text=self.tooltip_text, 
            **self.tooltip_style)
        
    def move(self, canvas, dx, dy):
        self.x += dx
        self.y += dy
        canvas.move(self.canvas_id, dx, dy)

    def set_style(self, style):
        self.style = style

    ############################################################################ 
    # Node Tooltip
    ############################################################################ 

    def get_tooltip_text(self):
        return self.tooltip_text

    def set_tooltip_text(self, tooltip_text):
        self.tooltip_text = tooltip_text
    
    def remove_tooltip(self):
        self.tooltip = None
        self.tooltip_text = None
    
    def set_tooltip_style(self, **style):
        self.tooltip_style = style

    def update_tooltip_style(self, **style):
        self.tooltip_style.update(style)

class nxCanvasEdge:

    DEFAULT_EDGE_TOOLTIP_STYLE = { 'bg' : '#FFFF00' }

    def __init__(self, nid1, nid2, eid):
        self.nid1, self.nid2 = nid1, nid2
        self.eid = eid 
        self.canvas_id = None # Set after drawing

        self.style = None

        self.tooltip = None
        self.tooltip_text = None
        self.tooltip_style = nxCanvasEdge.DEFAULT_EDGE_TOOLTIP_STYLE.copy()

    ############################################################################ 
    # Edge Drawing
    ############################################################################ 

    def draw(self, canvas):
        n1,n2 = canvas.nodes[self.nid1], canvas.nodes[self.nid2]
        self.canvas_id = canvas.create_line(
            n1.x, n1.y, 
            n2.x, n2.y, 
            **self.style.get())
        
        self.tooltip = CanvasTooltip(
            canvas, self.canvas_id, 
            text=self.tooltip_text, 
            **self.tooltip_style)

    def set_style(self, style):
        self.style = style

    ############################################################################ 
    # Edge Tooltip
    ############################################################################ 

    def get_tooltip_text(self):
        return self.tooltip_text

    def set_tooltip_text(self, tooltip_text):
        self.tooltip_text = tooltip_text
    
    def remove_tooltip(self):
        self.tooltip = None
        self.tooltip_text = None
    
    def set_tooltip_style(self, **style):
        self.tooltip_style = style

    def update_tooltip_style(self, **style):
        self.tooltip_style.update(style)
    
class GraphStyle:

    # Node Styles
    DEF_NORMAL_NODE_STYLE = { 
        'fill' : 'black', 
        'outline' : 'black', 
        'width' : 4
    }

    DEF_MARKED_NODE_STYLE = { 
        'fill' : 'red', 
        'outline' : 'red', 
        'width': 4
    }

    # Highlighting = blink between normal and marked style 3 times
    DEF_HIGHLIGHT_NODE_STYLE = { 
        'animation' : [ # duration in 100 ms
            {'style' : None, 'duration' : 2}, 
            {'style' : {'fill':'red', 'width':8}, 'duration' : 5}
        ], 
        'repeat' : 2
    }

    # Edge Styles
    DEF_NORMAL_EDGE_STYLE = { 
        'fill' : 'black', 
        'width': 4
    }

    DEF_MARKED_EDGE_STYLE = { 
        'fill' : 'black', 
        'dash' : (6,4), 
        'width': 4
    }

    # Highlighting = blink between normal and marked style 3 times
    DEF_HIGHLIGHT_EDGE_STYLE = { 
        'animation' : [ # duration in 100 ms
            {'style' : None, 'duration' : 2}, 
            {'style' : {'fill':'red', 'width':8}, 'duration' : 5}
        ], 
        'repeat' : 2
    }

    # An "enum" of styles
    NORMAL = 1
    MARKED = 2
    HIGHLIGHT = 3

    def __init__(self, component_type):
        self.component_type = component_type

        if self.component_type == 'node':
            self.normal_style = GraphStyle.DEF_NORMAL_NODE_STYLE.copy()
            self.marked_style = GraphStyle.DEF_MARKED_NODE_STYLE.copy()

            self.highlight_style = GraphStyle.DEF_HIGHLIGHT_NODE_STYLE.copy()
        
        elif self.component_type == 'edge':
            self.normal_style = GraphStyle.DEF_NORMAL_EDGE_STYLE.copy()
            self.marked_style = GraphStyle.DEF_MARKED_EDGE_STYLE.copy()

            self.highlight_style = GraphStyle.DEF_HIGHLIGHT_EDGE_STYLE.copy()

        # Set current style
        self.current_style = GraphStyle.NORMAL

        # Additional variables for highlighting
        self.hl_status = None
        self.current_style_cache = None

    def set(self, to):
        if to == GraphStyle.NORMAL:
            self.hl_status = None
            self.current_style = GraphStyle.NORMAL
        elif to == GraphStyle.MARKED:
            self.hl_status = None
            self.current_style = GraphStyle.MARKED
        elif to == GraphStyle.HIGHLIGHT:
            self.hl_status = 0
            self.current_style_cache = (self.current_style, self.get())
            self.current_style = GraphStyle.HIGHLIGHT
        return self.current_style
        
    def get(self):
        if self.current_style == GraphStyle.NORMAL:
            return self.normal_style
        elif self.current_style == GraphStyle.MARKED:
            return self.marked_style
        elif self.current_style == GraphStyle.HIGHLIGHT:
            return self.get_highlight_style()
    
    def get_highlight_style(self):
        status = self.hl_status
        for _ in range(self.highlight_style['repeat']):
            for stage in self.highlight_style['animation']:
                # Duration
                status -= stage['duration']
                if status < 0:
                    return stage['style'] or self.current_style_cache[1]
        
        self.hl_status = None
        self.set(self.current_style_cache[0])
        self.current_style_cache = None
        return self.get()

    def step_highlight(self, canvas, by=1):
        if self.hl_status is None:
            return
        self.hl_status += by
        if not self.is_highlight_animation_over():
            canvas.after(100, lambda : self.step_highlight(canvas))
        canvas.draw()
    
    def is_highlight_animation_over(self):
        return self.hl_status >= self.animation_total_time()

    def animation_total_time(self):
        return sum(stage['duration'] 
                    for stage in self.highlight_style['animation']) * \
                    self.highlight_style['repeat']

    def set_normal_style(self, **style):
        self.normal_style = style
    
    def update_normal_style(self, **style):
        self.normal_style.update(style)
    
    def reset_normal_style(self, **style):
        if self.component_type == 'node':
            self.normal_style = GraphStyle.DEF_NORMAL_NODE_STYLE.copy()
        elif self.component_type == 'edge':
            self.normal_style = GraphStyle.DEF_NORMAL_EDGE_STYLE.copy()
        
    def set_marked_style(self, **style):
        self.marked_style = style
    
    def update_marked_style(self, **style):
        self.marked_style.update(style)
    
    def set_highlight_style(self, **style):
        self.highlight_style = style
    
    def update_highlight_style(self, **style):
        self.highlight_style.update(style)

NodeStyle = lambda : GraphStyle('node')
EdgeStyle = lambda : GraphStyle('edge')

if __name__ == '__main__':

    import random

    def load_network():
        network = nx.random_lobster(10, 0.1, 0.9)
        for i,e in enumerate(network.edges()):
            network.edges[e]["eid"] = i
        canvas.set_network(network)
        canvas.draw()
    
    def mark_edge():
        eid = random.choice(range(canvas.network.number_of_edges()))
        canvas.mark_edge(eid)
    
    def hl_edge():
        eids = set((
            random.choice(range(canvas.network.number_of_edges())),
            random.choice(range(canvas.network.number_of_edges())),
            random.choice(range(canvas.network.number_of_edges()))))
        for eid in eids:
            canvas.highlight_edge(eid)

    root = tk.Tk()
    root.title('SEQUIN Toolkit')
    root.geometry('950x700+200+200')

    button = tk.Button(root, text="load network", command=load_network)
    button.pack()

    button2 = tk.Button(root, text='mark rand edge', command=mark_edge)
    button2.pack()

    button3 = tk.Button(root, text='highlight rand edge', command=hl_edge)
    button3.pack()

    canvas = nxCanvas(root)

    canvas.pack(fill='both', expand=True)

    root.mainloop()