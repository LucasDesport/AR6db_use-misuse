# AR6 Scenarios Database use and misuse

The code extracts the [AR6 Scenarios Database hosted by IIASA](https://data.ece.iiasa.ac.at/ar6/#/downloads) ([Byers et al, 2022](https://doi.org/10.5281/zenodo.7197970)) to reproduce the 5<sup>th</sup>, 50<sup>th</sup>, and 95<sup>th</sup> percentile pathways for the variables of Tables 3.2 and 3.4 of the IPCC AR6 WGIII Chapter 3 ([Riahi et al., 2023](https://doi.org/10.1017/9781009157926.005)). These pathways are analyzed in the [Model for the Assessment of Greenhouse Gas Induced Climate Change (MAGICC)](https://magicc.org/) and the [French TIMES Integrated Assessment Model (TIAM-FR)](https://github.com/LucasDesport/tiam-fr), whose outputs are plotted with Python codes. The results aim at discussing potential pitfalls when using statistics to design mitigation pathways.

## Requirements

Two databases are required to run the code.
The code reads in the IPCC AR6 Scenarios Database, using both data and metadata of all climate variables which refers to the *AR6_Scenarios_Database_World_ALL_CLIMATE_v1.1.csv* hosted on [IIASA website](https://data.ece.iiasa.ac.at/ar6/#/downloads). The database can be downloaded as a guest. The zipped file should be uploaded in the ```data``` folder.
Additionally, the code imports the outputs of TIAM-FR from a database (.db) to be released on Zenodo but available on request for now. This database should also be put in the ```data``` folder.
For the calculations, the code requires standard Python packages like `pandas`, `openpyxl`, `matplotlib` and `pillow`.

## Usage and structure

Run the codes step by step from 01 to 04.  
- `01_AR6_treatment.py` processes the AR6 Scenarios Database from the ```data``` folder to extract only the variables of Table 3.2 and 3.4 of the report. The user can choose which category to analyze by filling the `category` attribute. The outputs of this code are collect in the ```outputs``` folder.
- `02_tiam-fr_vs_constraints.py` processes TIAM-FR outputs from the `data` folder and AR6 data from previous code to generate a merged database in the `outputs` folder.
- `03_paper_fig1` processes the AR6 Scenarios Database and the outputs of MAGICC to plot a figure representing temperature evolution of category-specified scenarios compared to statistical scenarios.
- `04_paper_fig2-3` processes the database generated in `02_tiam-fr_vs_constraints.py` to plot TIAM-FR outputs against AR6 Scenarios database for a specific category and each variable selected in `01_AR6_treatment.py` and generates Figures 2 and Figure 3 of the paper.

These scripts can be opened in JupyterLab using the `jupytext` extension.

The figures are collected in the `figures` folder.  
Additional files available in the `models` folder contain TIMES constraints and MAGICC inputs used to generate both models outputs.

## References
Byers, E. et al. AR6 Scenarios Database. Intergovernmental Panel on Climate Change https://doi.org/10.5281/zenodo.7197970 (2022).  
Riahi, K. et al. Mitigation Pathways Compatible with Long-term Goals. in Climate Change 2022 - Mitigation of Climate Change 295–408 (Cambridge University Press, 2023). https://doi:10.1017/9781009157926.005.
