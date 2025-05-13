import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from src.backend.core.config import API_VERSION

#Set page layout and title
st.set_page_config(layout="wide")
st.title("Quarterly Financial Analyser")

#Initialize session state
if "scrape_complete" not in st.session_state:
    st.session_state.scrape_complete = False
if "visualization_ready" not in st.session_state:
    st.session_state.visualization_ready = False
if "company_name" not in st.session_state:
    st.session_state.company_name = ""

#Input for company name
st.subheader("Web Scraper")
company_name = st.text_input("Enter Company Name")

#Trigger scraping process
if st.button("Scrape Reports"):
    st.session_state.company_name = company_name
    payload = {"name": company_name}
    try:
        response = requests.post(f"http://localhost:8000/company/{API_VERSION}/get_company_name", json=payload)
        if response.status_code == 200:
            data = response.json()
            st.success(f"{data['name']}")
            st.session_state.scrape_complete = True
            st.session_state.visualization_ready = False
        else:
            st.error(f"Error from API: {response.json().get('detail', 'Unknown error')}")
    except requests.exceptions.RequestException as e:
        st.error(f"Request failed: {e}")

#Trigger visualization
if st.session_state.scrape_complete and not st.session_state.visualization_ready:
    if st.button("Visualize Data"):
        payload = {"name": st.session_state.company_name}
        try:
            response = requests.post(f"http://localhost:8000/visualize/{API_VERSION}/visualize_data", json=payload)
            if response.status_code == 200:
                st.success("Visualization started successfully.")
                st.session_state.visualization_ready = True
            else:
                st.error(f"Visualization API error: {response.json().get('detail', 'Unknown error')}")
        except requests.exceptions.RequestException as e:
            st.error(f"Request failed: {e}")

