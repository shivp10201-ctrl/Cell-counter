import streamlit as st
import cv2
import numpy as np

st.set_page_config(page_title="Neubauer Trypan Counter", layout="wide")
st.title("🔬 Automated Trypan Blue Cell Viability Calculator")
st.write("Optimized for smartphone microscope adapter images focusing on 4 corner squares.")

# --- Side Controls Panel ---
st.sidebar.header("🔬 Lab Parameters")
dilution_factor = st.sidebar.number_input("Dilution Factor (e.g., 2 for 1:1 Trypan Blue)", min_value=1.0, value=2.0, step=0.1)

st.sidebar.header("⚙️ Computer Vision Tuning")
min_dist = st.sidebar.slider("Minimum cell spacing (px)", 10, 100, 25)
min_rad = st.sidebar.slider("Minimum Cell Radius (px)", 5, 50, 12)
max_rad = st.sidebar.slider("Maximum Cell Radius (px)", 15, 150, 35)

# --- Workflow Selection Option ---
st.subheader("📸 Choose Your Capture Method")
capture_mode = st.radio(
    "How are you capturing your 4 Neubauer corner squares?",
    ("Option A: Single image containing all 4 corner squares", 
     "Option B: Four separate images (1 photo per corner square)"),
    index=0
)

# Core processing function to find live and dead cells in a single image frame
def process_single_frame(image_bytes, min_dist, min_rad, max_rad):
    file_bytes = np.asarray(bytearray(image_bytes), dtype=np.uint8)
    img = cv2.imdecode(file_bytes, 1)
    
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blurred = cv2.medianBlur(gray, 5)
    
    # 1. LIVE CELLS (glowing centers)
    live_circles = cv2.HoughCircles(
        blurred, cv2.HOUGH_GRADIENT, dp=1, minDist=min_dist,
        param1=50, param2=22, minRadius=min_rad, maxRadius=max_rad
    )
    
    # 2. DEAD CELLS (dark blue spots via inversion and thresholding)
    thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 21, 7)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3,3))
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
    dead_contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    live_count = 0
    dead_count = 0
    output_img = img.copy()
    
    if live_circles is not None:
        live_circles = np.uint16(np.around(live_circles))
        live_count = len(live_circles[0, :])
        for i in live_circles[0, :]:
            cv2.circle(output_img, (i[0], i[1]), i[2], (0, 255, 0), 2)  # Green for Live
            cv2.circle(output_img, (i[0], i[1]), 2, (0, 255, 0), 3)

    for cnt in dead_contours:
        area = cv2.contourArea(cnt)
        min_area = np.pi * (min_rad ** 2)
        max_area = np.pi * (max_rad ** 2)
        
        if min_area <= area <= max_area:
            M = cv2.moments(cnt)
            if M["m00"] != 0:
                cX = int(M["m10"] / M["m00"])
                cY = int(M["m01"] / M["m00"])
                
                is_duplicate = False
                if live_circles is not None:
                    for l_cell in live_circles[0, :]:
                        dist = np.sqrt((cX - l_cell[0])**2 + (cY - l_cell[1])**2)
                        if dist < min_dist:
                            is_duplicate = True
                            break
                
                if not is_duplicate:
                    dead_count += 1
                    cv2.drawContours(output_img, [cnt], -1, (255, 0, 0), 2)  # Blue for Dead
                    
    return live_count, dead_count, output_img

# --- Running the Selection Logistics ---
total_live = 0
total_dead = 0
processed_visuals = []
squares_counted = 4

if "Single image" in capture_mode:
    uploaded_file = st.file_uploader("Upload your single broad-view photo...", type=["jpg", "jpeg", "png"])
    if uploaded_file is not None:
        l_cnt, d_cnt, out_viz = process_single_frame(uploaded_file.read(), min_dist, min_rad, max_rad)
        total_live = l_cnt
        total_dead = d_cnt
        processed_visuals.append(("Full Field View", out_viz))

else:
    st.write("### Upload an image for each corner square:")
    col_u1, col_u2 = st.columns(2)
    with col_u1:
        f1 = st.file_uploader("Top Left Square Image", type=["jpg", "jpeg", "png"], key="sq1")
        f2 = st.file_uploader("Top Right Square Image", type=["jpg", "jpeg", "png"], key="sq2")
    with col_u2:
        f3 = st.file_uploader("Bottom Left Square Image", type=["jpg", "jpeg", "png"], key="sq3")
        f4 = st.file_uploader("Bottom Right Square Image", type=["jpg", "jpeg", "png"], key="sq4")
        
    files_list = [f1, f2, f3, f4]
    active_files = [f for f in files_list if f is not None]
    
    if len(active_files) > 0:
        squares_counted = len(active_files)
        for idx, f_obj in enumerate(active_files):
            l_cnt, d_cnt, out_viz = process_single_frame(f_obj.read(), min_dist, min_rad, max_rad)
            total_live += l_cnt
            total_dead += d_cnt
            processed_visuals.append((f"Square Asset {idx+1}", out_viz))

# --- Mathematical Operations & Reporting UI ---
if total_live > 0 or total_dead > 0:
    combined_total = total_live + total_dead
    
    # Standard Neubauer Formula: (Cells / Squares) * Dilution * 10,000
    live_density = (total_live / squares_counted) * dilution_factor * 10000
    total_density = (combined_total / squares_counted) * dilution_factor * 10000
    viability = (total_live / combined_total) * 100 if combined_total > 0 else 0

    st.markdown("---")
    st.subheader("📊 Combined Final Lab Results")
    
    m_col1, m_col2, m_col3, m_col4 = st.columns(4)
    m_col1.metric("🟢 Total Live Found", f"{total_live} cells")
    m_col2.metric("🔵 Total Dead Found", f"{total_dead} cells")
    m_col3.metric("📈 Viability Rating", f"{viability:.1f}%")
    m_col4.metric("🧫 Live Density Concentration", f"{live_density:.2e} cells/mL")
    
    if squares_counted < 4 and "Four separate images" in capture_mode:
        st.info(f"⚠️ Calculating math dynamically using {squares_counted} square(s). Upload all 4 for a standard complete run.")

    st.markdown("---")
    st.subheader("🔍 Visual Proof Verification")
    
    for title, viz_img in processed_visuals:
        st.write(f"**{title}**")
        st.image(cv2.cvtColor(viz_img, cv2.COLOR_BGR2RGB), caption="Green Circles = Live | Blue Outlines = Dead", use_container_width=True)
