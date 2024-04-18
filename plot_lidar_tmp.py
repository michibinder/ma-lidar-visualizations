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

import filter, cmaps, lidar_processor

plt.style.use('latex_default.mplstyle')

"""Config"""
VERTICAL_CUTOFF = 15 # km (LAMBDA_CUT)
FILTERTYPE      = "tmp"

def timelab_format_func(value, tick_number):
    dt = mdates.num2date(value)
    if dt.hour == 0:
        return "{}\n{}".format(dt.strftime("%Y-%b-%d"), dt.strftime("%H"))
    else:
        return dt.strftime("%H")

        
def plot_lidar_tmp(CONFIG_FILE):
    """Visualize lidar measurements (time-height diagrams + absolute temperature measurements)"""
    
    """Settings"""
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE)

    if config.get("INPUT","OBS_FILE") == "NONE":
        obs_list = sorted(glob.glob(os.path.join(config.get("INPUT","OBS_FOLDER") , config.get("GENERAL","RESOLUTION"))))
    else:
        obs_list = os.path.join(config.get("INPUT","OBS_FOLDER"), config.get("INPUT","OBS_FILE"))
    
    config["INPUT"]["ERA5-FOLDER"] = os.path.join(config.get("OUTPUT","FOLDER"),"era5-profiles")

    config["GENERAL"]["FILTERTYPE"] = FILTERTYPE
    os.makedirs(os.path.join(config.get("OUTPUT","FOLDER"),config.get("GENERAL","FILTERTYPE")), exist_ok=True)
    
    config['GENERAL']['NCPUS'] = str(int(multiprocessing.cpu_count()-2))
    print("[i]   CPUs available: {}".format(multiprocessing.cpu_count()))
    print("[i]   CPUs used: {}".format(config.get("GENERAL","NCPUS")))
    print("[i]   Observations (without duration limit): {}".format(len(obs_list)))
    stime   = time.time()

    args_list = []
    for ii, obs in enumerate(obs_list):
        args = (ii, config, obs)
        args_list.append(args)
    
    with multiprocessing.Pool(processes=config.getint("GENERAL","NCPUS")) as pool:
        pool.starmap(plot_lidar_tmp_standard, args_list)

    # running_procs = []
    # sema = multiprocessing.Semaphore(config.getint("GENERAL","NCPUS"))
    # for ii, obs in enumerate(obs_list):
    #     for p in running_procs[:]:
    #         if not p.is_alive():
    #             p.join()
    #             running_procs.remove(p)
    #     sema.acquire()
    #     proc = multiprocessing.Process(target=plot_lidar_tmp_standard, args=(ii, config, obs, sema))
    #     running_procs.append(proc)
    #     proc.start()
    # for proc in running_procs:
    #     proc.join()

    etime    = time.time()
    hours    = int((etime - stime) / 3600)
    minutes  = int(((etime - stime) % 3600) / 60)
    seconds  = int(((etime - stime) % 60)) # seconds = round(((etime - stime) % 60), 3)
    time_str = str(hours).zfill(2) + ":" + str(minutes).zfill(2) + ":" + str(seconds).zfill(2)
    print("")
    print(f"[i]  Visualizations completed in {time_str} hours.")


