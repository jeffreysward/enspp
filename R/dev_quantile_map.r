library("ensembleBMA")

# Load the data
data(prcpGrid)

# Put the data into an ensemble data object
prcpGridData <- ensembleData(forecasts = prcpGrid[,1:9],
    latitude = prcpGrid[,"latitude"], longitude = prcpGrid[,"longitude"],
    date = "20030115", forecastHour = 48, initializationTime = "00")

# Load the fit
data(prcpFit)

# Get the BMA quantile forecast
gridForc <- quantileForecast( prcpFit, prcpGridData,
    date = "20030115", q = c(0.5, 0.9))

# Make plots
library(fields)
library(maps)
plotProbcast( gridForc[,"0.5"], type = "image", zlim = c(0,280),
lon = prcpGridData$lon, lat = prcpGridData$lat)
title("Median Forecast for Precipitation", cex = 0.5)
plotProbcast( gridForc[,"0.9"], type = "image", zlim = c(0,280),
lon = prcpGridData$lon, lat = prcpGridData$lat)
title("Upper Bound Forecast for Precipitation", cex = 0.5)
