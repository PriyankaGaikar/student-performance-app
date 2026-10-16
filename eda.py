# eda.py  -  Step 2: load and clean the data
import pandas as pd

RAW_PATH = "data/student_performance_raw.csv"
CLEAN_PATH = "data/student_clean.csv"


def clean_data():
    # 1. LOAD the raw file
    df = pd.read_csv(RAW_PATH)
    print("Raw shape (rows, columns):", df.shape)

    # 2. REMOVE exact duplicate rows
    before = len(df)
    df = df.drop_duplicates()
    print("Duplicate rows removed:", before - len(df))

    # 3. FIX Gender: "male", " Female", "F", "M" -> "Male" / "Female"
    gender_map = {"male": "Male", "m": "Male", "female": "Female", "f": "Female"}
    df["Gender"] = df["Gender"].astype(str).str.strip().str.lower().map(gender_map)

    # 4. FIX Department: "cse", "Info Tech" -> "CSE", "IT"
    dept_map = {
        "cse": "CSE",
        "it": "IT",
        "info tech": "IT",
        "ece": "ECE",
        "mechanical": "Mechanical",
        "civil": "Civil",
    }
    df["Department"] = df["Department"].astype(str).str.strip().str.lower().map(dept_map)

    # 5. FIX Attendance_Pct: "72.1%" -> 72.1 ; "N/A" -> missing
    df["Attendance_Pct"] = (
        df["Attendance_Pct"].astype(str).str.replace("%", "", regex=False).str.strip()
    )
    df["Attendance_Pct"] = pd.to_numeric(df["Attendance_Pct"], errors="coerce")

    # 6. MARK impossible values as missing (they will be filled in step 7)
    df.loc[~df["Attendance_Pct"].between(0, 100), "Attendance_Pct"] = float("nan")
    df.loc[~df["Study_Hours"].between(0, 16), "Study_Hours"] = float("nan")
    df.loc[~df["Previous_Score"].between(0, 100), "Previous_Score"] = float("nan")

    # 7. FILL missing values
    number_cols = ["Attendance_Pct", "Study_Hours", "Previous_Score", "Assignments_Completed"]
    for col in number_cols:
        df[col] = df[col].fillna(df[col].median())
    for col in ["Gender", "Department"]:
        df[col] = df[col].fillna(df[col].mode()[0])

    # 8. CREATE the target G3 (grade out of 20) from Final_Score (out of 100)
    df["G3"] = (df["Final_Score"] / 5).round(1)

    # 9. KEEP only useful columns
    keep = ["Gender", "Department", "Academic_Year", "Attendance_Pct",
            "Study_Hours", "Previous_Score", "Assignments_Completed", "G3"]
    df = df[keep]

    # 10. SAVE and report
    df.to_csv(CLEAN_PATH, index=False)
    print("Clean shape (rows, columns):", df.shape)
    print("Missing values left:", int(df.isna().sum().sum()))
    print("Saved to", CLEAN_PATH)
    return df


if __name__ == "__main__":
    clean_df = clean_data()
    print()
    print(clean_df.head())