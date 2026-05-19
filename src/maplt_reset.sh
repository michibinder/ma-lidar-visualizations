#!/bin/bash

# conda activate unstable-venv
if [ -d ~/miniforge3 ]; then
  source ~/miniforge3/bin/activate unstable-venv
fi
if [ -d ~/miniconda3 ]; then
  source ~/miniconda3/bin/activate unstable-venv
fi
cd /export/data/maplot/ma-lidar-visualizations/src

#python3 plot_lidar_data.py ../config/coral.ini tmp true
rsync -avh --delete -e 'ssh -p 181' /export/data/maplot/ma-lidar-visualizations/data/coral/tmp/ bind_mc@extern05.pa.op.dlr.de:/var/www/html/ma-lidar-calendar/data/coral/tmp/

#python3 plot_lidar_data.py ../config/coral.ini filt-1D true
rsync -avh --delete -e 'ssh -p 181' /export/data/maplot/ma-lidar-visualizations/data/coral/filt-1D/ bind_mc@extern05.pa.op.dlr.de:/var/www/html/ma-lidar-calendar/data/coral/filt-1D/

#python3 plot_lidar_data.py ../config/coral.ini filt-stacked true
rsync -avh --delete -e 'ssh -p 181' /export/data/maplot/ma-lidar-visualizations/data/coral/filt-stacked/ bind_mc@extern05.pa.op.dlr.de:/var/www/html/ma-lidar-calendar/data/coral/filt-stacked/

#python3 plot_lidar_data.py ../config/telma.ini tmp true
rsync -avh --delete -e 'ssh -p 181' /export/data/maplot/ma-lidar-visualizations/data/telma/tmp/ bind_mc@extern05.pa.op.dlr.de:/var/www/html/ma-lidar-calendar/data/telma/tmp/

#python3 plot_lidar_data.py ../config/telma.ini filt-1D true
rsync -avh --delete -e 'ssh -p 181' /export/data/maplot/ma-lidar-visualizations/data/telma/filt-1D/ bind_mc@extern05.pa.op.dlr.de:/var/www/html/ma-lidar-calendar/data/telma/filt-1D/

#python3 plot_lidar_data.py ../config/telma.ini filt-stacked
rsync -avh --delete -e 'ssh -p 181' /export/data/maplot/ma-lidar-visualizations/data/telma/filt-stacked/ bind_mc@extern05.pa.op.dlr.de:/var/www/html/ma-lidar-calendar/data/telma/filt-stacked/