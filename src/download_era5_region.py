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
import psutil
import configparser
import datetime
import cdsapi
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

import filter, cmaps, era5_processor, lidar_processor

"""Config"""
duration_threshold = 6
reference_hour     = 15 # 15 for CORAL


def download_era5_region(CONFIG_FILE):
    """Visualize lidar measurements (time-height diagrams + absolute temperature measurements)"""
    print(datetime.datetime.now())

    """Settings"""
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE)

    if config.get("INPUT","OBS_FILE") == "NONE":
        obs_list = sorted(glob.glob(os.path.join(config.get("INPUT","OBS_FOLDER") , config.get("GENERAL","RESOLUTION"))))
    else:
        obs_list = os.path.join(config.get("INPUT","OBS_FOLDER"), config.get("INPUT","OBS_FILE"))
    
    # config['GENERAL']['NCPUS'] = str(int(multiprocessing.cpu_count()-2))
    config['GENERAL']['NCPUS'] = "4"
    print("[i]   CPUs available: {}".format(multiprocessing.cpu_count()))
    print("[i]   CPUs used: {}".format(config.get("GENERAL","NCPUS")))
    print("[i]   Observations (without duration limit): {}".format(len(obs_list)))

    """Define ERA5 data folder"""
    config["OUTPUT"]["ERA5-FOLDER"] = os.path.join(config.get("OUTPUT","FOLDER"),"era5-region")
    os.makedirs(config.get("OUTPUT","ERA5-FOLDER"), exist_ok=True)

    running_procs = []
    sema = multiprocessing.Semaphore(config.getint("GENERAL","NCPUS"))
    for ii, obs in enumerate(obs_list):
        for p in running_procs[:]:
            if not p.is_alive():
                p.join()
                running_procs.remove(p)
        sema.acquire()
        proc = multiprocessing.Process(target=download_and_interpolate_era5_data, args=(ii, config, obs, sema))
        running_procs.append(proc)
        proc.start()
    for proc in running_procs:
        proc.join()


