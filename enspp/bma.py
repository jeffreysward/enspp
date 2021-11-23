from rpy2.robjects import pandas2ri
import pandas as pd

from .util import _get_r_module, _attach_obs, _xr2pd


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