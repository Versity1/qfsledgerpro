// static/js/pwa-install.js
let deferredPrompt;
const installButton = document.getElementById('installPwaButton');

// Hide the button initially
if (installButton) {
    installButton.style.display = 'none';
}

// Listen for the beforeinstallprompt event
window.addEventListener('beforeinstallprompt', (e) => {
    // Prevent the mini-infobar from appearing on mobile
    e.preventDefault();
    // Stash the event so it can be triggered later
    deferredPrompt = e;
    
    // Show the install button
    if (installButton) {
        installButton.style.display = 'block';
        installButton.style.animation = 'fadeIn 0.5s ease-in-out';
    }
    
    // Log for debugging
    console.log('PWA installation available');
});

// Handle install button click
if (installButton) {
    installButton.addEventListener('click', async () => {
        if (!deferredPrompt) {
            alert('Installation already completed or not available');
            return;
        }
        
        // Show the install prompt
        deferredPrompt.prompt();
        
        // Wait for the user to respond to the prompt
        const { outcome } = await deferredPrompt.userChoice;
        
        // Log the outcome
        console.log(`User response to the install prompt: ${outcome}`);
        
        // We've used the prompt, and can't use it again
        deferredPrompt = null;
        
        // Hide the button after installation
        installButton.style.display = 'none';
    });
}

// Track successful installation
window.addEventListener('appinstalled', (evt) => {
    // Log install to analytics
    console.log('PWA was installed');
    
    // Hide the install button
    if (installButton) {
        installButton.style.display = 'none';
    }
    
    // Clear the deferredPrompt
    deferredPrompt = null;
});

// Check if app is already installed
if (window.matchMedia('(display-mode: standalone)').matches) {
    console.log('Running in standalone mode');
    if (installButton) {
        installButton.style.display = 'none';
    }
}