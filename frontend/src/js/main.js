// Main JavaScript file for MutualAid

// Initialize tooltips
const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
const tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
    return new bootstrap.Tooltip(tooltipTriggerEl);
});

// Initialize popovers
const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
const popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
    return new bootstrap.Popover(popoverTriggerEl);
});

// Add active class to current nav link
document.addEventListener('DOMContentLoaded', function() {
    const currentLocation = location.pathname;
    document.querySelectorAll('.nav-link').forEach(link => {
        if(link.getAttribute('href') === currentLocation) {
            link.classList.add('active');
            link.setAttribute('aria-current', 'page');
        }
    });
});

// Example of making an API call
async function fetchData(endpoint) {
    try {
        const response = await fetch(`/api/v1/${endpoint}`);
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return await response.json();
    } catch (error) {
        console.error('Error fetching data:', error);
        throw error;
    }
}
