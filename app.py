import streamlit as st
import streamlit.components.v1 as components
import base64

st.set_page_config(page_title="Instant Neubauer Counter", layout="wide")
st.title("🔬 Mobile Zoom-Enabled Trypan Counter")
st.write("📱 Pinch-to-zoom with two fingers to enlarge cells, then tap with one finger to place your dots precisely.")

uploaded_file = st.file_uploader("Upload your photo...", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    bytes_data = uploaded_file.read()
    b64_img = base64.b64encode(bytes_data).decode()
    mime_type = uploaded_file.type

    # --- Zoom-Enabled Interactive Layout Engine ---
    custom_canvas_html = f"""
    <div style="font-family: sans-serif; max-width: 100%; color: #31333F;">
        
        <!-- 🧪 Mobile Lab Input Section (Moved out of sidebar for full visibility) -->
        <div style="margin-bottom: 15px; background: #e8ecf4; padding: 12px; border-radius: 8px; display: flex; gap: 15px; align-items: center; flex-wrap: wrap;">
            <div style="display: flex; align-items: center; gap: 8px;">
                <label style="font-weight: bold; font-size: 15px;">🧪 Dilution Factor:</label>
                <input type="number" id="dilutionInput" value="2.0" step="0.1" min="1.0" style="width: 70px; padding: 6px; border-radius: 4px; border: 1px solid #ccc; font-weight: bold; font-size: 15px;">
            </div>
            <div style="display: flex; gap: 15px;">
                <label style="font-weight: bold; cursor: pointer; display: flex; align-items: center; gap: 5px; font-size: 15px;">
                    <input type="radio" name="tool" value="live" checked style="accent-color: #00FF00; transform: scale(1.2);"> 🟢 Live
                </label>
                <label style="font-weight: bold; cursor: pointer; display: flex; align-items: center; gap: 5px; font-size: 15px;">
                    <input type="radio" name="tool" value="dead" style="accent-color: #0000FF; transform: scale(1.2);"> 🔵 Dead
                </label>
            </div>
            <button id="clearBtn" style="margin-left: auto; padding: 6px 12px; background: #ff4b4b; color: white; border: none; border-radius: 4px; cursor: pointer; font-weight: bold; font-size: 14px;">🧹 Clear</button>
        </div>
        
        <!-- 📊 Live Metrics Panel -->
        <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; margin-bottom: 15px;">
            <div style="background: #ffffff; padding: 10px; border-radius: 6px; box-shadow: 0 1px 2px rgba(0,0,0,0.1); border-left: 4px solid #00FF00;">
                <div style="font-size: 12px; color: #555;">🟢 Live Cells</div>
                <div id="liveMetric" style="font-size: 18px; font-weight: bold;">0</div>
            </div>
            <div style="background: #ffffff; padding: 10px; border-radius: 6px; box-shadow: 0 1px 2px rgba(0,0,0,0.1); border-left: 4px solid #0000FF;">
                <div style="font-size: 12px; color: #555;">🔵 Dead Cells</div>
                <div id="deadMetric" style="font-size: 18px; font-weight: bold;">0</div>
            </div>
            <div style="background: #ffffff; padding: 10px; border-radius: 6px; box-shadow: 0 1px 2px rgba(0,0,0,0.1); border-left: 4px solid #ffaa00;">
                <div style="font-size: 12px; color: #555;">📈 Viability</div>
                <div id="viabilityMetric" style="font-size: 18px; font-weight: bold;">0.0%</div>
            </div>
            <div style="background: #ffffff; padding: 10px; border-radius: 6px; box-shadow: 0 1px 2px rgba(0,0,0,0.1); border-left: 4px solid #00aaaa;">
                <div style="font-size: 12px; color: #555;">🧫 Concentration</div>
                <div id="densityMetric" style="font-size: 15px; font-weight: bold;">0.00e+00 /mL</div>
            </div>
        </div>

        <div style="font-size: 12px; color: #777; margin-bottom: 5px; font-style: italic;">👉 Use 2 fingers to zoom or move picture. Use 1 finger to place cell marks.</div>

        <!-- Interactive Canvas Window Wrapper -->
        <div style="position: relative; display: block; width: 100%; overflow: hidden; border: 2px solid #bbb; border-radius: 8px; background: #222; height: 600px;">
            <canvas id="cellCanvas" style="position: absolute; top: 0; left: 0; transform-origin: 0 0; cursor: crosshair;"></canvas>
        </div>
    </div>

    <!-- Injecting Panzoom framework via CDN to safely handle smooth cross-platform mobile pinches -->
    <script src="https://jsdelivr.net"></script>
    <script>
        const canvas = document.getElementById('cellCanvas');
        const ctx = canvas.getContext('2d');
        const clearBtn = document.getElementById('clearBtn');
        const dilutionInput = document.getElementById('dilutionInput');
        
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

        // Configure Panzoom explicitly on your phone screen surface
        const panzoom = Panzoom(canvas, {{
            maxScale: 6,
            minScale: 0.5,
            contain: 'outside',
            // Blocks mouse tracking interference on phone taps
            touchAction: 'none' 
        }});
        
        // Listen to phone pinches via container wheel mechanics
        canvas.parentElement.addEventListener('wheel', panzoom.zoomWithWheel);

        function calculateMetrics() {{
            const liveCount = liveCells.length;
            const deadCount = deadCells.length;
            const totalCells = liveCount + deadCount;
            const dilutionFactor = parseFloat(dilutionInput.value) || 2.0;
            
            document.getElementById('liveMetric').innerText = liveCount + " cells";
            document.getElementById('deadMetric').innerText = deadCount + " cells";
            
            let viability = 0;
            if (totalCells > 0) {{ viability = (liveCount / totalCells) * 100; }}
            document.getElementById('viabilityMetric').innerText = viability.toFixed(1) + "%";
            
            let density = 0;
            if (liveCount > 0) {{ density = (liveCount / squaresCounted) * dilutionFactor * 10000; }}
            document.getElementById('densityMetric').innerText = density.toExponential(2) + " /mL";
        }}

        function redraw() {{
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            ctx.drawImage(img, 0, 0);
            
            liveCells.forEach(pt => {{
                ctx.beginPath();
                ctx.arc(pt.x, pt.y, 14, 0, 2 * Math.PI);
                ctx.fillStyle = '#00FF00';
                ctx.fill();
                ctx.lineWidth = 4;
                ctx.strokeStyle = '#000000';
                ctx.stroke();
            }});
            
            deadCells.forEach(pt => {{
                ctx.beginPath();
                ctx.arc(pt.x, pt.y, 14, 0, 2 * Math.PI);
                ctx.fillStyle = '#0000FF';
                ctx.fill();
                ctx.lineWidth = 4;
                ctx.strokeStyle = '#FFFFFF';
                ctx.stroke();
            }});
            
            calculateMetrics();
        }}

        // Track when dragging vs when tapping on screen arrays
        let isPanning = false;
        canvas.addEventListener('panzoomstart', () => {{ isPanning = false; }});
        canvas.addEventListener('panzoomchange', () => {{ isPanning = true; }});

        canvas.addEventListener('touchend', function(e) {{
            // Ignore if the action was a 2-finger zoom or drag movement
            if (isPanning || e.touches.length > 0) return;
            
            const rect = canvas.getBoundingClientRect();
            const panzoomOptions = panzoom.getScale();
            
            // Fixed Phone Pixel Coordinate Conversion Math Engine
            const touch = e.changedTouches[0];
            const clickX = (touch.clientX - rect.left) * (canvas.width / rect.width);
            const clickY = (touch.clientY - rect.top) * (canvas.height / rect.height);
            
            let removed = false;
            liveCells = liveCells.filter(pt => {{
                const dist = Math.sqrt((clickX - pt.x)**2 + (clickY - pt.y)**2);
                if (dist < 30) {{ removed = true; return false; }}
                return true;
            }});
            
            if (!removed) {{
                deadCells = deadCells.filter(pt => {{
                    const dist = Math.sqrt((clickX - pt.x)**2 + (clickY - pt.y)**2);
                    if (dist < 30) {{ removed = true; return false; }}
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

        // Trigger updates when manual numbers changes on row parameters
        dilutionInput.addEventListener('input', calculateMetrics);
        clearBtn.addEventListener('click', function() {{
            liveCells = [];
            deadCells = [];
            redraw();
        }});
    </script>
    """

    components.html(custom_canvas_html, height=850, scrolling=False)

