# ---
# jupyter:
#   jupytext:
#     formats: py:percent,ipynb
#     notebook_metadata_filter: language_info
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.16.4
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
#   language_info:
#     codemirror_mode:
#       name: ipython
#       version: 3
#     file_extension: .py
#     mimetype: text/x-python
#     name: python
#     nbconvert_exporter: python
#     pygments_lexer: ipython3
#     version: 3.10.13
# ---

# %% [markdown]
# # Script for Figure 2 and Figure 3 of the manuscript

# %% editable=true slideshow={"slide_type": ""}
import pandas as pd
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.patheffects as mpe
import scienceplots
import pathlib

DATADIR = pathlib.Path('data')
FIGOUT = pathlib.Path('figures')

mpl.style.use(["science", "nature"])

# %%
# Import the values to be plotted
df = pd.read_csv(DATADIR / 'tiam-fr_vs_constraints.csv', parse_dates=['Year'])

filtered = ['base'] # Removes the 'base' scenario as it matches the median trajectory
df = df[~df['Scenario'].isin(filtered)]

# Maps different groups
gmap = {
    r'^IMP-.*': 'imp',
    r'Median|\d+th|base': 'stat',  # groups the median and the 5th and 95th percentiles
    r'^[bgc].*|tab2': 'emissions',  # groups the pathways constrained by a combination of median pathways related to GHG (see Table 2 of the manuscript)
    r'^[nf].*|tab4': 'energy', # groups the pathways constrained by a combination of median pathways related to energy (see Table 3 of the manuscript)
}
df['Group'] = df['Scenario'].replace(gmap, regex=True)

# %% [markdown]
# ## Plotting rules
#
# The median and IMP-* are always above all the other curves. The beams are always below: 5-95th < budget < energy < trend

# %% editable=true slideshow={"slide_type": ""}
# X and Y axis labels
chart_elements = {
    'ghg': {'title': 'GHG emissions', 'ylabel': 'GtCO$_{2,eq}$', 'fig_id': None},
    'lcspe': {'title': 'Low-carbon share of primary energy', 'ylabel': 'Ratio', 'fig_id': 'a'},
    'co2elc': {'title': 'CO$_2$ intensity of electricity', 'ylabel': 'MtCO$_2$.TWh$^{-1}$', 'fig_id': 'b'},
    'esfe': {'title': 'Electricity share of final energy', 'ylabel': 'Ratio', 'fig_id': 'c'},
    'fed': {'title': 'Final energy demand', 'ylabel': 'EJ', 'fig_id': 'd'},
    'ccsfos': {'title': 'Fossil CCS', 'ylabel': 'GtCO$_2$', 'fig_id': 'e'},
    'nonnrg': {'title': 'Non-energy GHG emissions', 'ylabel': 'GtCO$_{2,eq}$', 'fig_id': 'f'}
}

kwds = {
    # Default parameters for each group
    "stat": {"color": "lightgray", "zorder": 100},
    "imp": {"path_effects": [mpe.Stroke(linewidth=2, foreground='black'), mpe.Normal()]},
    "emissions": {"color": "lightblue", "linewidth": 0.8, "linestyle": "dotted"},
    "energy": {"color": "lightcoral", "linewidth": 0.8, "linestyle": "dotted"},

    # Group STAT
    'Median': {"color": "black", "linewidth": 1.5, "linestyle": "solid"},
    '5th': {"color": "gray", "linewidth": 0.5, "linestyle": "dotted"},
    '95th':  {"color": "gray", "linewidth": 0.5, "linestyle": "dotted"},

    # Groupe IMP (Illustrative mitigation pathways)
    'IMP-LD': {"color": "#daa258", "linewidth": 1.2},  # C1
    'IMP-Ren': {"color": "#b4b8d9", "linewidth": 1.2},  # C1
    'IMP-SP': {"color": "#e5cf00", "linewidth": 1.2},  # C1
    'IMP-Neg': {"color": "#a7b18f", "linewidth": 1.2},  # C2
    'IMP-GS': {"color": "#629ebf", "linewidth": 1.2},  # C3
    'IMP-Neg-2.0': {"color": "#e5cf00", "linewidth": 1.2},  # C3
    'IMP-Ren-2.0': {"color": "#b4b8d9", "linewidth": 1.2},  # C3

    # Groupe EMISSIONS (bleu)
    "tab2": {"color": "darkblue", "linestyle": "solid", "linewidth": 1},
   
    # Groupe ENERGY (rouge)
    "tab4": {"color": "darkred", "linestyle": "solid", "linewidth": 1},
}


