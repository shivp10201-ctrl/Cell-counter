import streamlit as st
import cv2
import numpy as np

st.set_page_config(page_title="Neubauer Trypan Counter", layout="wide")
st.title("🔬 Automated Trypan Blue Cell Viability Calculator")
st.write("Optimized for oval/budding cells and smartphone microscope adapter images.")

# --- Side Controls Panel ---
st.sidebar.header("🔬 Lab Parameters")
dilution_factor = st.sidebar.number_input("Dilution Factor (e.g., 2 for 1:1 Trypan Blue)", min_value=1.0, value=2.0, step=0.1)

st.sidebar.header("⚙️ Fine-Tune Cell Sizes")
min_cell_area = st.sidebar.slider("Minimum Cell Size (Area)", 10, 500, 40)
max_cell_area = st.sidebar.slider("Maximum Cell Size (Area)", 500, 5000, 1500)
live_threshold = st.sidebar.slider("Live Cell Brightness Sensitivity", 100, 255, 165)
dead_circularity_thresh = st.sidebar.slider("Dead Cell Roundness Filter", 0.1, 1.0, 0.4)

# --- Workflow Selection Option ---
st.subheader("📸 Choose Your Capture Method")
capture_mode = st.radio(
    "How are you capturing your 4 Neubauer corner squares?",
    ("Option A: Single image containing all 4 corner squares", 
     "Option B: Four separate images (1 photo per corner square)"),
    index=0
)

def process_single_frame(image_bytes, min_area, max_area, live_thresh_val, circularity_val):
    file_bytes = np.asarray(bytearray(image_bytes), dtype=np.uint8)
    img = cv2.imdecode(file_bytes, 1)
    output_img = img.copy()
    
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    
    # 1. LIVE CELL DETECTION (Finding the bright, glowing white centers)
    _, live_mask = cv2.threshold(blurred, live_thresh_val, 255, cv2.THRESH_BINARY)
    live_contours, _ = cv2.findContours(live_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    live_count = 0
    live_centers = []
    for cnt in live_contours:
        area = cv2.contourArea(cnt)
        if min_area <= area <= max_area:
            M = cv2.moments(cnt)
            if M["m00"] != 0:
                cX = int(M["m10"] / M["m00"])
                cY = int(M["m01"] / M["m00"])
                live_centers.append((cX, cY))
                live_count += 1
                ellipse = cv2.fitEllipse(cnt) if len(cnt) >= 5 else cv2.boundingRect(cnt)
                if len(cnt) >= 5:
                    cv2.ellipse(output_img, ellipse, (0, 255, 0), 2)
                else:
                    x, y, w, h = cv2.boundingRect(cnt)
                    cv2.rectangle(output_img, (x, y), (x+w, y+h), (0, 255, 0), 2)

    # 2. DEAD CELL DETECTION (With added filters to ignore straight lines)
    dead_mask = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 31, 15)
    dead_contours, _ = cv2.findContours(dead_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    dead_count = 0
    for cnt in dead_contours:
        area = cv2.contourArea(cnt)
        if (min_area * 0.4) <= area <= (max_area * 0.8):
            perimeter = cv2.arcLength(cnt, True)
            if perimeter == 0:
                continue
                
            # Circularity math formula: 4 * pi * Area / Perimeter^2
            # A perfect circle = 1.0. A straight grid line = close to 0.0.
            circularity = 4 * np.pi * area / (perimeter * perimeter)
            
            if circularity >= circularity_val:
                M = cv2.moments(cnt)
                if M["m00"] != 0:
                    cX = int(M["m10"] / M["m00"])
                    cY = int(M["m01"] / M["m00"])
                    
                    # Prevent overlapping duplicates
                    is_duplicate = False
                    for (lX, lY) in live_centers:
                        if np.sqrt((cX - lX)**2 + (cY - lY)**2) < 20:
                            is_duplicate = True
                            break
                            
                    if not is_duplicate:
                        dead_count += 1
                        cv2.drawContours(output_img, [cnt], -1, (255, 0, 0), 2) # Blue outlines for Dead
                        
    return live_count, dead_count, output_img

# --- Running the Selection Logistics ---
total_live = 0
total_dead = 0
processed_visuals = []
squares_counted = 4

if "Single image" in capture_mode:
    uploaded_file = st.file_uploader("Upload your single broad-view photo...", type=["jpg", "jpeg", "png"])
    if uploaded_file is not None:
        l_cnt, d_cnt, out_viz = process_single_frame(uploaded_file.read(), min_cell_area, max_cell_area, live_threshold, dead_circularity_thresh)
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
            l_cnt, d_cnt, out_viz = process_single_frame(f_obj.read(), min_cell_area, max_cell_area, live_threshold, dead_circularity_thresh)
            total_live += l_cnt
            total_dead += d_cnt
            processed_visuals.append((f"Square Asset {idx+1}", out_viz))

# --- Mathematical Operations & Reporting UI ---
if total_live > 0 or total_dead > 0:
    combined_total = total_live + total_dead
    live_density = (total_live / squares_counted) * dilution_factor * 10000
    viability = (total_live / combined_total) * 100 if combined_total > 0 else 0

    st.markdown("---")
    st.subheader("📊 Combined Final Lab Results")
    
    m_col1, m_col2, m_col3, m_col4 = st.columns(4)
    m_col1.metric("🟢 Total Live Found", f"{total_live} cells")
    m_col2.metric("🔵 Total Dead Found", f"{total_dead} cells")
    m_col3.metric("📈 Viability Rating", f"{viability:.1f}%")
    m_col4.metric("🧫 Live Density Concentration", f"{live_density:.2e} cells/mL")

    st.markdown("---")
    st.subheader("🔍 Visual Proof Verification")
    for title, viz_img in processed_visuals:
        st.write(f"**{title}**")
        st.image(cv2.cvtColor(viz_img, cv2.COLOR_BGR2RGB), caption="Green Outline = Live | Blue Outline = Dead", use_container_width=True)