#Load and process data
if st.session_state.visualization_ready:
    dipd_df = pd.read_csv("data/processed_csv/dipd_processed_financial_data.csv")
    rexp_df = pd.read_csv("data/processed_csv/rexp_processed_financial_data.csv")

    #format column date
    month_map = {
        "Jan": "01", "Feb": "02", "Mar": "03", "Apr": "04",
        "May": "05", "Jun": "06", "Jul": "07", "Aug": "08",
        "Sep": "09", "Oct": "10", "Nov": "11", "Dec": "12"
    }

    orig_columns = dipd_df.columns[1:]
    formatted_columns = []
    for col in orig_columns:
        #Remove all non-alphanumeric characters
        clean_col = ''.join(filter(str.isalnum, col))  #e.g. "Mar2022", "June2023", "032022"
        
        #Handle 3-letter month + 4-digit year (e.g. Mar2022)
        month_abbr = clean_col[:3].title()
        year = clean_col[-4:]
        
        if month_abbr in month_map:
            month = month_map[month_abbr]
            formatted_columns.append(f"{month}/{year}")
        else:
            #numeric format, assume MMYYYY
            if len(clean_col) == 6:  #e.g. "032022"
                formatted_columns.append(f"{clean_col[:2]}/{clean_col[-4:]}")
            else:
                #fallback to original
                formatted_columns.append(col)  


    dipd_df.columns = ["Data Point Name"] + formatted_columns
    rexp_df.columns = ["Data Point Name"] + formatted_columns
        
    #Convert to datetime for filtering
    try:
        date_columns_dt = pd.to_datetime(formatted_columns, format='%m/%Y')

    except ValueError as e:
        st.error(f"Date parsing error: {e}")
        st.stop()

    #Date range slider
    st.subheader("Financial Dashboard")
    selected_range = st.slider(
        "Select Date Range:",
        min_value=date_columns_dt.min().date(),
        max_value=date_columns_dt.max().date(),
        value=(date_columns_dt.min().date(), date_columns_dt.max().date())
    )

    #Filter data based on range
    filtered_date_strs = [
        dt.strftime('%m/%Y') for dt in date_columns_dt
        if selected_range[0] <= dt.date() <= selected_range[1]
    ]
    existing_columns = [col for col in filtered_date_strs if col in dipd_df.columns]
    filtered_columns = ["Data Point Name"] + existing_columns

    dipd_filtered = dipd_df.loc[:, filtered_columns]
    rexp_filtered = rexp_df.loc[:, filtered_columns]

    #KPI metrics
    kpi = st.columns(4)
    kpi[0].metric("DIPD - Revenue", f"Rs. {dipd_filtered.iloc[0, -1]:,.2f}")
    kpi[1].metric("DIPD - Net Income", f"Rs. {dipd_filtered.iloc[5, -1]:,.2f}")
    kpi[2].metric("REXP - Revenue", f"Rs. {rexp_filtered.iloc[0, -1]:,.2f}")
    kpi[3].metric("REXP - Net Income", f"Rs. {rexp_filtered.iloc[5, -1]:,.2f}")

    #Financial ratios
    ratios = st.columns(4)

    def get_ratio(numerator, denominator):
        try:
            return round((numerator / denominator) * 100, 2)
        except ZeroDivisionError:
            return 0.0

    gross_profit_margin = get_ratio(
        dipd_filtered.iloc[0, -1] - dipd_filtered.iloc[1, -1], dipd_filtered.iloc[0, -1]
    )
    operating_margin = get_ratio(
        dipd_filtered.iloc[4, -1], dipd_filtered.iloc[0, -1]
    )
    net_profit_margin = get_ratio(
        dipd_filtered.iloc[5, -1], dipd_filtered.iloc[0, -1]
    )
    opex_ratio = get_ratio(
        dipd_filtered.iloc[3, -1], dipd_filtered.iloc[0, -1]
    )

    ratios[0].metric("Gross Profit Margin", f"{gross_profit_margin} %")
    ratios[1].metric("Operating Margin", f"{operating_margin} %")
    ratios[2].metric("Net Profit Margin", f"{net_profit_margin} %")
    ratios[3].metric("Operating Expense Ratio", f"{opex_ratio} %")

    #Visualization charts

    #Revenue
    combined_revenue_df = pd.concat([
        dipd_filtered[dipd_filtered["Data Point Name"] == "Revenue"].melt(
            id_vars=["Data Point Name"], var_name="Date", value_name="Value"
        ).assign(Company="DIPD"),
        rexp_filtered[rexp_filtered["Data Point Name"] == "Revenue"].melt(
            id_vars=["Data Point Name"], var_name="Date", value_name="Value"
        ).assign(Company="REXP")
    ])
    fig_revenue_combined = px.line(
        combined_revenue_df, x="Date", y="Value", color="Company",
        title="Revenue Trend - DIPD vs REXP"
    )

    #Net Income
    combined_net_income_df = pd.concat([
        dipd_filtered[dipd_filtered["Data Point Name"] == "Net Income"].melt(
            id_vars=["Data Point Name"], var_name="Date", value_name="Value"
        ).assign(Company="DIPD"),
        rexp_filtered[rexp_filtered["Data Point Name"] == "Net Income"].melt(
            id_vars=["Data Point Name"], var_name="Date", value_name="Value"
        ).assign(Company="REXP")
    ])
    fig_net_income_combined = px.line(
        combined_net_income_df, x="Date", y="Value", color="Company",
        title="Net Income Trend - DIPD vs REXP"
    )

    #Revenue vs Cost
    fig_dipd_rev_cost = px.scatter(
        x=dipd_filtered.iloc[0, 1:], y=dipd_filtered.iloc[1, 1:],
        labels={"x": "Revenue", "y": "Cost"}, title="Revenue vs Cost - DIPD"
    )
    fig_rexp_rev_cost = px.scatter(
        x=rexp_filtered.iloc[0, 1:], y=rexp_filtered.iloc[1, 1:],
        labels={"x": "Revenue", "y": "Cost"}, title="Revenue vs Cost - REXP"
    )

    #Income vs Expenses
    fig_dipd_income_exp = px.scatter(
        x=dipd_filtered.iloc[4, 1:], y=dipd_filtered.iloc[3, 1:],
        labels={"x": "Operational Income", "y": "Operating Expenses"},
        title="Income vs Expenses - DIPD"
    )
    fig_rexp_income_exp = px.scatter(
        x=rexp_filtered.iloc[4, 1:], y=rexp_filtered.iloc[3, 1:],
        labels={"x": "Operational Income", "y": "Operating Expenses"},
        title="Income vs Expenses - REXP"
    )

    #Revenue Distribution (DIPD)
    fig_dipd_revenue_dist = px.pie(
        dipd_filtered[dipd_filtered["Data Point Name"] == "Revenue"].melt(var_name="Date", value_name="Value"),
        names="Date", values="Value", title="Revenue Distribution - DIPD"
    )

    #Net Income Distribution (REXP)
    fig_rexp_net_income_dist = px.pie(
        rexp_filtered[rexp_filtered["Data Point Name"] == "Net Income"].melt(var_name="Date", value_name="Value"),
        names="Date", values="Value", title="Net Income Distribution - REXP"
    )

    #Chart layout
    row3 = st.columns(4)
    row3[0].plotly_chart(fig_revenue_combined, use_container_width=True, key="revenue_chart_1")
    row3[1].plotly_chart(fig_net_income_combined, use_container_width=True, key="net_income_chart")

    row3[2].plotly_chart(fig_rexp_rev_cost, use_container_width=True)
    row3[3].plotly_chart(fig_dipd_rev_cost, use_container_width=True)

    row4 = st.columns(4)
    row4[0].plotly_chart(fig_dipd_income_exp, use_container_width=True)
    row4[1].plotly_chart(fig_rexp_income_exp, use_container_width=True)
    row4[2].plotly_chart(fig_dipd_revenue_dist, use_container_width=True)
    row4[3].plotly_chart(fig_rexp_net_income_dist, use_container_width=True)


#Chatbot Section
st.subheader("Chatbot")
user_query = st.text_input("Enter Your Query")

if st.button("Submit"):
    payload = {"query": user_query}
    try:
        response = requests.post(f"http://localhost:8000/query/{API_VERSION}/query_data", json=payload)
        if response.status_code == 200:
            data = response.json()
            st.success(f"Answer: {data}")
        else:
            st.error(f"Error from API: {response.json().get('detail', 'Unknown error')}")
    except requests.exceptions.RequestException as e:
        st.error(f"Request failed: {e}")
