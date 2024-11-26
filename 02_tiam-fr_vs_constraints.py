# %%
import pandas as pd
import pathlib
import sqlite3

DATADIR = pathlib.Path('data')
DATADIROUT = pathlib.Path('outputs')
conn = sqlite3.connect(DATADIR / 'c1.db')

# %% [markdown]
# ## GHG

# %%
qs = """SELECT
   Scenario,
   Period as Year,
   SUM(
   CASE
      WHEN
         commodity = 'GHG'
      THEN
         PV
   END)/ 1000000 AS Value
FROM
   Var_Comnet
GROUP BY
   Scenario, Period;"""

df_ghg = pd.read_sql_query(qs, conn)

# %%
df_ghg

# %% [markdown]
# ## CCSFOS

# %%
qs = """SELECT
   Scenario,
   Period AS 'Year',
   SUM(PV)/1000000 AS 'Value'
FROM
   VAR_FOut
WHERE
   Process IN ('CCSDUMELCN', 'CCSDUMINDN', 'CCSDUMINDP', 'CCSDUMSUPN')
GROUP BY Scenario, Period

UNION

SELECT
   Scenario,
   '2020' AS 'Year',
   '0' AS Value
FROM
   VAR_FOut
WHERE
   Process IN ('CCSDUMELCN', 'CCSDUMINDN', 'CCSDUMINDP', 'CCSDUMSUPN')
GROUP BY
   Scenario, Year
ORDER BY
   Scenario, Year;"""

df_ccsfos = pd.read_sql_query(qs, conn)

# %%
df_ccsfos

# %% [markdown]
# ## LCSPE

# %%
qs = """SELECT
   Scenario,
   Period AS Year,
   'Low-carbon' AS 'Label',
   SUM(PV) AS Value
FROM
   VAR_FIn
WHERE 
   Process NOT LIKE ('TU_BIO%') AND 
   Commodity IN ('AGRSOL','COMSOL','RESSOL','ELCSOL',
                 'ELCNUC','ELCTDL','ELCWAV','ELCWIN',
                 'GEO','ELCHYD','INDHYD','INDREN','INDWIN',
                 'BIOARSH','BIOARSP','BIOBIN','BIOBMU',
                 'BIOCRP','BIOLOG','BIOOIL','BIOPRC',
                 'BIOWOOD')
GROUP BY
   Scenario,Label,Year

UNION ALL

SELECT
   Scenario,
   Period AS Year,
   'Fossil' AS 'Label',
   SUM(PV) AS Value 
FROM
   VAR_FIn 
WHERE 
   Process NOT LIKE ('TU_%') AND
   Process NOT LIKE ('UPR%') AND
   Commodity IN ('GASNGA','OILCRD','OILNGL',
                 'COABCO','COAHCO','MWSTNR')
GROUP BY
   Scenario,Label,Year

UNION ALL

SELECT
   Scenario,
   Period AS Year,
   'Low-carbon' AS 'Label',
   SUM(PV) AS Value 
FROM
   Var_FOut
WHERE
   Process IN ('UBIOSRCSLD100','UBIOSRCLIG100','UBIOCAGLIG100','UBIOMISLIG100','UBIOSWTLIG100')
GROUP BY
   Scenario,Label,Year

UNION ALL

SELECT
   Scenario,
   Period AS Year,
   'Low-carbon' AS 'Label',
   SUM(PV) AS Value 
FROM
   VAR_FIn
WHERE
   Commodity IN ('ELCCOA','ELCNGA','INDBFG','INDCOA','INDCOG','INDCOK','INDHFO','INDLPG',
                 'INDMWST','INDNGA','INDOIL','INDOVC','INDPTC','SUPCOA','SUPNGA',
                 'IISCOK','IISNGAS','IISCOA')
   AND (Process IN ('IISBCHCKBFCS01','IISCHRCAUD01',
                   'IISCHRCOAMXCS01','IISCOABFCS01',
                   'IISCRXCS01','IISCRXCS02',
                   'IISNGASBFCS01','IISNGBGUD01',
                   'IISNGBSNGMXCS01')
   OR Process LIKE 'HZ%'
   OR Process LIKE 'E%CC'
   OR Process LIKE 'EZ%'
   OR Process LIKE 'INM%MIX%CC')
GROUP BY
   Scenario,Label,Year;"""

