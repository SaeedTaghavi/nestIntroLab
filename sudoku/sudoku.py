#############################################################
#
# A PyNN Sudoku model
# Steve Furber, November 2015
#
#############################################################

import pyNN.spiNNaker as p
from pyNN.random import RandomDistribution
import spynnaker_external_devices_plugin.pyNN as ext
import subprocess
from threading import Thread
import os
import sys

import matplotlib
import time
matplotlib.use("Agg")
import pylab  # @IgnorePep8

run_time = 10000                        # run time in milliseconds
neurons_per_digit = 25                  # number of neurons per digit
fact = float(neurons_per_digit) / 10.0  # number of neurons per digit / 10
init_skew = 0.0                         # ms - skew between successive inputs
ms_per_bin = 100


# Run the visualiser
def read_output(visualiser, out):
    while visualiser.poll() is None:
        line = out.readline()
        if line:
            print line
    print "Visualiser exited - quitting"
    os._exit(0)

vis_exe = None
if sys.platform.startswith("win32"):
    vis_exe = "sudoku.exe"
elif sys.platform.startswith("darwin"):
    vis_exe = "sudoku_osx"
elif sys.platform.startswith("linux"):
    vis_exe = "sudoku_linux"
else:
    raise Exception("Unknown platform: {}".format(sys.platform))
vis_exe = os.path.abspath(os.path.join(os.path.dirname(__file__), vis_exe))
print "Executing", vis_exe
visualiser = subprocess.Popen(args=[
    vis_exe,
    "-neurons_per_number", str(neurons_per_digit),
    "-ms_per_bin", str(ms_per_bin)],
    stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=1)
Thread(target=read_output, args=[visualiser, visualiser.stdout]).start()

p.setup(timestep=1.0)
print "Creating Sudoku Network..."
n_cell = int(90 * fact)  # total number of neurons in a cell
n_stim = 30              # number of neurons in each stimulation source
n_N = n_cell / 9         # number of neurons per value in cell

# global distributions & parameters
weight_cell = RandomDistribution("uniform", [-0.2 / fact, -0.0 / fact])
weight_stim = RandomDistribution("uniform", [0.0, 0.2])
dur_nois = RandomDistribution("uniform", [30000.0, 30001.0])
weight_nois = 1.4
delay = 2.0


# Diabolical problem:

init = [[0, 0, 1, 0, 0, 8, 0, 7, 3],  # initialise non-zeros
        [0, 0, 5, 6, 0, 0, 0, 0, 1],  # NB use as init[8-y][x] -> cell[x][y]
        [7, 0, 0, 0, 0, 1, 0, 0, 0],
        [0, 9, 0, 8, 1, 0, 0, 0, 0],
        [5, 3, 0, 0, 0, 0, 0, 4, 6],
        [0, 0, 0, 0, 6, 5, 0, 3, 0],
        [0, 0, 0, 1, 0, 0, 0, 0, 4],
        [8, 0, 0, 0, 0, 9, 3, 0, 0],
        [9, 4, 0, 5, 0, 0, 7, 0, 0]]

corr = init

# Dream problem - no input!
"""
init = [[0 for x in range(9)] for y in range(9)]
corr = init
"""

#
# set up the 9x9 cell array populations
#
cell_params_lif = {
    'cm': 0.25,         # nF membrane capacitance
    'i_offset': 0.3,    # nA    bias current
    'tau_m': 20.0,      # ms    membrane time constant
    'tau_refrac': 2.0,  # ms    refractory period
    'tau_syn_E': 5.0,   # ms    excitatory synapse time constant
    'tau_syn_I': 5.0,   # ms    inhibitory synapse time constant
    'v_reset': -70.0,   # mV    reset membrane potential
    'v_rest': -65.0,    # mV    rest membrane potential
    'v_thresh': -50.0   # mV    firing threshold voltage
}

print "Creating Populations..."
cell = [[
    p.Population(
        n_cell, p.IF_curr_exp, cell_params_lif,
        label="Cell" + str(x + 1) + str(y + 1))
    for x in range(9)] for y in range(9)]
