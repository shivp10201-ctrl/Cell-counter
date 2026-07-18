import streamlit as st
import streamlit.components.v1 as components
import base64

st.set_page_config(page_title="Instant Neubauer Counter", layout="wide")
st.title("🔬 Lag-Free Interactive Trypan Blue Counter")
st.write("Taps draw instantly in your browser with zero network lag. The app calculates lab metrics automatically.")

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

squares_counted = 4

uploaded_file = st.file_uploader("Upload your photo...", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    # Convert image to Base64 so JavaScript can render it locally
    bytes_data = uploaded_file.read()
    b64_img = base64.b64encode(bytes_data).decode()
    mime_type = uploaded_file.type

    # --- High Performance Client-Side Canvas Component ---
    custom_canvas_html = f"""
    <div style="font-family: sans-serif; max-width: 100%;">
        <div style="margin-bottom: 15px; background: #f0f2f6; padding: 10px; border-radius: 8px; display: flex; gap: 15px; align-items: center;">
            <label style="font-weight: bold; cursor: pointer; display: flex; align-items: center; gap: 5px;">
                <input type="radio" name="tool" value="live" checked style="accent-color: #00FF00;"> 🟢 Mark Live Cell
            </label>
            <label style="font-weight: bold; cursor: pointer; display: flex; align-items: center; gap: 5px;">
                <input type="radio" name="tool" value="dead" style="accent-color: #0000FF;"> 🔵 Mark Dead Cell
            </label>
            <button id="clearBtn" style="margin-left: auto; padding: 6px 12px; background: #ff4b4b; color: white; border: none; border-radius: 4px; cursor: pointer; font-weight: bold;">🧹 Clear Canvas</button>
        </div>
        
        <div style="position: relative; display: inline-block; max-width: 100%;">
            <canvas id="cellCanvas" style="display: block; max-width: 100%; height: auto; border: 1px solid #ccc; cursor: crosshair;"></canvas>
        </div>
    </div>

    <script>
        const canvas = document.getElementById('cellCanvas');
        const ctx = canvas.getContext('2d');
        const clearBtn = document.getElementById('clearBtn');
        
        let liveCells = [];
        let deadCells = [];
        
        // Load the image safely into the local browser viewport
        const img = new Image();
        img.onload = function() {{
            canvas.width = img.width;
            canvas.height = img.height;
            redraw();
        }};
        img.src = "data:{mime_type};base64,{b64_img}";

        function redraw() {{
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            ctx.drawImage(img, 0, 0);
            
            // Instantly draw green dots locally
            liveCells.forEach(pt => {{
                ctx.beginPath();
                ctx.arc(pt.x, pt.y, 10, 0, 2 * Math.PI);
                ctx.fillStyle = '#00FF00';
                ctx.fill();
                ctx.lineWidth = 2;
                ctx.strokeStyle = '#000000';
                ctx.stroke();
            }});
            
            // Instantly draw blue dots locally
            deadCells.forEach(pt => {{
                ctx.beginPath();
                ctx.arc(pt.x, pt.y, 10, 0, 2 * Math.PI);
                ctx.fillStyle = '#0000FF';
                ctx.fill();
                ctx.lineWidth = 2;
                ctx.strokeStyle = '#FFFFFF';
                ctx.stroke();
            }});
            
            // Send the raw data tallies straight back to Streamlit metrics panel
            sendDataToStreamlit();
        }}

        canvas.addEventListener('click', function(e) {{
            const rect = canvas.getBoundingClientRect();
            const scaleX = canvas.width / rect.width;
            const scaleY = canvas.height / rect.height;
            const clickX = (e.clientX - rect.left) * scaleX;
            const clickY = (e.clientY - rect.top) * scaleY;
            
            let removed = false;
            liveCells = liveCells.filter(pt => {{
                const dist = Math.sqrt((clickX - pt.x)**2 + (clickY - pt.y)**2);
                if (dist < 20) {{ removed = true; return false; }}
                return true;
            }});
            
            if (!removed) {{
                deadCells = deadCells.filter(pt => {{
                    const dist = Math.sqrt((clickX - pt.x)**2 + (clickY - pt.y)**2);
                    if (dist < 20) {{ removed = true; return false; }}
                    return true;
                }});
            }}
            
            if (!removed) {{
                const selectedTool = document.querySelector('input[name="tool"]:checked').value;
                if (selectedTool === 'live') {{
                    liveCells.push({{ x: clickX, y: clickY }});
                }} else {{
                    deadCells.push({{ x: clickX, y: clickY }});
                }}
            }}
            
            redraw();
        }});

        clearBtn.addEventListener('click', function() {{
            liveCells = [];
            deadCells = [];
            redraw();
        }});

        function sendDataToStreamlit() {{
            const data = {{ live: liveCells.length, dead: deadCells.length }};
            window.parent.postMessage({{
                isStreamlitMessage: true,
                type: "streamlit:setComponentValue",
                value: data
            }}, "*");
        }}
    </script>
    """

    # FIXED: Changed scroller=True to scrolling=True to match Streamlit API parameters
    response_data = components.html(custom_canvas_html, height=750, scrolling=True)

    # --- Read Counts & Generate Metrics ---
    live_count = 0
    dead_count = 0
    
    if response_data is not None and isinstance(response_data, dict):
        live_count = response_data.get("live", 0)
        dead_count = response_data.get("dead", 0)

    combined_total = live_count + dead_count

    if combined_total > 0:
        live_density = (live_count / squares_counted) * dilution_factor * 10000
        viability = (live_count / combined_total) * 100
    else:
        live_density, viability = 0.0, 0.0

    # --- Final Reporting UI ---
    st.markdown("---")
    st.subheader("📊 Live Lab Metrics Summary")
    m_col1, m_col2, m_col3, m_col4 = st.columns(4)
    m_col1.metric("🟢 Live Total", f"{live_count} cells")
    m_col2.metric("🔵 Dead Total", f"{dead_count} cells")
    m_col3.metric("📈 Viability %", f"{viability:.1f}%")
    m_col4.metric("🧫 Live Density Concentration", f"{live_density:.2e} cells/mL")
