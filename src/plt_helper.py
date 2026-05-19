################################################################################
# Copyright 2023 German Aerospace Center                                       #
################################################################################
# This is free software you can redistribute/modify under the terms of the     #
# GNU Lesser General Public License 3 or later: http://www.gnu.org/licenses    #
################################################################################

import matplotlib.dates as mdates
import time
import os
from datetime import datetime
import numpy as np

import imageio.v2 as imageio
import logging
import warnings
warnings.simplefilter("ignore", RuntimeWarning)
warnings.filterwarnings('ignore', category=UserWarning, module='imageio_ffmpeg')
logging.getLogger('imageio_ffmpeg').setLevel(logging.ERROR)

"""Config"""
pbar_interval = 5 # %

def timelab_format_func(value, tick_number):
    dt = mdates.num2date(value)
    if dt.hour == 0:
        return "{}\n{}".format(dt.strftime("%Y-%b-%d"), dt.strftime("%H"))
    else:
        return dt.strftime("%H")


def major_formatter_lon(x, pos):
    """Using western coordinates"""
    return "%.f°W" % abs(x)
    ##return "%.f°E" % abs(x)


def major_formatter_lat(x, pos):
    return "%.f°S" % abs(x)


def show_progress(progress_counter, lock, stime, total_tasks):
    with lock:
        progress_counter.value += 1
        if total_tasks <= 100/pbar_interval:
            print(f"[p]  Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Number of tasks below progress bar limit.")
        else:
            if (progress_counter.value % (total_tasks // (100/pbar_interval))) == 0 or progress_counter.value == total_tasks or progress_counter.value == 1:
                progress = progress_counter.value / total_tasks
                elapsed = time.time() - stime
                eta = (elapsed / progress) * (1 - progress)

                # Convert elapsed and ETA to hours, minutes, and seconds
                elapsed_hrs, elapsed_rem = divmod(elapsed, 3600)
                elapsed_min, elapsed_sec = divmod(elapsed_rem, 60)
                eta_hrs, eta_rem = divmod(eta, 3600)
                eta_min, eta_sec = divmod(eta_rem, 60)

                # Progress bar
                total_hashtags = int(100/pbar_interval)
                hashtag_str = "#" * int(np.ceil(progress * total_hashtags))
                minus_str = "-" * int((1 - progress) * total_hashtags)

                print(f"[p]  |{hashtag_str}{minus_str}| Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Progress: {progress*100:05.2f}% - Elapsed: {int(elapsed_hrs):02d}:{int(elapsed_min):02d}:{int(elapsed_sec):02d} - ETA: {int(eta_hrs):02d}:{int(eta_min):02d}:{int(eta_sec):02d} (hh:mm:ss)", flush=True)

def add_watermark(fig):
    fig.text(0.25, 0.75, 'German Aerospace Center', style = 'italic', fontsize = 18, color = "grey", alpha=0.15, ha='center', va='center', rotation=30) 
    fig.text(0.75, 0.25, 'German Aerospace Center', style = 'italic', fontsize = 18, color = "grey", alpha=0.15, ha='center', va='center', rotation=30) 
    return fig


def create_animation(png_folder, output_path,fps=4):
    """Create animation (mp4) from pngs"""

    ## pip install imageio[ffmpeg]
    filenames    = sorted(os.listdir(png_folder))
    ## fps          = 4 or 10
    macro_block_size = 16 # Default is 16 for optimal compatibility

    # Increase the probesize to give FFmpeg more data to estimate the rate
    # writer_options = {'ffmpeg_params': ['-probesize', '100M']}  # Increase probesize to 5MB
    writer_options = {'ffmpeg_params': ['-probesize', '5000000', '-analyzeduration', '5000000']}

    with imageio.get_writer(output_path, fps=fps, macro_block_size=macro_block_size, **writer_options) as writer:
        for filename in filenames:
            if filename.endswith(".png"):
                image = imageio.imread(os.path.join(png_folder, filename))
                image = resize_to_macro_block(image, macro_block_size)
                writer.append_data(image)
    # imageio.mimsave(image_folder + "/era5_sequence.gif", images, duration=1/fps, palettesize=256/2)  # loop=0, quantizer="nq", palettesize=256


def resize_to_macro_block(image, macro_block_size):
    """Function to make image dimensions divisible by macro block size"""
    height, width = image.shape[:2]
    new_height = (height + macro_block_size - 1) // macro_block_size * macro_block_size
    new_width = (width + macro_block_size - 1) // macro_block_size * macro_block_size
    if (new_height != height) or (new_width != width):
        image = np.pad(image, ((0, new_height - height), (0, new_width - width), (0, 0)), 'constant')
    return image