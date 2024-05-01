var blacklistMap;

$(document).ready(function() {

    function isEmpty(obj) {
        for (let key in obj) {
            if (obj.hasOwnProperty(key)) {
                return false;
            }
        }
        return true;
    }

    function checkBlacklist() {
        fetch('checkBlacklist')
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok')
            }
            return response.json()
        })
        .then(data => {
            if (!isEmpty(data)) {
                if ($('#blacklistMapContainer').is(':hidden')) {
                    $('#blacklistMapContainer').show();
                }

                displayPersonsOnMap(data)
            }
        })

    }

    function displayPersonsOnMap(persons) {
        // Initialize the map on a specified div element
        try {
            if (blacklistMap) {
                blacklistMap.remove(); // Destroys the map object
            }
            blacklistMap = L.map('blacklistMap').setView([0, 0], 1);
            
        } catch (error) {
            console.error("Failed to initialize the map:", error);
            return; // Exit if the map cannot be initialized
        }
        
    
        // Load and display tile layers on the map (OpenStreetMap)
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: 'Map data &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        }).addTo(blacklistMap);

        const colors = ["red", "blue", "green", "purple", "orange", "yellow", "pink"];
        let colorIndex = 0;

        // Loop through each person and their locations

        persons.forEach(person => {
            console.log(person)
            
            var personIcon = new L.Icon({
                iconUrl: `https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-${colors[colorIndex % colors.length]}.png`,
                shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.3.4/images/marker-shadow.png',
                iconSize: [25, 41],
                iconAnchor: [12, 41],
                popupAnchor: [1, -34],
                shadowSize: [41, 41]
            });

            colorIndex = colorIndex + 1;
                    
            person.locations.forEach(location => {
                // Extract latitude and longitude from each location
                const lat = location.coordinates.lat;
                const lng = location.coordinates.lng;
    
                // Create a marker and add it to the map
                var marker = L.marker([lat, lng], {icon: personIcon}).addTo(blacklistMap);
   
                // Optionally, bind a popup to the marker
                marker.bindPopup(`<strong>Person Name:</strong> ${person.name}<br><strong>Date:</strong> ${location.date}`);
            });
        });
    }

    // Initial check
    checkBlacklist();

    // Set the interval to check every 10 seconds
    setInterval(checkBlacklist, 10000);
});
