import h5py
import webbrowser
import numpy as np
import string 
import math
from bokeh.plotting import figure
from bokeh.io import output_file, show
from bokeh.layouts import gridplot
from bokeh.models.ranges import *
from bokeh.models.tickers import FixedTicker
from plotly import tools 
import plotly.plotly as py 
import plotly.graph_objs as go 

#function to print array in cmdline 
def print_array (a, str):
    if (len(a) != 0):
        for i in range(len(a)):
            print("%s[%s]: %s" % (str, i, a[i]))
    else:
        print("\nArray passed in was empty!\n")

#receive hdf5 file as input and save it for extraction 
f = h5py.File('IHM_full.hdf5', 'r') 
#f = h5py.File('mytestfile.hdf5', 'r')

#array in which hdf5's groups will be appended
dataset_groups = []
#array in which actual data will be stored
dataset_values = []
 
#create the HTML file
output_file('lines.html')

#append data from hdf5 object into array
def append_attrs(name,obj):
    dataset_groups.append(obj)
f.visititems(append_attrs)

print(" %s ORIGINAL ALL DATA: " % f)
print_array(dataset_groups, "dataset_groups")

#populate data-only array with None so it can be iterated through if data exists, otherwise raise error
if(len(dataset_groups) != 0):
    dataset_values = [None] * len(dataset_groups)
else:
    raise ValueError('\nNo data groups exist, no data avaliable to extract\n') 

#if dataset_groups's element contains data, replace None in data array with data objects
for i in range(len(dataset_groups)):
    try:
        (dataset_groups[i]).dtype 
        dataset_values[i]=dataset_groups[i]
    except AttributeError:
       pass
#filter out None elements in array
dataset_values = list(filter(None, dataset_values))     

#print final array of data
print("%s ISOLATED DATA: " % f)
print_array(dataset_values, "dataset_values")

#if usable dataset detected needs to have its axis swapped
#only for 2d arrays
def swap_2Daxes(dataset):
    dataset = np.swapaxes(dataset, 0, 1)
    return dataset

#generate the plot figures in 1D array
def plotarray(xvar,yvar,titlelab,xlab,ylab):
    p = [0] * len(yvar)
    for i in (range(len(p))):
        p[i] = figure(title = titlelab,
                   x_axis_label = xlab,
                   y_axis_label =ylab,
                   plot_width=250, plot_height=250)
        p[i].line(xvar[i], yvar[i], line_width=1, color="navy")
        p[i].title.align = 'center'
        p[i].xaxis.ticker =  FixedTicker(ticks=[round(min(xvar[-1]),3), round((max(xvar[-1]))/2,3), round(max(xvar[-1]),3)])
    return p

#create 2D array of plots
def populatedisplay(array, index, length, plotholder):
    rangelist = list(range(length))
    if index == 0:
        for i in rangelist: 
            array[index].append(plotholder[i])
    elif index != 0:
        rangelistlong = [j+(length*index) for j in rangelist]
        for i in rangelistlong: 
            array[index].append(plotholder[i])

#find dataset value array that contains time
def get_time(dataset): 
    for i in range(len(dataset)):
        if dataset[i].name == '/time':  
            return dataset[i].value
    raise ValueError('No time var')

#find dataset value array that contains EMG data
def get_emg(dataset, timedataset):
    for i in range(len(dataset)):
        if '/Grid1/EMG' in dataset[i].name: 
            return dataset[i].value
        elif 'EMG' in dataset[i].name and dataset[i].shape[1] == timedataset.shape[0]:
            return dataset[i].value

#getting time and emg values
time_var = get_time(dataset_values)
numrows_time = len(time_var)
time_var = time_var.reshape(numrows_time, 1)
emg_var = get_emg(dataset_values, time_var)
new_timevar = np.repeat([time_var], len(emg_var), axis=0)
new_timevar = new_timevar[:,:,0]
new_timevar = new_timevar*1e-3
#generate plots for emg
eplot = plotarray(new_timevar,emg_var,'Electrode EMG','Time (s)','EMG mV')
#grid of plots needs to be a sqaure for the layout, this gets length/width of that square
emgsquarelen = math.sqrt(len(emg_var))
emgsquarelen = int(emgsquarelen)
rows = [[] for _ in range(emgsquarelen)]
for i in range(emgsquarelen):
    populatedisplay(rows, i, emgsquarelen, eplot)

#generate frequency and fft'ed emg values
emg_fft = np.fft.fft(emg_var)
freq = np.fft.fftfreq(len(emg_fft[0]))
new_freq = np.repeat([freq], len(emg_var), axis=0)
new_freq = abs(new_freq)
#generate plots for emg fft
fplot = plotarray(new_freq, emg_fft.real, 'Electrode EMG', 'Frequency (Hz)', 'EMG mV')
#grid of plots needs to be a sqaure for the layout, this gets length/width of that square
emgfftsquarelen = math.sqrt(len(emg_fft))
emgfftsquarelen = int(emgfftsquarelen)
rows2 = [[] for _ in range(emgfftsquarelen)]
for i in range(emgfftsquarelen):
    populatedisplay(rows2, i, emgfftsquarelen, fplot)


maxarray = []
for i in range(len(dataset_values[0])):
    for j in range(len(dataset_values[i])):
        for k in range(len(dataset_values[i][j])):
            maxarray.append(max(dataset_values[i][j][k]))
 
#gridplot needs plots as a list
layout = gridplot(list(rows))
layout2 = gridplot(list(rows2))

#show(layout)
show(layout2)