const loginBtn = document.getElementById('loginBtn');
const logoutBtn = document.getElementById('logoutBtn');
const downloadBtn = document.getElementById('downloadBtn');
const statusDiv = document.getElementById('status');
const loginSection = document.getElementById('loginSection');
const downloadSection = document.getElementById('downloadSection');
const progressContainer = document.getElementById('progressContainer');
const progressBar = document.getElementById('progressBar');
const progressStatus = document.getElementById('progressStatus');

// Variable para controlar la animación de progreso
let currentProgress = 0;
let targetProgress = 0;
let animationFrameId = null;

/**
 * Animar la barra de progreso suavemente
 */
function animateProgressBar() {
    if (currentProgress < targetProgress) {
        // Usar easing function para una animación suave
        currentProgress += (targetProgress - currentProgress) * 0.15;

        if (currentProgress > targetProgress - 0.5) {
            currentProgress = targetProgress;
        }

        progressBar.style.width = `${currentProgress}%`;
        const progressText = progressBar.querySelector('.progress-text');
        if (progressText) {
            progressText.textContent = `${Math.round(currentProgress)}%`;
        }

        animationFrameId = requestAnimationFrame(animateProgressBar);
    } else {
        cancelAnimationFrame(animationFrameId);
        animationFrameId = null;
    }
}

/**
 * Convert array of arrays to CSV format
 * @param {Array<Array<string>>} data - Array of rows (each row is an array of strings)
 * @returns {string} CSV formatted string
 */
function convertToCSV(data) {
    return data.map(row =>
        row.map(cell => {
            // Escape quotes and wrap in quotes if contains special characters
            if (typeof cell === 'string' && (cell.includes('"') || cell.includes(',') || cell.includes('\n'))) {
                return `"${cell.replace(/"/g, '""')}"`;
            }
            return cell;
        }).join(',')
    ).join('\n');
}

/**
 * Download a file to the user's downloads folder
 * @param {string} content - File content
 * @param {string} filename - File name
 * @param {string} mimeType - MIME type
 */
function downloadFile(content, filename, mimeType = 'text/csv') {
    const blob = new Blob([content], { type: mimeType });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
}

/**
 * Download data with progress tracking using Server-Sent Events.
 */
async function downloadWithProgress() {
    if (!progressContainer || !progressBar || !progressStatus) {
        console.error('Progress elements not found');
        return;
    }

    progressContainer.style.display = 'block';
    downloadBtn.disabled = true;
    logoutBtn.disabled = true;

    // Reset progress
    currentProgress = 0;
    targetProgress = 0;
    progressBar.style.width = '0%';

    try {
        const eventSource = new EventSource('/api/export/progress');

        eventSource.onmessage = (event) => {
            const data = JSON.parse(event.data);

            if (data.error) {
                progressStatus.textContent = `❌ Error: ${data.error}`;
                eventSource.close();
                downloadBtn.disabled = false;
                logoutBtn.disabled = false;
                return;
            }

            // Update target progress (will be animated smoothly)
            targetProgress = data.progress || 0;

            // Start animation if not already running
            if (!animationFrameId) {
                animateProgressBar();
            }

            progressStatus.textContent = data.status || 'Procesando...';

            // When complete, download files
            if (targetProgress === 100 && data.playlists && data.tracks) {
                eventSource.close();
                downloadCSVFiles(data.playlists, data.playlists_headers, data.tracks);

                // Hide progress bar after 2 seconds
                setTimeout(() => {
                    progressContainer.style.display = 'none';
                    progressStatus.textContent = 'Descargando...';
                    currentProgress = 0;
                    targetProgress = 0;
                    progressBar.style.width = '0%';
                    downloadBtn.disabled = false;
                    logoutBtn.disabled = false;
                }, 2000);
            }
        };

        eventSource.onerror = (error) => {
            console.error('EventSource error:', error);
            progressStatus.textContent = '❌ Error en la conexión';
            eventSource.close();
            downloadBtn.disabled = false;
            logoutBtn.disabled = false;
        };

    } catch (error) {
        console.error('Error:', error);
        progressStatus.textContent = `❌ Error: ${error}`;
        downloadBtn.disabled = false;
        logoutBtn.disabled = false;
    }
}/**
 * Download multiple CSV files.
 * 
 * @param {Array<Array>} playlists - Array of playlist data
 * @param {Array<string>} playlistsHeaders - Headers for playlists CSV
 * @param {Array<Array>} tracks - Array of track data
 */
function downloadCSVFiles(playlists, playlistsHeaders, tracks) {
    const date = new Date().toISOString().split('T')[0];

    // Download playlists CSV
    const playlistsCSV = convertToCSV([playlistsHeaders, ...playlists]);
    downloadFile(playlistsCSV, `playlists_${date}.csv`);

    // Download tracks CSV
    const tracksCSV = convertToCSV(tracks);
    downloadFile(tracksCSV, `tracks_${date}.csv`);

    // Show success message
    statusDiv.textContent = '✅ Archivos descargados correctamente a tu carpeta de descargas';
    statusDiv.className = 'status success';

    setTimeout(() => {
        statusDiv.textContent = '';
        statusDiv.className = 'status';
    }, 5000);
}

// Check authentication status and update UI
async function checkAuthStatus() {
    try {
        const response = await fetch('/api/auth/status');
        const data = await response.json();

        if (data.authenticated) {
            loginSection.style.display = 'none';
            downloadSection.style.display = 'block';
        } else {
            loginSection.style.display = 'block';
            downloadSection.style.display = 'none';
        }
    } catch (error) {
        console.error('Error checking auth status:', error);
        loginSection.style.display = 'block';
        downloadSection.style.display = 'none';
    }
}

// Login button handler
loginBtn.addEventListener('click', async () => {
    try {
        const response = await fetch('/api/auth/login');
        const data = await response.json();
        window.location.href = data.auth_url;
    } catch (error) {
        console.error('Error:', error);
        statusDiv.textContent = `❌ Error al iniciar sesión: ${error.message}`;
        statusDiv.className = 'status error';
    }
});

// Logout button handler
logoutBtn.addEventListener('click', async () => {
    try {
        await fetch('/api/auth/logout', { method: 'POST' });
        await checkAuthStatus();
        statusDiv.textContent = '✅ Sesión cerrada';
        statusDiv.className = 'status success';
        setTimeout(() => {
            statusDiv.textContent = '';
            statusDiv.className = 'status';
        }, 3000);
    } catch (error) {
        console.error('Error:', error);
        statusDiv.textContent = `❌ Error al cerrar sesión: ${error.message}`;
        statusDiv.className = 'status error';
    }
});

// Download button handler with progress tracking
downloadBtn.addEventListener('click', downloadWithProgress);

// Check auth status on page load
window.addEventListener('load', checkAuthStatus);