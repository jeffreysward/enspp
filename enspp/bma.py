from rpy2.robjects import pandas2ri
from .util import get_r_module


def fmt_training_data():
    # Get data for only north buoy at 100m and format
    wrfens_n = wrfens.sel(location='north', height=100)
    wrfens_n = wrfens_n.T.to_pandas()
    obs_n = obs.sel(location='north', height=100)
    obs_n = obs_n.to_pandas()

    # Get data for only south buoy at 100m and format
    wrfens_s = wrfens.sel(location='south', height=100)
    wrfens_s = wrfens_s.T.to_pandas()
    obs_s = obs.sel(location='south', height=100)
    obs_s = obs_s.to_pandas()

    # Put the observations and the ensemble forecast into the same DataFrame (north buoy)
    data_n = pd.concat([obs_n['2020-02-05':'2020-02-11'], wrfens_n], axis=1)
    data_n = data_n.rename(columns={0: 'Obs'})
    data_n = data_n.dropna().reset_index()

    # Put the observations and the ensemble forecast into the same DataFrame (south buoy)
    data_s = pd.concat([obs_s['2020-02-05':'2020-02-11'], wrfens_s], axis=1)
    data_s = data_s.rename(columns={0: 'Obs'})
    data_s = data_s.dropna().reset_index()

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