# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.16.4
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# %% [markdown]
# # Script to compute the AR6 Scenarios Database
# The [AR6 Scenarios Database](https://data.ece.iiasa.ac.at/ar6/#/workspaces) ([Byers et al., 2022](https://data.ece.iiasa.ac.at/ar6/#)) is imported to retrieve the statistical values of Tables 3.2 and Table 3.4 from IPCC AR6 WGIII Chapter 3 ([Riahi et al., 2023](https://www.cambridge.org/core/books/climate-change-2022-mitigation-of-climate-change/mitigation-pathways-compatible-with-longterm-goals/7C750344E39ECA3BD5CB14156FCEEFE9)). The user can choose which scenarios' category to extract.

# %%
import pandas as pd
from zipfile import ZipFile
import pathlib

DATADIR = pathlib.Path('data')
DATADIR.mkdir(exist_ok=True)


# %%
def load_ar6():
    # AR6 variables to be processed
    archive = DATADIR / "1668008030411-AR6_Scenarios_Database_World_ALL_CLIMATE_v1.1.csv.zip"
    cache = DATADIR / "AR6_Scenarios_Database_World_ALL_CLIMATE_subset_and_metadata_v1.1.csv"

    # Use cache if possible
    if cache.exists():
        return pd.read_csv(cache)

    variables = ['AR6 climate diagnostics|Infilled|Emissions|Kyoto Gases (AR6-GWP100)',
                 'AR6 climate diagnostics|Surface Temperature (GSAT)|MAGICCv7.5.3|50.0th Percentile',
                 'Final Energy',
                 'Final Energy|Electricity',
                 'Carbon Sequestration|CCS|Fossil',
                 'Emissions|CO2|Energy|Supply|Electricity',
                 'Secondary Energy|Electricity',
                 'Primary Energy',
                 'Primary Energy|Fossil|w/ CCS',
                 'Primary Energy|Nuclear',
                 'Primary Energy|Renewables (incl. Biomass)',
                 'Emissions|CO2',
                 'Emissions|CO2|Energy',
                 'Emissions|CO2|AFOLU',
                 'Emissions|CO2|Waste',
                 'Emissions|CO2|Industrial Processes',
                 'Emissions|CO2|Other',
                 'Emissions|CH4',
                 'Emissions|CH4|Energy',
                 'Emissions|CH4|AFOLU',
                 'Emissions|CH4|Waste',
                 'Emissions|CH4|Industrial Processes',
                 'Emissions|CH4|Other',
                 'Emissions|N2O',
                 'Emissions|N2O|Energy',
                 'Emissions|N2O|AFOLU',
                 'Emissions|N2O|Industrial Processes',
                 'Emissions|N2O|Waste',
                 'Emissions|N2O|Other',
                 'Emissions|F-Gases']

    # Import the database and metadata of scenarios and a subset of variables
    with ZipFile(archive) as zipfile:
        # Process database
        cols = ['Model', 'Scenario', 'Region', 'Variable', 'Unit'] + [str(i) for i in range(2020, 2101, 10)]
        data = pd.read_csv(zipfile.open('AR6_Scenarios_Database_World_ALL_CLIMATE_v1.1.csv'), usecols=cols)
        data = data[data['Variable'].isin(variables)]

        # Process metadata
        cols = ['Model', 'Scenario', 'Category', 'IMP_marker']
        meta = pd.read_excel(zipfile.open('AR6_Scenarios_Database_metadata_indicators_v1.1.xlsx'), sheet_name='meta_Ch3vetted_withclimate', usecols=cols)

    # Combine dataframes
    cols = ['Model', 'Scenario', 'Region', 'Variable', 'Unit', 'Year', 'Value', 'Category', 'IMP_marker']
    df = meta.merge(data, on=['Model', 'Scenario'], how='right')
    df = pd.melt(df, id_vars=df.columns[:7], var_name='Year', value_name='Value')
    df.to_csv(cache, index=False)
    return df


# %%
df = load_ar6()

