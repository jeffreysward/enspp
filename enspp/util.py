from rpy2.robjects.packages import STAP
import numpy as np
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


def _xr2pd(da):
    df = da.T.to_pandas().dropna().reset_index()
    return df


def _fxda(quantiles, wrfda_loc):    
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
            XLONG=wrfda_loc.XLONG.values,
            XLAT=wrfda_loc.XLAT.values
        ),
        attrs=dict(
            description="Wind Speed 100m",
            units="m s-1",
        ),
    )
    return fx