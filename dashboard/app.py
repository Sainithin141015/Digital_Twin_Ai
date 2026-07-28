"""
FinLife AI — Dashboard (Module 6: Conversational AI & Visualization Dashboard)

Run with:  streamlit run dashboard/app.py
Talks to the FastAPI backend over HTTP -- set API_BASE_URL if it's not on localhost:8000.
"""
import os
from datetime import date

import requests
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

st.set_page_config(page_title="FinLife AI", page_icon="💠", layout="wide")


# ---------- API helpers ----------
def api_post(path, json=None, data=None, auth=True):
    headers = {"Authorization": f"Bearer {st.session_state.token}"} if auth and st.session_state.get("token") else {}
    r = requests.post(f"{API_BASE_URL}{path}", json=json, data=data, headers=headers)
    return r


def api_get(path, params=None):
    headers = {"Authorization": f"Bearer {st.session_state.token}"} if st.session_state.get("token") else {}
    r = requests.get(f"{API_BASE_URL}{path}", params=params, headers=headers)
    return r


# ---------- auth screen ----------
if "token" not in st.session_state:
    st.session_state.token = None

if not st.session_state.token:
    st.title("💠 FinLife AI")
    st.caption("Personal Finance · Study · Habit Intelligence — sign in to continue")

    tab_login, tab_register = st.tabs(["Log in", "Register"])

    with tab_login:
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Log in")
        if submitted:
            r = api_post("/auth/login", data={"username": email, "password": password}, auth=False)
            if r.status_code == 200:
                st.session_state.token = r.json()["access_token"]
                st.rerun()
            else:
                st.error(r.json().get("detail", "Login failed"))

    with tab_register:
        with st.form("register_form"):
            name = st.text_input("Name")
            email_r = st.text_input("Email", key="reg_email")
            password_r = st.text_input("Password", type="password", key="reg_pass")
            submitted_r = st.form_submit_button("Create account")
        if submitted_r:
            r = api_post("/auth/register", json={"name": name, "email": email_r, "password": password_r}, auth=False)
            if r.status_code == 201:
                st.success("Account created — switch to the Log in tab.")
            else:
                st.error(r.json().get("detail", "Registration failed"))

    st.stop()


# ---------- authenticated app ----------
with st.sidebar:
    st.title("💠 FinLife AI")
    if st.button("Log out"):
        st.session_state.token = None
        st.rerun()

tabs = st.tabs(["📊 Overview", "💰 Finance", "📚 Study", "✅ Habits", "🔮 Simulation", "💬 Chat"])

# ---- Overview ----
with tabs[0]:
    st.header("Overview")
    month = date.today().strftime("%Y-%m")
    summary_r = api_get(f"/finance/summary/{month}")
    habit_r = api_get("/habit/stats")
    study_r = api_get("/study/analysis")

    c1, c2, c3 = st.columns(3)
    if summary_r.status_code == 200:
        s = summary_r.json()
        c1.metric("This month's net savings", f"₹{s['net_savings']:.0f}", f"{s['savings_rate']*100:.1f}% rate")
    if habit_r.status_code == 200:
        habits = habit_r.json()
        avg_completion = (sum(h["completion_rate_last_30d"] for h in habits) / len(habits) * 100) if habits else 0
        c2.metric("Avg habit completion (30d)", f"{avg_completion:.0f}%")
    if study_r.status_code == 200:
        subjects = study_r.json()
        declining = sum(1 for a in subjects if a["score_trend"] == "declining")
        c3.metric("Subjects trending down", declining)

    st.info("Use the tabs above to log data, see forecasts, and run what-if scenarios. Try the Chat tab for natural-language questions.")

# ---- Finance ----
with tabs[1]:
    st.header("Financial Analysis & Forecasting")

    with st.expander("➕ Log a transaction"):
        with st.form("txn_form"):
            col1, col2, col3 = st.columns(3)
            t_type = col1.selectbox("Type", ["expense", "income"])
            category = col2.text_input("Category", "food")
            amount = col3.number_input("Amount", min_value=0.0, step=100.0)
            t_date = st.date_input("Date", value=date.today())
            if st.form_submit_button("Add"):
                r = api_post("/finance/transactions", json={
                    "type": t_type, "category": category, "amount": amount, "date": str(t_date),
                })
                st.success("Logged!") if r.status_code == 201 else st.error(r.text)

    history_r = api_get("/finance/history")
    if history_r.status_code == 200 and history_r.json():
        hist = history_r.json()
        months = [h["month"] for h in hist]
        fig = go.Figure()
        fig.add_bar(x=months, y=[h["total_income"] for h in hist], name="Income", marker_color="#1E2761")
        fig.add_bar(x=months, y=[h["total_expense"] for h in hist], name="Expense", marker_color="#E8A33D")
        fig.update_layout(barmode="group", title="Income vs Expense by Month")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No transactions yet — add some above.")

    if st.button("Generate 6-month forecast"):
        r = api_get("/finance/forecast", params={"months_ahead": 6})
        if r.status_code == 200:
            fc = r.json()
            fig2 = px.line(
                x=[f["month"] for f in fc], y=[f["projected_savings"] for f in fc],
                labels={"x": "Month", "y": "Projected Savings (₹)"}, title="Projected Savings",
            )
            fig2.update_traces(line_color="#1E2761")
            st.plotly_chart(fig2, use_container_width=True)

