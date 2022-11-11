# This script cleans, joins and transforms data from different sources:
# 1) Thermal data
# 2) Behavioural data
# 3) Individual-level data (birthdate, etc).
# ...and calculates some litter-level statistics

library("dplyr")
library("matrixStats")

######
#IMPORT DATA
thermal_data_file <- paste(getwd(), "/ir_data.csv", sep = "")
thermal = read.csv(thermal_data_file)
thermal[thermal == 100] <- NA # Erroneous data was coded as 100
thermal <- thermal %>% 
  mutate(kittenid = factor(kittenid))

#add average temperatures and temperature changes
thermal$mean_before_right_eye <- rowMeans(thermal[startsWith(names(thermal),"before_right_eye")], na.rm = TRUE)
thermal$mean_before_left_eye <- rowMeans(thermal[startsWith(names(thermal),"before_left_eye")], na.rm = TRUE)
thermal$mean_before_nose <- rowMeans(thermal[startsWith(names(thermal),"before_nose")], na.rm = TRUE)
thermal$mean_after_right_eye <- rowMeans(thermal[startsWith(names(thermal),"after_right_eye")], na.rm = TRUE)
thermal$mean_after_left_eye <- rowMeans(thermal[startsWith(names(thermal),"after_left_eye")], na.rm = TRUE)
thermal$mean_after_nose <- rowMeans(thermal[startsWith(names(thermal),"after_nose")], na.rm = TRUE)
thermal$diff_right_eye <- thermal$mean_after_right_eye - thermal$mean_before_right_eye
thermal$diff_left_eye <- thermal$mean_after_left_eye - thermal$mean_before_left_eye
thermal$diff_nose <- thermal$mean_after_nose - thermal$mean_before_nose

#add behavioural data from the test, trial number and age during trial from separation data
kitten_behavior_file <- paste(getwd(), "/separationdata_clean_withinfo.csv", sep = "")
separation <- read.csv(kitten_behavior_file)

names(separation) <- gsub("scratch", "motor_activity", names(separation), fixed = TRUE) #scratch variable is actually motor activity, I was just too lazy to change it on the coding sheet way back when I didn't do things proper.
separation$trial_date <- as.Date(paste(separation$trialyear, separation$trialmonth, separation$trialday, sep = "-"))

separation <- separation %>%
  mutate(kittenid = factor(kittenid)) %>% 
  dplyr::select(kittenid,
                trial,
                freq_vocal,
                dur_motor_activity,
                trialyear,
                trialmonth,
                trialday)

kitten_info_file <- paste(getwd(), "/info_kitten.csv", sep = "")
kitten_info <- read.csv(kitten_info_file)
kitten_info$kittenid <- factor(kitten_info$kittenid)

thermal <- left_join(thermal, separation, by = c("kittenid", "trial"))
thermal <- left_join(thermal, kitten_info, by = c("kittenid"))

#calculate age (in days) at time of trial
thermal$birth_date <- as.Date(paste(thermal$birthyear, thermal$birthmonth, thermal$birthday, sep = "-"))
thermal$trial_date <- as.Date(paste(thermal$trialyear, thermal$trialmonth, thermal$trialday, sep = "-"))
thermal$days_old_on_trial <- thermal$trial_date - thermal$birth_date

thermal <- thermal %>%
  mutate(kittenid = factor(kittenid),
         litter = factor(litter),
         gramsperday = agd_measure1_weight / agd_measure1_daysold) %>% 
  mutate(littersexratio100 = littersexratio*100) %>%
  mutate_at(c("agd_measure1_mm",
              "agd_measure1_weight",
              "agd_measure2_mm",
              "agd_measure2_weight",
              "gramsperday",
              "littersizefinal",
              "littersexratio100"),
            .funs = list(centered = ~scale(., center = T, scale = F))) %>% 
  dplyr::select(kittenid,
                trial,
                freq_vocal,
                dur_motor_activity,
                diff_right_eye,
                diff_left_eye,
                diff_nose,
                mean_before_right_eye,
                mean_before_left_eye,
                mean_before_nose,
                mean_after_right_eye,
                mean_after_left_eye,
                mean_after_nose,
                litter,
                mom,
                sex,
                littersexratio,
                littersizefinal,
                gramsperday,
                days_old_on_trial)

#get litter mean values
thermal_litter <- thermal %>%
  dplyr::select(litter,
                diff_right_eye,
                diff_left_eye,
                diff_nose,
                dur_motor_activity,
                freq_vocal,
                diff_right_eye,
                diff_left_eye,
                diff_nose) %>% 
  group_by(litter, .drop = F) %>%
  summarise_at(c("dur_motor_activity",
                 "freq_vocal",
                 "diff_right_eye",
                 "diff_left_eye",
                 "diff_nose"), 
               .funs = list(
                 ~mean(., na.rm = T))) %>% 
  rename_at(vars(-litter), ~ paste0(., '_littermean'))

#join individual and litter mean data
thermal <- left_join(thermal, thermal_litter, by = "litter")

thermal <- thermal %>%
  mutate(freq_vocal_deviation = freq_vocal_littermean - freq_vocal) %>% 
  mutate(dur_motor_activity_deviation = dur_motor_activity_littermean - dur_motor_activity) %>% 
  mutate(diff_right_eye_deviation = diff_right_eye_littermean - diff_right_eye) %>% 
  mutate(diff_left_eye_deviation = diff_left_eye_littermean - diff_left_eye) %>% 
  mutate(diff_nose_deviation = diff_nose_littermean - diff_nose)

thermal_sd <- thermal %>% 
  group_by(kittenid) %>%
  summarise_at(c("mean_before_right_eye",
                 "mean_before_left_eye",
                 "mean_before_nose",
                 "diff_right_eye",
                 "diff_left_eye",
                 "diff_nose"), 
               .funs = list(
                 ~sd(.))) %>%
  ungroup(.) %>% 
  setNames(paste0('sd_', names(.))) %>% 
  rename(kittenid = sd_kittenid)

thermal <- left_join(thermal, thermal_sd, by = c("kittenid"))


write.table(x = thermal, file = "kitten_thermal_data", sep = ",", row.names = FALSE)

