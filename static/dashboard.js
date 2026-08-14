/**
 * OrbusSim Dummy V2 Dashboard
 * Vanilla JS - No Framework, No Build Step
 */
(function() {
    'use strict';

    // State
    let currentState = null;
    let currentCycleId = null;
    let lastIdleState = false;

    // DOM Elements
    const elements = {
        connIndicator: document.getElementById('conn-indicator'),
        connLabel: document.getElementById('conn-label'),
        hubState: document.getElementById('hub-state'),
        stateValue: document.getElementById('state-value'),
        jobIdValue: document.getElementById('job-id-value'),
        currentStationValue: document.getElementById('current-station-value'),
        tempValue: document.getElementById('temp-value'),
        fluorValue: document.getElementById('fluor-value'),
        progressBar: document.getElementById('station-progress-bar'),
        queueList: document.getElementById('queue-list'),
        queueEmpty: document.getElementById('queue-empty'),
        estopStatus: document.getElementById('estop-status'),
        btnEstopActivate: document.getElementById('btn-estop-activate'),
        btnEstopRelease: document.getElementById('btn-estop-release'),
        estopFeedback: document.getElementById('estop-feedback'),
        chartsHint: document.getElementById('charts-hint'),
        chartTemperature: document.getElementById('chart-temperature'),
        chartFluorescence: document.getElementById('chart-fluorescence'),
        jobTextarea: document.getElementById('job-textarea'),
        btnSubmitJob: document.getElementById('btn-submit-job'),
        jobSubmitFeedback: document.getElementById('job-submit-feedback'),
        carousel: document.getElementById('carousel'),
        activeIndicator: document.getElementById('active-indicator'),
        ringProgress: document.querySelector('.carousel__ring-progress')
    };

    // Station Names
    const stationNames = {
        1: 'Dosing',
        2: 'Mixing',
        3: 'Reaction',
        4: 'Fluorescence',
        5: 'Cleanup'
    };

    /**
     * State Poller (Panel A + Panel D)
     * Polls GET /api/state every 250ms for faster station transition detection
     */
    async function pollState() {
        try {
            const response = await fetch('/api/state');
            if (!response.ok) throw new Error('Failed to fetch state');
            
            const data = await response.json();
            currentState = data;
            
            // Update connection indicator
            setConnectionStatus(true);
            
            // Update telemetry values
            if (elements.stateValue) elements.stateValue.textContent = data.state || 'IDLE';
            if (elements.hubState) elements.hubState.textContent = data.state || 'IDLE';
            if (elements.jobIdValue) elements.jobIdValue.textContent = data.job_id || '-';
            if (elements.currentStationValue) {
                if (data.current_station && data.state === 'RUNNING') {
                    elements.currentStationValue.textContent = `Station ${data.current_station} (${stationNames[data.current_station]})`;
                } else {
                    elements.currentStationValue.textContent = '-';
                }
            }
            
            // Update active station highlight
            updateActiveStation(data);
            
            // Update progress bar
            updateProgressBar(data);
            
            // Update E-Stop status
            updateEstopStatus(data);
            
            // Track cycle_id for telemetry polling
            if (data.cycle_id) {
                currentCycleId = data.cycle_id;
            }
            
            // Extract latest temperature and fluorescence from state if available
            if (data.achieved_parameters) {
                const ap = data.achieved_parameters;
                if (ap.final_temperature_c !== null && ap.final_temperature_c !== undefined) {
                    if (elements.tempValue) elements.tempValue.textContent = `${ap.final_temperature_c.toFixed(1)} °C`;
                }
                if (ap.fluorescence_raw_final_au !== null && ap.fluorescence_raw_final_au !== undefined) {
                    if (elements.fluorValue) elements.fluorValue.textContent = `${ap.fluorescence_raw_final_au.toFixed(2)} a.u.`;
                }
            }
            
        } catch (error) {
            console.error('State poll error:', error);
            setConnectionStatus(false);
        }
    }

    function setConnectionStatus(isConnected) {
        if (isConnected) {
            elements.connIndicator.classList.remove('reconnecting');
            elements.connLabel.textContent = 'live';
        } else {
            elements.connIndicator.classList.add('reconnecting');
            elements.connLabel.textContent = 'reconnecting...';
        }
    }

    function updateActiveStation(data) {
        // Remove all active classes
        document.querySelectorAll('.carousel__station').forEach(station => {
            station.classList.remove('is-active');
        });
        
        // Add active class to current station if RUNNING
        if (data.state === 'RUNNING' && data.current_station >= 1 && data.current_station <= 5) {
            const activeStation = document.querySelector(`.carousel__station[data-station="${data.current_station}"]`);
            if (activeStation) {
                activeStation.classList.add('is-active');
            }
            
            // Update active indicator position on the ring
            updateActiveIndicatorPosition(data.current_station);
        }
        
        // Update carousel ring for E-Stop
        if (data.estop_active) {
            elements.carousel.classList.add('is-estop');
        } else {
            elements.carousel.classList.remove('is-estop');
        }
    }

    /**
     * Update active indicator position on the SVG ring
     * Station positions: 1=0°, 2=72°, 3=144°, 4=216°, 5=288° (clockwise from top)
     */
    function updateActiveIndicatorPosition(station) {
        if (!elements.activeIndicator || !elements.ringProgress) return;
        
        const radius = 140;
        const centerX = 200;
        const centerY = 200;
        
        // Calculate angle: station 1 at top (-90°), then clockwise
        const angleDeg = ((station - 1) * 72) - 90;
        const angleRad = (angleDeg * Math.PI) / 180;
        
        // Calculate position on circle
        const x = centerX + radius * Math.cos(angleRad);
        const y = centerY + radius * Math.sin(angleRad);
        
        // Update indicator position
        elements.activeIndicator.setAttribute('cx', x);
        elements.activeIndicator.setAttribute('cy', y);
        
        // Update progress ring (show progress up to current station)
        const circumference = 2 * Math.PI * radius;
        const progress = station / 5;
        const offset = circumference * (1 - progress);
        elements.ringProgress.style.strokeDashoffset = offset;
    }

    function updateProgressBar(data) {
        if (data.state === 'RUNNING' && data.current_station >= 1) {
            const progress = ((data.current_station - 1) / 5) * 100;
            elements.progressBar.style.width = `${progress}%`;
        } else if (data.state === 'OK' || data.last_job_status === 'OK') {
            elements.progressBar.style.width = '100%';
        } else {
            elements.progressBar.style.width = '0%';
        }
    }

    function updateEstopStatus(data) {
        if (data.estop_active) {
            elements.estopStatus.textContent = 'ACTIVE';
            elements.estopStatus.className = 'estop-status estop-status--active';
        } else {
            elements.estopStatus.textContent = 'nominal';
            elements.estopStatus.className = 'estop-status estop-status--nominal';
        }
    }

    /**
     * Queue Poller (Panel B)
     * Polls GET /api/queue every 2000ms
     */
    async function pollQueue() {
        try {
            const response = await fetch('/api/queue');
            if (!response.ok) throw new Error('Failed to fetch queue');
            
            const files = await response.json();
            
            if (files.length === 0) {
                elements.queueList.innerHTML = '';
                elements.queueEmpty.style.display = 'block';
            } else {
                elements.queueEmpty.style.display = 'none';
                elements.queueList.innerHTML = files.map(file => 
                    `<li>${file}</li>`
                ).join('');
            }
        } catch (error) {
            console.error('Queue poll error:', error);
        }
    }

    /**
     * Telemetry Poller (Panel F Charts)
     * Polls GET /api/jobs/{cycle_id}/telemetry every 3000ms
     */
    async function pollTelemetry() {
        if (!currentCycleId) {
            elements.chartsHint.textContent = 'no job data yet';
            clearCharts();
            return;
        }
        
        try {
            const response = await fetch(`/api/jobs/${currentCycleId}/telemetry`);
            if (!response.ok) {
                if (response.status === 404) {
                    elements.chartsHint.textContent = 'no job data yet';
                    clearCharts();
                    return;
                }
                throw new Error('Failed to fetch telemetry');
            }
            
            const data = await response.json();
            elements.chartsHint.textContent = `showing: ${currentCycleId}`;
            
            // Draw temperature chart
            if (data.temperature && data.temperature.length > 0) {
                drawLineChart(elements.chartTemperature, data.temperature, {
                    color: '#ffb700',
                    unit: '°C',
                    label: 'Temperature'
                });
            } else {
                drawWaitingMessage(elements.chartTemperature, 'waiting for station data...');
            }
            
            // Draw fluorescence chart
            if (data.fluorescence && data.fluorescence.length > 0) {
                drawLineChart(elements.chartFluorescence, data.fluorescence, {
                    color: '#00ff88',
                    unit: 'a.u.',
                    label: 'Fluorescence'
                });
            } else {
                drawWaitingMessage(elements.chartFluorescence, 'waiting for station data...');
            }
            
        } catch (error) {
            console.error('Telemetry poll error:', error);
            elements.chartsHint.textContent = 'error loading data';
        }
    }

    function clearCharts() {
        drawWaitingMessage(elements.chartTemperature, 'waiting for station data...');
        drawWaitingMessage(elements.chartFluorescence, 'waiting for station data...');
    }

    /**
     * Chart Rendering Function
     * Draws a line chart on canvas with glow effect
     */
    function drawLineChart(canvas, data, options) {
        const ctx = canvas.getContext('2d');
        const dpr = window.devicePixelRatio || 1;
        const rect = canvas.getBoundingClientRect();
        
        // Scale canvas for high DPI
        canvas.width = rect.width * dpr;
        canvas.height = rect.height * dpr;
        ctx.scale(dpr, dpr);
        
        const width = rect.width;
        const height = rect.height;
        const padding = { top: 30, right: 30, bottom: 40, left: 50 };
        const chartWidth = width - padding.left - padding.right;
        const chartHeight = height - padding.top - padding.bottom;
        
        // Clear canvas
        ctx.fillStyle = '#0d1117';
        ctx.fillRect(0, 0, width, height);
        
        // Find min/max values
        const xValues = data.map(d => d.time_ms / 1000);
        const yValues = data.map(d => d[Object.keys(d).find(k => k !== 'time_ms')]);
        const xMin = Math.min(...xValues);
        const xMax = Math.max(...xValues);
        const yMin = Math.min(...yValues);
        const yMax = Math.max(...yValues);
        
        // Draw grid
        ctx.strokeStyle = '#30363d';
        ctx.lineWidth = 1;
        
        // Horizontal grid lines
        for (let i = 0; i <= 4; i++) {
            const y = padding.top + (chartHeight / 4) * i;
            ctx.beginPath();
            ctx.moveTo(padding.left, y);
            ctx.lineTo(width - padding.right, y);
            ctx.stroke();
        }
        
        // Vertical grid lines
        for (let i = 0; i <= 4; i++) {
            const x = padding.left + (chartWidth / 4) * i;
            ctx.beginPath();
            ctx.moveTo(x, padding.top);
            ctx.lineTo(x, height - padding.bottom);
            ctx.stroke();
        }
        
        // Draw axes labels
        ctx.fillStyle = '#8b949e';
        ctx.font = '11px "JetBrains Mono"';
        ctx.textAlign = 'center';
        
        // X-axis labels (time in seconds)
        for (let i = 0; i <= 4; i++) {
            const x = padding.left + (chartWidth / 4) * i;
            const time = xMin + ((xMax - xMin) / 4) * i;
            ctx.fillText(`${time.toFixed(0)}s`, x, height - padding.bottom + 20);
        }
        
        // Y-axis labels
        ctx.textAlign = 'right';
        for (let i = 0; i <= 4; i++) {
            const y = padding.top + (chartHeight / 4) * i;
            const value = yMax - ((yMax - yMin) / 4) * i;
            ctx.fillText(value.toFixed(1), padding.left - 10, y + 4);
        }
        
        // Axis titles
        ctx.fillStyle = '#f0f6fc';
        ctx.textAlign = 'center';
        ctx.fillText('Time (s)', width / 2, height - 10);
        
        ctx.save();
        ctx.translate(15, height / 2);
        ctx.rotate(-Math.PI / 2);
        ctx.fillText(options.unit, 0, 0);
        ctx.restore();
        
        // Draw data line with glow
        ctx.beginPath();
        data.forEach((point, index) => {
            const x = padding.left + ((point.time_ms / 1000 - xMin) / (xMax - xMin || 1)) * chartWidth;
            const yValue = point[Object.keys(point).find(k => k !== 'time_ms')];
            const y = padding.top + ((yMax - yValue) / (yMax - yMin || 1)) * chartHeight;
            
            if (index === 0) {
                ctx.moveTo(x, y);
            } else {
                ctx.lineTo(x, y);
            }
        });
        
        // Glow effect
        ctx.strokeStyle = options.color;
        ctx.lineWidth = 3;
        ctx.lineCap = 'round';
        ctx.lineJoin = 'round';
        
        // Outer glow
        ctx.shadowColor = options.color;
        ctx.shadowBlur = 10;
        ctx.stroke();
        
        // Reset shadow
        ctx.shadowBlur = 0;
    }

    function drawWaitingMessage(canvas, message) {
        const ctx = canvas.getContext('2d');
        const dpr = window.devicePixelRatio || 1;
        const rect = canvas.getBoundingClientRect();
        
        canvas.width = rect.width * dpr;
        canvas.height = rect.height * dpr;
        ctx.scale(dpr, dpr);
        
        ctx.fillStyle = '#0d1117';
        ctx.fillRect(0, 0, rect.width, rect.height);
        
        ctx.fillStyle = '#8b949e';
        ctx.font = '12px "JetBrains Mono"';
        ctx.textAlign = 'center';
        ctx.fillText(message, rect.width / 2, rect.height / 2);
    }

    /**
     * E-Stop Button Handlers (Panel C)
     */
    async function handleEstopActivate() {
        try {
            const response = await fetch('/api/estop', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ active: true })
            });
            
            const data = await response.json();
            elements.estopFeedback.textContent = data.message || 'E-Stop triggered';
            elements.estopFeedback.style.color = '#ff4444';
            
            // Refresh state immediately
            pollState();
        } catch (error) {
            elements.estopFeedback.textContent = 'could not reach server';
            elements.estopFeedback.style.color = '#ff4444';
        }
    }

    async function handleEstopRelease() {
        try {
            const response = await fetch('/api/estop', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ active: false })
            });
            
            const data = await response.json();
            elements.estopFeedback.textContent = data.message || 'E-Stop released';
            elements.estopFeedback.style.color = '#00ff88';
            
            // Refresh state immediately
            pollState();
        } catch (error) {
            elements.estopFeedback.textContent = 'could not reach server';
            elements.estopFeedback.style.color = '#ff4444';
        }
    }

    /**
     * Job Submission Handler (Panel E)
     */
    async function handleSubmitJob() {
        const textareaValue = elements.jobTextarea.value.trim();
        
        if (!textareaValue) {
            alert('Please enter a valid JSON payload');
            return;
        }
        
        let payload;
        try {
            payload = JSON.parse(textareaValue);
        } catch (error) {
            alert(`Invalid JSON: ${error.message}`);
            return;
        }
        
        try {
            const response = await fetch('/api/job', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            
            const data = await response.json();
            
            if (response.ok) {
                elements.jobSubmitFeedback.textContent = data.message || 'Job submitted successfully';
                elements.jobSubmitFeedback.style.color = '#00ff88';
                elements.btnSubmitJob.classList.add('is-success');
                setTimeout(() => elements.btnSubmitJob.classList.remove('is-success'), 500);
            } else {
                // Handle validation errors
                const errorDetails = data.detail ? JSON.stringify(data.detail) : 'Validation failed';
                elements.jobSubmitFeedback.textContent = errorDetails;
                elements.jobSubmitFeedback.style.color = '#ff4444';
                elements.btnSubmitJob.classList.add('is-error');
                setTimeout(() => elements.btnSubmitJob.classList.remove('is-error'), 500);
            }
        } catch (error) {
            elements.jobSubmitFeedback.textContent = 'could not reach server';
            elements.jobSubmitFeedback.style.color = '#ff4444';
        }
    }

    /**
     * Initialize Dashboard
     */
    function init() {
        // Bind event listeners
        elements.btnEstopActivate.addEventListener('click', handleEstopActivate);
        elements.btnEstopRelease.addEventListener('click', handleEstopRelease);
        elements.btnSubmitJob.addEventListener('click', handleSubmitJob);
        
        // Start pollers
        pollState();
        pollQueue();
        pollTelemetry();
        
        setInterval(pollState, 150) // Schnelleres Polling für bessere Station-Erkennung (von 250ms auf 150ms reduziert);
        setInterval(pollQueue, 2000);
        setInterval(pollTelemetry, 3000);
        
        console.log('OrbusSim Dummy V2 Dashboard initialized');
    }

    // Boot on DOMContentLoaded
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