df_lcspe = pd.read_sql_query(qs, conn)

# %%
df_lcspe = (df_lcspe.pivot_table(index=['Scenario', 'Year'], columns='Label', values='Value', aggfunc='sum')
                    .assign(Value=lambda x: x['Low-carbon'] / (x.pop('Low-carbon') + x.pop('Fossil')))
                    .reset_index().rename_axis(columns=None))
df_lcspe

# %% [markdown]
# ## FED

# %%
qs = """SELECT 
   Scenario, 
   Period as 'Year',
   Process,
   SUM(Pv)/1000 as 'Value' 
FROM 
   Var_Fin 
GROUP BY
   Scenario,
   Process,
   Period;"""

df_fed = pd.read_sql_query(qs, conn)

# %%
dmap = pd.read_csv(DATADIR / 'mapping.csv', sep=';').set_index('Commodity')['Label']
label = df_fed.pop('Process').map(dmap)
df_fed = df_fed.loc[label == 'Final energy process']
df_fed = df_fed.groupby(['Scenario', 'Year'], as_index=False).sum()
df_fed

# %% [markdown]
# ## CO2ELC

# %%
qs = """SELECT
   Scenario,
   Period AS Year,
   Commodity,
   SUM(PV) AS Value
FROM
   VAR_FOut
WHERE
   Commodity IN ('ELC')
GROUP BY
   Scenario, Period, Commodity

UNION

SELECT
   Scenario,
   Period AS Year,
   Commodity,
   SUM(PV) AS Value
FROM
   VAR_Comnet
WHERE
   Commodity IN ('ELCCO2N')
GROUP BY
   Scenario, Period, Commodity;"""

df_co2elc = pd.read_sql_query(qs, conn)

# %%
df_co2elc = (df_co2elc.pivot_table(index=['Scenario', 'Year'], columns='Commodity', values='Value')
                      .assign(Value=lambda x: x.pop('ELCCO2N') / x.pop('ELC') * 3.6)  # x3.6 to transform MWh to PJ
                      .reset_index().rename_axis(columns=None))
df_co2elc

# %% [markdown]
# ## ESFE

# %%
qs = """SELECT 
   Scenario,
   Period as 'Year',
   SUM(PV)/1000 as 'ELCFIN'
FROM VAR_FIn
WHERE Process IN ('FT_INDELC', 'FT_AGRELC', 'FT_COMELC', 'FT_RESELC', 'FT_TRAELC')
GROUP BY Scenario, Period;"""

df_esfe = pd.read_sql_query(qs, conn)

# %%
df_esfe = (df_esfe.merge(df_fed, on=['Scenario', 'Year'])
                  .assign(Value=lambda x: x.pop('ELCFIN') / x['Value']))
df_esfe

# %% [markdown]
# ## NONNRG

# %%
qs = """SELECT
   Scenario,
   Period as Year,
   SUM(
   CASE
      WHEN
         Commodity IN ('NONNRG') 
      THEN
         PV 
   END)/ 1000000 AS Value
FROM
   Var_Comnet 
GROUP BY
   Scenario, Period;"""

df_nonnrg = pd.read_sql_query(qs, conn)

# %%
df_nonnrg

# %% [markdown]
# ## Export

# %%
constraints = pd.read_csv(DATADIR / 'constraints.csv', index_col=['Scenario', 'Year'])

dfs = {'ghg': df_ghg, 'lcspe': df_lcspe, 'fed': df_fed, 'esfe': df_esfe,
       'co2elc': df_co2elc, 'ccsfos': df_ccsfos, 'nonnrg': df_nonnrg}

df = pd.concat({var: df.loc[df['Year'] != '2018'].set_index(['Scenario', 'Year'])['Value'] for var, df in dfs.items()}, axis=1)
df = pd.concat([constraints, df], axis=0, sort=False)[dfs.keys()]
df.to_csv(DATADIROUT / 'tiam-fr_vs_constraints.csv')
