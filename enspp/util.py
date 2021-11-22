from rpy2.robjects.packages import STAP


def get_r_module(path, module_name):
    # Read the file with the R code
    with open(path, 'r') as f:
        string = f.read()

    # Parse the package using STAP
    module = STAP(string, module_name)

    return module


def fmt_data():
    # Get data for only north buoy at 100m and format
    wrfens_n = wrfens.sel(location='north', height=100)
    wrfens_n = wrfens_n.T.to_pandas()
    obs_n = obs.sel(location='north', height=100)
    obs_n = obs_n.to_pandas()