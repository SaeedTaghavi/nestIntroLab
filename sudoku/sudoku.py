# Copyright (c) 2017-2020 The University of Manchester
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

#############################################################
#
# A PyNN Sudoku model
# Steve Furber, November 2015
#
#############################################################
from pyNN.random import RandomDistribution
import pyNN.spiNNaker as p
import spynnaker.pyNN.external_devices as ext
import subprocess
import os
import sys
import traceback

run_time = 20000                        # run time in milliseconds
neurons_per_digit = 5                   # number of neurons per digit
fact = float(neurons_per_digit) / 10.0  # number of neurons per digit / 10
ms_per_bin = 100
running = False
ended = False


# Run the visualiser
def read_output(visualiser, out):
    result = visualiser.poll()
    while result is None:
        line = out.readline()
        if line:
            print(line)
        result = visualiser.poll()
    print("Visualiser exited: {} - quitting".format(result))
    if running and not ended:
        p.end()
    os._exit(0)  # pylint: disable=protected-access


def activate_visualiser(old_vis):
    vis_exe = None
    if old_vis:
        if sys.platform.startswith("win32"):
            vis_exe = "sudoku.exe"
        elif sys.platform.startswith("darwin"):
            vis_exe = "sudoku_osx"
        elif sys.platform.startswith("linux"):
            vis_exe = "sudoku_linux"
        else:
            raise NotImplementedError(f"Unknown platform: {sys.platform}")
        vis_exe = [os.path.abspath(os.path.join(
            os.path.dirname(__file__), vis_exe))]
        neur_per_num_opt = "-neurons_per_number"
        ms_per_bin_opt = "-ms_per_bin"
    else:
        vis_exe = ["spynnaker_sudoku"]
        neur_per_num_opt = "--neurons_per_number"
        ms_per_bin_opt = "--ms_per_bin"
    try:
        subprocess.Popen(
            args=vis_exe + [neur_per_num_opt, str(neurons_per_digit),
                            ms_per_bin_opt, str(ms_per_bin)],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=1)
        # Thread(target=read_output,
        #        args=[visualiser, visualiser.stdout]).start()
    except Exception:  # pylint: disable=broad-except
        if not old_vis:
            print("This example depends on https://github.com/"
                  "SpiNNakerManchester/sPyNNakerVisualisers")
            traceback.print_exc()
            print("trying old visualiser")
            activate_visualiser(old_vis=True)
        else:
            raise


activate_visualiser(old_vis=("OLD_VIS" in os.environ))

p.setup(timestep=1.0)
print("Creating Sudoku Network...")
n_cell = int(90 * fact)   # total number of neurons in a cell
n_stim = 30               # number of neurons in each stimulation source
n_N = n_cell // 9         # number of neurons per value in cell

# total number of neurons
n_total = n_cell * 9 * 9
n_stim_total = n_stim * 9 * 9

# global distributions & parameters
weight_cell = 0.2
weight_stim = 1
dur_nois = RandomDistribution("uniform", [30000.0, 30001.0])
weight_nois = 1.4
delay = 2.0
puzzle = 6

# initialise non-zeros
# NB use as init[8-y][x] -> cell[x][y]

if puzzle == 1:
    # Diabolical problem:
    init = [[0, 0, 1,  0, 0, 8,  0, 7, 3],
            [0, 0, 5,  6, 0, 0,  0, 0, 1],
            [7, 0, 0,  0, 0, 1,  0, 0, 0],

            [0, 9, 0,  8, 1, 0,  0, 0, 0],
            [5, 3, 0,  0, 0, 0,  0, 4, 6],
            [0, 0, 0,  0, 6, 5,  0, 3, 0],

            [0, 0, 0,  1, 0, 0,  0, 0, 4],
            [8, 0, 0,  0, 0, 9,  3, 0, 0],
            [9, 4, 0,  5, 0, 0,  7, 0, 0]]
elif puzzle == 2:
    init = [[2, 0, 0,  0, 0, 6,  0, 3, 0],
            [4, 8, 0,  0, 1, 9,  0, 0, 0],
            [0, 0, 7,  0, 2, 0,  9, 0, 0],

            [0, 0, 0,  3, 0, 0,  0, 9, 0],
            [7, 0, 8,  0, 0, 0,  1, 0, 5],
            [0, 4, 0,  0, 0, 7,  0, 0, 0],

            [0, 0, 4,  0, 9, 0,  6, 0, 0],
            [0, 0, 0,  6, 4, 0,  0, 1, 9],
            [0, 5, 0,  1, 0, 0,  0, 0, 8]]
