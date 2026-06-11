// Main app logic

document.addEventListener('DOMContentLoaded', () => {
    console.log('[EvaMusic] App loaded');
    
    // Initialize any global handlers
    initProgressBar();
});

function initProgressBar() {
    const progressBar = document.getElementById('progressBar');
    const scrubberBar = document.getElementById('scrubberBar');
    
    if (progressBar) {
        progressBar.addEventListener('click', (e) => {
            const rect = progressBar.getBoundingClientRect();
            const percent = (e.clientX - rect.left) / rect.width;
            const audio = document.getElementById('audioPlayer');
            if (audio.duration) {
                audio.currentTime = percent * audio.duration;
            }
        });
    }
    
    if (scrubberBar) {
        scrubberBar.addEventListener('click', (e) => {
            const rect = scrubberBar.getBoundingClientRect();
            const percent = (e.clientX - rect.left) / rect.width;
            const audio = document.getElementById('audioPlayer');
            if (audio.duration) {
                audio.currentTime = percent * audio.duration;
            }
        });
    }
}
