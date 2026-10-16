// script.js  -  Step 8: makes the page come alive
// Job: check the form -> send it to Flask (/predict) -> show the answer.

// ---------- 1. Find the pieces of the page we need to control ----------
const form = document.getElementById("predict-form");
const predictBtn = document.getElementById("predict-btn");
const btnText = document.getElementById("btn-text");
const btnSpinner = document.getElementById("btn-spinner");
const formError = document.getElementById("form-error");

const placeholder = document.getElementById("placeholder");
const resultBox = document.getElementById("result");
const gradeValue = document.getElementById("grade-value");
const gradeBar = document.getElementById("grade-bar");
const categoryBadge = document.getElementById("category");
const suggestionsList = document.getElementById("suggestions");
const modelName = document.getElementById("model-name");
const metricsBody = document.getElementById("metrics-body");

// ---------- 2. The same rules the Flask backend uses ----------
const NUMBER_RULES = {
  Attendance_Pct:        { min: 0, max: 100, label: "Attendance (%)" },
  Study_Hours:           { min: 0, max: 16,  label: "Study hours per day" },
  Previous_Score:        { min: 0, max: 100, label: "Previous score" },
  Assignments_Completed: { min: 0, max: 10,  label: "Assignments completed" },
};

const BADGE_CLASS = {
  "Excellent": "badge-excellent",
  "Good": "badge-good",
  "Average": "badge-average",
  "Needs Improvement": "badge-improve",
};

// ---------- 3. Small helper functions ----------
function showFieldError(name, message) {
  document.getElementById("err-" + name).textContent = message;
  document.getElementById(name).classList.add("invalid");
}

function clearErrors() {
  formError.textContent = "";
  document.querySelectorAll(".error").forEach(function (el) { el.textContent = ""; });
  document.querySelectorAll(".invalid").forEach(function (el) { el.classList.remove("invalid"); });
}

function setLoading(isLoading) {
  predictBtn.disabled = isLoading;
  btnText.textContent = isLoading ? "Predicting..." : "Predict Grade";
  btnSpinner.classList.toggle("hidden", !isLoading);
}

// Check the form in the browser first. Returns the data, or null if something is wrong.
function readAndValidateForm() {
  clearErrors();
  const data = {};
  let ok = true;

  ["Gender", "Department"].forEach(function (name) {
    const value = document.getElementById(name).value;
    if (value === "") {
      showFieldError(name, "Please choose an option.");
      ok = false;
    } else {
      data[name] = value;
    }
  });

  Object.keys(NUMBER_RULES).forEach(function (name) {
    const rule = NUMBER_RULES[name];
    const raw = document.getElementById(name).value.trim();
    if (raw === "") {
      showFieldError(name, rule.label + " is required.");
      ok = false;
      return;
    }
    const value = Number(raw);
    if (Number.isNaN(value)) {
      showFieldError(name, rule.label + " must be a number.");
      ok = false;
    } else if (value < rule.min || value > rule.max) {
      showFieldError(name, rule.label + " must be between " + rule.min + " and " + rule.max + ".");
      ok = false;
    } else {
      data[name] = value;
    }
  });

  return ok ? data : null;
}

// ---------- 4. Show the answer from the server ----------
function showResult(result) {
  placeholder.classList.add("hidden");
  resultBox.classList.remove("hidden");

  gradeValue.textContent = result.predicted_grade.toFixed(1);
  gradeBar.style.width = (result.predicted_grade / result.out_of * 100) + "%";

  categoryBadge.textContent = result.category;
  categoryBadge.className = "badge " + (BADGE_CLASS[result.category] || "");

  // Suggestions (textContent keeps it safe: text is never treated as HTML)
  suggestionsList.innerHTML = "";
  result.suggestions.forEach(function (tip) {
    const li = document.createElement("li");
    li.textContent = tip;
    suggestionsList.appendChild(li);
  });

  // Model evaluation table
  modelName.textContent = result.model_name;
  metricsBody.innerHTML = "";
  Object.keys(result.metrics).forEach(function (name) {
    const m = result.metrics[name];
    const tr = document.createElement("tr");
    if (name === result.model_name) tr.classList.add("best");
    [name, m.MAE, m.RMSE, m.R2].forEach(function (cell) {
      const td = document.createElement("td");
      td.textContent = cell;
      tr.appendChild(td);
    });
    metricsBody.appendChild(tr);
  });

  // On phones the result sits below the form, so scroll down to it
  if (window.innerWidth <= 800) {
    resultBox.scrollIntoView({ behavior: "smooth", block: "start" });
  }
}

function resetResult() {
  resultBox.classList.add("hidden");
  placeholder.classList.remove("hidden");
  gradeBar.style.width = "0";
}

// ---------- 5. What happens when "Predict Grade" is pressed ----------
form.addEventListener("submit", async function (event) {
  event.preventDefault();                 // stop the page from reloading

  const data = readAndValidateForm();
  if (data === null) return;              // the browser already showed the problems

  setLoading(true);
  try {
    const response = await fetch("/predict", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    const result = await response.json();

    if (!response.ok) {
      // The server refused the input: show its messages
      if (result.fields) {
        Object.keys(result.fields).forEach(function (name) {
          showFieldError(name, result.fields[name]);
        });
      }
      formError.textContent = result.error || "Something went wrong. Please try again.";
      return;
    }

    showResult(result);
  } catch (error) {
    formError.textContent = "Could not reach the server. Is it still running?";
  } finally {
    setLoading(false);                    // always turn the spinner off
  }
});

// "Clear" button: wipe messages and results
form.addEventListener("reset", function () {
  clearErrors();
  resetResult();
});

// Remove a field's red error as soon as the user edits it
form.addEventListener("input", function (event) {
  const name = event.target.id;
  const msg = document.getElementById("err-" + name);
  if (msg) msg.textContent = "";
  event.target.classList.remove("invalid");
});