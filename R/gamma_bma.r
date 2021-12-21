library("ensembleBMA")

fit_bma <- function(wspdtrain, n_ens_members = 5) {

    # Put the training and test data into an ensembleData object
    train_ensd <- ensembleData(forecasts = wspdtrain[,3:(n_ens_members + 2)], 
                               dates = wspdtrain$Time, 
                               observations = wspdtrain$Obs, 
                               forecastHour = 0, 
                               initializationTime = "00", 
                               exchangeable = NULL)

    # Fit the BMA distribution
    bma_fit <- fitBMAgamma(train_ensd, control = controlBMAgamma(startupSpeed = 0))

    return(bma_fit)
}

quant_bma <- function(bma_fit, wspdtest, n_ens_members = 5, quantiles = seq(from=0.01, to=0.99, by=0.01), type = "temporal") {

    # Put the training and test data into an ensembleData object
    if (type == "temporal") {
        test_ensd <- ensembleData(forecasts = wspdtest[,3:(n_ens_members + 2)], 
                                dates = wspdtest$Time, 
                                observations = wspdtest$Obs, 
                                forecastHour = 0, 
                                initializationTime = "00", 
                                exchangeable = NULL)
    } else if (type == "spatial") {
        test_ensd <- ensembleData(forecasts = wspdtest[,2:(n_ens_members + 1)], 
                                dates = wspdtest$Time, 
                                latitude = wspdtest$XLAT, 
                                longitude = wspdtest$XLONG,
                                forecastHour = 0, 
                                initializationTime = "00", 
                                exchangeable = NULL)
    } else {
        stop("Invalid value for type variable. Use temporal or spatial.")
    }

    quant_bma<- ensembleBMA::quantileForecast(bma_fit, test_ensd, quantiles=quantiles)
    
    return(quant_bma)
}

crps_bma <- function(bma_fit, wspdtest, n_ens_members = 5) {
    
    # Put the training and test data into an ensembleData object
    test_ensd <- ensembleData(forecasts = wspdtest[,3:(n_ens_members + 2)], 
                              dates = wspdtest$Time, 
                              observations = wspdtest$Obs, 
                              forecastHour = 0, 
                              initializationTime = "00", 
                              exchangeable = NULL)

    # Calculate the CRPS (for each forecast lead time)
    crps_bma<- ensembleBMA::crps(bma_fit, test_ensd)[, 2]
    
    return(crps_bma)
}

