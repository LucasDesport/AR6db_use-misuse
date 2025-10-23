# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.17.1
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
import numpy as np
from zipfile import ZipFile
import pathlib
import re

DATADIR = pathlib.Path('data')
OUTDIR1 = pathlib.Path('models/TIMES_UserConstraints')
OUTDIR2 = pathlib.Path('models/MAGICC_Inputs')
DATADIR.mkdir(exist_ok=True)
OUTDIR1.mkdir(exist_ok=True)
OUTDIR2.mkdir(exist_ok=True)


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
# The file *constraints.csv* in the output of this script becomes the input of the next script *02_tiam-fr_vs_constraints.py*

# %%
dfs = {'ghg': ghg, 'lcspe': lcspe, 'fed': fed, 'esfe': esfe,
       'co2elc': co2elc, 'ccsfos': ccsfos, 'nonnrg': nonnrg}
out = (pd.concat(dfs, names=['Variable']).reset_index('Variable')
        .pivot_table(index=['Scenario', 'Year'], columns='Variable', values='Value', sort=False))
out.to_csv(OUTDIR1 / 'constraints.csv')

# %% [markdown]
# # Processing emission variables only

# %% [markdown]
# ## This other processing is to extract percentiles for emission variables only to be submitted to the MAGICC emulator.

# %% jupyter={"source_hidden": true}
# The following dictonnary is used in the function load_ar6_emissions so the nomenclature of the AR6 Scenarios Database matches that of MAGICC
emission_units = {
    "Emissions|BC": "Mt BC / yr",
    "Emissions|CH4": "Mt CH4 / yr",
    "Emissions|CO": "Mt CO / yr",
    "Emissions|CO2|MAGICC AFOLU": "Mt CO2 / yr",
    "Emissions|CO2|MAGICC Fossil and Industrial": "Mt CO2 / yr",
    "Emissions|NH3": "Mt NH3 / yr",
    "Emissions|NOx": "Mt NOx / yr",
    "Emissions|OC": "Mt OC / yr",
    "Emissions|Sulfur": "Mt SO2 / yr",
    "Emissions|VOC": "Mt VOC / yr",
    "Emissions|C2F6": "kt C2F6 / yr",
    "Emissions|C3F8": "kt C3F8 / yr",
    "Emissions|C4F10": "kt C4F10 / yr",
    "Emissions|C5F12": "kt C5F12 / yr",
    "Emissions|PFC|C6F14": "kt C6F14 / yr",
    "Emissions|C7F16": "kt C7F16 / yr",
    "Emissions|C8F18": "kt C8F18 / yr",
    "Emissions|CCl4": "kt CCl4 / yr",
    "Emissions|CF4": "kt CF4 / yr",
    "Emissions|CFC11": "kt CFC11 / yr",
    "Emissions|CFC113": "kt CFC113 / yr",
    "Emissions|CFC114": "kt CFC114 / yr",
    "Emissions|CFC115": "kt CFC115 / yr",
    "Emissions|CFC12": "kt CFC12 / yr",
    "Emissions|CH2Cl2": "kt CH2Cl2 / yr",
    "Emissions|CH3Br": "kt CH3Br / yr",
    "Emissions|CH3CCl3": "kt CH3CCl3 / yr",
    "Emissions|CH3Cl": "kt CH3Cl / yr",
    "Emissions|CHCl3": "kt CHCl3 / yr",
    "Emissions|HCFC141b": "kt HCFC141b / yr",
    "Emissions|HCFC142b": "kt HCFC142b / yr",
    "Emissions|HCFC22": "kt HCFC22 / yr",
    "Emissions|HFC125": "kt HFC125 / yr",
    "Emissions|HFC134a": "kt HFC134a / yr",
    "Emissions|HFC143a": "kt HFC143a / yr",
    "Emissions|HFC152a": "kt HFC152a / yr",
    "Emissions|HFC227ea": "kt HFC227ea / yr",
    "Emissions|HFC23": "kt HFC23 / yr",
    "Emissions|HFC236fa": "kt HFC236fa / yr",
    "Emissions|HFC245fa": "kt HFC245fa / yr",
    "Emissions|HFC32": "kt HFC32 / yr",
    "Emissions|HFC365mfc": "kt HFC365mfc / yr",
    "Emissions|HFC|HFC43-10": "kt HFC4310mee / yr",
    "Emissions|Halon1202": "kt Halon1202 / yr",
    "Emissions|Halon1211": "kt Halon1211 / yr",
    "Emissions|Halon1301": "kt Halon1301 / yr",
    "Emissions|Halon2402": "kt Halon2402 / yr",
    "Emissions|N2O": "kt N2O / yr",
    "Emissions|NF3": "kt NF3 / yr",
    "Emissions|SF6": "kt SF6 / yr",
    "Emissions|SO2F2": "kt SO2F2 / yr",
    "Emissions|cC4F8": "kt cC4F8 / yr"
}


