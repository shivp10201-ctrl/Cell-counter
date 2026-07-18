import streamlit as st
import streamlit.components.v1 as components
import base64

st.set_page_config(page_title="Instant Neubauer Counter", layout="wide")
st.title("🔬 Instant Touch Counter & Viability Calculator")
st.write("Tap on your cells. The image marks and the mathematical calculations update together instantly.")

# --- Side Controls Panel ---
st.sidebar.header("🔬 Lab Parameters")
dilution_factor = st.sidebar.number_input("Dilution Factor (e.g., 2 for 1:1 Trypan Blue)", min_value=1.0, value=2.0, step=0.1)

uploaded_file = st.file_uploader("Upload your photo...", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    # Convert image to Base64 so JavaScript can render it locally
    bytes_data = uploaded_file.read()
    b64_img = base64.b64encode(bytes_data).decode()
    mime_type = uploaded_file.type

    # --- High Performance Client-Side Canvas & Math Component ---
    custom_canvas_html = f"""
    <div style="font-family: sans-serif; max-width: 100%; color: #31333F;">
        <!-- Control Toolbar -->
        <div style="margin-bottom: 15px; background: #f0f2f6; padding: 12px; border-radius: 8px; display: flex; gap: 15px; align-items: center; wrap: wrap;">
            <label style="font-weight: bold; cursor: pointer; display: flex; align-items: center; gap: 5px; font-size: 16px;">
                <input type="radio" name="tool" value="live" checked style="accent-color: #00FF00; transform: scale(1.2);"> 🟢 Mark Live Cell
            </label>
            <label style="font-weight: bold; cursor: pointer; display: flex; align-items: center; gap: 5px; font-size: 16px;">
                <input type="radio" name="tool" value="dead" style="accent-color: #0000FF; transform: scale(1.2);"> 🔵 Mark Dead Cell
            </label>
            <button id="clearBtn" style="margin-left: auto; padding: 8px 16px; background: #ff4b4b; color: white; border: none; border-radius: 4px; cursor: pointer; font-weight: bold;">扫 Clear All</button>
        </div>
        
        <!-- Live Metrics Panel (Built directly into the Canvas View) -->
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px; margin-bottom: 20px;">
            <div style="background: #ffffff; padding: 15px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); border-left: 5px solid #00FF00;">
                <div style="font-size: 14px; color: #555;">🟢 Total Live</div>
                <div id="liveMetric" style="font-size: 24px; font-weight: bold; margin-top: 5px;">0 cells</div>
            </div>
            <div style="background: #ffffff; padding: 15px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); border-left: 5px solid #0000FF;">
                <div style="font-size: 14px; color: #555;">🔵 Total Dead</div>
                <div id="deadMetric" style="font-size: 24px; font-weight: bold; margin-top: 5px;">0 cells</div>
            </div>
            <div style="background: #ffffff; padding: 15px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); border-left: 5px solid #ffaa00;">
                <div style="font-size: 14px; color: #555;">📈 Viability</div>
                <div id="viabilityMetric" style="font-size: 24px; font-weight: bold; margin-top: 5px;">0.0%</div>
            </div>
            <div style="background: #ffffff; padding: 15px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); border-left: 5px solid #00aaaa;">
                <div style="font-size: 14px; color: #555;">🧫 Live Density</div>
                <div id="densityMetric" style="font-size: 20px; font-weight: bold; margin-top: 5px; white-space: nowrap;">0.00e+00 cells/mL</div>
            </div>
        </div>

        <!-- Interactive Photo Area -->
        <div style="position: relative; display: inline-block; max-width: 100%;">
            <canvas id="cellCanvas" style="display: block; max-width: 100%; height: auto; border: 1px solid #ccc; cursor: crosshair; border-radius: 8px;"></canvas>
        </div>
    </div>

    <script>
        const canvas = document.getElementById('cellCanvas');
        const ctx = canvas.getContext('2d');
        const clearBtn = document.getElementById('clearBtn');
        
        // Lab constant variables passed from Streamlit sidebar interface
        const dilutionFactor = {dilution_factor};
        const squaresCounted = 4; 
        
        let liveCells = [];
        let deadCells = [];
        
        const img = new Image();
        img.onload = function() {{
            canvas.width = img.width;
            canvas.height = img.height;
            redraw();
        }};
        img.src = "data:{mime_type};base64,{b64_img}";

        function calculateMetrics() {{
            const liveCount = liveCells.length;
            const deadCount = deadCells.length;
            const totalCells = liveCount + deadCount;
            
            // 1. Update text fields for counts
            document.getElementById('liveMetric').innerText = liveCount + " cells";
            document.getElementById('deadMetric').innerText = deadCount + " cells";
            
            // 2. Neubauer Viability Math
            let viability = 0;
            if (totalCells > 0) {{
                viability = (liveCount / totalCells) * 100;
            }}
            document.getElementById('viabilityMetric').innerText = viability.toFixed(1) + "%";
            
            // 3. Concentration Density Formula: (Cells / 4 Squares) * Dilution * 10,000
            let density = 0;
            if (liveCount > 0) {{
                density = (liveCount / squaresCounted) * dilutionFactor * 10000;
            }}
            document.getElementById('densityMetric').innerText = density.toExponential(2) + " cells/mL";
        }}

        function redraw() {{
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            ctx.drawImage(img, 0, 0);
            
            // Draw green dots instantly
            liveCells.forEach(pt => {{
                ctx.beginPath();
                ctx.arc(pt.x, pt.y, 12, 0, 2 * Math.PI);
                ctx.fillStyle = '#00FF00';
                ctx.fill();
                ctx.lineWidth = 3;
                ctx.strokeStyle = '#000000';
                ctx.stroke();
            }});
            
            // Draw blue dots instantly
            deadCells.forEach(pt => {{
                ctx.beginPath();
                ctx.arc(pt.x, pt.y, 12, 0, 2 * Math.PI);
                ctx.fillStyle = '#0000FF';
                ctx.fill();
                ctx.lineWidth = 3;
                ctx.strokeStyle = '#FFFFFF';
                ctx.stroke();
            }});
            
            // Run math updates immediately locally
            calculateMetrics();
        }}

        canvas.addEventListener('click', function(e) {{
            const rect = canvas.getBoundingClientRect();
            const scaleX = canvas.width / rect.width;
            const scaleY = canvas.height / rect.height;
            const clickX = (e.clientX - rect.left) * scaleX;
            const clickY = (e.clientY - rect.top) * scaleY;
            
            // Tap near an existing point to erase it
            let removed = false;
            liveCells = liveCells.filter(pt => {{
                const dist = Math.sqrt((clickX - pt.x)**2 + (clickY - pt.y)**2);
                if (dist < 24) {{ removed = true; return false; }}
                return true;
            }});
            
            if (!removed) {{
                deadCells = deadCells.filter(pt => {{
                    const dist = Math.sqrt((clickX - pt.x)**2 + (clickY - pt.y)**2);
                    if (dist < 24) {{ removed = true; return false; }}
                    return true;
                }});
            }}
            
            // Add point if not an undo touch action
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
    </script>
    """

    # Render everything directly inside a scrolling window container
    components.html(custom_canvas_html, height=900, scrolling=True)
