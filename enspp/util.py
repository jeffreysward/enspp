from rpy2.robjects.packages import STAP
import numpy as np
import pandas as pd
import xarray as xr


def _get_r_module(path, module_name):
    # Read the file with the R code
    with open(path, 'r') as f:
        string = f.read()

    # Parse the package using STAP
    module = STAP(string, module_name)

    return module


def _attach_obs(wrfda, obsda, location='north', height=100):
    # Get data for only north buoy at 100m and format
    if 'location' in wrfda.dims:
        wrfda_loc = wrfda.sel(location=location, height=height)
    else:
        wrfda_loc = wrfda
    obsda_loc = obsda.sel(Time=slice(wrfda.Time[0], wrfda.Time[-1]), location=location, height=height)

    # Put the observations and the ensemble forecast into the same DataFrame (north buoy)
    data_loc = xr.concat([obsda_loc, wrfda_loc], 'model')

    return data_loc


def _xr2pd(da, drop_na=True):
    if drop_na:
        df = da.T.to_pandas().dropna().reset_index()
    else:
        df = da.T.to_pandas().reset_index()
    return df


def _fxda(quantiles, wrfda_loc):
    try:
        lon_vals = wrfda_loc.XLONG.values
    except:
        lon_vals = 999
    try:
        lat_vals = wrfda_loc.XLAT.values
    except:
        lat_vals = 999

    # Format the forecast and obs variables into xarray DataSets. 
    fx = xr.DataArray(
        data=[quantiles],
        dims=[
            "Start_time", 
            "Step_index", 
            "Percentile"
            ],
        coords=dict(
            Start_time=wrfda_loc.Time[0:1].values,
            Step_index=np.arange(0, len(wrfda_loc.Time), 1),
            Percentile=np.arange(1, quantiles.shape[1] + 1, 1),
            XLONG=lon_vals,
            XLAT=lat_vals
        ),
        attrs=dict(
            description="Wind Speed 100m",
            units="m s-1",
        ),
    )
    return fx


def _fxda_grid(quantiles, wspdgrid_unstacked, wrfda):
    # Use the multi-index from the unstacked version of the gridded DataFrame to create the new DataFrame
    fx = pd.DataFrame(quantiles, index=wspdgrid_unstacked.index, columns=np.array([10, 50, 90]))
    # Stack the percentiles into the multi-index
    fx = fx.stack(dropna=False)
    # Convert the pd.DataFrame to a xr.DataArray
    fx = fx.to_xarray()
    # Rename the dimension that pandas created when stacking the percentiles
    fx = fx.rename({'level_3':'Percentile'})
    # Add the latitude and longitude information back to the DataArray
    fx = fx.assign_coords(XLONG=(['south_north', 'west_east'], wrfda.XLONG.values))
    fx = fx.assign_coords(XLAT=(['south_north', 'west_east'], wrfda.XLAT.values))

    return fx


def _get_ensdirs(date_string):
    """
    Get directory names for all ensemble members.
    """
    ensdir1 = f'{date_string}_28mp4lw4sw2lsm5pbl1cu/'  # Lee 2017
    ensdir2 = f'{date_string}_8mp1lw1sw2lsm1pbl1cu/'  # Draxl 2014a
    ensdir3 = f'{date_string}_8mp1lw1sw2lsm2pbl1cu/'  # Draxl 2014b
    ensdir4 = f'{date_string}_8mp1lw1sw2lsm2pbl3cu/'  # Vernon 2018
    ensdir5 = f'{date_string}_8mp4lw2sw2lsm5pbl3cu/'  # Optis 2021

    return [ensdir1, ensdir2, ensdir3, ensdir4, ensdir5]
    # return [ensdir2, ensdir4, ensdir5]
