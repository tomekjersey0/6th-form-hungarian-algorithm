import pandas as pds
from scipy.optimize import linear_sum_assignment
import io

def handler(pd, **kwargs): 
    activity_capacity = {
        "rugby": 30, 
        "rec football": 44, 
        "cv room": 25, 
        "basketball": 25, 
        "water polo": 18, 
        "table tennis": 24, 
        "squash": 12
    }

    # --- 1. READ CSV SAFELY ---
    try:
        csv_data = pd.steps['trigger']['event']['body']
        # decode if bytes
        if isinstance(csv_data, bytes):
            csv_data = csv_data.decode('utf-8')
        df = pds.read_csv(io.StringIO(csv_data.strip()))
        # strip column names
        df.columns = [c.strip() for c in df.columns]
        if 'StudentEmail' not in df.columns or 'StudentRankings' not in df.columns:
            raise ValueError("Missing 'StudentEmail' or 'StudentRankings' column in CSV.")
    except Exception as e:
        return {"status": 400, "body": f"Error reading CSV data: {e}", "headers": {"Content-Type": "text/plain"}}

    all_activities = list(activity_capacity.keys())
    num_activities = len(all_activities)
    max_score = num_activities + 1

    # --- 2. BUILD SCORE MATRIX ---
    score_matrix = pds.DataFrame(0, index=df['StudentEmail'], columns=all_activities)

    for index, row in df.iterrows():
        email = row['StudentEmail']
        try:
            rankings = [r.strip().lower() for r in row['StudentRankings'].split(',')]
        except AttributeError:
            rankings = []
        total_ranks = len(rankings)

        for i, activity in enumerate(rankings):
            if activity in score_matrix.columns:
                score_matrix.loc[email, activity] = total_ranks - i

    # --- 3. CONVERT SCORES TO COSTS ---
    cost_matrix_base = max_score - score_matrix

    # --- 4. EXPAND MATRIX FOR CAPACITY ---
    expanded_cols = []
    activity_map = []
    for act, cap in activity_capacity.items():
        for i in range(cap):
            expanded_cols.append(f"{act}_{i+1}")
            activity_map.append(act)

    final_cost_matrix = pds.DataFrame(index=df['StudentEmail'], columns=expanded_cols)

    for student in final_cost_matrix.index:
        for i, slot in enumerate(expanded_cols):
            activity = activity_map[i]
            final_cost_matrix.loc[student, slot] = cost_matrix_base.loc[student, activity]

    # fill NaNs and ensure numeric type
    final_cost_matrix = final_cost_matrix.fillna(max_score).astype(float)
    cost_array = final_cost_matrix.values

    # --- 5. RUN HUNGARIAN ALGORITHM ---
    row_ind, col_ind = linear_sum_assignment(cost_array)

    # --- 6. BUILD ASSIGNMENTS ---
    assignments = []
    for r, c in zip(row_ind, col_ind):
        student_email = final_cost_matrix.index[r]
        assigned_activity = activity_map[c]
        cost_of_assignment = final_cost_matrix.iloc[r, c]

        if cost_of_assignment < max_score: 
            assignments.append({
                "StudentEmail": student_email, 
                "AssignedActivity": assigned_activity
            })

    # --- 7. OUTPUT CSV ---
    assignments_df = pds.DataFrame(assignments)
    output = io.StringIO()
    assignments_df.to_csv(output, index=False)
    final_csv_text = output.getvalue()

    return {
        "status": 200,
        "body": final_csv_text,
        "headers": {
            "Content-Type": "text/csv",
            "Content-Disposition": "attachment; filename=Allocations.csv"
        }
    }
