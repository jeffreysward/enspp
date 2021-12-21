import pandas as pd
import enspp.util as util
import wrfpywind.data_preprocess as dp

# Path to data
datadir = '/share/mzhang/jas983/wrf_data/met4ene/wrfout/ARW/'

# Specify the start dates  
start_dates = pd.date_range('2019-12-09', periods=23)

# Specify the end dates by specifying how long these simlulations should last
end_dates = start_dates + pd.DateOffset(days=4)

for ii in range(0, len(start_dates)):
    print(start_dates[ii].strftime('%Y-%m-%d'))
    dirs = util._get_ensdirs(start_dates[ii].strftime('%Y-%m-%d'))

    # The file produced after the basic postprocessing is named as 
    wo = f"ow_wrfout_d03_{start_dates[ii].strftime('%Y-%m-%d')}-{end_dates[ii].strftime('%Y-%m-%d')}"

    # Name for the outfile
    output_name = f"../data/ensds_{start_dates[ii].strftime('%Y%m%d')}-{end_dates[ii].strftime('%d')}.nc"

    # Read in data and put wind speed data from the ensemble into a new file.
    wrfens = dp.fmt_wrfens_wspd(wrfout_headdir=datadir, 
                        wrfout_dirs=dirs,
                        wrfout_files=[wo],
                        model_names=[
                                    'Lee 2017',
                                    'Draxl 2014a', 
                                    'Draxl 2014b', 
                                    'Veron 2018', 
                                    'Optis 2021'],
                        heights=[20, 40, 60, 80, 100, 120, 140, 160, 180, 200],
                        locations='all',
                        save_nc=True, 
                        nc_filename=output_name
                        )
