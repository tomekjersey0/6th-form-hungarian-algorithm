# 🧑‍💻 Activity Assignment Optimizer

This Python script uses the **Hungarian Algorithm** (via `scipy.optimize.linear_sum_assignment`) to solve the optimal assignment problem, matching a set of students to a limited number of activity slots based on their preference scores to maximize overall satisfaction.

## 🚀 How to Run the Script

### 1. Setup Environment

It's strongly recommended to use a virtual environment to manage dependencies.

1.  **Create Virtual Environment:**
    ```bash
    python3 -m venv venv
    ```
2.  **Activate Environment:**
    * **Mac/Linux:** `source venv/bin/activate`
    * **Windows (Command Prompt):** `venv\Scripts\activate`
3.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

### 2. Required Input Files

The script requires two files to be present in the same directory:

#### A. `ScoreMatrix.csv` (Student Preference Data)

This CSV contains all student preference scores.

* **Column 1:** Must be named `StudentEmail` (or similar unique identifier).
* **Remaining Columns:** Must be named exactly after the activities defined in `activities.json`.
* **Data:** The values represent the students' preference scores (e.g., 1-8). **A higher score means a higher preference.**

| StudentEmail | Football | Basketball | Table Tennis |
| :--- | :--- | :--- | :--- |
| student1@school.domain | 8 | 2 | 5 |
| student2@school.domain | 1 | 7 | 8 |

#### B. `activities.json` (Activity Capacity)

This JSON file defines the available activities and their maximum enrollment capacity.

* **Format:** A simple key-value object mapping the activity name (string) to its capacity (positive integer).
* **Note:** The keys must match the column names in `ScoreMatrix.csv`.

```json
{
  "Football": 5,
  "Basketball": 3,
  "Table Tennis": 7
}
```

### 3. Execution
With the environment active and the input files ready, run the main script:
```Bash
python assigner.py
```

### 📋 What to Edit in the Script
You will likely only need to modify the **Config** section at the top of the `assigner.py` file to fit your specific setup.

VariableDescriptioninput_csvThe name of your input CSV file (default: "ScoreMatrix.csv").output_csvThe name of the resulting assignment file (default: "Assignments.csv").max_scoreCRITICAL: The highest preference score used in your system (default: 8). This is used to convert preference (max-score) to cost (min-score). Must be set correctly.

### 💡 How the Optimization Works
The script is a solver for a **minimum cost assignment problem**:
1. It reads the student preference scores (ScoreMatrix.csv).
2. It converts the capacities in activities.json into individual 'slots' for the cost matrix. (e.g., 5 slots for "Coding Club").
3. It converts the preference score into a cost using the formula: Cost = max_score - Preference.
* *Result*: High preference (e.g., score 8) becomes low cost (e.g., $8-8=0$). Low preference becomes high cost.
4. The `linear_sum_assignment` function finds the assignment of students to slots that results in the lowest total cost (i.e., the highest total preference).

### 📊 Output
The script generates the `Assignments.csv` file, which includes:
* `StudentEmail`
* `AssignedActivity`
* All the original preference columns (for audit and easy reference).