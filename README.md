# citibike_safety
Analysis of NYC Citi Bike stations and cycling crashes

# Citi Bike Safety Analysis

This project analyzes the relationship between Citi Bike stations and cycling crashes in New York City, with the goal of promoting helmet usage among bike-share users.

## Project Overview

The project aims to:
1. Analyze the spatial distribution of Citi Bike stations across NYC
2. Analyze the distribution of bicycle crashes involving injuries and fatalities
3. Explore the relationship between station locations and crash patterns
4. Support a proposal for implementing a QR code-based helmet incentive system

## Features

This repository contains two main Python tools:

### 1. Citi Bike Station Analyzer
- Fetches and processes Citi Bike station data
- Provides station statistics and visualizations
- Creates interactive maps of the Citi Bike network

### 2. Bike Safety Analyzer
- Processes NYC Open Data crash information
- Analyzes proximity of crashes to Citi Bike stations
- Creates visualizations showing both datasets
- Generates detailed interactive maps with crash and station data

## Getting Started


### Prerequisites
- Python 3.x
- Required libraries: pandas, matplotlib, numpy, requests

### Installation
```bash
# Clone the repository
git clone https://github.com/yourusername/citibike-safety-analysis.git
cd citibike-safety-analysis

# Install required packages
pip install pandas matplotlib numpy requests
```

### Usage

#### Step 1: Generate Citi Bike station data
```bash
python citibike_analyzer.py
```
- Choose option 1 to load from API
- Use default URL: https://gbfs.citibikenyc.com/gbfs/en/station_information.json
- Save the data locally when prompted

#### Step 2: Analyze crash data
```bash
python bike_safety_analyzer.py
```
- Load crash data from NYC Open Data API or local file
- Follow the menu prompts to run different analyses
- Generate interactive maps showing both datasets

## Data Sources

- Citi Bike System Data: https://data.cityofnewyork.us/NYC-DOT/Citi-Bike-System-Data/vsnr-94wk
- NYPD Motor Vehicle Collisions: https://data.cityofnewyork.us/Public-Safety/Motor-Vehicle-Collisions-Crashes/h9gi-nx95

## Future Enhancements

- Heat map comparison of station density vs. crash density
- Analysis of crash severity in relation to station proximity
- Time-based analysis considering peak Citi Bike usage hours
- Integration of bike shop location data for helmet purchases

## Project Background

This project was inspired by a personal experience with cycling safety and aims to develop a practical solution to increase helmet usage among Citi Bike riders.

## Contact

[kateycox]