# %%
def load_ar6_emission_percentiles(cat):
    """
    Compute 5th, 50th, and 95th percentiles of AR6 emissions
    across all models and scenarios for each variable and year.
    Saves three CSVs (p5, p50, p95) in DATADIR.
    """
    archive = DATADIR / "1668008312256-AR6_Scenarios_Database_World_v1.1.csv.zip"
    filename = "AR6_Scenarios_Database_World_v1.1.csv"

    variables = ['Emissions|BC', 'Emissions|C2F6', 'Emissions|PFC|C6F14', 'Emissions|CF4', 'Emissions|CH4', 'Emissions|CO',
            'Emissions|CO2|AFOLU', 'Emissions|CO2|Energy and Industrial Processes', 'Emissions|HFC|HFC125', 'Emissions|HFC|HFC134a',
            'Emissions|HFC|HFC143a', 'Emissions|HFC|HFC227ea', 'Emissions|HFC|HFC23', 'Emissions|HFC|HFC245fa',
            'Emissions|HFC|HFC32', 'Emissions|HFC|HFC43-10', 'Emissions|N2O', 'Emissions|NH3', 'Emissions|NOx',
            'Emissions|OC', 'Emissions|SF6', 'Emissions|Sulfur', 'Emissions|VOC'
            ]

    year_cols = [str(2015)] + [str(i) for i in range(2020, 2101, 10)]
    cols = ['Variable', 'Region', 'Unit'] + year_cols

    # Import the database and metadata of scenarios and a subset of variables
    with ZipFile(archive) as zipfile:
        # Process database
        cols = ['Model', 'Scenario', 'Region', 'Variable', 'Unit'] + [str(2015)] + [str(i) for i in range(2020, 2101, 10)]
        data = pd.read_csv(zipfile.open('AR6_Scenarios_Database_World_v1.1.csv'), usecols=cols)        
        df = data[(data['Variable'].isin(variables)) & (data['Region'] == 'World')].copy()

        # Process metadata
        cols = ['Model', 'Scenario', 'Category']
        meta = pd.read_excel(zipfile.open('AR6_Scenarios_Database_metadata_indicators_v1.1.xlsx'), sheet_name='meta_Ch3vetted_withclimate', usecols=cols)

    # Combine dataframes
    cols = ['Model', 'Scenario', 'Region', 'Variable', 'Unit', 'Year', 'Value', 'Category']
    df = meta.merge(df, on=['Model', 'Scenario'], how='right')
    df = pd.melt(df, id_vars=df.columns[:6], var_name='Year', value_name='Value')

    df = df[df['Category'] == cat].drop(columns='Category')

    # Adjusting variables names to match MAGICC inputs template
    df.loc[:, "Variable"] = df["Variable"].replace({
                                "Emissions|PFC|C6F14": "Emissions|C6F14",
                                "Emissions|CO2|AFOLU": "Emissions|CO2|MAGICC AFOLU",
                                "Emissions|CO2|Energy and Industrial Processes": "Emissions|CO2|MAGICC Fossil and Industrial",
                                "Emissions|HFC|HFC125": "Emissions|HFC125",
                                "Emissions|HFC|HFC134a": "Emissions|HFC134a",
                                "Emissions|HFC|HFC143a": "Emissions|HFC143a",
                                "Emissions|HFC|HFC227ea": "Emissions|HFC227ea",
                                "Emissions|HFC|HFC23": "Emissions|HFC23",
                                "Emissions|HFC|HFC245fa": "Emissions|HFC245fa",
                                "Emissions|HFC|HFC32": "Emissions|HFC32",
                                "Emissions|HFC|HFC43-10": "Emissions|HFC4310mee"
                                })

    df.loc[:, "Unit"] = df["Unit"].replace({
                               "kt HFC43-10/yr": "kt HFC4310mee / yr"
                              })

    # Pivot dataframe
    cols = ['Model', 'Scenario', 'Region', 'Variable', 'Unit']
    df = df.pivot_table(index=cols, columns='Year', values='Value').reset_index()

    # Convert year columns to numeric
    for col in year_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    # Percentile computation
    def percentile(col, q):
        valid = col.dropna().to_numpy()
        if valid.size == 0:
            return np.nan
        return np.percentile(valid, q)

    # Group by variable and unit
    grouped = df.groupby(['Variable', 'Unit'])[year_cols]

    # Apply aggregation for each percentile
    df_p5  = grouped.aggregate(lambda col: percentile(col, 5)).reset_index()
    df_p50 = grouped.aggregate(lambda col: percentile(col, 50)).reset_index()
    df_p95 = grouped.aggregate(lambda col: percentile(col, 95)).reset_index()

    # Name columns properly
    df_p5.columns  = ['Variable','Unit'] + year_cols
    df_p50.columns = ['Variable','Unit'] + year_cols
    df_p95.columns = ['Variable','Unit'] + year_cols

    # Add metadata columns in consistent order
    for label, df_out in zip(['p5','p50','p95'], [df_p5, df_p50, df_p95]):
        df_out['model'] = f'AR6_{cat}'
        df_out['region'] = 'World'
        df_out['scenario'] = label
        df_out.rename(columns={'Variable':'variable','Unit':'unit'}, inplace=True)
        df_out = df_out[['model','region','scenario','unit','variable'] + year_cols]
        # save each
        df_out.to_csv(OUTDIR2 / f"AR6_{cat}_emissions_{label}.csv", index=False)