# %% [markdown]
# The following variables are either those given in Tables 3.2 and 3.4 of IPCC AR6 WGIII Chapter 3 (([Riahi et al., 2023](https://www.cambridge.org/core/books/climate-change-2022-mitigation-of-climate-change/mitigation-pathways-compatible-with-longterm-goals/7C750344E39ECA3BD5CB14156FCEEFE9)) or are furtherly computed to retrieve these variables.

# %%
# Load the AR6 Scenarios Database for a given category and set of variables
cat = 'C1'
dfc = df[df['Category'] == cat]

# %%
# Check that the number of scenarios within the explored category matches the IPCC records
dfc[['Model', 'Scenario']].drop_duplicates().shape[0]  # 97 for C1


# %%
# Compute statictical and extract IMP scenarios
def process_scenarios(df):
    stat = (df.groupby('Year')['Value'].quantile([0.05, 0.50, 0.95])
              .unstack().set_axis(pd.Index(['5th', 'Median', '95th'], name='Scenario'), axis=1)
              .stack().rename('Value').swaplevel().sort_index().reset_index())

    imp = (df[df['IMP_marker'] != 'non-IMP']
             .assign(Scenario=lambda x: 'IMP-' + x['IMP_marker'])
             .drop(columns=['IMP_marker', 'Model']))

    return pd.concat([stat, imp], ignore_index=True)


# %% [markdown]
# ## Electricity share of final energy (ESFE)

# %%
# Filter necessary variables to compute the ratio of electricity in final energy demand globally
var = ['Final Energy', 'Final Energy|Electricity']
esfe = dfc[dfc['Variable'].isin(var)]

# Calculate the ratio of electricity in final energy
calc_esfe = lambda x: x['Final Energy|Electricity'] / x['Final Energy']

esfe = (pd.pivot(esfe, columns='Variable', index=['IMP_marker', 'Model', 'Scenario', 'Year'], values='Value')
          .sort_values(['Scenario', 'Year'])
          .reset_index().rename_axis(columns=None)
          .assign(Value=calc_esfe)
          .drop(columns=var))

esfe = process_scenarios(esfe).assign(Value=lambda x: x['Value'].round(2))  # percentage

# %% [markdown]
# ## Greenhouse gases (GHG)

# %%
# Filter only the necessary variable
var = ['AR6 climate diagnostics|Infilled|Emissions|Kyoto Gases (AR6-GWP100)']
ghg = dfc[dfc['Variable'].isin(var)]

ghg = (ghg.drop(columns=['Category', 'Region', 'Unit', 'Variable'])
          .sort_values(['Scenario', 'Year']))

ghg = process_scenarios(ghg).assign(Value=lambda x: x['Value'].round(0).div(1000))  # to obtain values in Gt

# %% [markdown]
# ## Final energy demand (FED)

# %%
# Filter only the necessary variable
var = ['Final Energy']
fed = dfc[dfc['Variable'].isin(var)]

fed = (fed.drop(columns=['Category', 'Region', 'Unit', 'Variable'])
          .sort_values(['Scenario', 'Year']))

fed = process_scenarios(fed).assign(Value=lambda x: x['Value'].round(0))

# %% [markdown]
# ## Fossil CO<sub>2</sub> (CCSFOS)

# %%
# Filter only the necessary variable
var = ['Carbon Sequestration|CCS|Fossil']
ccsfos = dfc.loc[dfc['Variable'].isin(var)]

ccsfos = (ccsfos.drop(columns=['Category', 'Region', 'Unit', 'Variable'])
                .sort_values(['Scenario', 'Year']))

ccsfos = process_scenarios(ccsfos).assign(Value=lambda x: x['Value'].round(0).div(1000))  # to obtain values in Gt

# %% [markdown]
# ## CO<sub>2</sub> intensity of electricity (CO2ELC)

# %%
# Filter variables needed to calculate the ratio of carbon content of electricity to electricity generation
var = ['Secondary Energy|Electricity', 'Emissions|CO2|Energy|Supply|Electricity']
co2elc = dfc[dfc['Variable'].isin(var)]

