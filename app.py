import streamlit as st
import cv2
import numpy as np
from PIL import Image, ImageDraw
from streamlit_image_coordinates import streamlit_image_coordinates

st.set_page_config(page_title="Manual Neubauer Counter", layout="wide")
st.title("🔬 Interactive Click-to-Count Trypan Blue Calculator")
st.write("Tap directly on your image to track cells. The app handles all calculations automatically.")

# --- Session State Storage Configuration ---
if "live_cells" not in st.session_state:
    st.session_state["live_cells"] = []
if "dead_cells" not in st.session_state:
    st.session_state["dead_cells"] = []

# --- Side Controls Panel ---
st.sidebar.header("🔬 Lab Parameters")
dilution_factor = st.sidebar.number_input("Dilution Factor (e.g., 2 for 1:1 Trypan Blue)", min_value=1.0, value=2.0, step=0.1)

# Clear Button to reset counts
if st.sidebar.button("🧹 Clear All Marks"):
    st.session_state["live_cells"] = []
    st.session_state["dead_cells"] = []
    st.rerun()

# --- Workflow Capture Method ---
st.subheader("📸 Choose Your Capture Method")
capture_mode = st.radio(
    "How are you capturing your 4 Neubauer corner squares?",
    ("Option A: Single image containing all 4 corner squares", 
     "Option B: Four separate images (1 photo per corner square)"),
    index=0
)

squares_counted = 4
uploaded_file = None

if "Single image" in capture_mode:
    uploaded_file = st.file_uploader("Upload your photo...", type=["jpg", "jpeg", "png"])
else:
    st.write("### Select a square to label:")
    square_choice = st.radio("Active Counting Target:", ("Square 1", "Square 2", "Square 3", "Square 4"), horizontal=True)
    uploaded_file = st.file_uploader(f"Upload photo for {square_choice}...", type=["jpg", "jpeg", "png"], key=square_choice)

# --- Interactive Clicking Area ---
if uploaded_file is not None:
    # Open image as PIL for clean coordinate drawing
    img_pil = Image.open(uploaded_file).convert("RGB")
    draw = ImageDraw.Draw(img_pil)
    
    # Visual Marker Drawing Loop
    for (x, y) in st.session_state["live_cells"]:
        draw.ellipse([x-8, y-8, x+8, y+8], fill="#00FF00", outline="black") # Bright Green Dot
    for (x, y) in st.session_state["dead_cells"]:
        draw.ellipse([x-8, y-8, x+8, y+8], fill="#0000FF", outline="white") # Bright Blue Dot

    # Action Toggle Switch
    st.markdown("---")
    tally_type = st.radio("🖋️ **Tap Mode:** What are you marking right now?", ("🟢 Mark Live Cell", "🔵 Mark Dead Cell"), horizontal=True)

    st.write("👇 **Tap or Click the cells inside the image area below:**")
    
    # Capture the exact tapped coordinate point
    value = streamlit_image_coordinates(img_pil, key="clickable_canvas")

    if value is not None:
        clicked_pt = (value["x"], value["y"])
        
        # Check if user clicked near an existing marker to delete it (Undo feature)
        removed = False
        for pt in st.session_state["live_cells"]:
            if np.sqrt((clicked_pt[0]-pt[0])**2 + (clicked_pt[1]-pt[1])**2) < 15:
                st.session_state["live_cells"].remove(pt)
                removed = True
                break
        if not removed:
            for pt in st.session_state["dead_cells"]:
                if np.sqrt((clicked_pt[0]-pt[0])**2 + (clicked_pt[1]-pt[1])**2) < 15:
                    st.session_state["dead_cells"].remove(pt)
                    removed = True
                    break
        
        # Add new point if it wasn't an undo click
        if not removed:
            if "Mark Live" in tally_type:
                st.session_state["live_cells"].append(clicked_pt)
            else:
                st.session_state["dead_cells"].append(clicked_pt)
        
        st.rerun()

# --- Mathematical Operations ---
live_count = len(st.session_state["live_cells"])
dead_count = len(st.session_state["dead_cells"])
combined_total = live_count + dead_count

if combined_total > 0:
    live_density = (live_count / squares_counted) * dilution_factor * 10000
    viability = (live_count / combined_total) * 100
else:
    live_density, viability = 0.0, 0.0

# --- Reporting UI Panel ---
st.markdown("---")
st.subheader("📊 Live Lab Metrics Summary")
m_col1, m_col2, m_col3, m_col4 = st.columns(4)
m_col1.metric("🟢 Live Total", f"{live_count} cells")
m_col2.metric("🔵 Dead Total", f"{dead_count} cells")
m_col3.metric("📈 Viability %", f"{viability:.1f}%")
m_col4.metric("🧫 Live Density Concentration", f"{live_density:.2e} cells/mL")



