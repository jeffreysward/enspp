import numpy as np

def post_process_2018(reforecast_data_all, obs_all, pp_days):

        days = 25 # last 25 days for the given time (e.g., 12z last 25 days)
        weights_all = np.full((11, pp_days), np.nan)

        x0 = np.asarray([15.0, 0.10, 0.15, 0.23, 0.30, 0.10, 0.15, 0.23, 
                0.30, 0.10, 0.15, 0.23, 6.5, 0.3])

        CRPS_pp_all = np.full((pp_days), np.nan)
        CRPS_reg_all = np.full((pp_days), np.nan)
        i_pp_all = np.full((len(obs_all)), np.nan)
        i_reg_all = np.full((len(obs_all)), np.nan)
        pred_mean_all = np.full((pp_days), np.nan)
        me_all = np.full((pp_days), np.nan)
        stan_dev_all = np.full((pp_days),np.nan)
        obs_pp = np.full((pp_days),np.nan)
	cdf_all_pp = np.full((pp_days), np.nan)
	cdf_all_reg = np.full((pp_days), np.nan)
        

        idx_nan = np.argwhere(np.isnan(obs_all))
        obs_all = np.delete(obs_all, idx_nan)
        reforecast_data_all = np.delete(reforecast_data_all, idx_nan, axis=0)
        
        # Constraint
        con = {'type': 'ineq',
                'fun': lambda x: x[1:14]}
        cons = [con]

        if len(obs_all) < 54:
                
                low_me_avg = np.nan
                high_me_avg = np.nan

                CRPS_pp_all = np.nan
                CRPS_reg_all = np.nan
                i_pp_all = np.nan
                i_reg_all = np.nan
                me_all = np.nan


        else:

                for w in range(0, pp_days): # this is the total number of days we are pping
                        #print w
                        start = w
                        end = w + days
                        reforecast_data = reforecast_data_all[start:end+1, :]
                        obs = obs_all[start:end+1] # this was +2 in the original (?)

                        S_squared = np.var(reforecast_data, axis=1) # variance is s^2
                
                        def crps(x):
                                ''' Define the CRPS function '''
                                crps_all = 0
                                for j in range(days):
                                        standard_dev = math.sqrt(math.sqrt(x[12]**2) + math.sqrt(x[13]**2) * S_squared[j])
                
                                        Z = (obs[j] - (x[0] + x[1] * reforecast_data[j,0] +\
                                                x[2] * reforecast_data[j,1] +\
                                                x[3] * reforecast_data[j,2] +\
                                                x[4] * reforecast_data[j,3] +\
                                                x[5] * reforecast_data[j,4] +\
                                                x[6] * reforecast_data[j,5] +\
                                                x[7] * reforecast_data[j,6] +\
                                                x[8] * reforecast_data[j,7] +\
                                                x[9] * reforecast_data[j,8] +\
                                                x[10] * reforecast_data[j,9] +\
                                                x[11] * reforecast_data[j,10]))\
                                                / standard_dev
                
                                        crps_one = standard_dev * (Z * (2 * norm.cdf(Z) - 1) + 2 * norm.pdf(Z) - \
                                        (1 / math.sqrt(math.pi)))
                
                                        crps_all = crps_all + crps_one
                                	crps_mean = crps_all / float(days)
                
                                return crps_mean
                        
                        res = minimize(crps, x0, method='SLSQP', constraints=cons)

                        new_x = np.around(np.asarray(res.x), decimals=3) # new coefficients
                        print '  new_x: ', new_x

                        weights_all[:,w] = new_x[1:12]

                        # Calculate variables for probabilistic forecasts

                        # post-processed (pp)
                        standard_dev_pp = math.sqrt(math.sqrt(new_x[12]**2) +\
                                math.sqrt(new_x[13]**2) * S_squared[-1]) # this was 7 (?)
                        #stan_dev_all[w] = standard_dev_pp
                        pred_mean_pp = new_x[0] + new_x[1] * reforecast_data[-1,0] +\
                                new_x[2] * reforecast_data[-1,1] +\
                                new_x[3] * reforecast_data[-1,2] +\
                                new_x[4] * reforecast_data[-1,3] +\
                                new_x[5] * reforecast_data[-1,4] +\
                                new_x[6] * reforecast_data[-1,5] +\
                                new_x[7] * reforecast_data[-1,6] +\
                                new_x[8] * reforecast_data[-1,7] +\
                                new_x[9] * reforecast_data[-1,8] +\
                                new_x[10] * reforecast_data[-1,9] +\
                                new_x[11] * reforecast_data[-1,10]
                        pred_mean_all[w] = pred_mean_pp
                        obs_pp[w] = obs[-1]

                        # regular (reg), i.e. no post-processing
                        standard_dev_reg = np.sqrt(np.var(reforecast_data[-1,:]))
                        mean_reg = np.mean(reforecast_data[-1,:])

                        print '  mean regular: ', mean_reg
                        print '  mean pp: ', pred_mean_pp
                        print '  obs: ', obs[-1]

                        # Calculate ME
                        me = pred_mean_pp - obs[-1]
                        me_all[w] = me

                        ## Calculate CRPS for both scenarios
                        Z_pp = (obs[-1] - pred_mean_pp) / standard_dev_pp
			cdf_all_pp[w] = Z_pp
                        CRPS_pp = standard_dev_pp * (Z_pp * (2 * norm.cdf(Z_pp) - 1) + 2 * norm.pdf(Z_pp) -
                                (1 / math.sqrt(math.pi)))
                        CRPS_pp_all[w] = CRPS_pp
                
                        Z_reg = (obs[-1] - mean_reg) / standard_dev_reg
			cdf_all_reg[w] = Z_reg
                        CRPS_reg = standard_dev_reg * (Z_reg * (2 * norm.cdf(Z_reg) - 1) + 2 * norm.pdf(Z_reg) -
                                (1 / math.sqrt(math.pi)))
                        CRPS_reg_all[w] = CRPS_reg
                
                
                        ## Calculate ignorance score for both scenarios
                        i_pp = np.log(2 * math.pi * standard_dev_pp**2) / 2 + (obs[-1] - pred_mean_pp)**2 / \
                                (2 * standard_dev_pp**2)
                
                        i_pp_all[w] = i_pp
                
                        i_reg = np.log(2 * math.pi * standard_dev_reg**2) / 2 + (obs[-1] - mean_reg)**2 / \
                                (2 * standard_dev_reg**2)
                
                        i_reg_all[w] = i_reg
                
                # Locate 5 warmest and coldest days
                obs_new = obs_all[days:days+pp_days]    
                highest = np.argpartition(obs_new, -5)[-5:]
                lowest = np.argpartition(obs_new, 5)[:5]
                
                high_me = me_all[highest]
                low_me = me_all[lowest]

                high_me_avg = np.mean(high_me)
                low_me_avg = np.mean(low_me)


                i_pp_all = np.nanmedian(i_pp_all)
                i_reg_all = np.nanmedian(i_reg_all)
                me_all = np.nanmean(me_all)

        return CRPS_pp_all, CRPS_reg_all, me_all, weights_all, high_me_avg, low_me_avg, pred_mean_all, obs_pp, cdf_all_pp, cdf_all_reg