# Calculate the carbon content of electricity
calc_co2elc = lambda x: x['Emissions|CO2|Energy|Supply|Electricity'] / x['Secondary Energy|Electricity'] * 3.6

co2elc = (pd.pivot(co2elc, columns='Variable', index=['IMP_marker', 'Model', 'Scenario', 'Year'], values='Value')
          .sort_values(['Scenario', 'Year'])
          .reset_index().rename_axis(columns=None)
          .assign(Value=calc_co2elc)
          .drop(columns=var))

co2elc = process_scenarios(co2elc).assign(Value=lambda x: x['Value'].round(0))

# %% [markdown]
# ## Low-carbon share of primary energy (LCSPE)
# According to IPCC AR6, the low-carbon share of energy includes *renewables (including biomass, solar, wind, hydro, geothermal, ocean); fossil fuels when used with CCS; and, nuclear power.*

# %%
# Filter variables needed to calculate the low-carbon share of primary energy
var = ['Primary Energy', 'Primary Energy|Fossil|w/ CCS','Primary Energy|Nuclear', 'Primary Energy|Renewables (incl. Biomass)']
lcspe = dfc.loc[dfc['Variable'].isin(var)]

# Calculate the low-carbon share of primary energy
calc_lcspe = lambda x: x[['Primary Energy|Fossil|w/ CCS', 'Primary Energy|Nuclear', 'Primary Energy|Renewables (incl. Biomass)']].sum(axis=1) / x['Primary Energy']

lcspe = (pd.pivot(lcspe, columns='Variable', index=['IMP_marker', 'Model', 'Scenario', 'Year'], values='Value')
           .sort_values(['Scenario', 'Year'])
           .reset_index().rename_axis(columns=None)
           .assign(Value=calc_lcspe)
           .drop(columns=var))

lcspe = process_scenarios(lcspe).assign(Value=lambda x: x['Value'].round(2))  # percentage

# %% [markdown]
# ## Non-energy GHG emissions (NONNRG)
# To retrieve non-energy GHG emissions the energy-related GHG emissions are deducted from the total GHG emissions, using IPCC AR6 global warming potentials to convert each GHG in CO<sub>2eq</sub>.

# %%
# Filter only necessary variables
var = ['Emissions|CO2','Emissions|CO2|Energy', 'Emissions|CH4','Emissions|CH4|Energy',
        'Emissions|N2O','Emissions|N2O|Energy', 'Emissions|F-Gases']
nonnrg = dfc.loc[dfc['Variable'].isin(var)]

# Calculate the non-energy GHG emissions
calc_nonnrg = lambda x: x['Emissions|CO2'] - x['Emissions|CO2|Energy'] + (x['Emissions|CH4'] - x['Emissions|CH4|Energy'])*29.8 + (x['Emissions|N2O'] - x['Emissions|N2O|Energy'])*0.273 + x['Emissions|F-Gases']

nonnrg = (pd.pivot(nonnrg, columns='Variable', index=['IMP_marker', 'Model', 'Scenario', 'Year'], values='Value')
            .sort_values(['Scenario', 'Year'])
            .reset_index().rename_axis(columns=None)
            .assign(Value=calc_nonnrg)
            .drop(columns=var))

nonnrg = process_scenarios(nonnrg).assign(Value=lambda x: x['Value'].round(0).div(1000))  # to obtain values in Gt

# %% [markdown]
# ## CSV output

# %% [markdown]
# The file *constraints.csv* in thr output of this script becomes the input of the next script *02_tiam-fr_vs_constraints.py*

# %%
dfs = {'ghg': ghg, 'lcspe': lcspe, 'fed': fed, 'esfe': esfe,
       'co2elc': co2elc, 'ccsfos': ccsfos, 'nonnrg': nonnrg}
out = (pd.concat(dfs, names=['Variable']).reset_index('Variable')
        .pivot_table(index=['Scenario', 'Year'], columns='Variable', values='Value', sort=False))
out.to_csv(DATADIR / 'constraints.csv')

# %%
out
