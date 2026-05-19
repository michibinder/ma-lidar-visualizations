#!/bin/bash

if [ -d ~/miniforge3 ]; then
  source ~/miniforge3/bin/activate unstable-venv
fi
if [ -d ~/miniconda3 ]; then
  source ~/miniconda3/bin/activate unstable-venv
fi
cd /export/data2/maplot/ma-lidar-visualizations/src

# python3 download_era5_region.py ../config/coral.ini

# python3 plot_era5_composition.py ../config/coral.ini era5-tropo
# rsync -avh --ignore-existing -e 'ssh -p 181' /export/data2/maplot/ma-lidar-visualizations/data/coral/era5-tropo/ bind_mc@extern05.pa.op.dlr.de:/var/www/html/ma-lidar-calendar/data/coral/era5-tropo/

# python3 plot_era5_composition.py ../config/coral.ini era5-jet-pvu
rsync -avh --ignore-existing -e 'ssh -p 181' /export/data2/maplot/ma-lidar-visualizations/data/coral/era5-jet-pvu/ bind_mc@extern05.pa.op.dlr.de:/var/www/html/ma-lidar-calendar/data/coral/era5-jet-pvu/

#python3 plot_era5_composition.py ../config/coral.ini era5-jet
# python3 plot_era5_composition.py ../config/coral.ini era5-jet true
# rsync -avh --ignore-existing -e 'ssh -p 181' /export/data2/maplot/ma-lidar-visualizations/data/coral/era5-jet/ bind_mc@extern05.pa.op.dlr.de:/var/www/html/ma-lidar-calendar/data/coral/era5-jet/
# rsync -avh --delete -e 'ssh -p 181' /export/data/maplot/ma-lidar-visualizations/data/coral/era5-jet/ bind_mc@extern05.pa.op.dlr.de:/var/www/html/ma-lidar-calendar/data/coral/era5-jet/