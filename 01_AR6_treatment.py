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
import pathlib
import pandas as pd
import os

DATADIROUT = pathlib.Path('outputs')


# %%
def load_data(category, variables):
    """Imports the database of scenarios and their variables according to the category entered by the user.

    category (string): a category from the column 'Category' of the database (e.g., 'C1')
    variables (list): a list of variables from the column 'Variable' of the database (e.g., ['Final Energy','Final Energy|Electricity']

    Returns a dataframe.
    """
    #df = pd.read_csv('.\AR6_Scenarios_Database_World_v1.1\AR6_Scenarios_Database_World_v1.1.csv')
    #df.to_parquet('.\AR6_Scenarios_Database_World_v1.1.parquet')
    df = pd.read_parquet('.\data\AR6_Scenarios_Database_World_v1.1.parquet')

    # Define the columns of the dataframe
    cols = ['Model', 'Scenario', 'Region', 'Variable', 'Unit'] + [str(i) for i in range(2020, 2101, 10)]

    # Select pairs of models and scenarios belonging to the user-defined category
    cdict = pd.read_excel('.\data\AR6_Scenarios_Database_metadata_indicators_v1.1.xlsx', sheet_name='meta_Ch3vetted_withclimate')
    df = df.merge(cdict, on=['Model', 'Scenario'], how='left')
    df = df[df['Category'] == category]
    df = df.drop(columns=['Category'])

    df = df.loc[df['Variable'].isin(variables), cols]
    df = pd.melt(df, id_vars=cols[:5], var_name='Year', value_name='Value')

    return df


# %%
def load_IMP(category):
    """Select the Illustrative Mitigation Pathways of a given category with the name of the scenarios and their alias.

    category (string): a category from the column 'Category' of the database (e.g., 'C1')

    Returns a list of the full name of the category-specific IMPs and a dictionnary of the IMPs with their alias.
    """
    
    df = pd.read_excel('.\data\AR6_Scenarios_Database_metadata_indicators_v1.1.xlsx', sheet_name='meta_Ch3vetted_withclimate')

    # Define the columns of the dataframe
    cols = ['Scenario', 'Category', 'IMP_marker']

    # Extracts the IMPs
    df = df.loc[df['Category'].isin([category]), cols]
    df = df[df['IMP_marker'] != 'non-IMP']
    IMP_Scen = df['Scenario']
    IMP_Scen = IMP_Scen.values.tolist()

    IMP = df.drop(columns=['Category'])
    IMP = {str(key): 'IMP-' + value for key, value in zip(IMP.iloc[:, 0], IMP.iloc[:, 1])}
    
    return IMP_Scen, IMP


# %% [markdown]
# The following variables are either those given in Tables 3.2 and 3.4 of IPCC AR6 WGIII Chapter 3 (([Riahi et al., 2023](https://www.cambridge.org/core/books/climate-change-2022-mitigation-of-climate-change/mitigation-pathways-compatible-with-longterm-goals/7C750344E39ECA3BD5CB14156FCEEFE9)) or are furtherly computed to retrieve these variables.

