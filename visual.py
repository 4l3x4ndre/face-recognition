import networkx as nx
import matplotlib as mpl

# Use a dedicated backend to handle interactive gui
mpl.use('TkAgg')

import matplotlib.patches as patches
import matplotlib.pyplot as plt

# Interactive mode on
plt.ion()

from matplotlib.animation import FuncAnimation
from matplotlib.widgets import Button, Slider, Rectangle
import time
import math
import random


class State:
    def __init__(self, g, g_nx, spread_func, root):

        # ALL THE FOLLOWING OF __INIT__ INITIALIZE VALUES

        self.index = 0
        self.g = g
        self.g_nx = g_nx
        self.root = root

        # Positions of the nodes to keep them in the same place and not
        # redraw completely the graph
        self.pos = nx.fruchterman_reingold_layout(self.g_nx)

        # Keep track of graph colors
        self.colors = ['#35FFAD' for i in range(self.g_nx.number_of_nodes())]

        # Spread function to create a step by step spread
        self.spread = spread_func
        self.spread_attributes = {'g':g, 'id':0, 'r':root, 'q':[root], 'c':[]}

        # Infected nodes: {node_name: day of infection}
        # With the day, we can create an immunity system
        self.infected = {root:0}

        # Like infected but with immune
        self.immune = {}

        # Values that will be modified
        self.r0 = 3 
        self.r0_delta = 3
        # Day to immunity (DTI)
        self.day_to_immunity = 3
        # Immunity period in days
        self.immunity_period = 10
        # Death probability when infected
        self.deathprob = .1

        # Colors
        self.color_pallet = {
            "normal": "#35FFAD", # also in self.colors
            "infected": "#FF4348",
            "immune": "#7B02FF",
            "dead": "#000000"
        }

        # General infos
        self.is_stopped = False
        self.is_auto = False
        self.closing = False
        self.change = True
    
        # The number of cases, updated in the 'next' method
        self.nbcases = 1 # the first one is the root

    def start_loop(self):
        """
        Start the infinite loop to handle changes and draw them
        """
        self.loop()

    def loop(self):
        """
        The main loop to maintain the plt on
        """

        # While we did not press the close button -> continue the loop
        while not self.closing:
            # True when pressing next
            if self.change:
                self.change = False
                self.draw()
            # True when pressing auto
            elif self.is_auto:
                # Check if the auto should stop
                if not self.check_auto():
                    self.is_auto = False
                    continue
                self.next()
                self.change = False
                self.draw()
                plt.pause(1)

            # Draw then pause
            plt.draw()
            plt.pause(.1)
        
    def set_node_colors(self):
        """
        Set colors according to immune/normal or infected/dead
        """
    
        # immune/normal
        for i in range(len(list(self.g_nx.nodes))):
            nodex = list(self.g_nx.nodes)[i] # node name

            # if in immune array -> node is immune
            if nodex in self.immune:
                self.colors[i] = self.color_pallet['immune']

            # not immune and not infected ? -> normal
            elif nodex not in self.infected:
                self.colors[i] = self.color_pallet['normal']

        # infected/dead color
        # Checking all the infected node in the infected dict
            # We associate the node [dict key] to its appropriate index in the networkx graph
        # If value is -1 -> means dead. Otherwise it is just infected
        for node, d in self.infected.items():

            # Get the matching index
            index_in_g_nx = list(self.g_nx.nodes).index(node)
            
            # Check the value of the dict then affect the matching color
            if self.infected[node] == -1:
                self.colors[index_in_g_nx] = self.color_pallet['dead']
            elif node not in self.immune:
                self.colors[index_in_g_nx] = self.color_pallet['infected']

    def draw_buttons(self):
        """
        Draw all buttons in plt.
        """ 
        # Button to continue the spread ([x0, y0, width, height])
        b_axnext = plt.axes([0.002, 0.02, 0.05, 0.025])
        # Reference to the button need to stay inside the class
        self.bnext = Button(b_axnext, 'Next')
        self.bnext.on_clicked(self.next)

        # Button to transit to the end
        b_axend = plt.axes([0.002, 0.05, 0.05, 0.025])
        #Reference to that button
        self.bend = Button(b_axend, 'Auto')
        self.bend.on_clicked(self.last_action)

        # Button to stop everything
        b_axstop = plt.axes([0.002, 0.08, 0.05, 0.025])
        #Reference to that button
        self.bstop = Button(b_axstop, 'Stop')
        self.bstop.on_clicked(self.stop)
        
        # Button to close
        b_axclose = plt.axes([1-0.05, 1-0.025, 0.05, 0.025])
        #Reference to that button
        self.bclose = Button(b_axclose, 'Close')
        self.bclose.on_clicked(self.close)

    def draw_sliders(self):
        """
        Draw all sliders in plt.
        """
        # r0 slider
        axcolor = 'lightgrey'
        ax_r0slider = plt.axes([0.01, 0.25, 0.015, 0.3], facecolor=axcolor)
        self.r0_slider = Slider(
            ax=ax_r0slider,
            label="R0",
            valmin=0,
            valmax=10,
            valinit=self.r0,
            valfmt='%0.0f',
            valstep =1.0,
            orientation="vertical"
        )
        self.r0_slider.on_changed(self.r0_changed)

        # day to immunity slider
        axcolor = 'lightgrey'
        ax_dtislider = plt.axes([0.01, 0.617, 0.015, 0.3], facecolor=axcolor)
        self.dti_slider = Slider(
            ax=ax_dtislider,
            label="Infected\nperiod\n(days)",
            valmin=0,
            valmax=10,
            valinit=self.day_to_immunity,
            valfmt='%0.0f',
            valstep =1.0,
            orientation="vertical"
        )
        self.dti_slider.on_changed(self.daytoimmunity_changed)

        
        # immunity period slider
        axcolor = 'lightgrey'
        ax_ipslider = plt.axes([1-0.035, 0.05, 0.015, 0.3], facecolor=axcolor)
        self.ip_slider = Slider(
            ax=ax_ipslider,
            label="Immunity\nperdiod\n(days)",
            valmin=0,
            valmax=100,
            valinit=self.immunity_period,
            valfmt='%0.0f',
            valstep =1.0,
            orientation="vertical"
        )
        self.ip_slider.on_changed(self.immunityperiod_changed)
        
        # death probability slider
        axcolor = 'lightgrey'
        ax_dpslider = plt.axes([1-0.035, 0.5, 0.015, 0.2], facecolor=axcolor)
        self.dp_slider = Slider(
            ax=ax_dpslider,
            label="Immunity\nperdiod\n(days)",
            valmin=0,
            valmax=1,
            valinit=self.deathprob,
            valstep=.001,
            orientation="vertical"
        )
        self.dp_slider.on_changed(self.deathproba_changed)

    def draw_texts(self, ax):
        """
        Draw all texts in plt.
        ax: the plot ax
        """

        # Stats on the spread
        plt.text(-.05,.2,
                'Cases: ' + str(self.nbcases) + '/' + str(len(self.g.vertices())),
                horizontalalignment='left',
                verticalalignment='center', 
                color='black', 
                transform=ax.transAxes,
                fontsize = 15
        )

        # Text to keep track of days
        plt.text(-.05,.15,
            'Day: ' + str(self.index),
            horizontalalignment='left',
            verticalalignment='center',
            color='r',
            transform=ax.transAxes,
            fontsize = 20
        )

    def draw(self):
        """
        Draw the graph with the positions stored as well as buttons/texts/sliders.
        """
        
        # Set the appropriate color for each node according to its state(immune, infected, ...) to then draw the graph
        self.set_node_colors()

        # Clear the figure
        plt.clf()

        # Create axes in which the graph will fit
        ax = plt.gca()        

        # Adjust canvas size
        plt.subplots_adjust(top=.9, left=0.05, bottom=0, right=.95) 
 
        # Draw the networkx graph with the same position thanks to the node positions stored
        nx.draw(self.g_nx, cmap = plt.get_cmap('jet'), node_color = self.colors, with_labels=True, pos=self.pos, edge_color='#BABBC1')
        
        self.draw_texts(ax)
        self.draw_buttons()
        self.draw_sliders()

    def immunityperiod_changed(self, event):
        """
        Change the immunity_period.
        Called when the slider's value change.
        """
        self.immunity_period = int(self.ip_slider.val)

    def daytoimmunity_changed(self, event):
        """
        Change the day_to_immunity.
        Called when the slider's value change.
        """
        self.day_to_immunity = int(self.dti_slider.val)

    def r0_changed(self, event):
        """
        Change the r0
        Called when the slider's value change.
        """
        # Converting the value of the slider in int as we need a int r0
        self.r0 = int(self.r0_slider.val)

        # Updating our delta: min and max infections that are possible for the same node
        self.r0_delta = int(self.r0/2)


    def next(self, event=None):
        """
        Continue the spread.
        """
        # Index/day
        self.index += 1

        # Continue the spread by calling the spread function
        r = self.spread(
                self.spread_attributes['g'],
                self.immune,
                self.index,
                self.spread_attributes['r'],
                self.r0,
                self.r0_delta,
                self.spread_attributes['q'],
                self.spread_attributes['c'],
        )
        self.spread_attributes['q'] = r['q']
        self.spread_attributes['c'] = r['c']
        
        # Update our infected tracker : new infected => current day or dead
        for n in self.spread_attributes['c'] + [n for n in self.spread_attributes['q'] if n not in self.spread_attributes['c']]:
            if n not in self.infected and n not in self.immune:
                # Vital prognosis engaged                
                if random.random() <= self.deathprob:
                    print(n, "just died")
                    # -1 means dead
                    self.infected[n] = -1
                    if n in self.spread_attributes['c']: 
                        c = self.spread_attributes['c'].copy()
                        c.remove(n)
                        self.spread_attributes['c'] = c.copy()
                    if n in self.spread_attributes['q']:
                        c = self.spread_attributes['q'].copy()
                        c.remove(n)
                        self.spread_attributes['q'] = c.copy()
                else:
                    self.infected[n] = self.index
                    self.nbcases += 1
            elif n in self.infected and self.infected[n] == -1:
                if n in self.spread_attributes['c']: 
                    c = self.spread_attributes['c'].copy()
                    c.remove(n)
                    self.spread_attributes['c'] = c.copy()
                if n in self.spread_attributes['q']:
                    c = self.spread_attributes['q'].copy()
                    c.remove(n)
                    self.spread_attributes['q'] = c.copy()


        infected_to_remove = []
        for n, d in self.infected.items():
            if d != -1 and self.index >= d + self.day_to_immunity:
                if n in self.spread_attributes['c']: 
                    c = self.spread_attributes['c'].copy()
                    c.remove(n)
                    self.spread_attributes['c'] = c.copy()
                if n in self.spread_attributes['q']:
                    c = self.spread_attributes['q'].copy()
                    c.remove(n)
                    self.spread_attributes['q'] = c.copy()
                self.nbcases -= 1
                self.immune[n] = self.index
                infected_to_remove.append(n)

        for n in infected_to_remove:
            self.infected.pop(n)

        immunity_to_remove = []
        for n, d in self.immune.items():
            if self.index >= d + self.day_to_immunity + self.immunity_period:
                immunity_to_remove.append(n)

        for n in immunity_to_remove:
            self.immune.pop(n)
        

        # Debug infected
        print('////////////////////////')
        for n, d in self.infected.items():
            print(n, d)
        print(len(list(self.infected.keys())))
        print('////////////////////////')

        print('~~~~~~~~~~~~~~~~~~~~~')
        for n, d in self.immune.items():
            print(n, d)
        print('~~~~~~~~~~~~~~~~~~~~~')

        # Debug info
        print('############################# start checked')
        print(self.spread_attributes['c'])
        print('############################# start queued')
        print(self.spread_attributes['q'])

        # Make it possible to the loop to detect changed        
        self.change = True


    
    def last_action(self, event):
        """
        Called by a button, start the automatic process.
        """

        # We launch the automatic by unstopping it then activate it
        self.is_stopped = False
        self.is_auto = True

    def check_auto(self):
        # If no one is infected and the population ir 100% normal (or immune) then it's over
        if self.color_pallet['infected'] not in self.colors and not (self.color_pallet['normal'] in self.colors and self.color_pallet['immune'] in self.colors): return False
        return True


    def stop(self, event):
        """
        Shutdown (just a value) the process.
        """
        print("stop auto")
        self.is_stopped = True
        self.is_auto = False

    def deathproba_changed(self, event):
        """
        Call when the slider's value changed.
        """
        self.deathprob = self.dp_slider.val

    def close(self, event):
        """
        Close the windows.
        Called by a button.
        """
        self.closing = True
        self.is_auto = False
        plt.close('all')
    

def show_graph(g, spread_func, root):

    
    # Networkx Graph setup
    g_nx = nx.Graph()
    for vertice in g.vertices():
        for n in g.neighbors(vertice):
            g_nx.add_edge(vertice, n)

    print(
            g_nx.number_of_nodes(),
            g_nx.number_of_edges()
    )

    # Plot setup (height, width)
    fig = plt.figure(figsize=(15, 7))
    
    # Creating an instance of State to keep track of the state of the graph
    state = State(g, g_nx, spread_func, root)
    state.start_loop()


