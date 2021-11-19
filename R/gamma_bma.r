library("ensembleBMA")

fit_bma <- function(wspdtrain, n_ens_members = 5) {

    # Put the training and test data into an ensembleData object
    train_ensd <- ensembleData(forecasts = wspdtrain[,4:(n_ens_members + 3)], 
                               dates = wspdtrain$Time, 
                               observations = wspdtrain$Obs, 
                               forecastHour = 0, 
                               initializationTime = "00", 
                               exchangeable = NULL)

    # Fit the BMA distribution
    bma_fit <- fitBMAgamma(train_ensd, control = controlBMAgamma(startupSpeed = 0))

    return(bma_fit)
}

quant_bma <- function(bma_fit, wspdtest, n_ens_members = 5, quantiles = seq(from=0.01, to=0.99, by=0.01)) {

    # Put the training and test data into an ensembleData object
    test_ensd <- ensembleData(forecasts = wspdtest[,4:(n_ens_members + 3)], 
                              dates = wspdtest$Time, 
                              observations = wspdtest$Obs, 
                              forecastHour = 0, 
                              initializationTime = "00", 
                              exchangeable = NULL)

    # Extract the quantiles
    # if (n_quantiles == 99) { 
    #     quant_bma<- ensembleBMA::quantileForecast(bma_fit, test_ensd, quantiles=seq(from=0.01, to=0.99, by=0.01))
    # } else if (n_quantiles == 10) {
    #     quant_bma<- ensembleBMA::quantileForecast(bma_fit, test_ensd, quantiles=seq(from=0.1, to=0.9, by=0.1))
    # } else if  (n_quantiles == 3) {
    #     quant_bma<- ensembleBMA::quantileForecast(bma_fit, test_ensd, quantiles=c(0.25, 0.5, 0.75))
    # } else {
    #     stop("Unsupported quantile number. Please choose from 3, 10, or, 99.")
    # }

    quant_bma<- ensembleBMA::quantileForecast(bma_fit, test_ensd, quantiles=quantiles)
    
    return(quant_bma)
}

crps_bma <- function(bma_fit, wspdtest, n_ens_members = 5) {
    
    # Put the training and test data into an ensembleData object
    test_ensd <- ensembleData(forecasts = wspdtest[,4:(n_ens_members + 3)], 
                              dates = wspdtest$Time, 
                              observations = wspdtest$Obs, 
                              forecastHour = 0, 
                              initializationTime = "00", 
                              exchangeable = NULL)

    # Calculate the CRPS (for each forecast lead time)
    crps_bma<- ensembleBMA::crps(bma_fit, test_ensd)[, 2]
    
    return(crps_bma)
}

