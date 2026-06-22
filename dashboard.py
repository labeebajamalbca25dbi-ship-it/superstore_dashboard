import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
import numpy as np


st.set_page_config(page_title="Superstore Dashboard",page_icon="📊",layout="wide",initial_sidebar_state="expanded")

@st.cache_data
def load_data():
    df=pd.read_csv("data\superstore_clean.csv",parse_dates=["Order Date","Ship Date"])
    return df


df=load_data()

st.title("Superstore Sales Dashboard")

with st.sidebar:
    st.header("Filters")
    regions = st.multiselect("Region", options=df["Region"].unique(), default=df["Region"].unique())
    
    years= st.multiselect("Order Year", options=df["Order Year"].unique(), default=df["Order Year"].unique())

    with st.form("date_filters"):
        st.write("Date range" )
        start=st.date_input("Start date", value=df["Order Date"].min().date())
        end=st.date_input("End date", value=df["Order Date"].max().date())
        submitted=st.form_submit_button("Apply")

    if st.button("Refresh data"):
       st.cache_data.clear()
       st.rerun()

filtered = df[df["Region"].isin(regions) & df["Order Year"].isin(years)]   
if submitted:
    filtered = filtered[
    filtered["Order Date"].dt.date.between(start, end)
]
st.sidebar.divider()
csv_bytes= df.to_csv(index=False).encode("utf-8")
st.sidebar.download_button("Dowload filtered data",data=csv_bytes,file_name="superstore_filtered.csv",mime="text/csv")

disc_arr = filtered["Discount"].values
sales_arr = filtered["Sales"].values
high_disc_pct = np.percentile(disc_arr, 75) if len(disc_arr) else 0
high_disc_n = int(np.sum(disc_arr > high_disc_pct)) if len (disc_arr) else 0
z_scores = (sales_arr - np.mean(sales_arr)) / np.std(sales_arr) if len (sales_arr)else 0
outlier_n = int(np.sum(np.abs(z_scores) > 3)) if len(z_scores) else 0
mean_margin = filtered["Profit margin"].mean() if len(filtered) else 0

st.write(f"showing {len(filtered):,} rows")


c1,c2,c3=st.columns(3)
c1.metric("Total Sales",f"${filtered.Sales.sum():,.0f}")
c2.metric("Total Profit",f"${filtered.Profit.sum():,.0f}")
c3.metric("Average Discount",f"{filtered.Discount.mean()*100:.1f}%")

tab1,tab2,tab3,tab4=st.tabs(["Overview","By category","Region","quality alerts"])
with tab1:
   st.write("Filtered data")
   st.dataframe(filtered.head(20),use_container_width=True,hide_index=True)
   st.subheader("Monthly sales trend")
   Monthly_yr = (filtered.groupby([filtered['Order Date'].dt.to_period("M").astype(str),"Order Year"])["Sales"].sum().reset_index().rename(columns={"Order Date":"Month"}))
   fig01=px.line(Monthly_yr,x="Month",y = "Sales",color="Order Year",title="Monthly sales by year")
   st.plotly_chart(fig01, use_container_width=True)

with tab2:
     st.subheader("sales by category")
     top10=filtered.groupby("Sub-Category")["Sales"].sum().nlargest(10).sort_values()
     fig, ax = plt.subplots(figsize =(7,4))
     bars = ax.barh(top10.index,top10.values,color="blue")
     ax.bar_label(bars, fmt="$%,0f",padding=4,fontsize=8)
     ax.set_xlabel("Total sales")
     ax.set_title("Top 10 sub category by sales")
     plt.tight_layout()
     st.pyplot(fig)
     plt.close(fig)

st.subheader("Sub category breakdown")
summary = filtered.groupby("Sub-Category").agg(
     Sales=("Sales","sum"),profit=("Profit","sum")).sort_values("Sales",ascending=False)
st.dataframe(summary.style.format("${:,.0f}"),use_container_width=True)

fig = px.scatter(filtered,x="Sales",y="Profit",
     color="Category",size="Quantity",
     hover_data=["Sub-Category"],title="Sales vs profit by category")
st.plotly_chart(fig, use_container_width=True)


with tab3:
    st.subheader("Profit by regions")
    reg = filtered.groupby("Region")["Profit"].sum().reset_index()
    fig= px.pie(reg, names="Region", values="Profit",
    hole=0.4,title="Profit share by region")
    st.plotly_chart(fig, use_container_width=True)      
     
st.markdown("---")  

min_year=filtered["Order Year"].min()
max_year=filtered["Order Year"].max()
st.caption(f"Showing {len(filtered):,} rows. {min_year}-{max_year}. Built by OJT. DBI Skill Park")

with tab4:
    st.subheader("Quality Alerts")

if mean_margin < 10:
    st.error(f"Low margins ({mean_margin:.1f}%) — investigate discounts and product mix.")
elif mean_margin < 20:
    st.warning(f"Moderate margins ({mean_margin:.1f}%) — room to improve.")
else:
    st.success(f"Healthy margins ({mean_margin:.1f}%) — pricing strategy is working.")

st.info(
    f"{high_disc_n} orders have discount above the 75th percentile "
    f"({high_disc_pct * 100:.1f}%)."
)
if outlier_n > 0:
    st.warning(f"{outlier_n} sales outliers detected (|z-score| > 3).")
else:
    st.success("No sales outliers detected.")

with st.expander("View outlier rows"):
    
   outlier_mask = np.abs(z_scores) > 3 if len(z_scores) else np.array([], dtype=bool)

   outliers = filtered[outlier_mask] if len(outlier_mask) else filtered.iloc[0:0]


st.dataframe(outliers[["Order ID", "Order Date", "Sales", "Profit", "Region"]],use_container_width=True)

st.markdown("---")