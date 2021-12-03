from rpy2.robjects import pandas2ri
import numpy as np
import pandas as pd
import wrfpywind.data_preprocess as pp
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
    data = _xr2pd(data, drop_na=False)

    return data


def get_fmt_df(obs, start_date, end_date, datadir='../data/', type='train'):
    # Open the xarray Dataset contianing wind speed data for the entire domain 
    # note that you must use a `Dataset` object for the `extract_buoy_da` function to work.
    ensds = xr.open_dataset(f"{datadir}ensds_{start_date.strftime('%Y%m%d')}-{end_date.strftime('%d')}.nc")

    # Get data only at the buoy locations
    ensda = pp.extract_buoy_da(ensds, varname='wspd_wrf', locations=['south', 'north'])

    # Combine ensemble data and training or test data into a pd.DataFrame in the correct format
    if type == 'train':
        fmt_df = fmt_training_data(ensda, obs)
    elif type == 'test':
        fmt_df = fmt_test_data(ensda, obs)
    else:
        print(f'{type} is invalid.')
        raise ValueError
    
    return fmt_df


def get_bma_fit(train_data, gamma_bma=None):
    """
    Wrapper function for the R fit_bma function in the gamma_bma module
    """
    # Activate pandas2ri
    pandas2ri.activate()

    if gamma_bma is None:
        # Read the R gamma_bma module into Python
        gamma_bma = _get_r_module('../R/gamma_bma.r', 'gamma_bma')

    # Fit the BMA model 
    fit = gamma_bma.fit_bma(train_data, n_ens_members=5)
    
    return fit


def read_fmt_fit_bma(t_init, obs, n_days=2, sim_len=4, datadir='../data/'):
    """
    Lorem ipsum
    """
    # Convert the initialization time to a Timestamp if it's not given as one
    if type(t_init) != pd.Timestamp:
        t_init = pd.to_datetime(t_init)

    # Find the first training day
    d1_training = t_init - pd.DateOffset(days=n_days)

    # Specify the start dates  
    start_dates = pd.date_range(d1_training, periods=n_days)

    # Specify the end dates by specifying how long these simlulations should last
    end_dates = start_dates + pd.DateOffset(days=sim_len)

    for ii in range(0,len(start_dates)):
        # Read in an format the training data
        train_data_new = get_fmt_df(obs, start_dates[ii], end_dates[ii], datadir=datadir, type='train')

        if ii == 0:
            # Create the train_data DataFrame
            train_data = train_data_new
        else:
            # Concat the new data into the same training DataFrame 
            train_data = pd.concat([train_data, train_data_new], axis=0)

    # Finally remove any data from after the WRF initialization time
    train_data = train_data[train_data['Time'] < t_init]

    # And reset the index
    train_data = train_data.reset_index(drop=True)

    # Fit the BMA parameters
    fit = get_bma_fit(train_data)

    return fit


def get_crps(fit, test_data, n_ens_members=5, gamma_bma=None):
    """
    Wrapper function for the R crps_bma function in the gamma_bma module
    """
    # Activate pandas2ri
    pandas2ri.activate()

    if gamma_bma is None:
        # Read the R gamma_bma module into Python
        gamma_bma = _get_r_module('../R/gamma_bma.r', 'gamma_bma')

    # Calculate the CRPS
    crps = gamma_bma.crps_bma(fit, test_data, n_ens_members=5)

    return crps


def quantile_fx(fit, wrfda_slice, obsda, gamma_bma=None, quantiles=np.arange(0.01, 1, 0.01)):
    """
    Create a quantile forcast using a previously-fit BMA model.  
    """
    if gamma_bma is None:
        # Read the R gamma_bma module into Python
        gamma_bma = _get_r_module('../R/gamma_bma.r', 'gamma_bma')

    # Format the ensemble data for t_init
    data_t = fmt_test_data(wrfda_slice, obsda)

    # Extract the quantiles for t_init
    q = gamma_bma.quant_bma(fit, data_t, n_ens_members=5, quantiles=quantiles)

    # Format the quantiles into a DataArray
    fx = _fxda(q, wrfda_slice)

    return fx


def quantile_fx_multiloc(fit, wrfda, obsda, gamma_bma=None, quantiles=np.arange(0.01, 1, 0.01)):
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
            data_t = fmt_test_data(wrfda_slice, obsda)
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
