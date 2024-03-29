################################################################################
# Copyright 2023 German Aerospace Center                                       #
################################################################################
# This is free software you can redistribute/modify under the terms of the     #
# GNU Lesser General Public License 3 or later: http://www.gnu.org/licenses    #
################################################################################

import os
import sys
import glob
import shutil
import configparser
import datetime

import numpy as np
import xarray as xr

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.colors import BoundaryNorm
from matplotlib.ticker import AutoMinorLocator, MultipleLocator
from mpl_toolkits.axes_grid1 import make_axes_locatable

import warnings
warnings.simplefilter("ignore", RuntimeWarning)

import filter, cmaps

plt.style.use('latex_default.mplstyle')


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
    
    os.makedirs(os.path.join(config.get("OUTPUT","FOLDER"),'tmp'), exist_ok=True)
    zrange = eval(config.get("GENERAL","ALTITUDE_RANGE"))
    trange = eval(config.get("GENERAL","TRANGE"))
    
    ii = 0
    for obs in obs_list:
        if (ii % 50) == 0:
            print("Plotting measurement: {}".format(ii))

        file_name = os.path.split(obs)[-1]
        ds = xr.open_dataset(obs, decode_times=False)

        """Decode time with time offset"""
        # - Change from milliseconds to seconds - #
        # ds.assign_coords({'time':ds.time.values / 1000})
        ds.coords['time'] = ds.time.values / 1000
        ds.integration_start_time.values = ds.integration_start_time.values / 1000
        ds.integration_end_time.values = ds.integration_end_time.values / 1000
        
        # - Set reference date - #
        ### Reference date is first reference
        ### 'Time offset' is 'seconds' after reference date
        ### Time is 'seconds' after time offset
        unit_str = ds.time_offset.attrs['units']
        ds.attrs['reference_date'] = unit_str[14:-6]
        
        # - Set reference date in units attribute - #
        time_reference = datetime.datetime.strptime(ds.reference_date, '%Y-%m-%d %H:%M:%S.%f')
        time_offset = datetime.timedelta(seconds=float(ds.time_offset.values[0]))
        new_time_reference = time_reference + time_offset
        time_reference_str = datetime.datetime.strftime(new_time_reference, '%Y-%m-%d %H:%M:%S')

        ds.time.attrs['units'] = 'seconds since ' + time_reference_str
        ds.integration_start_time.attrs['units'] = 'seconds since ' + time_reference_str
        ds.integration_end_time.attrs['units'] = 'seconds since ' + time_reference_str
        ds.time.attrs['resolution'] = "15"

        ds = xr.decode_cf(ds, decode_coords = True, decode_times = True) 

        """Define timeframe"""
        # - Date for plotting should always refer to beginning of the plot (04:00 UTC) - #
        start_date = datetime.datetime.utcfromtimestamp(ds.time.values[0].astype('O')/1e9)
        duration = datetime.datetime.utcfromtimestamp(ds.integration_end_time.values[-1].astype('O')/1e9) -  datetime.datetime.utcfromtimestamp(ds.integration_start_time.values[0].astype('O')/1e9)# for calendar
        if config.get("GENERAL","TIMEFRAME_NIGHT") != "NONE":
            timeframe = eval(config.get("GENERAL", "TIMEFRAME_NIGHT"))
            if timeframe[1] < timeframe[0]:
                fixed_intervall = timeframe[1] + 24 - timeframe[0]
            else: 
                fixed_intervall = timeframe[1] - timeframe[0]
                
            fixed_start_date = datetime.datetime(start_date.year, start_date.month, start_date.day, timeframe[0], 0,0)
            reference_hour   = 15
            if (start_date.hour > reference_hour) and (fixed_start_date.hour > reference_hour):
                ds['date_startp'] = fixed_start_date
                ds['date_endp']   = fixed_start_date + datetime.timedelta(hours=fixed_intervall)
            elif (start_date.hour > reference_hour) and (fixed_start_date.hour < reference_hour): # prob in range of 0 to 10
                ds['date_startp'] = fixed_start_date + datetime.timedelta(hours=24)
                ds['date_endp']   = fixed_start_date + datetime.timedelta(hours=24+fixed_intervall)
            elif (start_date.hour < reference_hour) and (fixed_start_date.hour > reference_hour):
                ds['date_startp'] = fixed_start_date - datetime.timedelta(hours=24)
                ds['date_endp']   = fixed_start_date - datetime.timedelta(hours=24-fixed_intervall)
            else: # (start_date.hour < 15) and (fixed_start_date.hour < 15):
                ds['date_startp'] = fixed_start_date
                ds['date_endp']   = fixed_start_date + datetime.timedelta(hours=fixed_intervall)
                
            ds['fixed_timeframe'] = 1
        else:
            timeframe = config.getint("GENERAL", "TIMEFRAME")
            start_date = datetime.datetime.utcfromtimestamp(ds.time.values[0].astype('O')/1e9)
            ds['date_startp'] = start_date
            ds['date_endp']   = start_date + datetime.timedelta(hours=timeframe)
            ds['fixed_timeframe'] = 1
            
        """ Temperature missing values (Change 0 to NaN)"""
        ds.temperature.values = np.where(ds.temperature == 0, np.nan, ds.temperature)
        ds.temperature_err.values = np.where(ds.temperature_err == 0, np.nan, ds.temperature_err)

        """Data for plotting"""
        ds['alt_plot'] = (ds.altitude + ds.altitude_offset + ds.station_height) / 1000 #km
        vert_res       = (ds['alt_plot'][1]-ds['alt_plot'][0]).values[0]
        tprime_bwf20, tbg20 = filter.butterworth_filter(ds["temperature"].values, highcut=1/20, fs=1/vert_res, order=5, mode='low')
        tprime_bwf15, tbg15 = filter.butterworth_filter(ds["temperature"].values, highcut=1/15, fs=1/vert_res, order=5, mode='low')
        tprime_bwf15, _ = filter.butterworth_filter(ds["temperature"].values, highcut=1/15, fs=1/vert_res, order=5, mode='high')
        #ds['tprime_bwf20'] = butterworthf(ds, highcut=1/20, fs=1/0.1, order=5, single_column_filter=True)['tmp_pert']
        #tprime_bwf15, tbg15 = butterworthf(ds, highcut=1/15, fs=1/0.1, order=5, single_column_filter=True)['tmp_pert']
        #meanT = ds["temperature"].mean(dim='time')
        tprime_temp  = (ds["temperature"]-ds["temperature"].mean(dim='time')).values

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
        # if ds.fixed_timeframe.values:
        #     date = datetime.datetime.utcfromtimestamp(ds.date_endp.values.astype('O')/1e9)
        # else: 
        #     date = datetime.datetime.utcfromtimestamp(ds.time.values[-1].astype('O')/1e9)
        
        # - Use date of first measurement - #
        date = datetime.datetime.utcfromtimestamp(ds.time.values[0].astype('O')/1e9)
        axes[0,0].text(-0.015, 1.0, "UTC", horizontalalignment='right', verticalalignment='bottom', transform=axes[0,0].transAxes)


        if ds.instrument_name == "":
            ds.instrument_name = "LIDAR"
        fig.suptitle('          German Aerospace Center (DLR)\n \
        {}, {}\n \
        ------------------------------\n \
        Resolution: {}$\,$km  x  {}$\,$min'.format(ds.instrument_name, ds.station_name, ds.altitude.resolution / 1000, ds.time.resolution))

        """Save figure"""
        hours = duration.seconds // 3600
        minutes = (duration.seconds % 3600) // 60
        duration_str = ''
        if hours <= 9:
            duration_str = duration_str + '0' + str(int(hours))
        else:
            duration_str = duration_str + str(int(hours))
        duration_str = duration_str + 'h'
        if minutes <= 9:
            duration_str = duration_str + '0' + str(int(minutes))
        else:
            duration_str = duration_str + str(int(minutes))
        duration_str = duration_str + 'min'
        fig_name = file_name[:14] + duration_str + '.png'
        fig.savefig(os.path.join(config.get("OUTPUT","FOLDER"),'tmp',fig_name), facecolor='w', edgecolor='w', format='png', dpi=150, bbox_inches='tight') # orientation='portrait'

        ii += 1 
    return


if __name__ == '__main__':
    """Provide ini file as argument and pass it to function"""
    """Try changing working directory for Crontab"""
    try:
        os.chdir(os.path.dirname(sys.argv[0]))
    except:
        print('[i]  Working directory already set!')
    plot_lidar_tmp(sys.argv[1])