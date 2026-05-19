#!/bin/bash

# nk: this is for the active lidars. data from past campaigns can be copied by hand with these commands to the server

ins=$1
if [[ $ins != 'coral' ]] && [[ $ins != 'telma' ]] && [[ $ins != 'OP' ]]; then
	echo "wrong or missing argument; choose coral or telma or OP"
	exit
fi

src_path=/export/data2/maplot/ma-lidar-visualizations/data

server=natalie@extern05.pa.op.dlr.de
targ_path=/var/www/html/ma-lidar-calendar/data

if [ -d /athome/f_maplt/miniforge3 ]; then
  source ~/miniforge3/bin/activate unstable-venv
fi
if [ -d /athome/f_maplt/miniconda3 ]; then
  source /athome/f_maplt/miniconda3/bin/activate unstable-venv
fi
cd /export/data2/maplot/ma-lidar-visualizations/src

# nk 251020 removed --ignore-existing because it didn't update
python3 plot_lidar_data.py ../config/${ins}.ini tmp
rsync -avh --delete -O -e 'ssh -p 181' ${src_path}/${ins}/tmp/ ${server}:${targ_path}/${ins}/tmp/
# -O is for --omit-dir-times

python3 plot_lidar_data.py ../config/${ins}.ini filt-1D
rsync -avh --delete -O -e 'ssh -p 181' ${src_path}/${ins}/filt-1D/ ${server}:${targ_path}/${ins}/filt-1D/

python3 plot_lidar_data.py ../config/${ins}.ini filt-stacked
rsync -avh --delete -O -e 'ssh -p 181' ${src_path}/${ins}/filt-stacked/ ${server}:${targ_path}/${ins}/filt-stacked/

python3 plot_lidar_data.py ../config/${ins}.ini aerosol
rsync -avh --delete -O -e 'ssh -p 181' ${src_path}/${ins}/aerosol/ ${server}:${targ_path}/${ins}/aerosols/

python3 plot_lidar_data.py ../config/${ins}.ini nlc
rsync -avh --delete -O -e 'ssh -p 181' ${src_path}/${ins}/nlc/ ${server}:${targ_path}/${ins}/nlc/


# latest long file for display on index.html
# 7 hours gives no results in summer
latest=`ls -1 ${src_path}/${ins}/tmp/*.png | tail -n 50 | awk '{n=split($1,a,"/"); if(int(substr(a[n],15,2)) > 3){ print a[n];}}' | tail -n 1`
rsync -avh --delete -O -e 'ssh -p 181' ${src_path}/${ins}/tmp/$latest ${server}:${targ_path}/${ins}/latest.png

