// --- Urban CO2 Digital Twin V4.0 (Dark HUD Restoration) ---
const mapContainer = document.getElementById('map-container');
const baseMap = document.getElementById('base-map');
const mapUpload = document.getElementById('map-upload');
const heatmapCanvas = document.getElementById('heatmap-canvas');
const uiCanvas = document.getElementById('ui-canvas');
const heatCtx = heatmapCanvas.getContext('2d');
const uiCtx = uiCanvas.getContext('2d');

const btnSimulate = document.getElementById('btn-simulate');
const btnClear = document.getElementById('btn-clear');
const coordReadout = document.getElementById('coord-readout');
const entityListContainer = document.getElementById('entity-list');

const gridResInput = document.getElementById('grid-res');
const resValText = document.getElementById('res-val');
const mppInput = document.getElementById('mpp');
const mppValText = document.getElementById('mpp-val');

const windXInput = document.getElementById('wind-x');
const windYInput = document.getElementById('wind-y');
const stabilityInput = document.getElementById('stability-class');

const mTotal = document.getElementById('m-total');
const mMax = document.getElementById('m-max');

// --- Global State ---
let entities = [];
let activeType = 'point';
let lineStart = null;
let GRID_RESOLUTION = 100;

// --- Initialization ---
function syncCanvasSize() {
    heatmapCanvas.width = baseMap.clientWidth;
    heatmapCanvas.height = baseMap.clientHeight;
    uiCanvas.width = baseMap.clientWidth;
    uiCanvas.height = baseMap.clientHeight;
    drawUI();
}

baseMap.onload = syncCanvasSize;
window.addEventListener('resize', syncCanvasSize);
if (baseMap.complete) syncCanvasSize();

// --- HUD Interaction ---
document.querySelectorAll('.type-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        document.querySelector('.type-btn.active').classList.remove('active');
        btn.classList.add('active');
        activeType = btn.dataset.type;
        lineStart = null;
        
        document.getElementById('line-hint').style.display = (activeType === 'line') ? 'block' : 'none';
        document.getElementById('params-point').style.display = (activeType === 'point') ? 'block' : 'none';
        document.getElementById('params-line').style.display = (activeType === 'line') ? 'block' : 'none';
        document.getElementById('params-area').style.display = (activeType === 'area') ? 'block' : 'none';
        document.getElementById('params-sink').style.display = (activeType.includes('sink')) ? 'block' : 'none';
        
        const capLabel = document.getElementById('cap-label');
        if (activeType === 'natural_sink') capLabel.innerText = "Capture Density";
        else if (activeType === 'artificial_sink') capLabel.innerText = "Capture Capacity";

        document.getElementById('s-w').parentElement.style.display = (activeType === 'natural_sink') ? 'flex' : 'none';
        document.getElementById('sink-dim-label').style.display = (activeType === 'natural_sink') ? 'block' : 'none';
    });
});

gridResInput.oninput = () => { GRID_RESOLUTION = parseInt(gridResInput.value); resValText.innerText = GRID_RESOLUTION; };
mppInput.oninput = () => { mppValText.innerText = parseFloat(mppInput.value).toFixed(1); };

// --- Map Interaction ---
mapUpload.addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = (ev) => baseMap.src = ev.target.result;
        reader.readAsDataURL(file);
    }
});

function getNormalizedCoords(e) {
    const rect = baseMap.getBoundingClientRect();
    return {
        x: (e.clientX - rect.left) / rect.width,
        y: 1 - ((e.clientY - rect.top) / rect.height)
    };
}

mapContainer.addEventListener('mousemove', (e) => {
    const coords = getNormalizedCoords(e);
    if (coords.x >= 0 && coords.x <= 1 && coords.y >= 0 && coords.y <= 1) {
        coordReadout.innerText = `GRID: [X: ${Math.floor(coords.x * GRID_RESOLUTION)}, Y: ${Math.floor(coords.y * GRID_RESOLUTION)}]`;
    }
});

