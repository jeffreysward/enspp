library("ensembleBMA")
library("ensembleMOS")
library("crch")
library("gamlss")
library("SpecsVerification")
library("scoringRules")

### MOS
## Data Prep
# Load the data into R
data("temp", package = "ensemblepp")
# Set the dates as rownames
temp$date<- as.Date(rownames(temp))
# Subset the data to include only data from Dec, Jan, and Feb
temp<- temp[format(temp$date, "%m") %in% c("12", "01", "02"),]
# Calculate the ensemble mean and standard deviation
temp$ensmean<- apply(temp[,2:12], 1, mean)
temp$enssd<- apply(temp[,2:12], 1, sd)
# Split the date into training and testing sets
temptrain<- temp[temp$date<"2010-03-01",]
temptest<- temp[temp$date>= "2010-03-01",]
# Plot the observations vs the ensemble mean of the fx
plot(temp~ensmean, data = temptrain)
abline(0, 1, lty = 2)

## MOS Model Fitting
# Fit a linear regression to the ensemble mean
MOS<- lm(temp~ensmean, data = temptrain)
abline(MOS)
# Generate MOS predictions
fcMOS<- predict(MOS, newdata = temptest)
plot(fcMOS[1:20], type = "l", lty = 2, ylab = "2m temperature", 
    xlab = "date", xaxt = "n", ylim = c(-35, 10))
axis(1, at = seq(1,20,6), temptest$date[seq(1, 20, 6)])

lines(temptest$temp[1:20])
lines(temptest$ensmean[1:20], lty = 3)

## Verification
rbind(raw = c(BIAS = mean(temptest$ensmean-temptest$temp), 
        MAE = mean(abs(temptest$ensmean - temptest$temp)), 
        RMSE = sqrt(mean((temptest$ensmean - temptest$temp)^2))), 
    MOS = c(BIAS = mean(fcMOS-temptest$temp), 
        MAE = mean(abs(fcMOS - temptest$temp)), 
        RMSE = sqrt(mean((fcMOS - temptest$temp)^2))))

### Univariate Ensemble Postprocessing 
# Put the train and test data into "ensembleData" objects
temptrain_eD<- ensembleData(forecasts = temptrain[,2:12],
    dates = temptrain$date, observations = temptrain$temp,
    forecastHour = 24, initializationTime = "00", exchangeable = rep(1, 11))
temptest_eD<- ensembleData(forecasts = temptest[,2:12],
    dates = temptest$date, observations = temptest$temp,
    forecastHour = 24, initializationTime = "00", exchangeable = rep(1, 11))
# Plot a verification rank histogram
rank<- apply(temptrain[, 1:12], 1, rank)[1,]
hist(rank, breaks = 0:12 + 0.5, main = "Verification Rank Histogram")
# Plot a boxplot of absolute forecast errors
sdcat<- cut(temptrain$enssd,
    breaks = quantile(temptrain$enssd, seq(0, 1, 0.2)))
boxplot(abs(residuals(MOS))~sdcat, ylab = "absolute error",
    xlab = "ensemble standard deviation", main = "Spread-Skill")

## Fit a NGR Model
# Carry out maximum likelihood estimation of model coefficients
# using two different R packages "crch" and "gamlss"
NGR_crch<- crch(temp~ensmean|enssd, data = temptrain)
NGR_gamlss<- gamlss(temp~ensmean, sigma.formula =~enssd, data = temptrain)
# crch() can also be used to fit models with minimum CRPS estimatio and 
# sigma parameterization
NGR_crch2<- crch(temp~ensmean|I(enssd^2), data = temptrain,
    link.scale = "quad", type = "crps")
# fitMOS() also provides another implementation of this model althought
# it requires an "ensembleData" object as input
NGR_ensembleMOS<- fitMOS(temptrain_eD, model = "normal")
# We can access the coefficients with where NGR_ensembleMOS$B is actually
# a vector of coefficients -- one for each ensemble member -- but since
# the ensemble members are considered interchangable all of these 
# coefficients equal 1/11
coef_ensembleMOS<- c(NGR_ensembleMOS$a, 11 * NGR_ensembleMOS$B[1],
    NGR_ensembleMOS$c, NGR_ensembleMOS$d)
# We can compare the model coefficients produced using the different methods
rbind(crch = coef(NGR_crch),
    gamlss = c(coef(NGR_gamlss), coef(NGR_gamlss, what = "sigma")),
    ensembleMOS = coef_ensembleMOS, crch2 = coef(NGR_crch2))


## Fit a BMA and other ensemble dressing models
BMA<- fitBMA(temptrain_eD, model = "normal")
smuy2<- var(MOS$residuals)
st2<- mean(temptrain$enssd^2)
dress<- sqrt(smuy2 - (1 + 1/8) * st2)
# Compare BMA and ensemble dressing
rbind(BMA = c(BMA$biasCoefs[,1], BMA$sd), ensdress = c(coef(MOS), sd = dress))

## Fit an affine kernel dressing model
AKD<- FitAkdParameters(ens = as.matrix(temptrain[,2:12]),obs = temptrain$temp)

