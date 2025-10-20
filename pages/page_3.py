import streamlit as st
from numpy import random as np
import matplotlib.pyplot as plt

st.set_page_config(page_title="Plot")

# Main page content
st.markdown("# Plot")
st.sidebar.markdown("# Plot")


# Helper Functions to generate circles

def plot_generator(x, y, r, c):
    ax = plt.gca()
    ax.set_xlim((0, 30))
    ax.set_ylim((0, 30))

    for i in range(len(x)):
        figure = plt.Circle((x[i], y[i]), r[i % 5], color=c[i % 5])
        ax.add_artist(figure)
    return st.pyplot()


# APP
st.title("Galaxy Cluster Generator")

if st.button("Run the Machine"):
    x = np.randint(0, 30, 50)
    y = np.randint(0, 30, 50)
    r = [0.2, 0.4, 0.6, 0.8, 1.0]
    c = ['r', 'g', 'b', 'y', 'c']
    plot_generator(x, y, r, c)