# %%
def make_plot(var, df, fig_id):
    width, height = mpl.rcParams["figure.figsize"]
    fig, ax = plt.subplots(figsize=(width, height), dpi=300, constrained_layout=True)
    
    ax.set_title(chart_elements[var]['title'])
    if fig_id:
        ax.set_title(f'({fig_id})', loc='left', fontsize=10)

    piv = df.pivot_table(index=['Group', 'Scenario'], columns='Year', values=var)
    grp = piv.groupby('Group')

    # Legend
    lines = {}
    area = {}
    
    # STAT group
    df1 = grp.get_group('stat').droplevel('Group')
    lines['Median'] = ax.plot(df1.loc['Median'], **(kwds['stat'] | kwds['Median']))
    lines['5th'] = ax.plot(df1.loc['5th'], **(kwds['stat'] | kwds['5th']))
    lines['95th'] = ax.plot(df1.loc['95th'], **(kwds['stat'] | kwds['95th']))
    area['stat'] = ax.fill_between(df1.columns, df1.loc['5th'], df1.loc['95th'], color=kwds["stat"]["color"], alpha=0.5)
    
    # IMP group
    df1 = grp.get_group('imp').droplevel('Group')
    for scen, data in df1.iterrows():
        lines[scen] = ax.plot(data, **(kwds['imp'] | kwds[scen]))
    
    # ENERGY group
    df1 = grp.get_group('energy').droplevel('Group')
    area['energy'] = ax.fill_between(df1.columns, df1.min(axis=0), df1.max(axis=0), color=kwds["energy"]["color"], alpha=0.5)
    lines['tab4'] = ax.plot(df1.loc['tab4'], **(kwds['energy'] | kwds['tab4']))
    
    # EMISSIONS group
    df1 = grp.get_group('emissions').droplevel('Group')
    area['emissions'] = ax.fill_between(df1.columns, df1.min(axis=0), df1.max(axis=0), color=kwds["emissions"]["color"], alpha=0.5)
    lines['tab2'] = ax.plot(df1.loc['tab2'], **(kwds['emissions'] | kwds['tab2']))
    
    ax.set_ylabel(chart_elements[var]['ylabel'])
    ax.tick_params(axis='x', labelrotation=45)
    ax.tick_params(axis='x', which='minor', bottom=False, top=False)
    ax.set_xlim(pd.Timestamp("2020-01-01"), pd.Timestamp("2100-01-01"))
    ax.axhline(color='gray', linewidth=0.5)
    
    return fig, ax


# %% editable=true slideshow={"slide_type": ""}
FIGOUT.mkdir(exist_ok=True)

for var in chart_elements:
    subdf = df[['Scenario', 'Year', 'Group', var]].copy()

    fig, ax = make_plot(var, subdf, chart_elements[var].get('fig_id'))
    fig.savefig(FIGOUT / f"{var}.png", bbox_inches='tight')
    plt.show()

# %% [markdown]
# # Plot the legend

# %%
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle

scale = 1
width, height = mpl.rcParams["figure.figsize"]
fig_legend, ax_legend = plt.subplots(figsize=(width*scale, height*scale), dpi=300)

legend = {
    'Median pathway': Line2D([0], [0], **(kwds['stat'] | kwds['Median'])),
    'Ensemble of energy-constrained pathways': Rectangle((0, 0), 1, 1, **kwds['energy']),
    'IMP-Low Demand (IMP-LD)': Line2D([0], [0], **(kwds['imp'] | kwds['IMP-LD'])),

    'Full combination of median GHG-constrained pathways': Line2D([0], [0], **(kwds['emissions'] | kwds['tab2'])),
    '5th-95th percentile ensemble': Rectangle((0, 0), 1, 1, **kwds['stat']),
    'IMP-Sustainable Pathway (IMP-SP) ': Line2D([0], [0], **(kwds['imp'] | kwds['IMP-SP'])),

    'Full combination of median energy-constrained pathways': Line2D([0], [0], **(kwds['energy'] | kwds['tab4'])),
    'Ensemble of GHG-constrained pathways': Rectangle((0, 0), 1, 1, **kwds['emissions']),
    'IMP-Renewables (IMP-Ren)': Line2D([0], [0], **(kwds['imp'] | kwds['IMP-Ren'])),
}

ax_legend.legend(handles=legend.values(), labels=legend.keys(), loc='center', ncol=3)
ax_legend.axis('off')
plt.subplots_adjust(top=1e-6, bottom=0)
fig_legend.savefig(FIGOUT / "legend.png", bbox_inches='tight')

plt.show()
