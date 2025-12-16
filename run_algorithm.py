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
    max_score = num_activities + 1 # Used for non-ranked activities

    # --- 2. BUILD SCORE MATRIX ---
    # Store the actual list of rankings to look up the rank later
    ranking_data = {}
    
    score_matrix = pds.DataFrame(0, index=df['StudentEmail'], columns=all_activities)

    for index, row in df.iterrows():
        email = row['StudentEmail']
        try:
            # lower and strip for normalization
            rankings = [r.strip().lower() for r in row['StudentRankings'].split(',')]
            # Store the rankings list for later lookup
            ranking_data[email] = rankings
        except AttributeError:
            rankings = []
            ranking_data[email] = []
            
        total_ranks = len(rankings)

        for i, activity in enumerate(rankings):
            if activity in score_matrix.columns:
                # Score: total_ranks for 1st choice, total_ranks-1 for 2nd, etc.
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

    # fill NaNs (non-ranked activities) with max_score, and ensure numeric type
    final_cost_matrix = final_cost_matrix.fillna(max_score).astype(float)
    cost_array = final_cost_matrix.values

    # --- 5. RUN HUNGARIAN ALGORITHM ---
    # 
    row_ind, col_ind = linear_sum_assignment(cost_array)

    # --- 6. BUILD ASSIGNMENTS WITH RANK ---
    assignments = []
    # Dictionary to track the count of assignments per activity
    assigned_counts = {act: 0 for act in all_activities}
    
    for r, c in zip(row_ind, col_ind):
        student_email = final_cost_matrix.index[r]
        assigned_activity = activity_map[c]
        cost_of_assignment = final_cost_matrix.iloc[r, c]

        # Only include assignments that are one of the student's choices (cost < max_score)
        if cost_of_assignment < max_score: 
            
            # Determine the rank of the assigned activity
            try:
                rankings_list = ranking_data[student_email]
                i = -1
                for idx, activity_name in enumerate(rankings_list):
                    # Compare normalized names
                    if activity_name == assigned_activity.lower():
                        i = idx
                        break
                        
                assigned_rank = i + 1
            except Exception:
                assigned_rank = 'N/A'
            
            assignments.append({
                "StudentEmail": student_email, 
                "AssignedActivity": assigned_activity,
                "AssignedRank": assigned_rank # The new column
            })
            
            # Tally the successful assignment
            assigned_counts[assigned_activity] += 1

    # --- 7. CALCULATE REMAINING CAPACITY AND FORMAT OUTPUT ---
    assignments_df = pds.DataFrame(assignments)
    output = io.StringIO()
    
    # 7.1. Write the main allocation data
    assignments_df.to_csv(output, index=False)
    
    # 7.2. Calculate remaining capacity
    remaining_capacity = {}
    for act in all_activities:
        capacity = activity_capacity[act]
        assigned = assigned_counts[act]
        remaining_capacity[act] = capacity - assigned

    # 7.3. Prepare the summary table
    summary_data = {
        "Activity": all_activities,
        "TotalCapacity": [activity_capacity[act] for act in all_activities],
        "AssignedStudents": [assigned_counts[act] for act in all_activities],
        "RemainingEmptySlots": [remaining_capacity[act] for act in all_activities]
    }
    summary_df = pds.DataFrame(summary_data)

    # 7.4. Append the summary to the CSV output
    # Add a separator line for clarity
    output.write('\n\n')
    output.write('### Summary of Remaining Activity Slots for Manual Allocation ###\n') 
    
    # Write the summary DataFrame without the index and a header row (for manual readability)
    summary_df.to_csv(output, index=False, header=True)
    
    final_csv_text = output.getvalue()

    return {
        "status": 200,
        "body": final_csv_text,
        "headers": {
            "Content-Type": "text/csv",
            "Content-Disposition": "attachment; filename=Allocations_with_Summary.csv"
        }
    }
