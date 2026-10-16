# visualize.py  -  Step 3: explore the clean data with numbers and charts
import os
import pandas as pd
import matplotlib
matplotlib.use("Agg")            # draw charts straight into files (no pop-up windows)
import matplotlib.pyplot as plt
import seaborn as sns

CLEAN_PATH = "data/student_clean.csv"
CHART_DIR = "static/charts"
os.makedirs(CHART_DIR, exist_ok=True)

sns.set_theme(style="whitegrid")

df = pd.read_csv(CLEAN_PATH)

# ---------- PART A: numbers ----------
print("=== Summary of the numbers ===")
print(df.describe().round(2))

print("\n=== Average G3 by Department ===")
print(df.groupby("Department")["G3"].mean().round(2).sort_values(ascending=False))

print("\n=== Average G3 by Gender ===")
print(df.groupby("Gender")["G3"].mean().round(2))

number_cols = ["Attendance_Pct", "Study_Hours", "Previous_Score",
               "Assignments_Completed", "Academic_Year", "G3"]
corr = df[number_cols].corr()
print("\n=== How strongly each column moves with G3 (-1 to +1) ===")
print(corr["G3"].drop("G3").round(2).sort_values(ascending=False))


# ---------- PART B: charts ----------
def save(name):
    plt.tight_layout()
    plt.savefig(f"{CHART_DIR}/{name}", dpi=120)
    plt.close()
    print("Saved", f"{CHART_DIR}/{name}")


# Chart 1: how are final grades spread out?
plt.figure(figsize=(7, 4))
sns.histplot(df["G3"], bins=20, kde=True, color="#4f46e5")
plt.title("Distribution of Final Grades (G3 out of 20)")
plt.xlabel("G3")
save("1_grade_distribution.png")

# Chart 2: heatmap of relationships between numbers
plt.figure(figsize=(7, 5))
sns.heatmap(corr, annot=True, fmt=".2f", cmap="coolwarm", center=0)
plt.title("Correlation Heatmap")
save("2_correlation_heatmap.png")

# Chart 3: study hours vs grade
plt.figure(figsize=(7, 4))
sns.regplot(data=df, x="Study_Hours", y="G3",
            scatter_kws={"alpha": 0.4}, line_kws={"color": "red"})
plt.title("Study Hours vs Final Grade")
save("3_study_hours_vs_g3.png")

# Chart 4: previous score vs grade
plt.figure(figsize=(7, 4))
sns.regplot(data=df, x="Previous_Score", y="G3",
            scatter_kws={"alpha": 0.4}, line_kws={"color": "red"})
plt.title("Previous Score vs Final Grade")
save("4_previous_score_vs_g3.png")

# Chart 5: grades by department
plt.figure(figsize=(7, 4))
sns.boxplot(data=df, x="Department", y="G3", hue="Department", legend=False)
plt.title("Final Grade by Department")
save("5_grade_by_department.png")

print("\nDone! Open the folder static/charts to see your 5 charts.")