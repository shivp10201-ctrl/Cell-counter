import streamlit as st

st.set_page_config(page_title="Neubauer Lab Counter", layout="wide")
st.title("🔬 Neubauer Trypan Blue Viability Calculator")
st.write("A bulletproof manual tally interface. Enter your counts per square below to calculate final metrics instantly.")

# --- Side Controls Panel ---
st.sidebar.header("🔬 Lab Parameters")
dilution_factor = st.sidebar.number_input("Dilution Factor (e.g., 2 for 1:1 Trypan Blue)", min_value=1.0, value=2.0, step=0.1)

# --- Workflow Capture Method ---
st.subheader("📸 Choose Your Capture Method")
capture_mode = st.radio(
    "How are you capturing your 4 Neubauer corner squares?",
    ("Option A: Single image containing all 4 corner squares", 
     "Option B: Four separate images (1 photo per corner square)"),
    index=0
)

uploaded_file = st.file_uploader("Upload your microscope reference photo here...", type=["jpg", "jpeg", "png"])

# Layout columns to put your image and the tally sheet side-by-side
col_img, col_tally = st.columns([2, 1])

with col_img:
    if uploaded_file is not None:
        st.image(uploaded_file, caption="Your Reference Photo - Use this to look and tally", use_container_width=True)
    else:
        st.info("💡 Upload your photo to see it here while counting.")

with col_tally:
    st.subheader("🧮 Tally Log Sheet")
    st.write("Double-click cells below to change values:")
    
    # Initialize a clean lab log frame natively tracked by Streamlit
    initial_data = [
        {"Square": "Square 1 (Top Left)", "Live Cells": 0, "Dead Cells": 0},
        {"Square": "Square 2 (Top Right)", "Live Cells": 0, "Dead Cells": 0},
        {"Square": "Square 3 (Bottom Left)", "Live Cells": 0, "Dead Cells": 0},
        {"Square": "Square 4 (Bottom Right)", "Live Cells": 0, "Dead Cells": 0},
    ]
    
    # Render an interactive spreadsheet that passes data natively to Python
    edited_df = st.data_editor(
        initial_data,
        column_config={
            "Square": st.column_config.TextColumn("Chamber Square", disabled=True),
            "Live Cells": st.column_config.NumberColumn("🟢 Live Tally", min_value=0, default=0, step=1),
            "Dead Cells": st.column_config.NumberColumn("🔵 Dead Tally", min_value=0, default=0, step=1),
        },
        disabled=False,
        hide_index=True,
        key="lab_spreadsheet"
    )

# --- Read Data Out of the Live Spreadsheet Matrix ---
total_live = sum([row["Live Cells"] for row in edited_df])
total_dead = sum([row["Dead Cells"] for row in edited_df])
combined_total = total_live + total_dead
squares_counted = 4

# --- Mathematical Operations & Reporting UI ---
if combined_total > 0:
    # Standard Neubauer Formula: (Cells / Squares) * Dilution * 10,000
    live_density = (total_live / squares_counted) * dilution_factor * 10000
    viability = (total_live / combined_total) * 100
else:
    live_density, viability = 0.0, 0.0

st.markdown("---")
st.subheader("📊 Combined Final Lab Results")

m_col1, m_col2, m_col3, m_col4 = st.columns(4)
m_col1.metric("🟢 Total Live Found", f"{total_live} cells")
m_col2.metric("🔵 Total Dead Found", f"{total_dead} cells")
m_col3.metric("📈 Viability Rating", f"{viability:.1f}%")
m_col4.metric("🧫 Live Density Concentration", f"{live_density:.2e} cells/mL")

