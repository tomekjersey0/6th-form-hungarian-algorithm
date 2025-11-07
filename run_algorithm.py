import json
import os
import pandas as pd
from scipy.optimize import linear_sum_assignment

# --- Config ---
input_csv = "ScoreMatrix.csv"   # your exported matrix
output_csv = "Assignments.csv"  # result
max_score = 8                   # max score used in scoring

# --- Load activity capacities from JSON ---
activity_file = "activities.json"  # path to your JSON file

if not os.path.exists(activity_file):
    raise FileNotFoundError(f"{activity_file} not found. Create it with activity capacities (see example).")

with open(activity_file, "r", encoding="utf-8") as f:
    activity_capacity = json.load(f)

if not isinstance(activity_capacity, dict):
    raise ValueError("activity_capacity.json must contain a JSON object mapping activity names to integer capacities.")

# validate capacities
for act, cap in activity_capacity.items():
    if not isinstance(cap, int) or cap < 1:
        raise ValueError(f"Capacity for activity '{act}' must be a positive integer (found: {cap}).")

# --- Read CSV ---
df = pd.read_csv(input_csv)

# Validate that all activities exist in CSV
missing_activities = set(activity_capacity.keys()) - set(df.columns)
if missing_activities:
    raise ValueError(f"Activities in JSON not found in CSV columns: {missing_activities}")

# --- Expand activities into individual slots ---
expanded_cols = []
activity_map = []  # maps expanded columns back to original activity
for act, cap in activity_capacity.items():
    for i in range(cap):
        expanded_cols.append(f"{act}_{i+1}")
        activity_map.append(act)

# --- Build cost matrix ---
cost_matrix = []
for idx, row in df.iterrows():
    student_scores = []
    for act in activity_map:
        # convert to cost: higher preference → lower cost
        student_scores.append(max_score - row[act])
    cost_matrix.append(student_scores)

cost_matrix = pd.DataFrame(cost_matrix, columns=expanded_cols, index=df["StudentEmail"])

# --- Run Hungarian algorithm ---
row_ind, col_ind = linear_sum_assignment(cost_matrix)

# --- Build results ---
assignments = []
for r, c in zip(row_ind, col_ind):
    student = cost_matrix.index[r]
    activity = activity_map[c]
    assignments.append({"StudentEmail": student, "AssignedActivity": activity})

assignments_df = pd.DataFrame(assignments)

# Optional: merge back original scores for reference
final_df = pd.merge(assignments_df, df, on="StudentEmail", how="left")

# --- Save to CSV ---
final_df.to_csv(output_csv, index=False)

print(f"Assignments saved to {output_csv}")