for x in range(9):
    for y in range(9):
        ext.activate_live_output_for(cell[x][y], tag=1, port=17897)

#
# add a noise source to each cell
#
print "Creating Noise Sources..."
nois = [[
    p.Population(
        n_cell, p.SpikeSourcePoisson,
        {"rate": 20.0, "start": 0.0, "duration": dur_nois},
        label="Noise" + str(x + 1) + str(y + 1))
    for x in range(9)] for y in range(9)]

# connect noise neurons one-to-one to cell neurons
conn_nois = p.OneToOneConnector(weight_nois)
for x in range(9):
    for y in range(9):
        p.Projection(nois[x][y], cell[x][y], conn_nois, target="excitatory")

#
# set up the cell internal inhibitory connections
#
print "Setting up cell inhibition..."
for x in range(9):
    for y in range(9):

        # full constant matrix of weight_cell apart from n_N squares on
        # diagonal
        connections_cell = [
            (i, j, 0.0 if i // n_N == j // n_N else weight_cell.next(), delay)
            for i in range(n_cell) for j in range(n_cell)
        ]
        conn_cell = p.FromListConnector(connections_cell)
        p.Projection(cell[x][y], cell[x][y], conn_cell, target="inhibitory")


#
# set up the inter-cell inhibitory connections
#
def interCell(x, y, r, c):
    """ Inhibit same number: connections are n_N squares on diagonal of
        weight_cell() from cell[x][y] to cell[r][c]
    """
    connections_intC = [
        (i, j, weight_cell.next(), delay)
        for i in range(n_cell)
        for j in range(n_N * (i // n_N), n_N * (i // n_N + 1))]
    conn_intC = p.FromListConnector(connections_intC)
    p.Projection(cell[x][y], cell[r][c], conn_intC, target="inhibitory")
    return

print "Setting up inhibition between cells..."
for x in range(9):
    for y in range(9):
        for r in range(9):
            if r != x:
                interCell(x, y, r, y)  # by row...
        for c in range(9):
            if c != y:
                interCell(x, y, x, c)  # by column...
        for r in range(3 * (x // 3), 3 * (x // 3 + 1)):
            for c in range(3 * (y // 3), 3 * (y // 3 + 1)):
                if r != x and c != y:
                    interCell(x, y, r, c)  # & by square

#
# set up & connect the initial (stimulation) conditions
#
print "Fixing initial numbers..."
s = 0
stim = []
for x in range(9):
    for y in range(9):
        if init[8 - y][x] != 0:
            connections_stim = []
            for i in range(n_stim):

                # one n_N square on diagonal
                for j in range(
                        n_N * (init[8 - y][x] - 1), n_N * init[8 - y][x]):
                    connections_stim.append((i, j, weight_stim.next(), delay))
            conn_stim = p.FromListConnector(connections_stim)
            stim.append(
                p.Population(
                    n_stim, p.SpikeSourcePoisson,
                    {"rate": 10.0, "start": init_skew * (s + 1)},
                    label="Stim" + str(s)))
            p.Projection(stim[s], cell[x][y], conn_stim, target="excitatory")
            s += 1

#
# initialise the network, run, and get results
#
for x in range(9):
    for y in range(9):
        cell[x][y].initialize(
            "v", RandomDistribution("uniform", [-65.0, -55.0]))
        cell[x][y].record()

p.run(run_time)

f, axarr = pylab.subplots(9, 9)
for y in range(9):
    for x in range(9):
        spikes = cell[x][y].getSpikes()
        axarr[8 - y][x].plot(
            [i[1] for i in spikes], [i[0] for i in spikes], "b,")
        axarr[8 - y][x].axis([0, run_time, -1, n_cell + 1])
        axarr[8 - y][x].axis('off')
pylab.savefig("sudoku.png")

p.end()

while not visualiser.poll():
    time.sleep(0.1)
