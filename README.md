
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
Student rankings are parsed. Score is assigned: higher rank = higher score. For N ranked activities, the first choice gets the score N, second gets N -1, etc. This socre is later converted ito a cost: Cost = Max_Score - Score

4. **Expand Matrix for Capacity**
The cost matrix is expanded by duplicating activity columns to match their capacity (e.g., "Water Polo" with capacity 5 becomes five columns: "Water Polo_1" to "Water Polo_5").

5. **Run Optimisation**
The Hungarian Algorithm (`linear_sum_assignment`) is applied to the final cost array to find the minimum total cost assignment between students (rows) and activity slots (columns).

6. **Generate Output**
The results are filtered to only include assignments where a student received a ranked activity (cost less than `max_score`) and compiled into an output CSV file named `Allocations.csv`.

# Input CSV Format

| Column Name | Description | Example Data |
| :--- | :--- | :--- |
| StudentEmail | Unique identifier for the student | `l.page@example.edu` |
| StudentRankings | A comma-separated string of the student's activity preferences, in order | `1st XI,Badminton,Rec football` |

## Example Input

The script returns a CSV file (`Allocations.csv`) containing the optimal assignment:

| Column Name | Description |
| :--- | :--- |
| **StudentEmail** | The email of the assigned student. |
| **AssignedActivity** | The activity slot the student was assigned to. |

**Example Output**

`StudentEmail,AssignedActivity
alice@example.com,Table Tennis
bob@example.com,CV`