elif puzzle == 3:
    init = [[0, 0, 3,  2, 0, 0,  0, 7, 0],
            [0, 0, 5,  0, 0, 0,  3, 0, 0],
            [0, 0, 8,  9, 7, 0,  0, 5, 0],

            [0, 0, 0,  8, 9, 0,  0, 0, 0],
            [0, 5, 0,  0, 0, 0,  0, 2, 0],
            [0, 0, 0,  0, 6, 1,  0, 0, 0],

            [0, 1, 0,  0, 2, 5,  6, 0, 0],
            [0, 0, 4,  0, 0, 0,  8, 0, 0],
            [0, 9, 0,  0, 0, 7,  5, 0, 0]]
elif puzzle == 4:
    init = [[0, 1, 0,  0, 0, 0,  0, 0, 2],
            [8, 7, 0,  0, 0, 0,  5, 0, 4],
            [5, 0, 2,  0, 0, 0,  0, 9, 0],

            [0, 5, 0,  4, 0, 9,  0, 0, 1],
            [0, 0, 0,  7, 3, 2,  0, 0, 0],
            [9, 0, 0,  5, 0, 1,  0, 4, 0],

            [0, 2, 0,  0, 0, 0,  4, 0, 8],
            [4, 0, 6,  0, 0, 0,  0, 1, 3],
            [1, 0, 0,  0, 0, 0,  0, 2, 0]]
elif puzzle == 5:
    init = [[8, 9, 0,  2, 0, 0,  0, 7, 0],
            [0, 0, 0,  0, 8, 0,  0, 0, 0],
            [0, 4, 1,  0, 3, 0,  5, 0, 0],

            [2, 5, 8,  0, 0, 0,  0, 0, 6],
            [0, 0, 0,  0, 0, 0,  0, 0, 0],
            [6, 0, 0,  0, 0, 0,  1, 4, 7],

            [0, 0, 7,  0, 1, 0,  4, 3, 0],
            [0, 0, 0,  0, 2, 0,  0, 0, 0],
            [0, 2, 0,  0, 0, 7,  0, 5, 1]]
elif puzzle == 6:
    # "World's hardest sudoku":
    # http://www.telegraph.co.uk/news/science/science-news/9359579/\
    # Worlds-hardest-sudoku-can-you-crack-it.html
    init = [[8, 0, 0,  0, 0, 0,  0, 0, 0],
            [0, 0, 3,  6, 0, 0,  0, 0, 0],
            [0, 7, 0,  0, 9, 0,  2, 0, 0],

            [0, 5, 0,  0, 0, 7,  0, 0, 0],
            [0, 0, 0,  0, 4, 5,  7, 0, 0],
            [0, 0, 0,  1, 0, 0,  0, 3, 0],

            [0, 0, 1,  0, 0, 0,  0, 6, 8],
            [0, 0, 8,  5, 0, 0,  0, 1, 0],
            [0, 9, 0,  0, 0, 0,  4, 0, 0]]
else:
    init = [[1, 0, 0,  4, 0, 0,  0, 0, 0],
            [7, 0, 0,  5, 0, 0,  6, 0, 3],
            [0, 0, 0,  0, 3, 0,  4, 2, 0],

            [0, 0, 9,  0, 0, 0,  0, 3, 5],
            [0, 0, 0,  3, 0, 5,  0, 0, 0],
            [6, 3, 0,  0, 0, 0,  1, 0, 0],

            [0, 2, 6,  0, 5, 0,  0, 0, 0],
            [9, 0, 4,  0, 0, 6,  0, 0, 7],
            [0, 0, 0,  0, 0, 8,  0, 0, 2]]

# Dream problem - no input!
# init = [[0 for x in range(9)] for y in range(9)]
corr = init

p.set_number_of_neurons_per_core(p.IF_curr_exp, 200)