# %%
df2 = load_ar6_emission_percentiles('C1')


# %% [markdown]
# ## This last function can be used to extract emissions from a given scenario and model

# %%
def load_ar6_emissions(model, scen):
    # AR6 variables to be processed
    archive = DATADIR / "1668008312256-AR6_Scenarios_Database_World_v1.1.csv.zip"

    variables = ['Emissions|BC', 'Emissions|C2F6', 'Emissions|PFC|C6F14', 'Emissions|CF4', 'Emissions|CH4', 'Emissions|CO',
            'Emissions|CO2|AFOLU', 'Emissions|CO2|Energy and Industrial Processes', 'Emissions|HFC|HFC125', 'Emissions|HFC|HFC134a',
            'Emissions|HFC|HFC143a', 'Emissions|HFC|HFC227ea', 'Emissions|HFC|HFC23', 'Emissions|HFC|HFC245fa',
            'Emissions|HFC|HFC32', 'Emissions|HFC|HFC43-10', 'Emissions|N2O', 'Emissions|NH3', 'Emissions|NOx',
            'Emissions|OC', 'Emissions|SF6', 'Emissions|Sulfur', 'Emissions|VOC'
            ]

    # Import the database and metadata of scenarios and a subset of variables
    with ZipFile(archive) as zipfile:
        # Process database
        cols = ['Model', 'Scenario', 'Region', 'Variable', 'Unit'] + [str(2015)] + [str(i) for i in range(2020, 2101, 10)]
        data = pd.read_csv(zipfile.open('AR6_Scenarios_Database_World_v1.1.csv'), usecols=cols)        
        df = data[(data['Variable'].isin(variables)) & (data['Model'] == model) & (data['Scenario'] == scen)].copy()

        # If a variable is missing, insert it and set 0 values for each period
        df['Variable'] = df['Variable'].astype(str)
        for var in variables:
            if var not in df['Variable'].values:
                year_cols = [col for col in df.columns if col.isdigit()]
                new_row = {
                    "Model": model,   # or use the appropriate values from df
                    "Region": "World",
                    "Scenario": scen,
                    "Unit": emission_units.get(var, "Unknown variable"),
                    "Variable": var,
                }
                for col in year_cols:
                    new_row[col] = 0.0
                    
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

        # Adjusting variables names to match MAGICC inputs template
        df.loc[:, "Variable"] = df["Variable"].replace({
                                    "Emissions|PFC|C6F14": "Emissions|C6F14",
                                    "Emissions|CO2|AFOLU": "Emissions|CO2|MAGICC AFOLU",
                                    "Emissions|CO2|Energy and Industrial Processes": "Emissions|CO2|MAGICC Fossil and Industrial",
                                    "Emissions|HFC|HFC125": "Emissions|HFC125",
                                    "Emissions|HFC|HFC134a": "Emissions|HFC134a",
                                    "Emissions|HFC|HFC143a": "Emissions|HFC143a",
                                    "Emissions|HFC|HFC227ea": "Emissions|HFC227ea",
                                    "Emissions|HFC|HFC23": "Emissions|HFC23",
                                    "Emissions|HFC|HFC245fa": "Emissions|HFC245fa",
                                    "Emissions|HFC|HFC32": "Emissions|HFC32",
                                    "Emissions|HFC|HFC43-10": "Emissions|HFC4310mee"
                                    })
        df.loc[:, "Unit"] = df["Unit"].replace({"Mt NO2/yr": "Mt NOx/yr"})

        df = df.rename(columns={'Model': 'model', 'Region': 'region', 'Scenario': 'scenario', 'Unit': 'unit', 'Variable': 'variable'})

        # Reoder columns
        first_cols = ['model', 'region', 'scenario', 'unit', 'variable']
        rest_cols = [col for col in df.columns if col not in first_cols]
        df = df[first_cols + rest_cols]

        df = df.sort_values(by='variable', ascending=True)
    
    # Sanitize arguments' names before saving
    csv_model = re.sub(r'[^\w\-\.]+', '_', model).replace('.', 'p')
    csv_scen  = re.sub(r'[^\w\-\.]+', '_', scen).replace('.', 'p')
    cache = OUTDIR2 / f"AR6_{csv_model}_{csv_scen}.csv"

    df.to_csv(cache, index=False)


# %%
load_ar6_emissions('AIM/Hub-Global 2.0','1.5C')

# %%
