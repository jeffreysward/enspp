library("ensembleBMA")
# Load the data
wspd <- read.table("/Users/jeffreysward/Box Sync/01_Research/01_Renewable_Analysis/WRF_Solar_and_Wind/enspp/data/formatted_data.csv", 
                   sep = ",",
                   header = TRUE
                   )

# Split the date into training and testing sets
wspdtrain<- wspd[wspd$Time<="2020-02-11",]
wspdtest<- wspd[wspd$Time>"2020-02-11",]

# Plot a verification rank histogram
rank<- apply(wspdtrain[, 2:7], 1, rank)[1,]
hist(rank, breaks = 0:6 + 0.5, main = "Verification Rank Histogram")

# Put the training and test data into an ensembleData object
train_ensd <- ensembleData(forecasts = wspdtrain[,3:7],  # Ensemble forecasts
                           dates = wspdtrain$Time,  # fitBMA gamma doesn't use this
                           observations = wspdtrain$Obs,  # Corresponding observations
                           forecastHour = 0,  # I'm pretty sure that fitBMAgamma doesn't use this
                           initializationTime = "00",  # I'm pretty sure that fitBMAgamma doesn't use this
                           exchangeable = NULL  # with this, we are saying that all the members are statistically distinguishable
                           )

# Put the training and test data into an ensembleData object
test_ensd <- ensembleData(forecasts = wspdtest[,3:7],  # Ensemble forecasts
                           dates = wspdtest$Time,  # fitBMA gamma doesn't use this
                           observations = wspdtest$Obs,  # Corresponding observations
                           forecastHour = 0,  # I'm pretty sure that fitBMAgamma doesn't use this
                           initializationTime = "00",  # I'm pretty sure that fitBMAgamma doesn't use this
                           exchangeable = NULL  # with this, we are saying that all the members are statistically distinguishable
                           )

bma_fit <- fitBMAgamma(train_ensd,
                       control = controlBMAgamma(startupSpeed = 0),  # Can enter arguments here to control the fitting in a more custom way
                       )
# Visualize the BMA predictive density
plot(bma_fit, test_ensd[1,])

# Calculate the probabilities and quantiles
quant_bma<- ensembleBMA::quantileForecast(bma_fit, test_ensd, quantiles=seq(from=0.01, to=0.99, by =0.01))

# Plot a dashed line at the 50th quantile
plot(quant_bma[, 50], type = "l", lty = 2, ylab = "100m Wind Speed",
     xlab = "date", xaxt = "n", ylim = c(0, 25))
axis(1, at = seq(1, 125, 6), test_ensd$dates[seq(1, 125, 6)])
# Shade the area between the 25th and 75th quantiles
polygon(c(1:125, 125:1), c(quant_bma[1:125, 25], quant_bma[125:1, 75]),
    col = gray(0.1, alpha = 0.1), border = FALSE)
# Shade the area between the 10th and 90th quantiles
polygon(c(1:125, 125:1), c(quant_bma[1:125, 10], quant_bma[125:1, 90]),
    col = gray(0.1, alpha = 0.1), border = FALSE)
# Shade the area between the 1th and 99th quantiles
polygon(c(1:125, 125:1), c(quant_bma[1:125, 1], quant_bma[125:1, 99]),
    col = gray(0.1, alpha = 0.1), border = FALSE)
# Plot the observation with a solid line 
lines(test_ensd$observations)

## Verification ##
# Calculate the CRPS (for each forecast lead time)
crps_bma<- ensembleBMA::crps(bma_fit, test_ensd)[, 2]

# Plot the CRPS for each lead time using a boxplot
boxplot(crps_bma, ylab = "CRPS")

# Probability Integral Transforms (PITs) can be used to assess the reliability
# (i.e., calibration) of continuous probabilistic forecasts
pit_bma<- pit(bma_fit, test_ensd)

hist(pit_bma, main = "BMA PIT", freq = FALSE,
     xlab = "", ylab = "", ylim = c(0, 2.5))
abline(h = 1, lty = 2)



