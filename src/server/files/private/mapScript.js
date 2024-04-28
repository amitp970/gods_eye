var map;

function initMap(locations) {
    // Initialize the map on the "map" div
    try {
        if (map) {
            map.remove(); // Destroys the map object
        }
        map = L.map('map').setView([0, 0], 1);
        
    } catch (error) {
        console.error("Failed to initialize the map:", error);
        return; // Exit if the map cannot be initialized
    }
    

    // Load and display tile layers on the map (OpenStreetMap by default)
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution: '© OpenStreetMap contributors'
    }).addTo(map);

    // Add markers for each location
    locations.forEach(location => {
        if (location.date) { // Ensure there is a valid date
            L.marker([location.coordinates.lat, location.coordinates.lng]) // Latitude and longitude required
                .addTo(map)
                .bindPopup(`Date: ${location.date.toISOString()}`); // Bind a popup with the date
        }
    });

    // Adjust map view to show all markers
    if (locations.length) {
        var group = new L.featureGroup(locations.map(location => L.marker([location.coordinates.lat, location.coordinates.lng])));
        if (group.getLayers().length > 0) {  // Check if there are any layers
            map.fitBounds(group.getBounds().pad(0.5));
        }
    }
    
}

initMap()