mapContainer.addEventListener('click', (e) => {
    const coords = getNormalizedCoords(e);
    if (coords.x < 0 || coords.x > 1 || coords.y < 0 || coords.y > 1) return;

    if (activeType === 'line') {
        if (!lineStart) {
            lineStart = coords;
            document.getElementById('line-hint').innerText = "CLICK END POINT";
        } else {
            entities.push({
                type: 'line', id: Date.now(),
                x1_pct: lineStart.x, y1_pct: lineStart.y, x2_pct: coords.x, y2_pct: coords.y,
                traffic_count: parseFloat(document.getElementById('l-traffic').value),
                emission_factor: parseFloat(document.getElementById('l-ef').value)
            });
            lineStart = null;
            document.getElementById('line-hint').innerText = "CLICK START POINT";
            updateUI();
        }
    } else {
        const entity = { type: activeType, id: Date.now(), x_pct: coords.x, y_pct: coords.y };
        if (activeType === 'point') {
            entity.rate = parseFloat(document.getElementById('p-rate').value);
            entity.stack_height = parseFloat(document.getElementById('p-height').value);
        } else if (activeType === 'area') {
            entity.radius = parseFloat(document.getElementById('a-radius').value);
            entity.intensity = parseFloat(document.getElementById('a-intensity').value);
        } else if (activeType === 'natural_sink') {
            entity.capture_density = parseFloat(document.getElementById('s-cap').value);
            entity.width = parseFloat(document.getElementById('s-w').value);
            entity.height = parseFloat(document.getElementById('s-h').value);
        } else if (activeType === 'artificial_sink') {
            entity.capture_capacity = parseFloat(document.getElementById('s-cap').value);
        }
        entities.push(entity);
        updateUI();
    }
});

function updateUI() {
    updateList();
    drawUI();
}

function updateList() {
    entityListContainer.innerHTML = '';
    entities.forEach(ent => {
        const item = document.createElement('div');
        item.className = 'source-item';
        const label = ent.type.replace('_', ' ').toUpperCase();
        item.innerHTML = `<span>${label}</span> <button class="btn-delete" onclick="deleteEntity(${ent.id})">×</button>`;
        entityListContainer.appendChild(item);
    });
}

window.deleteEntity = (id) => {
    entities = entities.filter(e => e.id !== id);
    updateUI();
};

function drawUI() {
    uiCtx.clearRect(0, 0, uiCanvas.width, uiCanvas.height);
    const W = uiCanvas.width;
    const H = uiCanvas.height;

    entities.forEach(ent => {
        uiCtx.strokeStyle = ent.type.includes('sink') ? '#00ffff' : '#ff3333';
        uiCtx.lineWidth = 2;
        const sx = ent.x_pct * W;
        const sy = H - (ent.y_pct * H);

        if (ent.type === 'point' || ent.type === 'artificial_sink') {
            uiCtx.beginPath(); uiCtx.arc(sx, sy, 6, 0, Math.PI * 2); uiCtx.stroke();
            uiCtx.beginPath(); uiCtx.moveTo(sx - 10, sy); uiCtx.lineTo(sx + 10, sy); uiCtx.moveTo(sx, sy - 10); uiCtx.lineTo(sx, sy + 10); uiCtx.stroke();
        } else if (ent.type === 'line') {
            uiCtx.beginPath(); uiCtx.moveTo(ent.x1_pct * W, H - (ent.y1_pct * H)); uiCtx.lineTo(ent.x2_pct * W, H - (ent.y2_pct * H)); uiCtx.stroke();
        } else if (ent.type === 'area') {
            uiCtx.beginPath(); uiCtx.arc(sx, sy, (ent.radius / GRID_RESOLUTION) * W, 0, Math.PI * 2); uiCtx.stroke();
        } else if (ent.type === 'natural_sink') {
            uiCtx.strokeRect(sx, sy, (ent.width / GRID_RESOLUTION) * W, -(ent.height / GRID_RESOLUTION) * H);
        }
    });
}