# %%
# AR6 variables to be processed.
variables = ['AR6 climate diagnostics|Infilled|Emissions|Kyoto Gases (AR6-GWP100)',
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

# %%
# Load the AR6 Scenarios Database for a given category and set of variables
category = 'C1'
df = load_data(category,variables)
IMP_Scen, IMP = load_IMP(category)

# %%
# Check that the number of scenarios within the explored category matches the IPCC records.s
df[['Model', 'Scenario']].drop_duplicates().shape[0]

# %% [markdown]
# ## Electricity share of final energy (ESFE)

# %%
# Filter necessary variables to compute the ratio of electricity in final energy demand globally
var = ['Final Energy', 'Final Energy|Electricity']
esfe = df.loc[df['Variable'].isin(var)]

# %%
#Calculate the ratio of electricity in final energy
esfe = pd.pivot_table(esfe, columns='Variable', index=['Model','Scenario','Year'], values='Value').reset_index().rename_axis(columns=None)
esfe['Value']=esfe['Final Energy|Electricity']/esfe['Final Energy']
esfe = esfe.drop(columns=['Final Energy','Final Energy|Electricity'])

# %%
# Extract the values for IMPs only
esfe_imp = esfe.loc[esfe['Scenario'].isin(IMP_Scen), ['Scenario', 'Year', 'Value']]
esfe_imp['Scenario'] = esfe_imp['Scenario'].replace(IMP)

# %%
#Calculates the median and the 5th and 95th percentiles
centiles = esfe.groupby(['Year'])['Value'].quantile([0.05, 0.50, 0.95]).unstack(level=-1).reset_index()
centiles.columns = ['Year', '5th', 'Median', '95th']
centiles
esfe = pd.melt(centiles, id_vars=['Year'], var_name='Scenario', value_name='Value')

# %%
# Merge the centiles with the IMPs
esfe = pd.merge(esfe, esfe_imp, how='outer', sort='Scenario').sort_values(by=['Scenario','Year'], ascending=[False, True])

# %% [markdown]
# ## Greenhouse gases (GHG)

# %%
# Filter only the necessary variable for GHG emissions
var = ['AR6 climate diagnostics|Infilled|Emissions|Kyoto Gases (AR6-GWP100)']
ghg = df.loc[df['Variable'].isin(var)]

# %%
# Extract the values for IMPs only
ghg_imp = ghg.loc[ghg['Scenario'].isin(IMP_Scen), ['Scenario', 'Year', 'Value']]
ghg_imp['Scenario'] = ghg_imp['Scenario'].replace(IMP)

# %%
# Calculates the median and the 5th and 95th percentiles
centiles = ghg.groupby(['Year'])['Value'].quantile([0.05, 0.50, 0.95]).unstack(level=-1).reset_index()
centiles.columns = ['Year', '5th', 'Median', '95th']
centiles
ghg = pd.melt(centiles, id_vars=['Year'], var_name='Scenario', value_name='Value')

# %%
# Merge the centiles with the IMPs
ghg = pd.merge(ghg, ghg_imp, how='outer', sort='Scenario').sort_values(by=['Scenario','Year'], ascending=[False, True])
ghg['Value'] = ghg['Value'].round(0)/1000 # to obtain values in Gt

# %% [markdown]
# ## Final energy demand (FED)

# %%
# Filter only the necessary variable
var = ['Final Energy']
fed = df.loc[df['Variable'].isin(var)]

# %%
# Extract the values for IMPs only
fed_imp = fed.loc[fed['Scenario'].isin(IMP_Scen), ['Scenario', 'Year', 'Value']]
fed_imp['Scenario'] = fed_imp['Scenario'].replace(IMP)

# %%
#Calculates the median and the 5th and 95th percentiles
centiles = fed.groupby(['Year'])['Value'].quantile([0.05, 0.50, 0.95]).unstack(level=-1).reset_index()
centiles.columns = ['Year', '5th', 'Median', '95th']
centiles
fed = pd.melt(centiles, id_vars=['Year'], var_name='Scenario', value_name='Value')

# %%
# Merge the centiles with the IMPs
fed = pd.merge(fed, fed_imp, how='outer', sort='Scenario').sort_values(by=['Scenario','Year'], ascending=[False, True])
fed['Value'] = fed['Value'].round(0)

# %% [markdown]
# ## Fossil CO<sub>2</sub> (CCSFOS)

# %%
# Filter only the necessary variable
var = ['Carbon Sequestration|CCS|Fossil']
ccsfos = df.loc[df['Variable'].isin(var)]

# %%
# Extract the values for IMPs only
ccsfos_imp = ccsfos.loc[ccsfos['Scenario'].isin(IMP_Scen), ['Scenario', 'Year', 'Value']]
ccsfos_imp['Scenario'] = ccsfos_imp['Scenario'].replace(IMP)

# %%
# Calculates the median and the 5th and 95th percentiles
centiles = ccsfos.groupby(['Year'])['Value'].quantile([0.05, 0.50, 0.95]).unstack(level=-1).reset_index()
centiles.columns = ['Year', '5th', 'Median', '95th']
centiles
ccsfos = pd.melt(centiles, id_vars=['Year'], var_name='Scenario', value_name='Value')

# %%
# Merge the centiles with the IMPs
ccsfos = pd.merge(ccsfos, ccsfos_imp, how='outer', sort='Scenario').sort_values(by=['Scenario','Year'], ascending=[False, True])
ccsfos['Value'] = ccsfos['Value'].round(0)/1000 # to obtain values in Gt

# %% [markdown]
# ## CO<sub>2</sub> intensity of electricity (CO2ELC)

# %%
# Filter variables needed to calculate the ratio of carbon content of electricity to electricity generation
var = ['Secondary Energy|Electricity','Emissions|CO2|Energy|Supply|Electricity']
co2elc = df.loc[df['Variable'].isin(var)]

# %%
#Calculate the carbon content of electricity
co2elc = pd.pivot_table(co2elc, columns='Variable', index=['Model','Scenario','Year'], values='Value').reset_index().rename_axis(columns=None)
co2elc['Value']=co2elc['Emissions|CO2|Energy|Supply|Electricity']/co2elc['Secondary Energy|Electricity']*3.6
co2elc = co2elc.drop(columns=var)

# %%
# Extract the values for IMPs only
co2elc_imp = co2elc.loc[co2elc['Scenario'].isin(IMP_Scen), ['Scenario', 'Year', 'Value']]
co2elc_imp['Scenario'] = co2elc_imp['Scenario'].replace(IMP)

# %%
#Calculates the median and the 5th and 95th percentiles
centiles = co2elc.groupby(['Year'])['Value'].quantile([0.05, 0.50, 0.95]).unstack(level=-1).reset_index()
centiles.columns = ['Year', '5th', 'Median', '95th']
centiles
co2elc = pd.melt(centiles, id_vars=['Year'], var_name='Scenario', value_name='Value')

# %%
# Merge the centiles with the IMPs
co2elc = pd.merge(co2elc, co2elc_imp, how='outer', sort='Scenario').sort_values(by=['Scenario','Year'], ascending=[False, True])
co2elc = co2elc.dropna(how='any')

# %% [markdown]
# ## Low-carbon share of primary energy (LCSPE)
# According to IPCC AR6, the low-carbon share of energy includes *renewables (including biomass, solar, wind, hydro, geothermal, ocean); fossil fuels when used with CCS; and, nuclear power.*

# %%
# Filter variables needed to calculate the low-carbon share of primary energy
var = ['Primary Energy','Primary Energy|Fossil|w/ CCS','Primary Energy|Nuclear','Primary Energy|Renewables (incl. Biomass)']
lcspe = df.loc[df['Variable'].isin(var)]

# %%
#Calculate the low-carbon share of primary energy
lcspe = pd.pivot_table(lcspe, columns='Variable', index=['Model','Scenario','Year'], values='Value').reset_index().rename_axis(columns=None)
lcspe.fillna(0)
lcspe['Value'] = (lcspe['Primary Energy|Fossil|w/ CCS']+lcspe['Primary Energy|Nuclear']+lcspe['Primary Energy|Renewables (incl. Biomass)'])/lcspe['Primary Energy']
lcspe.fillna(0)
lcspe = lcspe.drop(columns=var)
lcspe = lcspe.dropna(how='any')

# %%
# Extract the values for IMPs only
lcspe_imp = lcspe.loc[lcspe['Scenario'].isin(IMP_Scen), ['Scenario', 'Year', 'Value']]
lcspe_imp['Scenario'] = lcspe_imp['Scenario'].replace(IMP)

# %%
#Calculates the median and the 5th and 95th percentiles
centiles = lcspe.groupby(['Year'])['Value'].quantile([0.05, 0.50, 0.95]).unstack(level=-1).reset_index()
centiles.columns = ['Year', '5th', 'Median', '95th']
centiles
lcspe = pd.melt(centiles, id_vars=['Year'], var_name='Scenario', value_name='Value')

# %%
# Merge the centiles with the IMPs
lcspe = pd.merge(lcspe, lcspe_imp, how='outer', sort='Scenario').sort_values(by=['Scenario','Year'], ascending=[False, True])
lcspe = lcspe.dropna(how='any')

# %% [markdown]
# ## Non-energy GHG emissions (NONNRG)
# To retrieve non-energy GHG emissions the energy-related GHG emissions are deducted from the total GHG emissions, using IPCC AR6 global warming potentials to convert each GHG in CO<sub>2eq</sub>.

# %%
# Filter only necessary variables
var = ['Emissions|CO2','Emissions|CO2|Energy',
        'Emissions|CH4','Emissions|CH4|Energy',
        'Emissions|N2O','Emissions|N2O|Energy',
        'Emissions|F-Gases']
nonnrg = df.loc[df['Variable'].isin(var)]

# %%
#Calculate the non-energy GHG emissions
nonnrg = pd.pivot_table(nonnrg, columns='Variable', index=['Model','Scenario','Year'], values='Value').reset_index().rename_axis(columns=None)
nonnrg['Value'] = nonnrg['Emissions|CO2'] - nonnrg['Emissions|CO2|Energy'] + (nonnrg['Emissions|CH4'] - nonnrg['Emissions|CH4|Energy'])*29.8 + (nonnrg['Emissions|N2O'] - nonnrg['Emissions|N2O|Energy'])*273/1000 + nonnrg['Emissions|F-Gases']


# %%
# Extract the values for IMPs only
nonnrg_imp = nonnrg.loc[nonnrg['Scenario'].isin(IMP_Scen), ['Model','Scenario', 'Year', 'Value']]
nonnrg_imp['Scenario'] = nonnrg_imp['Scenario'].replace(IMP)
nonnrg_imp = nonnrg_imp.drop(columns=['Model'])

# %%
#Calculates the median and the 5th and 95th percentiles
centiles = nonnrg.groupby(['Year'])['Value'].quantile([0.05, 0.50, 0.95]).unstack(level=-1).reset_index()
centiles.columns = ['Year', '5th', 'Median', '95th']
centiles
nonnrg = pd.melt(centiles, id_vars=['Year'], var_name='Scenario', value_name='Value')

# %%
# Merge the centiles with the IMPs
nonnrg = pd.merge(nonnrg, nonnrg_imp, how='outer', sort='Scenario').sort_values(by=['Scenario','Year'], ascending=[False, True])
nonnrg = nonnrg.dropna(how='any')
nonnrg['Value'] = nonnrg['Value'].round(0)/1000 # to obtain values in Gt

# %% [markdown]
# ## CSV output

# %% [markdown]
# The file *constraints.csv* in thr output of this script becomes the input of the next script *02_tiam-fr_vs_constraints.py*

# %%
dfs = {'ghg': ghg, 'lcspe': lcspe, 'fed': fed, 'esfe': esfe,
       'co2elc': co2elc, 'ccsfos': ccsfos, 'nonnrg': nonnrg}
out = (pd.concat(dfs, names=['Variable']).reset_index('Variable')
        .pivot_table(index=['Scenario', 'Year'], columns='Variable', values='Value'))
out.to_csv(DATADIROUT / 'constraints.csv')

# %%
