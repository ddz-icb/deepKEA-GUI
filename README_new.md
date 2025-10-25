# fuzzyKEA

**Fuzzy Kinase Enrichment Analysis**

A professional bioinformatics tool for kinase enrichment analysis with fuzzy matching capabilities.

## Features

- **Fuzzy Matching**: Flexible position tolerance for phosphosite matching
- **Multiple Statistical Tests**: Fisher's Exact Test or Chi-Square Test
- **Multiple Testing Correction**: Benjamini-Hochberg (FDR), Benjamini-Yekutieli, or Bonferroni
- **Dual-Level Analysis**: Site-level and substrate-level enrichment
- **Interactive Visualization**: Dynamic bar plots for enrichment results
- **Professional UI**: Clean, modern interface designed for scientific applications

## Installation

### Prerequisites

- Python 3.8+
- Required packages (install via conda/pip):
  - dash
  - dash-bootstrap-components
  - pandas
  - plotly
  - scipy
  - statsmodels
  - tqdm

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/ddz-icb/deepKEA-GUI.git
   cd deepKEA-GUI
   ```

2. Install dependencies:
   ```bash
   conda env create -f env/EDA_DDZ_env.yaml
   conda activate <env_name>
   ```

3. Download required dataset:
   - Visit [PhosphoSitePlus](https://www.phosphosite.org/staticDownloads)
   - Download `Kinase_Substrate_Dataset`
   - Place as `assets/Kinase_Substrate_Dataset.txt`

## Usage

1. Start the application:
   ```bash
   python app.py
   ```

2. Open your browser to `http://localhost:8050`

3. Enter phosphosites in the format:
   ```
   UNIPROT_GENENAME_SITE
   ```
   Example:
   ```
   P06732_CKM_T108
   O15273_TCAP_S161
   ```

4. Configure analysis parameters:
   - **Position Tolerance**: Maximum position difference for fuzzy matching (0-10)
   - **Max Inferred Hits**: Limit imputed sites per kinase
   - **Amino Acid Matching**: Exact, S/T Similar, or Ignore
   - **Phosphorylatable Residues**: Select S, T, Y, H
   - **Statistical Test**: Fisher's Exact or Chi-Square
   - **Multiple Testing Correction**: FDR-BH, FDR-BY, or Bonferroni

5. Click "Start Analysis" to run enrichment analysis

6. View and download results

## Parameters

### Position Tolerance (Fuzzy Mode)
- **0**: Exact position matching only
- **1-10**: Allow position differences up to N amino acids

### Amino Acid Matching
- **Exact**: Match exact amino acid (e.g., S only matches S)
- **S/T Similar**: Treat serine and threonine as equivalent
- **Ignore**: Ignore amino acid type, match on position only

### Statistical Tests
- **Fisher's Exact Test**: Recommended for small sample sizes, exact p-values
- **Chi-Square Test**: For larger datasets, asymptotic approximation

### Multiple Testing Correction
- **Benjamini-Hochberg (FDR)**: Controls false discovery rate (recommended)
- **Benjamini-Yekutieli**: More conservative FDR control
- **Bonferroni**: Very conservative, controls family-wise error rate

## Output

### Site-Level Results
- **KINASE**: Kinase name
- **P_VALUE**: Raw p-value from statistical test
- **ADJ_P_VALUE**: Multiple testing corrected p-value
- **UPID**: UniProt ID (linked)
- **FOUND**: Number of hits in your input
- **SUB#**: Total number of known substrates

### Substrate-Level Results
- Aggregated by unique substrate (protein)
- Same columns as site-level

## Data

- **PhosphoSitePlus®**: Kinase-substrate relationships
  - Source: [PhosphoSitePlus](https://www.phosphosite.org)
  - Organism: Human
  - Last updated: September 14, 2024

## Version

- **Current Version**: 1.0.0-alpha
- **Status**: Active development

## Citation

If you use fuzzyKEA in your research, please cite:
```
[Citation to be added]
```

## License

[License to be added]

## Contact

For questions and support:
- **GitHub Issues**: https://github.com/ddz-icb/deepKEA-GUI/issues
- **Email**: [Contact to be added]

## Acknowledgments

- PhosphoSitePlus® for kinase-substrate data
- Dash framework for the interactive interface