function getJetColor(v) {
    const val = v / 255;
    const r = Math.max(0, Math.min(255, 255 * Math.min(4 * val - 1.5, -4 * val + 4.5)));
    const g = Math.max(0, Math.min(255, 255 * Math.min(4 * val - 0.5, -4 * val + 3.5)));
    const b = Math.max(0, Math.min(255, 255 * Math.min(4 * val + 0.5, -4 * val + 2.5)));
    return {r, g, b};
}

btnSimulate.addEventListener('click', async () => {
    btnSimulate.innerText = "CALCULATING...";
    const wx = parseFloat(windXInput.value);
    const wy = parseFloat(windYInput.value);
    const speed = Math.sqrt(wx*wx + wy*wy) * 10;
    const dir = (Math.atan2(wy, wx) * 180 / Math.PI + 360) % 360;

    const payload = {
        grid_size: GRID_RESOLUTION,
        wind_speed: speed || 0.1,
        wind_direction_deg: dir,
        stability_class: stabilityInput.value,
        receptor_height: 0.0,
        metres_per_pixel: parseFloat(mppInput.value),
        entities: entities.map(ent => {
            const b = { type: ent.type };
            if (ent.type === 'line') {
                b.x1 = ent.x1_pct * GRID_RESOLUTION; b.y1 = ent.y1_pct * GRID_RESOLUTION;
                b.x2 = ent.x2_pct * GRID_RESOLUTION; b.y2 = ent.y2_pct * GRID_RESOLUTION;
                b.traffic_count = ent.traffic_count; b.emission_factor = ent.emission_factor;
            } else {
                b.x = ent.x_pct * GRID_RESOLUTION; b.y = ent.y_pct * GRID_RESOLUTION;
                if (ent.type === 'point') { b.rate = ent.rate; b.stack_height = ent.stack_height; }
                if (ent.type === 'area') { b.radius = ent.radius; b.intensity = ent.intensity; }
                if (ent.type === 'natural_sink') { b.capture_density = ent.capture_density; b.width = ent.width; b.height = ent.height; }
                if (ent.type === 'artificial_sink') { b.capture_capacity = ent.capture_capacity; }
            }
            return b;
        })
    };

    try {
        const res = await fetch('http://localhost:8000/simulate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        renderHeatmap(data.grid);
        updateMetrics(data.grid);
    } catch (e) {
        alert("ENGINE OFFLINE");
    } finally {
        btnSimulate.innerText = "ENGAGE";
    }
});

function renderHeatmap(grid) {
    heatCtx.clearRect(0, 0, heatmapCanvas.width, heatmapCanvas.height);
    const cellW = heatmapCanvas.width / GRID_RESOLUTION;
    const cellH = heatmapCanvas.height / GRID_RESOLUTION;
    for (let r = 0; r < GRID_RESOLUTION; r++) {
        for (let c = 0; c < GRID_RESOLUTION; c++) {
            const val = grid[r][c];
            if (val > 0.1) {
                const {r: red, g, b} = getJetColor(val);
                heatCtx.fillStyle = `rgba(${red}, ${g}, ${b}, 0.6)`;
                heatCtx.fillRect(c * cellW, r * cellH, cellW + 1, cellH + 1);
            }
        }
    }
}

function updateMetrics(grid) {
    let t = 0, m = 0;
    grid.forEach(row => row.forEach(v => { t += v; if (v > m) m = v; }));
    mTotal.innerText = (t / 10).toFixed(1);
    mMax.innerText = m.toFixed(2);
}

btnClear.addEventListener('click', () => {
    entities = [];
    updateUI();
    heatCtx.clearRect(0, 0, heatmapCanvas.width, heatmapCanvas.height);
});