#
# set up the 9x9 cell array populations
#
cell_params_lif = {
    'cm': 0.25,         # nF membrane capacitance
    'i_offset': 0.5,    # nA    bias current
    'tau_m': 20.0,      # ms    membrane time constant
    'tau_refrac': 2.0,  # ms    refractory period
    'tau_syn_E': 5.0,   # ms    excitatory synapse time constant
    'tau_syn_I': 5.0,   # ms    inhibitory synapse time constant
    'v_reset': -70.0,   # mV    reset membrane potential
    'v_rest': -65.0,    # mV    rest membrane potential
    'v_thresh': -50.0,  # mV    firing threshold voltage
}

print("Creating Populations...")
cells = p.Population(n_total, p.IF_curr_exp, cell_params_lif, label="Cells",
                     additional_parameters={"spikes_per_second": 200})
cells.record("spikes")
ext.activate_live_output_for(cells, tag=1, port=17897)

#
# add a noise source to each cell
#
print("Creating Noise Sources...")
noise = p.Population(
    n_total, p.SpikeSourcePoisson,
    {"rate": 20.0},
    label="Noise")
p.Projection(noise, cells, p.OneToOneConnector(),
             synapse_type=p.StaticSynapse(weight=weight_nois))


#
# set up the cell internal inhibitory connections
#
print("Setting up cell inhibition...")
connections = list()
for x in range(9):
    for y in range(9):
        base = ((y * 9) + x) * n_cell

        # full constant matrix of weight_cell apart from n_N squares on
        # diagonal
        connections_cell = [
            (i + base, j + base,
             0.0 if i // n_N == j // n_N else weight_cell, delay)
            for i in range(n_cell) for j in range(n_cell)
        ]
        connections.extend(connections_cell)


#
# set up the inter-cell inhibitory connections
#
def interCell():
    """ Inhibit same number: connections are n_N squares on diagonal of
        weight_cell() from cell[x][y] to cell[r][c]
    """
    base_source = ((y * 9) + x) * n_cell
    base_dest = ((c * 9) + r) * n_cell
    connections_intC = [
        (i + base_source, j + base_dest, weight_cell, delay)
        for i in range(n_cell)
        for j in range(n_N * (i // n_N), n_N * (i // n_N + 1))]

    connections.extend(connections_intC)


print("Setting up inhibition between cells...")
for x in range(9):
    for y in range(9):
        for r in range(9):
            if r != x:
                interCell()  # by row...
        for c in range(9):
            if c != y:
                interCell()  # by column...
        for r in range(3 * (x // 3), 3 * (x // 3 + 1)):
            for c in range(3 * (y // 3), 3 * (y // 3 + 1)):
                if r != x and c != y:
                    interCell()  # & by square
conn_intC = p.FromListConnector(connections)
p.Projection(cells, cells, conn_intC, receptor_type="inhibitory")

#
# set up & connect the initial (stimulation) conditions
#
print("Fixing initial numbers...")
s = 0
connections_stim = []
for x in range(9):
    for y in range(9):
        if init[8 - y][x] != 0:
            base_stim = ((y * 9) + x) * n_stim
            base = ((y * 9) + x) * n_cell
            for i in range(n_stim):

                # one n_N square on diagonal
                for j in range(
                        n_N * (init[8 - y][x] - 1), n_N * init[8 - y][x]):
                    connections_stim.append(
                        (i + base_stim, j + base, weight_stim, delay))

            s += 1

if len(connections_stim) > 0:
    stim = p.Population(
        n_stim_total, p.SpikeSourcePoisson,
        {"rate": 10.0}, label="Stim")
    conn_stim = p.FromListConnector(connections_stim)
    p.Projection(stim, cells, conn_stim, receptor_type="excitatory")
#
# initialise the network, run, and get results
cells.initialize(v=RandomDistribution("uniform", [-65.0, -55.0]))

running = True
p.run(run_time)

# spikes = cells.getSpikes()
# f, axarr = pylab.subplots(9, 9)
# for y in range(9):
#     for x in range(9):
#         base = ((y * 9) + x) * n_cell
#         next_base = base + n_cell
#         ids = spikes[:, 0]
#         cell_spikes = spikes[numpy.where((ids >= base) & (ids < next_base))]
#         axarr[8 - y][x].plot(
#             [i[1] for i in cell_spikes],
#             [i[0] - base for i in cell_spikes], ".")
#         axarr[8 - y][x].axis([0, run_time, -1, n_cell + 1])
#         # axarr[8 - y][x].axis('off')
# pylab.show()
# pylab.savefig("sudoku.png")

p.end()
ended = True
