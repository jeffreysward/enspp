from rpy2.robjects import pandas2ri
import numpy as np
import pandas as pd
import xarray as xr

from .util import _get_r_module, _attach_obs, _xr2pd, _fxda


def fmt_training_data(wrfda, obsda):
    # Get and format data for only north buoy at 100m
    data_n = _attach_obs(wrfda, obsda, location='north', height=100)
    # Covert the xr.DataArray into a pd.DataFrame & remove NaNs
    data_n = _xr2pd(data_n)

    # Get and format data for only south buoy at 100m
    data_s = _attach_obs(wrfda, obsda, location='south', height=100)
    # Covert the xr.DataArray into a pd.DataFrame & remove NaNs
    data_s = _xr2pd(data_s)

    # Combine the data from the two buoys into the same dataframe 
    data = pd.concat([data_s, data_n], axis=0)

    # Reset the index and dropping (as it will just be the repeating sequence)
    data = data.reset_index(drop=True)

    return data


def fmt_test_data(wrfda, obsda):
    # We need an observation as a placeholder (it won't actually be used), 
    # so we'll use the one from the north buoy
    data = _attach_obs(wrfda, obsda, location='north', height=100)
    # Covert the xr.DataArray into a pd.DataFrame & remove NaNs
    data = _xr2pd(data)

    return data


def get_bma_fit(train_data):
    # Activate pandas2ri
    pandas2ri.activate()

    # Read the R gamma_bma module into Python
    gamma_bma = _get_r_module('../R/gamma_bma.r', 'gamma_bma')

    # Fit the BMA model 
    fit = gamma_bma.fit_bma(train_data, n_ens_members=5)
    
    return fit


def bma_quantile_fx(fit, wrfda, obsda, gamma_bma=None, quantiles=np.arange(0.01, 1, 0.01)):
    """
    Create a quantile forcast using a previously-fit BMA model.  
    """
    if gamma_bma is None:
        # Read the R gamma_bma module into Python
        gamma_bma = _get_r_module('../R/gamma_bma.r', 'gamma_bma')

    # This function is currently quite slow...
    # Loop over the south_north dimension
    for ii in range(0, len(wrfda.XLAT)):
        # Loop over the west_east dimension
        for jj in range(0, len(wrfda.XLONG)):
            # Select data for only one location
            wrfda_slice = wrfda.isel(south_north=ii, west_east=jj)
            data_t = fmt_test_data(wrfda, obsda)
            # Extract the quantiles using the BMA test fit
            q = gamma_bma.quant_bma(fit, data_t, n_ens_members=5, quantiles=quantiles)
            # Format the quantiles into a DataArray
            fx_we_new = _fxda(q, wrfda_slice)
            # Combine the DataArrays over the west_east dimension
            if jj == 0:
                fx_we = fx_we_new
            else:
                fx_we = xr.concat([fx_we, fx_we_new], 'west_east')
        # Combine DataArrays over the south_north dimension
        if ii == 0:
            fx = fx_we
        else:
            fx = xr.concat([fx, fx_we], 'south_north')
        
    return fx
    