## Prediction
# Get the "location" and "scale" parameters 
mean_NGR<- predict(NGR_crch,  newdata = temptest, type = "location")
sd_NGR<- predict(NGR_crch,  newdata = temptest, type = "scale")
mean_NGR2<- predict(NGR_crch2, newdata = temptest, type = "location")
sd_NGR2<- predict(NGR_crch2, newdata = temptest, type = "scale")
# Compute the predictive densities and probabilities
x<- seq(-10, 10, 0.1)
pdf_NGR<- dnorm(x, mean_NGR[1], sd_NGR[1])
cdf_NGR<- pnorm(0, mean_NGR, sd_NGR)
# Generate the predictive quantiles 0.25, 0.5, and 0.75 for all dates in the test set
quant_NGR<- predict(NGR_crch, newdata = temptest, type = "quantile", at = c(0.25, 0.5, 0.75))
# For BMA and the other ensemble dressing techniques, 
# we first need the corrected ensemble forecasts
corrected_BMA<- apply(temptest[,2:12], 2, function(x) BMA$biasCoefs[,1] %*% rbind(1, x))
corrected_dress<- apply(temptest[,2:12], 2, function(x) coef(MOS) %*% rbind(1, x))
AKDobj<- DressEnsemble(ens = as.matrix(temptest[2:12]), 
    dressing.method = "akd", parameters = as.list(AKD))
dressobj<- list(ens = corrected_dress, 
    ker.wd = matrix(dress, nrow = nrow(corrected_dress), ncol = 11))
# Calculate the probabilities and quantiles
cdf_BMA<- cdf(BMA, temptest_eD, values = 0)
cdf_AKD<- rowMeans(pnorm(0,  AKDobj$ens,  AKDobj$ker.wd))
cdf_dress<- rowMeans(pnorm(0, dressobj$ens, dressobj$ker.wd))

# Plot the densities for all methods
par(mfrow = c(1,4))
plot(x, pdf_NGR, type = "l", xlab = "Temperature", ylab = "Density", lwd = 3, main = "NGR")
abline(v = temptest$temp[1], col = "orange", lwd = 3)
plot(BMA, temptest_eD[1,])
title(main = "BMA")
plot(density(dressobj$ens[1,], bw = dressobj$ker.wd[1, 1]),
    xlab= "Temperature", main = "ensemble dressing", lwd = 3)
abline(v = temptest$temp[1], col = "orange", lwd = 3)
plot(density(AKDobj$ens[1,], bw = AKDobj$ker.wd[1, 1]),
    xlab = "Temperature", main = "AKD", lwd = 3)
abline(v = temptest$temp[1], col = "orange", lwd = 3)

# Plot multiple time periods
par(mfrow = c(1,2))
plot(quant_NGR[1:20, 2], type = "l", lty = 2, ylab = "2m temperature",
    xlab = "date", xaxt = "n", ylim = c(-15, 10))
axis(1, at = seq(1, 20, 6), temptest$date[seq(1, 20, 6)])
polygon(c(1:20, 20:1), c(quant_NGR[1:20, 1], quant_NGR[20:1, 3]),
    col = gray(0.1, alpha = 0.1), border = FALSE)
lines(temptest$temp[1:20])
plot(cdf_NGR[1:20], type = "l", ylab = "Pr(T<0)",
    xlab = "date", xaxt = "n", ylim = c(0, 1))
axis(1, at = seq(1, 20, 6), temptest$date[seq(1, 20, 6)])
points(temptest$temp<0)

## Verification
# Calculate the CRPS
crps_all<- cbind(
    NGR1 = scoringRules::crps(temptest$temp, family = "normal",
        mean = mean_NGR, sd = sd_NGR),
    NGR2 = scoringRules::crps(temptest$temp, family = "normal",
        mean = mean_NGR2, sd = sd_NGR2),
    BMA  = ensembleBMA::crps(BMA, temptest_eD)[, 2],
    dress = DressCrps(dressobj, temptest$temp),
    AKD  = DressCrps(AKDobj, temptest$temp))
# Compute the average CRPS on 250 bootstrap samples
bootmean<- function(scores, nsamples = 250) {
    boot<- NULL
    for(i in 1:nsamples) {
        bindex<- sample(nrow(scores), replace = TRUE)
        boot<- rbind(boot, colMeans(scores[bindex,]))
        }
        boot
}
# Plot all the bootstrap means of the CRPS using a boxplot
boxplot(bootmean(crps_all), ylab = "CRPS")
# Compute the predictive log-density
ign_all<- cbind(
    NGR1 = -dnorm(temptest$temp, mean_NGR, sd_NGR, log = TRUE),
    NGR2 = -dnorm(temptest$temp, mean_NGR2, sd_NGR2, log = TRUE),
    BMA  = -log(rowSums(BMA$weights * dnorm(temptest$temp, corrected_BMA, BMA$sd))),
    dress = -log(rowMeans(dnorm(temptest$temp, dressobj$ens, dressobj$ker.wd))),
    AKD  = -log(rowMeans(dnorm(temptest$temp, AKDobj$ens, AKDobj$ker.wd))))
# Plot all the bootstrap means of the log-density using a boxplot
boxplot(bootmean(ign_all), ylab = "IS")

# Probability Integral Transforms (PITs) can be used to assess the reliability
# (i.e., calibration) of continuous probabilistic forecasts
pit<- cbind(
    NGR1 = pnorm(temptest$temp, mean_NGR, sd_NGR),
    NGR2 = pnorm(temptest$temp, mean_NGR2, sd_NGR2),
    BMA  = pit(BMA, temptest_eD),
    dress = rowMeans(pnorm(temptest$temp, dressobj$ens, dressobj$ker.wd)),
    AKD  = rowMeans(pnorm(temptest$temp, AKDobj$ens, AKDobj$ker.wd)))
# Plot the PITs
par(mfrow = c(1, ncol(pit)))
for(model in colnames(pit)){
    hist(pit[, model], main = model, freq = FALSE,
    xlab = "", ylab = "", ylim = c(0, 1.6))
    abline(h = 1, lty = 2)
    }   
