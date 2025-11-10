
# 6th Form Hungarian Algorithm

This Python script, defined within a `handler` function, solves an activity assignment problem by matching students to their preferred activities while respecting capacity constraints. It uses the Hungarian Algorithm (via `scipy.optimize.linear_sum_assignment`) to find the assignment that minimizes the total cost (which corresponds to maximizing student preference).
## 🚀 Key Features

- **Preference-Based Assignment** - Converts student rankings into a cost matrix to prioritize higher-ranked activities
- **Capacity Constraints** - Models activity capacity by expanding the cost matrix, ensuring no activity is oversubscribed.
- **CSV Input/Output** - Reads student preferences from an incoming CSV and outputs the final assignments as a CSV file.
- **Robust Error Handling** - Includes checks for missing required columns in the input data.
## Requirements

The script relies on the following Python libraries:

- `Pandas` for data manipulation (reading CSVs, creating dataframes)
- `Scipy` for running the Hungarian algorithm


# How it Works

1. **Define Capacity**
A dictionary, `activity_capacity`, sets the maximum number of students for each activity (e.g. "Water Polo": 5).

2. **Load Input Data**
The handler expects the raw CSV data in the `pd.steps['trigger']['event']['body']` structure. This CSV is read into a pandas DataFrame.

3. **Calculate Preference Scores (Cost Matrix Base)**

