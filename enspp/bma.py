from rpy2.robjects import pandas2ri
from .util import _get_r_module, _wrfobs_xr2pd


def fmt_training_data(wrfda, obsda):
    # Get and format data for only south buoy at 100m
    data_n = _wrfobs_xr2pd(wrfda, obsda, location='north', height=100)

    # Get and format data for only south buoy at 100m
    data_s = _wrfobs_xr2pd(wrfda, obsda, location='south', height=100)

    # Combine the data from the two buoys into the same dataframe 
    data = pd.concat([data_s, data_n], axis=0)

    # Reset the index again, this time dropping it
    data = data.reset_index(drop=True)



def get_bma_fit(train_data):
    # Activate pandas2ri
    pandas2ri.activate()

    # Read the R gamma_bma module into Python
    gamma_bma = get_r_module('../R/gamma_bma.r', 'gamma_bma')

    # Fit the BMA model 
    fit = gamma_bma.fit_bma(train_data, n_ens_members=5)
    
    return fit