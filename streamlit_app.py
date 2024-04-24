# streamlit_app.py

import streamlit as st
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource

# Create a Bokeh plot
p = figure(title="My Bokeh Plot", plot_width=400, plot_height=400)
p.circle([1, 2, 3, 4, 5], [6, 7, 2, 4, 5], size=15, color="navy", alpha=0.5)

# Display the Bokeh plot using Streamlit
st.bokeh_chart(p, use_container_width=True)
