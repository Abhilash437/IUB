import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import io
from datetime import datetime, timedelta

# Constants
usd_to_inr = 83.0  # Approx exchange rate
canara_loan_usd = 4700000 / usd_to_inr
mpower_loan_usd = 63000

# Yearly expenses in USD
yearly_expenses = {
    'Tuition and Fees': 34011,
    'Room and Board': 12431,
    'Health Insurance': 1916,
    'Miscellaneous': 2470,
    'Total': 50828
}

# Semester-wise and monthly breakdown
semesters = 4  # Assuming 4 semesters in 2 years
semester_fee_usd = yearly_expenses['Tuition and Fees'] / 2
semester_health_insurance_usd = yearly_expenses['Health Insurance'] / 2

# Monthly living expense plan in USD
monthly_living = {
    'Rent': 390,
    'Utilities': 70,
    'Groceries & Misc': 200,
    'Total': 390 + 70 + 200
}

# Streamlit App
st.title("Masters in USA - Expense Tracker")

st.markdown("### Summary")
st.write(f"Total Yearly Expense: ${yearly_expenses['Total']:,}")
st.write(f"Per Semester Tuition Fee: ${semester_fee_usd:,.0f}")
st.write(f"Per Semester Health Insurance: ${semester_health_insurance_usd:,.0f}")
st.write(f"Canara Loan (54.5% of all semester fees): ${canara_loan_usd:,.0f}")
st.write(f"MPower Loan (FY 25-26 only): ${mpower_loan_usd:,}")

st.markdown("---")
st.markdown("### Monthly Tracker Table")

# Number of months to simulate
months = pd.date_range(start="2025-08-01", end="2027-08-01", freq='MS')

# Build the editable DataFrame
def generate_default_table():
    data = []
    for i, month in enumerate(months):
        living_expense = monthly_living['Total']
        data.append({
            'Month': month.strftime('%b %Y'),
            'Living Expense ($)': living_expense,
            'RA Income ($)': 0,
            'Semester Fee ($)': 0,
            'Health Insurance ($)': 0,
            'Covered by Canara ($)': 0,
            'Covered by MPower ($)': 0,
            'Living Borrowed from MPower ($)': 0,
            'Cumulative MPower Borrowed ($)': 0,
            'Interest on MPower ($)': 0,
            'Net Monthly Balance ($)': 0
        })

    df = pd.DataFrame(data)

    # Add semester fee and insurance at correct months
    semester_months = [datetime(2025, 8, 1), datetime(2026, 1, 1), datetime(2026, 8, 1), datetime(2027, 1, 1)]

    for sem_date in semester_months:
        month_str = sem_date.strftime('%b %Y')
        total_fee_usd = semester_fee_usd
        insurance_usd = semester_health_insurance_usd
        canara_share = (total_fee_usd + insurance_usd) * 0.545
        mpower_share = (total_fee_usd + insurance_usd) * 0.455

        df.loc[df['Month'] == month_str, 'Semester Fee ($)'] = total_fee_usd
        df.loc[df['Month'] == month_str, 'Health Insurance ($)'] = insurance_usd
        df.loc[df['Month'] == month_str, 'Covered by Canara ($)'] = canara_share
        df.loc[df['Month'] == month_str, 'Covered by MPower ($)'] = mpower_share

    return df

if 'expense_df' not in st.session_state:
    st.session_state.expense_df = generate_default_table()

edited_df = st.data_editor(st.session_state.expense_df, use_container_width=True, num_rows="dynamic")

# Calculations
adjusted_living_borrow = []
cumulative_mpower_borrow = []
interest_list = []
net_balances = []
cumulative = 0
starting_balance = 5000
previous_net_balance = starting_balance

for idx, row in edited_df.iterrows():
    ta_income = row['RA Income ($)']
    living_cost = row['Living Expense ($)']
    interest = cumulative * 0.012

    if previous_net_balance >= (living_cost + interest):
        net_balance = previous_net_balance - (living_cost + interest) + ta_income
        mpower_living_borrow = 0
    else:
        mpower_living_borrow = max(living_cost - ta_income, 0)
        net_balance = previous_net_balance - interest + ta_income - living_cost

    total_monthly_borrow = mpower_living_borrow + row['Covered by MPower ($)']
    cumulative += total_monthly_borrow
    interest = cumulative * 0.012

    adjusted_living_borrow.append(mpower_living_borrow)
    cumulative_mpower_borrow.append(cumulative)
    interest_list.append(interest)
    net_balances.append(net_balance)

    previous_net_balance = net_balance

# Store updated values back
edited_df['Living Borrowed from MPower ($)'] = adjusted_living_borrow
edited_df['Cumulative MPower Borrowed ($)'] = cumulative_mpower_borrow
edited_df['Interest on MPower ($)'] = interest_list
edited_df['Net Monthly Balance ($)'] = net_balances

# Display updated table
st.markdown("### Final Monthly Overview")
st.dataframe(edited_df.set_index('Month'))

# Loan and repayment calculation
total_mpower_borrowed = sum(adjusted_living_borrow) + sum(edited_df['Covered by MPower ($)'])
total_interest = sum(interest_list)
total_repayment = total_mpower_borrowed + total_interest
total_net_balance = edited_df['Net Monthly Balance ($)'].sum()

st.markdown("### Summary Calculations")
st.write(f"Total MPower Borrowed ($): {total_mpower_borrowed:,.0f}")
st.write(f"Total Interest to be Paid on MPower ($): {total_interest:,.0f}")
st.write(f"Total Repayment Amount ($): {total_repayment:,.0f}")
st.write(f"Final Net Balance Over Duration ($): {total_net_balance + starting_balance:,.0f}")

st.markdown("---")
st.markdown("### Visualizations")

# 1. Cumulative MPower Borrowed
st.subheader("Cumulative MPower Borrowed Over Time")
fig1, ax1 = plt.subplots()
ax1.plot(edited_df['Month'], cumulative_mpower_borrow, marker='o', color='blue')
ax1.set_xlabel("Month")
ax1.set_ylabel("Cumulative Borrowed ($)")
ax1.set_title("Cumulative MPower Borrowed")
plt.xticks(rotation=45)
st.pyplot(fig1)

# 2. Net Monthly Balance
st.subheader("Net Monthly Balance Over Time")
fig2, ax2 = plt.subplots()
ax2.plot(edited_df['Month'], net_balances, marker='s', color='green')
ax2.set_xlabel("Month")
ax2.set_ylabel("Net Balance ($)")
ax2.set_title("Monthly Net Balance")
plt.xticks(rotation=45)
st.pyplot(fig2)

excel_buffer = io.BytesIO()
edited_df.to_excel(excel_buffer, index=False, engine='openpyxl')
excel_buffer.seek(0)

st.download_button(
    label="📥 Download as Excel",
    data=excel_buffer,
    file_name="masters_expense_tracker_usd.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
