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
# # Script to plot Figure 1 of the manuscript
# Figure 1 represents the temperature evolution (50<sup>th</sup> percentile of AR6 climate diagnostics) of the 97 scenarios of C1, compared to the temperature output of MAGICC ([Meinshausen et al., 2021](https://magicc.org/)) when submitting the combined emissions pathway for the median, 50<sup>th</sup> and 95<sup>th</sup> centiles. Users can leverage the code to replicate the figure with other categories.

# %%
import pandas as pd
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.patheffects as mpe
import scienceplots
import pathlib

mpl.style.use(["science", "nature"])
DATADIR = pathlib.Path('data')
MODELDIR = pathlib.Path('models/MAGICC_Inputs')
FIGOUT = pathlib.Path('figures')

from matplotlib.ticker import MultipleLocator
from matplotlib.ticker import AutoMinorLocator, NullLocator


# %%
def load_ar6(category):
    """Imports the database of scenarios according to the category specified by the user..
    """
    df = pd.read_parquet(DATADIR / 'AR6_Scenarios_Database_World_ALL_CLIMATE_v1.1_with_category.parquet') 

    # Define the columns of the dataframe
    cols = ['Model', 'Scenario', 'Region', 'Variable', 'Unit'] + [str(i) for i in range(1995, 2101, 1)]
    
    # Select pairs of models and scenarios belonging to the user-defined category
    cdict = pd.read_excel(DATADIR / 'AR6_Scenarios_Database_metadata_indicators_v1.1.xlsx', sheet_name='meta_Ch3vetted_withclimate')
    df = df.merge(cdict, on=['Model', 'Scenario'], how='left')
    df = df[df['Category'] == category]
    df = df.drop(columns=['Category'])

    df = df.loc[df['Variable'].isin(['AR6 climate diagnostics|Surface Temperature (GSAT)|MAGICCv7.5.3|50.0th Percentile']), cols]
    df = pd.melt(df, id_vars=cols[:5], var_name='Year', value_name='Value').sort_values(by=['Model','Scenario', 'Year'])
    df = df.drop(columns=['Variable','Region','Unit'])
    df = df.astype({'Year': "int", 'Value': "float"})

    return df.query('Year >= 2000')


# %%
def load_magicc(category):
    """Imports the precompiled 5th, 50th and 95th percentiles emissions pathways according to the category specified by the user.
    """
    cols =  ['climate_model', 'data_id', 'model', 'quantile', 'reference_period_end_year', 'reference_period_start_year', 'region', 'scenario', 'stage', 'todo', 'unit', 'variable']
    
    df5 = pd.read_csv(DATADIR / f'{category}_5th_magicc.csv')
    df5 = df5[df5['variable'] == 'Surface Temperature']
    df5 = pd.melt(df5, id_vars=cols, var_name='Year', value_name='Value')
    df5 = df5[['scenario','Year','Value']]
    df5 = df5.rename(columns={'scenario': 'Scenario'})

    df50 = pd.read_csv(DATADIR / f'{category}_med_magicc.csv')
    df50 = df50[df50['variable'] == 'Surface Temperature']
    df50 = pd.melt(df50, id_vars=cols, var_name='Year', value_name='Value')
    df50 = df50[['scenario','Year','Value']]
    df50 = df50.rename(columns={'scenario': 'Scenario'})

    df95 = pd.read_csv(DATADIR / f'{category}_95th_magicc.csv')
    df95 = df95[df95['variable'] == 'Surface Temperature']
    df95 = pd.melt(df95, id_vars=cols, var_name='Year', value_name='Value')
    df95 = df95[['scenario','Year','Value']]
    df95 = df95.rename(columns={'scenario': 'Scenario'})

    df = pd.concat([df5, df50, df95], ignore_index=True).astype({'Year': "int", 'Value': "float"})
    
    return df


# %%
# Load the AR6 Scenarios Database for a given category and set of variables
category = 'C1'
ar6 = load_ar6(category)
magicc = load_magicc(category)

# %%
DATADIROUT.mkdir(exist_ok=True)

fig, ax = plt.subplots(figsize=(5, 3), dpi=300)
plt.xlim(2000, 2100)
plt.ylim(0, 2)
ax.set_xticks(range(2000, 2101, 10))
ax.xaxis.set_minor_locator(plt.NullLocator()) 
ax.yaxis.set_major_locator(MultipleLocator(0.25))
ax.yaxis.set_minor_locator(MultipleLocator(0.05))

ax.legend()
ax.set_xlabel('Year', fontsize=10)
ax.set_ylabel('Temperature [K]', fontsize=10)

pw_colors = {
    str(category)+' 5$^{th}$ pathway': 'blue',
    str(category)+' 95$^{th}$ pathway': 'red',
    str(category)+' median pathway': 'green'
}

magicc['Scenario'] = magicc['Scenario'].replace(str(category)+'_5th', str(category)+' 5$^{th}$ pathway')
magicc['Scenario'] = magicc['Scenario'].replace(str(category)+'_95th', str(category)+' 95$^{th}$ pathway')
magicc['Scenario'] = magicc['Scenario'].replace(str(category)+'_med', str(category)+' median pathway')

for scenario in magicc['Scenario'].unique():
    subset = magicc[magicc['Scenario'] == scenario]
    color = pw_colors.get(scenario)
    ax.plot(subset['Year'], subset['Value'], label=scenario, zorder=1, color=color)

# Assign a unique label to the category-specified scenarios
for i, (*_, subset) in enumerate(ar6.groupby(['Model', 'Scenario'])):
    label = str(category)+' scenarios' if i == 0 else '_nolegend_'
    ax.plot(subset['Year'], subset['Value'], color='gray', alpha=0.5, label=label, zorder=0)

ax.legend(loc='lower left', fontsize=8)

plt.tight_layout()
plt.show()

fig.savefig(FIGOUT / "Figure1.png", bbox_inches='tight')


# %%
