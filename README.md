# DeepKEA-GUI

**DeepKEA-GUI** is a web-based Dash application for exploring kinase enrichment results in phosphoproteomic data. This tool is developed as part of a bachelor thesis in collaboration with the German Diabetes Center (DDZ).

## 🚀 Overview

The application allows users to upload and explore output tables from kinase enrichment tools. It provides interactive plots and filtering options to simplify the analysis of kinase-based enrichment data.

## 🛠️ Installation and Setup

Follow these steps to set up the application on your local machine.

---

### 1. Clone the Repository

```bash
git clone https://github.com/ddz-icb/deepKEA-GUI.git
cd deepKEA-GUI
```


### 2. Set Up the Conda Environment

A pre-configured Conda environment file is provided under `env/EDA_DDZ_env.yaml`.

#### Create the environment:

```bash
conda env create -f env/EDA_DDZ_env.
```

#### Activate the environment:
```bash
conda activate EDA_DDZ_env
```

#### Run the app:
```bash
python app.py
```
