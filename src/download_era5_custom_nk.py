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
import cdsapi
#from ecmwfapi import ECMWFDataServer

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
DATE = "2018-06-16/to/2018-06-19"
# coral only
AREA = '-53/-68/-54/-67' # # North, West, South, East. Default: global

## KEYWORDS:
## https://confluence.ecmwf.int/display/UDOC/Keywords+in+MARS+and+Dissemination+requests

def download_era5():
    """Download data from ECMWF Tape archive"""
    # c = cdsapi.Client(quiet=True)
    c = cdsapi.Client()
    # server = ECMWFDataServer()

    datadir = "/athome/kaif_na/tana/Southwave/era5/"
    file_ml = os.path.join(datadir, "era5_ml.nc")

    print("[i] Retrieving full model level data...")
    c.retrieve('reanalysis-era5-complete', {
        'class'   : 'ea',
        'date'    : DATE,
        'expver'  : '1',
        'levelist': '1/to/137',
        'levtype' : 'ml',
        'param'   : '129/130/131/132/133/152',
        'stream'  : 'oper',
        'time'    : '00:00:00/01:00:00/02:00:00/03:00:00/04:00:00/05:00:00/06:00:00/07:00:00/08:00:00/09:00:00/10:00:00/11:00:00/12:00:00/13:00:00/14:00:00/15:00:00/16:00:00/17:00:00/18:00:00/19:00:00/20:00:00/21:00:00/22:00:00/23:00:00',
        #'time'    : '00:00:00/to/23:00:00',
        'type'    : 'an',
        'area'    : AREA,
        'grid'    : '0.25/0.25',               # Latitude/longitude. Default: spherical harmonics or reduced Gaussian grid
        'format'  : 'netcdf', # 'short'??
        'truncation' : 'av' # 'av', '639', '21' vs 'resol':
    }, file_ml)
    
    file_ml_coeff = 'input/era5-ml-coeff.csv'
    print("[i] Interpolating model levels...")
    era5_processor.prepare_interpolated_ml_ds(file_ml,file_ml_T21,file_ml_coeff,file_ml_int)             

if __name__ == '__main__':
    """Try changing working directory for Crontab"""
    try:
        os.chdir(os.path.dirname(sys.argv[0]))
    except:
        print('[i]   Working directory already set!')
    download_era5()
