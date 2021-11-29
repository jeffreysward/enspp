import pandas as pd
import enspp.util as util
import wrfpywind.data_preprocess as dp

# Path to data
datadir = '/share/mzhang/jas983/wrf_data/met4ene/wrfout/ARW/'

# Specify the forecast initialization time
t_init = '2019-12-10'
t_init = pd.to_datetime(t_init)

# Start by formatting the directory
d = t_init - pd.Timedelta(days=1)
d_end = d + pd.Timedelta(days=4)
dirs = util._get_ensdirs(d.strftime('%Y-%m-%d'))

# The file produced after the basic postprocessing is named as 
wo = f"ow_wrfout_d03_{d.strftime('%Y-%m-%d')}-{d_end.strftime('%Y-%m-%d')}"

# Name for the outfile
output_name = f"../data/ensds_{d.strftime('%Y%m%d')}-{d_end.strftime('%d')}.nc"

# Read in data and put wind speed data from the ensemble into a new file.
wrfens = dp.fmt_wrfens_wspd(wrfout_headdir=datadir, 
                    wrfout_dirs=dirs,
                    wrfout_files=[wo],
                    model_names=[
                                #  'Lee 2017',
                                 'Draxl 2014a', 
                                #  'Draxl 2014b', 
                                 'Veron 2018', 
                                 'Optis 2021'],
                    heights=[20, 40, 60, 80, 100, 120, 140, 160, 180, 200],
                    locations='all',
                    save_nc=True, 
                    nc_filename=output_name
                    )