# ---- Study ----
with tabs[2]:
    st.header("Study & Productivity Intelligence")

    with st.expander("➕ Log a study session"):
        with st.form("study_form"):
            subject = st.text_input("Subject", "Math")
            duration = st.number_input("Duration (minutes)", min_value=1, value=60)
            focus = st.slider("Focus score", 1, 10, 7)
            if st.form_submit_button("Log session"):
                r = api_post("/study/sessions", json={"subject": subject, "duration_min": duration, "focus_score": focus})
                st.success("Logged!") if r.status_code == 201 else st.error(r.text)

    with st.expander("➕ Log an academic score"):
        with st.form("score_form"):
            subj2 = st.text_input("Subject", "Math", key="subj2")
            assessment = st.text_input("Assessment", "Quiz 1")
            score = st.slider("Score (%)", 0, 100, 75)
            if st.form_submit_button("Log score"):
                r = api_post("/study/records", json={"subject": subj2, "assessment_name": assessment, "score": score})
                st.success("Logged!") if r.status_code == 201 else st.error(r.text)

    analysis_r = api_get("/study/analysis")
    if analysis_r.status_code == 200 and analysis_r.json():
        df = analysis_r.json()
        fig = px.bar(df, x="subject", y="avg_academic_score", color="score_trend",
                     title="Average Score by Subject", color_discrete_map={
                         "improving": "#1E9E6C", "declining": "#D9534F", "steady": "#1E2761", "insufficient_data": "#CADCFC",
                     })
        st.plotly_chart(fig, use_container_width=True)

    if st.button("Generate study plan"):
        r = api_get("/study/plan")
        if r.status_code == 200:
            plan = r.json()
            if plan["items"]:
                st.table(plan["items"])
            else:
                st.warning("Log some sessions/scores first.")

# ---- Habits ----
with tabs[3]:
    st.header("Habit & Lifestyle Analytics")

    with st.expander("➕ Create a habit"):
        with st.form("habit_form"):
            hname = st.text_input("Habit name", "Exercise")
            hcat = st.text_input("Category", "health")
            if st.form_submit_button("Create"):
                r = api_post("/habit", json={"name": hname, "category": hcat})
                st.success("Created!") if r.status_code == 201 else st.error(r.text)

    habits_r = api_get("/habit")
    if habits_r.status_code == 200 and habits_r.json():
        habits = habits_r.json()
        names = [h["name"] for h in habits]
        chosen = st.selectbox("Log today's habit", names) if names else None
        if chosen and st.button("Mark completed today"):
            hid = next(h["id"] for h in habits if h["name"] == chosen)
            r = api_post(f"/habit/{hid}/logs", json={"completed": True})
            st.success("Logged!") if r.status_code == 201 else st.error(r.text)

    stats_r = api_get("/habit/stats")
    if stats_r.status_code == 200 and stats_r.json():
        stats = stats_r.json()
        fig = px.bar(stats, x="name", y="completion_rate_last_30d", title="30-Day Completion Rate", color="current_streak")
        st.plotly_chart(fig, use_container_width=True)

    insights_r = api_get("/habit/insights")
    if insights_r.status_code == 200:
        for i in insights_r.json().get("insights", []):
            st.write(i)

# ---- Simulation ----
with tabs[4]:
    st.header("Future Outcome Simulation Engine")
    with st.form("sim_form"):
        name = st.text_input("Scenario name", "Raise + expense cut")
        col1, col2, col3 = st.columns(3)
        extra_income = col1.number_input("Extra monthly income (₹)", value=0.0, step=500.0)
        extra_expense = col2.number_input("Extra monthly expense (negative = cut)", value=0.0, step=500.0)
        extra_study = col3.number_input("Extra study hrs/week", value=0.0, step=1.0)
        if st.form_submit_button("Run simulation"):
            r = api_post("/simulation/run", json={
                "scenario_name": name, "extra_monthly_income": extra_income,
                "extra_monthly_expense": extra_expense, "extra_study_hours_per_week": extra_study,
            })
            if r.status_code == 200:
                result = r.json()
                st.success(result["summary"])
                fc = result["finance"]["forecast"]
                if fc:
                    fig = px.line(x=[f["month"] for f in fc], y=[f["projected_savings"] for f in fc],
                                  labels={"x": "Month", "y": "Projected Savings (₹)"}, title=f"Scenario: {name}")
                    st.plotly_chart(fig, use_container_width=True)
                if result["study_projection"]:
                    st.write("Study impact:", result["study_projection"])

# ---- Chat ----
with tabs[5]:
    st.header("Conversational AI")
    st.caption("Ask things like: \"how am I doing this month\", \"forecast next 6 months\", \"study plan\", \"how are my habits\", \"what if I save 5000 more a month\"")

    if "chat_log" not in st.session_state:
        st.session_state.chat_log = []

    for role, msg in st.session_state.chat_log:
        with st.chat_message(role):
            st.write(msg)

    user_msg = st.chat_input("Ask FinLife AI...")
    if user_msg:
        st.session_state.chat_log.append(("user", user_msg))
        r = api_post("/chat", json={"message": user_msg})
        reply = r.json()["reply"] if r.status_code == 200 else f"Error: {r.text}"
        st.session_state.chat_log.append(("assistant", reply))
        st.rerun()
