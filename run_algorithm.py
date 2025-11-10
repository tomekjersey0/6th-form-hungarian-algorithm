import pandas as pds
from scipy.optimize import linear_sum_assignment
import io

def handler(pd, **kwargs): 
    activity_capacity = {
        "Water Polo": 5, "1st XI": 10, "Badminton": 8, "CV": 20, 
        "Rec football": 15, "Squash": 5, "Table Tennis": 10
    }
    
    try:
        csv_data = pd.steps['trigger']['event']['body']
        df = pds.read_csv(io.StringIO(csv_data.strip())) 
        if 'StudentEmail' not in df.columns or 'StudentRankings' not in df.columns:
             raise ValueError("Missing 'StudentEmail' or 'StudentRankings' column in CSV.")
    except Exception as e:
        return {"status": 400, "body": f"Error reading CSV data: {e}", "headers": {"Content-Type": "text/plain"}}
        
    all_activities = list(activity_capacity.keys())
    num_activities = len(all_activities)
    max_score = num_activities + 1 
    
    # 3. PARSE AND SCORE MATRIX GENERATION 
    score_matrix = pds.DataFrame(0, index=df['StudentEmail'], columns=all_activities)

    for index, row in df.iterrows():
        email = row['StudentEmail']
        try:
            rankings = [r.strip() for r in row['StudentRankings'].split(',')]
        except AttributeError:
            rankings = []
        total_ranks = len(rankings)

        for i, activity in enumerate(rankings):
            score = total_ranks - i
            if activity in score_matrix.columns:
                score_matrix.loc[email, activity] = score

    # 4. CONVERT SCORES TO COSTS
    cost_matrix_base = max_score - score_matrix
    
    # 5. EXPAND MATRIX FOR CAPACITY HANDLING
    expanded_cols = []
    activity_map = []  
    for act, cap in activity_capacity.items():
        for i in range(cap):
            expanded_cols.append(f"{act}_{i+1}")
            activity_map.append(act)

    final_cost_matrix = pds.DataFrame(index=df["StudentEmail"], columns=expanded_cols)
    
    for student in final_cost_matrix.index:
        for i, slot in enumerate(expanded_cols):
            activity = activity_map[i]
            final_cost_matrix.loc[student, slot] = cost_matrix_base.loc[student, activity]

    # --- CRITICAL TYPE FIX ---
    # Fill any remaining NaNs with the max cost (lowest preference)
    final_cost_matrix = final_cost_matrix.fillna(max_score)
    # Ensure the entire matrix is float type before conversion to NumPy array
    final_cost_matrix = final_cost_matrix.astype(float)
    # -------------------------

    cost_array = final_cost_matrix.values
    
    # 6. RUN HUNGARIAN ALGORITHM
    row_ind, col_ind = linear_sum_assignment(cost_array)

    # 7. BUILD FINAL RESULTS
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

    assignments_df = pds.DataFrame(assignments)
    
    output = io.StringIO()
    assignments_df.to_csv(output, index=False)
    final_csv_text = output.getvalue()
    
    # 8. RETURN HTTP RESPONSE
    return {
        "status": 200,
        "body": final_csv_text,
        "headers": {
            "Content-Type": "text/csv",
            "Content-Disposition": "attachment; filename=Allocations.csv"
        }
    }