def plot_lidar_tmp_standard(ii,config,obs):
    # (ii,config,obs) = args_list
    
    try:
        file_name = os.path.split(obs)[-1]
        zrange = eval(config.get("GENERAL","ALTITUDE_RANGE"))
        trange = eval(config.get("GENERAL","TRANGE"))
        ds = lidar_processor.open_and_decode_lidar_measurement(obs)
        ds = lidar_processor.process_lidar_measurement(config, ds)

        """Data for plotting"""
        tprime_bwf15, tbg15 = filter.butterworth_filter(ds["temperature"].values, cutoff=1/VERTICAL_CUTOFF, fs=1/ds.vres, order=5, mode='both')
        tprime_temp     = (ds["temperature"]-ds["temperature"].mean(dim='time')).values

        vars = [ds["temperature"].values, tbg15, tprime_bwf15]
        """Figure"""
        gskw = {'hspace':0.04, 'wspace':0.03, 'width_ratios': [4,2], 'height_ratios': [4.25,1,4.25,1]} #  , 'width_ratios': [5,5]}
        fig, axes = plt.subplots(4,2, figsize=(7,12), sharey=True, gridspec_kw=gskw)
        axes[1,0].axis('off')
        axes[1,1].axis('off')
        axes[3,0].axis('off')
        axes[3,1].axis('off')

        h_fmt      = mdates.DateFormatter('%H')
        hlocator   = mdates.HourLocator(byhour=range(0,24,2))
        filter_str =["Temperature", "","15km BW-highpass"]
        for k in [0,2]:
            ax_lid = axes[k,0]
            ax0    = axes[k,1]
            if k==0:
                cb_range  = eval(config.get("GENERAL", "TRANGE"))
                clev      = np.arange(cb_range[0],cb_range[1],10)
                clev_l    = np.arange(cb_range[0]+10,cb_range[1]-10,20)
                cbar_l    = "temperature / K" 
                cmap      = plt.get_cmap('turbo')
            elif k==2:
                clev = [-32,-16,-8,-4,-2,-1,-0.5,0.5,1,2,4,8,16,32] # 32
                clev_l = [-16,-4,-1,1,4,16]
                cbar_l    = "T' / K" 
                cmap = cmaps.get_wave_cmap()

            norm = BoundaryNorm(boundaries=clev, ncolors=cmap.N, clip=True)
            pcolor0 = ax_lid.pcolormesh(ds.time.values, ds.alt_plot.values, np.matrix.transpose(vars[k]),
                                cmap=cmap, norm=norm)

            ax_lid.set_xlim(ds['date_startp'],ds['date_endp'])
            ax_lid.xaxis.set_major_locator(hlocator)
            ax_lid.xaxis.set_major_formatter(plt.FuncFormatter(timelab_format_func))
            ax_lid.yaxis.set_major_locator(MultipleLocator(10))
            ax_lid.yaxis.set_minor_locator(AutoMinorLocator()) 
            ax_lid.xaxis.set_minor_locator(AutoMinorLocator())
            ax_lid.xaxis.set_label_position('top')
            ax_lid.tick_params(which='both', labelbottom=False,labeltop=True)            
            ax_lid.set_ylabel('altitude / km')

            ypp = 0.965
            ax_lid.text(0.03, ypp, filter_str[k], transform=ax_lid.transAxes, verticalalignment='top', bbox={"boxstyle" : "round", "lw":0.67, "facecolor":"white", "edgecolor":"black"})
            # if k==0:
            #     info_str = ""
            #    ax_lid.text(0.5, ypos, info_str, transform=ax_lid.transAxes, verticalalignment='top', horizontalalignment='center', bbox={"boxstyle" : "round", "lw":0.67, "facecolor":"white", "edgecolor":"black"})
            ax_lid.grid()

            # ---- T-axis ---- #
            lw_thin=0.1
            lw_thick=2
            trange_prof = eval(config.get("GENERAL", "TRANGE_PROF"))
            ax0.set_xlim(trange_prof[0],trange_prof[1])
            ax0.yaxis.set_minor_locator(AutoMinorLocator()) 
            ax0.xaxis.set_minor_locator(AutoMinorLocator())
            ax0.set_ylabel('altitude / km')
            ax0.yaxis.set_label_position("right")
            ax0.xaxis.set_label_position('top')
            ax0.yaxis.tick_right()
            ax0.tick_params(which='both', labelbottom=False, labeltop=True, labelright=True, left=True, top=True, bottom=False)

            if k==2:
                ax1 = ax0.twiny()
                ax1.axvline(x=0,c='grey',lw=lw_thick-1)
                ax1.set_xlim([-49.5,25])
                ax1.xaxis.set_minor_locator(AutoMinorLocator())
                ax1.tick_params(which='both', axis='x', bottom=True, top=False, labeltop=False, labelbottom=True, colors='red')
                ax1.spines['bottom'].set_color('red')
                ax1.xaxis.set_label_position('bottom')

            if k==0:
                ax0.set_xlabel('temperature / K')
                ax0.tick_params(which='both', bottom=True)
            else:
                ax0.tick_params(which='both',labeltop=True,top=True,bottom=False,labelbottom=False)
            if k==2:
                ax1.set_xlabel("T' / K", color='red')
            
            for t in range(0,np.shape(ds['temperature'])[0],4):      
                ax0.plot(ds["temperature"][t],ds['alt_plot'],lw=lw_thin,color='black')
                if k==2:
                    ax1.plot(vars[k][t],ds['alt_plot'],lw=lw_thin,color='red')
            ax0.plot(np.mean(ds["temperature"],axis=0),ds['alt_plot'],lw=lw_thick,color='black')
            if k==2:
                ax1.plot(np.nanmean(vars[k],axis=0),ds['alt_plot'], lw=lw_thick, color='red')
            ax0.grid()

            numb_str = ['a','b','c','d','c','d']
            xpp0 = 0.95
            xpp1 = 0.92
            ax_lid.text(xpp0, ypp, numb_str[2*k], verticalalignment='top', horizontalalignment='right', transform=ax_lid.transAxes, weight='bold', bbox={"boxstyle" : "circle", "lw":0.67, "facecolor":"white", "edgecolor":"black"})
            if k==2:
                ax1.text(xpp1, ypp, numb_str[2*k+1], verticalalignment='top', horizontalalignment='right', transform=ax1.transAxes, weight='bold', bbox={"boxstyle" : "circle", "lw":0.67, "facecolor":"white", "edgecolor":"black"})
            else:
                ax0.text(xpp1, ypp, numb_str[2*k+1], verticalalignment='top', horizontalalignment='right', transform=ax0.transAxes, weight='bold', bbox={"boxstyle" : "circle", "lw":0.67, "facecolor":"white", "edgecolor":"black"})

            # - COLORBAR - #
            cbar = fig.colorbar(pcolor0, ax=axes[k+1,0], location='bottom', ticks=clev_l, fraction=1, shrink=0.9, aspect=25, extend='both') # aspect=30
            cbar.set_label(cbar_l)

        axes[0,0].set_ylim(zrange[0],zrange[1])

        """Formatting"""
        TRES = int(config.get("GENERAL","RESOLUTION").split("Z")[0][2:])
        VRES = int(config.get("GENERAL","RESOLUTION").split("Z")[-1][:-3])
        axes[0,0].text(-0.025, 1.0, "UTC", horizontalalignment='right', verticalalignment='bottom', transform=axes[0,0].transAxes)

        fig.suptitle('          German Aerospace Center (DLR)\n \
        {}, {}\n \
        ------------------------------\n \
        Resolution: {}$\,$km  x  {}$\,$min'.format(config.get("GENERAL","INSTRUMENT"), config.get("GENERAL","STATION_NAME"), VRES, TRES))

        """Save figure"""
        fig_name = file_name[:14] + ds.duration_str + '.png'
        fig.savefig(os.path.join(config.get("OUTPUT","FOLDER"),config.get("GENERAL","FILTERTYPE"),fig_name), facecolor='w', edgecolor='w', format='png', dpi=150, bbox_inches='tight') # orientation='portrait'
        
        print(f"Number of plotted measurements: {ii+1}", end='\r')
    except:
        print(f"Plot failed for measurement: {file_name}")
    # sema.release()

if __name__ == '__main__':
    """Provide ini file as argument and pass it to function"""
    """Try changing working directory for Crontab"""
    try:
        os.chdir(os.path.dirname(sys.argv[0]))
    except:
        print('[i]  Working directory already set!')
    plot_lidar_tmp(sys.argv[1])