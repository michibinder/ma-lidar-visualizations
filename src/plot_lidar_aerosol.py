################################################################################
# Copyright 2023 German Aerospace Center                                       #
################################################################################
# This is free software you can redistribute/modify under the terms of the     #
# GNU Lesser General Public License 3 or later: http://www.gnu.org/licenses    #
################################################################################

import os
import sys
import time
import glob
import shutil
import configparser
import datetime
import multiprocessing

import numpy as np
import xarray as xr

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.colors import BoundaryNorm
from matplotlib.ticker import AutoMinorLocator, MultipleLocator
from mpl_toolkits.axes_grid1 import make_axes_locatable

import warnings
warnings.simplefilter("ignore", RuntimeWarning)

import filter, cmaps, lidar_processor, plt_helper

plt.style.use('latex_default.mplstyle')

def plot_lidar_aerosol(config, obs, pbar):
    """Visualize lidar measurement (aerosol)"""

    file_name = os.path.split(obs)[-1]
    zrange = eval(config.get("GENERAL","ALTITUDE_RANGE_AEROSOL"))
    trange = eval(config.get("GENERAL","BSRRANGE"))
    ds = lidar_processor.open_and_decode_lidar_measurement(obs)
    if ds is None:
        return
    ds = lidar_processor.process_lidar_measurement(config, ds)

    """Figure"""
    fig, axes = plt.subplots(2,1,figsize=(6,10))

    h_fmt      = mdates.DateFormatter('%H')
    hlocator   = mdates.HourLocator(byhour=range(0,24,6))
    filter_str = "Backscatter ratio"
        
    ax_lid = axes[0]
    cb_range  = eval(config.get("GENERAL", "BSRRANGE"))
    cb_range[0]=1
    cb_range[1]=2.1
    clev      = np.arange(cb_range[0],cb_range[1],0.1)
    #clev_l    = np.arange(cb_range[0]+0.5,cb_range[1]-0.5,1)
    cbar_l    = "backscatter ratio" 
    cbar_l    = "" 
    cmap      = plt.get_cmap('plasma')

    norm = BoundaryNorm(boundaries=clev, ncolors=cmap.N, clip=True)
    pcolor0 = ax_lid.pcolormesh(ds.time.values, ds.alt_plot.values, np.matrix.transpose(ds["bsr"].values),
                            cmap=cmap, norm=norm)

    ax_lid.set_xlim(ds['date_startp'],ds['date_endp'])
    ax_lid.xaxis.set_major_locator(hlocator)
    ax_lid.xaxis.set_major_formatter(plt.FuncFormatter(plt_helper.timelab_format_func))
    ax_lid.yaxis.set_major_locator(MultipleLocator(10))
    ax_lid.yaxis.set_minor_locator(AutoMinorLocator()) 
    ax_lid.xaxis.set_minor_locator(AutoMinorLocator())
    ax_lid.xaxis.set_label_position('top')
    ax_lid.tick_params(which='both', labelbottom=False,labeltop=True)            
    ax_lid.set_ylabel('altitude / km')

    ypp = 0.965
    ax_lid.text(0.03, ypp, filter_str, transform=ax_lid.transAxes, verticalalignment='top', bbox={"boxstyle" : "round", "lw":0.67, "facecolor":"white", "edgecolor":"black"})
    ax_lid.grid()
    
    # - COLORBAR - #
    cbar = fig.colorbar(pcolor0, ax=ax_lid, location='bottom', aspect=25, extend='both')
    cbar.set_label(cbar_l)
#---
    
    ax_lid = axes[1]
    cb_range  = eval(config.get("GENERAL", "BSRRANGE"))
    cb_range[0]=2
    cb_range[1]=6.4
    clev      = np.arange(cb_range[0],cb_range[1],0.4)
    #clev_l    = np.arange(cb_range[0]+0.5,cb_range[1]-0.5,1)
    cbar_l    = "backscatter ratio" 
    cmap      = plt.get_cmap('plasma')

    norm = BoundaryNorm(boundaries=clev, ncolors=cmap.N, clip=True)
    pcolor0 = ax_lid.pcolormesh(ds.time.values, ds.alt_plot.values, np.matrix.transpose(ds["bsr"].values),
                            cmap=cmap, norm=norm)

    ax_lid.set_xlim(ds['date_startp'],ds['date_endp'])
    ax_lid.xaxis.set_major_locator(hlocator)
    ax_lid.xaxis.set_major_formatter(plt.FuncFormatter(plt_helper.timelab_format_func))
    ax_lid.yaxis.set_major_locator(MultipleLocator(10))
    ax_lid.yaxis.set_minor_locator(AutoMinorLocator()) 
    ax_lid.xaxis.set_minor_locator(AutoMinorLocator())
    ax_lid.xaxis.set_label_position('top')
    ax_lid.tick_params(which='both', labelbottom=False,labeltop=True)            
    ax_lid.set_ylabel('altitude / km')

    ypp = 0.965
#    ax_lid.text(0.03, ypp, filter_str, transform=ax_lid.transAxes, verticalalignment='top', bbox={"boxstyle" : "round", "lw":0.67, "facecolor":"white", "edgecolor":"black"})
    ax_lid.grid()

    # - COLORBAR - #
    #cbar = fig.colorbar(pcolor0, ax=axes, location='bottom', ticks=clev_l, fraction=1, shrink=0.9, aspect=25, extend='both') # aspect=30
    cbar = fig.colorbar(pcolor0, ax=ax_lid, location='bottom', aspect=25, extend='both')
    cbar.set_label(cbar_l)
#---

    axes[0].set_ylim(zrange[0],zrange[1])
    axes[1].set_ylim(zrange[0],zrange[1])

    """Formatting"""
    TRES = int(config.get("GENERAL","RESOLUTION_AEROSOL").split("Z")[0][2:])
    VRES = int(config.get("GENERAL","RESOLUTION_AEROSOL").split("Z")[-1][:-3])
#    axes[0].text(.2, -0.75, "UTC", horizontalalignment='right', verticalalignment='bottom', transform=axes[0].transAxes)
    
    axes[1].text(1, -0.75, np.char.add('date created ',ds['date_created'].to_numpy()), horizontalalignment='right',verticalalignment='bottom',transform=axes[1].transAxes, fontsize=10)

    fig.tight_layout(rect=[0, 0, 1, .9])

    fig.suptitle('          German Aerospace Center (DLR)\n \
    {}, {}\n \
    ------------------------------\n \
    Resolution: {}$\,$m  x  {}$\,$min'.format(config.get("GENERAL","INSTRUMENT"), config.get("GENERAL","STATION_NAME"), VRES, TRES))

    """Watermark"""
    fig = plt_helper.add_watermark(fig)
    
    """Save figure"""
    fig_name = file_name[:14] + ds.duration_str + '.png'
    fig.savefig(os.path.join(config.get("OUTPUT","FOLDER"),config.get("GENERAL","CONTENT"),fig_name), facecolor='w', edgecolor='w', format='png', dpi=150, bbox_inches='tight') # orientation='portrait'

    """Finish"""
    plt_helper.show_progress(pbar['progress_counter'], pbar['lock'], pbar["stime"], pbar['ntasks'])