def download_and_interpolate_era5_data(ii,config,obs,sema):
    file_name = os.path.split(obs)[-1]
    ds = lidar_processor.open_and_decode_lidar_measurement(obs)
    if ds is None:
        sema.release()
        return

    """Define timeframe (decide which days to download ERA5 data)"""
    ## For TELMA its probably ok to get date of start and next date (TIMEFRAME_NIGHT == 'NONE')
    start_date = ds.start_time_utc
    if config.get("GENERAL","TIMEFRAME_NIGHT") != "NONE":
        if (ds.start_time_utc.hour < reference_hour):
            """Get previous day"""
            start_date = ds.start_time_utc - datetime.timedelta(hours=24)
                
    if ds.duration > datetime.timedelta(hours=duration_threshold):
        """Check if file already exists"""
        nc_file_name = file_name[:13]
        file_ml     = os.path.join(config.get("OUTPUT","ERA5-FOLDER"), nc_file_name + '-ml.nc')
        file_ml_T21 = os.path.join(config.get("OUTPUT","ERA5-FOLDER"), nc_file_name + '-ml-T21.nc')
        file_ml_int = os.path.join(config.get("OUTPUT","ERA5-FOLDER"), nc_file_name + '-ml-int.nc')
        file_pl     = os.path.join(config.get("OUTPUT","ERA5-FOLDER"), nc_file_name + '-pl.nc')
        file_pvu    = os.path.join(config.get("OUTPUT","ERA5-FOLDER"), nc_file_name + '-pvu.nc')

        """Download ERA5 data"""
        if config.get("GENERAL","INSTRUMENT") == "TELMA":
            DATE = start_date.strftime("%Y-%m-%d")
        else:
            DATE = start_date.strftime("%Y-%m-%d") + "/to/" + (start_date + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
        ## AREA = '-25/-120/-85/-30',          
        AREA = config.get("ERA5","AREA")
        c = cdsapi.Client(quiet=True)

        if not os.path.exists(file_ml_int):
            if not os.path.exists(file_ml):
                print(f"[i][{ii}]   Retrieving full model data...")
                # - Request model level data - #
                c.retrieve('reanalysis-era5-complete', {
                    'class'   : 'ea',
                    'date'    : DATE,
                    'expver'  : '1',
                    'levelist': '1/to/137',
                    'levtype' : 'ml',
                    'param'   : '129/130/131/132/133/152',
                    'stream'  : 'oper',
                    'time'    : '00:00:00/01:00:00/02:00:00/03:00:00/04:00:00/05:00:00/06:00:00/07:00:00/08:00:00/09:00:00/10:00:00/11:00:00/12:00:00/13:00:00/14:00:00/15:00:00/16:00:00/17:00:00/18:00:00/19:00:00/20:00:00/21:00:00/22:00:00/23:00:00',
                    # 'time'    : '00:00:00/to/23:00:00',
                    'type'    : 'an',
                    'area'    : AREA,
                    'grid'    : '0.25/0.25',               # Latitude/longitude. Default: spherical harmonics or reduced Gaussian grid
                    'format'  : 'netcdf', # 'short'??
                    'resol'   : 'av', # 'av', '639', '21'
                }, file_ml)

            if not os.path.exists(file_ml_T21):
                print(f"[i][{ii}]   Retrieving T21 model data...")
                # - Request model level data - #
                c.retrieve('reanalysis-era5-complete', {
                    'class'   : 'ea',
                    'date'    : DATE,
                    'expver'  : '1',
                    'levelist': '1/to/137',
                    'levtype' : 'ml',
                    'param'   : '129/130/131/132/133/152',
                    'stream'  : 'oper',
                    'time'    : '00:00:00/01:00:00/02:00:00/03:00:00/04:00:00/05:00:00/06:00:00/07:00:00/08:00:00/09:00:00/10:00:00/11:00:00/12:00:00/13:00:00/14:00:00/15:00:00/16:00:00/17:00:00/18:00:00/19:00:00/20:00:00/21:00:00/22:00:00/23:00:00',
                    # 'time'    : '00:00:00/to/23:00:00',
                    'type'    : 'an',
                    'area'    : AREA,
                    'grid'    : '0.25/0.25',               # Latitude/longitude. Default: spherical harmonics or reduced Gaussian grid
                    'format'  : 'netcdf', # 'short'??
                    'resol'   : '21', # 'av', '639', '21'
                }, file_ml_T21)

            print(f"[i][{ii}]   Interpolating model levels...")
            era5_processor.prepare_interpolated_ml_ds(file_ml,file_ml_T21,file_ml_int)
            os.remove(file_ml)
            os.remove(file_ml_T21)

        if (not os.path.exists(file_pl)):
            print(f"[i][{ii}]   Retrieving pressure level data...")
            c.retrieve('reanalysis-era5-complete', {
                'class'   : 'ea',
                'date'    : DATE,
                'expver'  : '1',
                'levelist': '1/2/3/5/7/10/20/30/50/70/100/125/150/175/200/225/250/300/350/400/450/500/550/600/650/700/750/775/800/825/850/875/900/925/950/975/1000',
                'levtype' : 'pl',
                'param'   : '60.128/129.128/131/132', # '60.128/129.128/130.128/131/132/133.128/138.128/155.128/157.128'
                'stream'  : 'oper',
                'time'    : '00:00:00/01:00:00/02:00:00/03:00:00/04:00:00/05:00:00/06:00:00/07:00:00/08:00:00/09:00:00/10:00:00/11:00:00/12:00:00/13:00:00/14:00:00/15:00:00/16:00:00/17:00:00/18:00:00/19:00:00/20:00:00/21:00:00/22:00:00/23:00:00',
                # 'time'    : '00:00:00/to/23:00:00',
                'type'    : 'an',
                'area'    : AREA,          # North, West, South, East. Default: global
                'grid'    : '0.25/0.25',               # Latitude/longitude. Default: spherical harmonics or reduced Gaussian grid
                'format'  : 'netcdf',                # Output needs to be regular lat-lon, so only works in combination with 'grid'!
            }, file_pl)

        if (not os.path.exists(file_pvu)):
            print(f"[i][{ii}]   Retrieving 2PVU level data...")
            c.retrieve('reanalysis-era5-complete', {
                'class'   : 'ea',
                'date'    : DATE,
                'expver'  : '1',
                'levelist': '2000',
                'levtype' : 'pv',
                'param'   : '3.128/54.128/129.128/131.128/132.128/133.128',
                'stream'  : 'oper',
                'time'    : '00:00:00/01:00:00/02:00:00/03:00:00/04:00:00/05:00:00/06:00:00/07:00:00/08:00:00/09:00:00/10:00:00/11:00:00/12:00:00/13:00:00/14:00:00/15:00:00/16:00:00/17:00:00/18:00:00/19:00:00/20:00:00/21:00:00/22:00:00/23:00:00',
                'type'    : 'an',
                'area'    : AREA,          # North, West, South, East. Default: global
                'grid'    : '0.25/0.25',               # Latitude/longitude. Default: spherical harmonics or reduced Gaussian grid
                'format'  : 'netcdf',
            }, file_pvu)

        print(f"[i][{ii}]   ERA5 data prepared for observation: {obs}")
    else:
        print(f"[i][{ii}]   Duration below limit for observation: {obs}")
    sema.release()

if __name__ == '__main__':
    """provide ini file as argument and pass it to function"""
    """Try changing working directory for Crontab"""
    try:
        os.chdir(os.path.dirname(sys.argv[0]))
    except:
        print('[i]  Working directory already set!')
    download_era5_region(sys.argv[1])