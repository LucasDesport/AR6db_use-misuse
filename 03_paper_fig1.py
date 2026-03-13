# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.19.1
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
FIGOUT = pathlib.Path('figures')

from matplotlib.ticker import MultipleLocator
from matplotlib.ticker import AutoMinorLocator, NullLocator


# %%
def load_ar6_climate(cat):
    """Imports the database of scenarios according to the category specified by the user.
    """
    var = 'AR6 climate diagnostics|Surface Temperature (GSAT)|MAGICCv7.5.3|50.0th Percentile'
    
    df = (pd.read_csv(DATADIR / "AR6_Scenarios_Database_World_ALL_CLIMATE_subset_and_metadata_v1.1.csv")
             .loc[lambda x: x['Variable'].eq(var) & x['Category'].eq(cat) & x['Year'].ge(2000),
                  ['Model', 'Scenario', 'Year', 'Value']])

    return df


# %%
def load_magicc(cat):
    """Imports the precompiled 5th, 50th, 75th and 95th percentiles emissions pathways according to the category specified by the user."""
    var = 'Surface Temperature'
    year_cols = [str(i) for i in range(2000, 2101)]
    cols = ['scenario', 'variable', 'quantile'] + year_cols
    scenarios = ['p5', 'p50', 'p75', 'p95']

    dfs = []
    for scen in scenarios:
        df = pd.read_csv(DATADIR / f"{cat}_{scen}_magicc.csv", usecols=cols)

        # Filter for the correct variable and quantile
        df = df[(df['variable'] == var) & (df['quantile'] == 0.50)]

        # Ensure only the relevant columns are kept
        df = df[['scenario'] + year_cols]

        # Rename and melt
        df = df.rename(columns={'scenario': 'Scenario'})
        df = pd.melt(df, id_vars='Scenario', var_name='Year', value_name='Value')

        # Convert types
        df = df.astype({'Year': int, 'Value': float})

        dfs.append(df)

    return pd.concat(dfs, ignore_index=True)



# %%
# Load the AR6 Scenarios Database for a given category and set of variables
cat = 'C1'
ar6 = load_ar6_climate(cat)
magicc = load_magicc(cat)

# %%
(FIGOUT / "paper").mkdir(parents=True, exist_ok=True)
(FIGOUT / "zenodo").mkdir(parents=True, exist_ok=True)

width, height = mpl.rcParams["figure.figsize"]
fig, ax = plt.subplots(figsize=(width, height), dpi=300, constrained_layout=True)

pw_colors = {
    f'{cat} 5$^{{th}}$ pathway': 'blue',
    f'{cat} 75$^{{th}}$ pathway': 'orange',
    f'{cat} 95$^{{th}}$ pathway': 'red',
    f'{cat} median pathway': 'green'
}

magicc['Scenario'] = magicc['Scenario'].replace({
    f'{cat}_p5': f'{cat} 5$^{{th}}$ pathway',
    f'{cat}_p75': f'{cat} 75$^{{th}}$ pathway',
    f'{cat}_p95': f'{cat} 95$^{{th}}$ pathway',
    f'{cat}_p50': f'{cat} median pathway'})

# Re-plot
for scen, subset in magicc.groupby('Scenario', sort=False):
    color = pw_colors.get(scen)
    ax.plot(subset['Year'], subset['Value'], label=scen, zorder=1, color=color)

for i, (*_, subset) in enumerate(ar6.groupby(['Model', 'Scenario'])):
    label = f'{cat} scenarios' if i == 0 else '_nolegend_'
    ax.plot(subset['Year'], subset['Value'], color='gray', alpha=0.5, lw=0.2, label=label, zorder=0)


ax.legend(loc='lower left')
ax.set_ylabel('Temperature [K]')
ax.tick_params(axis='x', labelrotation=45)
ax.tick_params(axis='x', which='minor', bottom=False, top=False)
ax.set_xlim(2000, 2100)
ax.set_ylim(0, 2)
ax.set_xticks(range(2000, 2101, 10))

fig.savefig(FIGOUT / "paper" / "Figure1.png", bbox_inches='tight')
fig.savefig(FIGOUT / "zenodo" / "Figure1.png", bbox_inches='tight')
plt.show()


# %%

# %%
