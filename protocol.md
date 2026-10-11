# Synthetic treatment comparison

Before analysis: use 10,000 synthetic people (seed 42), 30% severe illness. Treatment probabilities: mild 0.2, severe 0.8. Adverse-event probabilities: mild untreated 0.10, treated 0.05; severe untreated 0.40, treated 0.25. No additional confounding, missingness or loss to follow-up. The population average risk difference is −0.08.

Compare crude risk difference with direct standardisation to fixed 70/30 mild/severe shares. Bootstrap whole people 500 times (seed 123), keeping target weights fixed. Report undefined resamples instead of replacing missing cells. Repeat with randomised 50/50 assignment (seed 43). Generate 100 independent datasets at n=1,000 and n=10,000, seeds 100000+n+replicate. Report bias and RMSE relative to the population truth.

Extension fixed before execution: flip recorded severity independently at rates 0, 0.1 and 0.3, seed 777, while retaining the true severity in assignment/outcome generation. Standardise to the known recorded-severity distribution (severe share 0.3+0.4q). Compare against the true-severity oracle. All quantities are fictional and have no treatment or patient interpretation.
