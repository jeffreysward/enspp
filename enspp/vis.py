"Functioins for visualization."

import numpy as np
import pandas as pd
import seaborn as sns
import xarray as xr
import matplotlib.pyplot as plt
from matplotlib import cm
import stoc_solar.vis as ssvis

def fan(fx=None, obs=None, p1=None, p2=None, t_issue='01/01/2018', n_days=4, fx_res='10T', title=None, 
        cmap=cm.Greens, percentile_vals=None, fig_w=5, fig_h=5, ylab=True, ylab_txt='Wind Speed (ms$^{-1}$)', 
        show_fig=True, save_fig=False, fig_path='../data/plots/fan_plot.png', **kwargs):
    """
    Create a fan plot of a probabilistic forecast, and overlay the observation.
    Alternatively, create only the fan plot or only plot the observation time series. 
    Finally, by specifing values for `p1` and `p2` you can fill the area between two quantiles. 

    You can also pass in `titlefontsize`, `fontsize`, `min`, and `max` as `kwargs`.

    :param fx: probabilistic forecast.
    :type fx: `xarray.DataArray` or `numpy.ndarray`
    :param obs: observation vector.
    :type obs: `xarray.DataArray` or `numpy.array`
    :param p1: if you want to fill between two quantiles only, this specifies
        the lower bound quantile.
    :type p1: `int`
    :param p2: if you want to fill between two quantiles only, this specifies
        the upper bound quantile.
    :type p2: `int`
    :param t_issue: forecast issue time.
    :type t_issue: `str`
    :param fx_res: forecast resolution (e.g., "H" corresponds to hourly,
        "5T" corresponds to 5-minute).
    :type fx_res: `str`
    :param title: plot title.
    :type title: `str`
    :param cmap: matplotlib colormap.
    :type cmap: `matplotlib.cm`
    :param percentile_vals: if you pass in the foecast as a `numpy.ndarray`, 
        you can manualy specify the forecast percentiles using this variable.
    :type percentile_vals: `list` 
    :param fig_w: figure width.
    :type fig_w: `float`
    :param ylab: option to show the y-axis label (default True shows the label).
    :type ylab: `bool`
    :param show_fig: option to show the figure (default True shows the figure).
    :type show_fig: `bool`
    :param save_fig: option to save the figure (default True saves the figure).
    :type save_fig: `bool`
    :param fig_path: full path to save the figure.
    :type fig_path: `str`
    """
    fig = plt.figure(figsize=(fig_w, fig_h))
    ax = fig.add_subplot(111)
    if title is not None:
        ax.set_title(title, loc='right', fontsize=kwargs.get('titlefontsize', 20))
    ax.xaxis.set_ticks_position('bottom')
    ax.tick_params(axis='x', rotation=45, labelsize=kwargs.get('fontsize', 16))
    ax.yaxis.set_ticks_position('left')
    ax.tick_params(axis='y', labelsize=kwargs.get('fontsize', 16))
    # ax.set_xlabel('Hours since forecast start')
    if ylab:
        ax.set_ylabel(ylab_txt, fontsize=kwargs.get('fontsize', 16))
    else:
        ax.set_ylabel('')

    ax.grid(False)
    # ax.set_facecolor('xkcd:white')

    if type(fx) is np.ndarray:
        # Since we have no date information with the numpy arrays, we simply plot what is passed
        # Check to see if an observation was passed
        if obs is not None:
            try:
                x_obs = [ii + 1 for ii in range(0, len(obs))]
            except TypeError:
                x_obs = 1
            plt.plot(x_obs, obs, color='black')
        if fx is not None:
            # Set alpha values to control the fill color
            if percentile_vals is None:
                percentile_vals = [ii + 1 for ii in range(0, 98)]
            alpha_fill = ssvis.get_alphas(np.array(percentile_vals))
            colors = []
            for n in range(len(alpha_fill)):
                colors.append(cmap(alpha_fill[n]))

            # We assume the second fx dimension is the timestep index
            x = [ii + 1 for ii in range(0, fx.shape[1])]
            if p1 is None:
                for p in percentile_vals[:-1]:
                    y1 = fx[p - 1, :]
                    y2 = fx[p, :]
                    ax.fill_between(x, y1, y2,
                                    # facecolor='xkcd:tomato red', edgecolor='none',
                                    # alpha=alpha_fill[int(p - 1)],
                                    facecolor=colors[int(p - 1)], edgecolor=colors[int(p - 1)],
                                    linewidth=1,
                                    )
            else:
                y1 = fx[p1, :]
                y2 = fx[p2, :]
                ax.fill_between(x, y1, y2,
                                facecolor=colors[int(p1)], edgecolor=colors[int(p1)],
                                linewidth=1,
                                )


            # Get the highest value
            highest_val = np.max(fx)
        else:
            highest_val = np.max(obs)

    elif type(fx) is xr.DataArray:
        # Check to see if an observation was passed
        if obs is not None:
            t_issue = pd.to_datetime(t_issue)
            # Subtract one timestep from the fx_horizon
            obs_slice = obs.sel(Time=slice(t_issue, t_issue + pd.Timedelta(days=n_days) - pd.Timedelta(minutes=10)))
            x_obs = obs_slice.Time
            plt.plot(x_obs, obs_slice.values, color='black')

        # Check to see if a forecast was passed
        if fx is not None:
            # Set alpha values to control the fill color
            alpha_fill = ssvis.get_alphas(fx.Percentile.values)
            colors = []
            for n in range(len(alpha_fill)):
                colors.append(cmap(alpha_fill[n]))

            # Create a datetime array so that we can plot observations at shorter time scales
            x = pd.date_range(t_issue, freq=fx_res, periods=len(fx.Step_index))
            if p1 is None:
                for p in fx.Percentile[:-1].values:
                    y1 = fx.sel(Start_time=t_issue, Percentile=p)
                    y2 = fx.sel(Start_time=t_issue, Percentile=(p + 1))
                    ax.fill_between(x, y1, y2,
                                    # facecolor='xkcd:tomato red', edgecolor='none',
                                    # alpha=alpha_fill[int(p - 1)],
                                    facecolor=colors[int(p - 1)], edgecolor=colors[int(p - 1)],
                                    linewidth=1,
                                    )
            else:
                y1 = fx.sel(Start_time=t_issue, Percentile=p1)
                y2 = fx.sel(Start_time=t_issue, Percentile=p2)
                ax.fill_between(x, y1, y2,
                                facecolor=colors[int(p1)], edgecolor=colors[int(p1)],
                                linewidth=1,
                                )
                
            # Get the highest power
            highest_val = fx.sel(Start_time=slice(t_issue)).max().values
        else:
            highest_val = obs_slice.max().values

    # Draw a line at zero
    ax.axhline(y=0, color='black', linestyle='-', linewidth=0.75)

    # Set the domain 
    try:
        plt.xticks(ha='right')
        ax.set_xlim([x[1], x[-1]])
    except NameError:
        ax.set_xlim([x_obs[0], x_obs[-1]])
    # Set the range
    maximum = kwargs.get('max', highest_val * 1.05)
    minimum = kwargs.get('min', 0)
    ax.set_ylim([minimum, maximum])

    # Save the plot
    if save_fig:
        plt.savefig(fig_path, dpi=300, transparent=True, bbox_inches='tight')

    # Show the figure
    if show_fig:
        plt.show()
    else:
        plt.close()
