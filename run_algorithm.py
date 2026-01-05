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
        if isinstance(csv_data, bytes):
            csv_data = csv_data.decode('utf-8')
        df = pds.read_csv(io.StringIO(csv_data.strip()))
        df.columns = [c.strip() for c in df.columns]
        if 'StudentEmail' not in df.columns or 'StudentRankings' not in df.columns:
            raise ValueError("Missing 'StudentEmail' or 'StudentRankings' column in CSV.")
    except Exception as e:
        return {"status": 400, "body": f"Error reading CSV data: {e}", "headers": {"Content-Type": "text/plain"}}

    all_activities = list(activity_capacity.keys())
    num_activities = len(all_activities)
    max_score = num_activities + 1  # Used for non-ranked activities

    # --- 2. BUILD SCORE MATRIX ---
    ranking_data = {}
    score_matrix = pds.DataFrame(0, index=df['StudentEmail'], columns=all_activities)

    for _, row in df.iterrows():
        email = row['StudentEmail']
        try:
            rankings = [r.strip().lower() for r in row['StudentRankings'].split(',')]
            ranking_data[email] = rankings
        except AttributeError:
            rankings = []
            ranking_data[email] = []
            
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

    final_cost_matrix = final_cost_matrix.fillna(max_score).astype(float)
    cost_array = final_cost_matrix.values

    # --- 5. RUN HUNGARIAN ALGORITHM ---
    row_ind, col_ind = linear_sum_assignment(cost_array)

    # --- 6. BUILD ASSIGNMENTS WITH RANK ---
    assignments = []
    assigned_counts = {act: 0 for act in all_activities}
    
    for r, c in zip(row_ind, col_ind):
        student_email = final_cost_matrix.index[r]
        assigned_activity = activity_map[c]
        cost_of_assignment = final_cost_matrix.iloc[r, c]

        # Only include assignments that are one of the student's choices (cost < max_score)
        if cost_of_assignment < max_score: 
            rankings_list = ranking_data.get(student_email, [])
            assigned_rank = None

            # Find rank (1-based) by matching normalized names
            for idx, activity_name in enumerate(rankings_list):
                if activity_name == assigned_activity.lower():
                    assigned_rank = idx + 1
                    break

            # If somehow not found despite cost < max_score, mark as 0 (unknown)
            if assigned_rank is None:
                assigned_rank = 0

            assignments.append({
                "StudentEmail": student_email, 
                "AssignedActivity": assigned_activity,
                "AssignedRank": assigned_rank
            })
            assigned_counts[assigned_activity] += 1

    # --- 7. CALCULATE REMAINING CAPACITY AND FORMAT OUTPUT ---
    assignments_df = pds.DataFrame(assignments)
    output = io.StringIO()

    # --- 7.0 HUMAN-READABLE, RANK-GROUPED OUTPUT ---
    assignments_df = pds.DataFrame(assignments)
    output = io.StringIO()

    if assignments_df.empty:
        output.write("No valid ranked assignments produced.\n")
    else:
        assignments_df["AssignedRank"] = (
            pds.to_numeric(assignments_df["AssignedRank"], errors="coerce")
            .fillna(0)
            .astype(int)
        )

        # Only ranked assignments
        ranked_df = assignments_df[assignments_df["AssignedRank"] > 0]

        max_rank = ranked_df["AssignedRank"].max()

        rank_labels = {
            1: "First",
            2: "Second",
            3: "Third"
        }

        for rank in range(1, max_rank + 1):
            label = rank_labels.get(rank, f"{rank}th")
            section_title = f"### {label} Choice Assignments ###\n"
            output.write(section_title)

            section_df = ranked_df[ranked_df["AssignedRank"] == rank] \
                .sort_values(by=["AssignedActivity", "StudentEmail"])

            if section_df.empty:
                output.write("None\n\n")
            else:
                section_df.to_csv(output, index=False)
                output.write("\n")

    # 7.1 Remaining capacity
    remaining_capacity = {}
    for act in all_activities:
        capacity = activity_capacity[act]
        assigned = assigned_counts[act]
        remaining_capacity[act] = capacity - assigned

    # 7.2 Summary table (remaining slots)
    summary_data = {
        "Activity": all_activities,
        "TotalCapacity": [activity_capacity[act] for act in all_activities],
        "AssignedStudents": [assigned_counts[act] for act in all_activities],
        "RemainingEmptySlots": [remaining_capacity[act] for act in all_activities]
    }
    summary_df = pds.DataFrame(summary_data)

    output.write('\n\n')
    output.write('### Summary of Remaining Activity Slots for Manual Allocation ###\n')
    summary_df.to_csv(output, index=False, header=True)

    # 7.3 Choice distribution segment (1st vs 2nd vs 3rd ... up to worst assigned)
    output.write('\n\n')
    output.write('### Choice Distribution of Assigned Students ###\n')

    if assignments_df.empty:
        output.write('No ranked assignments were produced.\n')
    else:
        valid_ranks = assignments_df.loc[assignments_df["AssignedRank"] > 0, "AssignedRank"]
        if valid_ranks.empty:
            output.write('No valid ranks found in assignments.\n')
        else:
            max_assigned_rank = int(valid_ranks.max())
            total_assigned = int((assignments_df["AssignedRank"] > 0).sum())

            # Count each rank from 1..max_assigned_rank (include zeros for missing ranks)
            rank_counts = (
                assignments_df.loc[assignments_df["AssignedRank"] > 0]
                .groupby("AssignedRank")
                .size()
                .reindex(range(1, max_assigned_rank + 1), fill_value=0)
            )

            choice_summary_df = pds.DataFrame({
                "ChoiceRank": rank_counts.index,
                "AssignedCount": rank_counts.values,
                "Ratio": [c / total_assigned if total_assigned else 0 for c in rank_counts.values],
                "Percent": [round((c / total_assigned) * 100, 2) if total_assigned else 0 for c in rank_counts.values],
            })

            # Optional: a compact "1:2:3" style ratio line
            ratio_line = ":".join(str(int(x)) for x in rank_counts.values)
            output.write(f"TotalAssigned={total_assigned}\n")
            output.write(f"CountsByChoiceRank (1..{max_assigned_rank}) = {ratio_line}\n\n")

            choice_summary_df.to_csv(output, index=False, header=True)

    final_csv_text = output.getvalue()

    return {
        "status": 200,
        "body": final_csv_text,
        "headers": {
            "Content-Type": "text/csv",
            "Content-Disposition": "attachment; filename=Allocations_with_Summary.csv"
        }
    }
