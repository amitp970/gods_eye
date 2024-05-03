function analyzeLocationData(data) {
    const locations = data.locations;

    // Total number of location entries
    const totalEntries = locations.length;

    // Date frequency map
    const dateMap = {};
    // Coordinate frequency map
    const coordinateMap = {};

    locations.forEach(location => {
        const fullDate = new Date(location.date.$date);
        const dateString = fullDate.toISOString().split('T')[0]; // Formats to 'YYYY-MM-DD'

        const coordinateString = `${location.coordinates.lat}, ${location.coordinates.lng}`;

        // Counting dates (only by day, ignoring time)
        if (dateMap[dateString]) {
            dateMap[dateString]++;
        } else {
            dateMap[dateString] = 1;
        }

        // Counting coordinates
        if (coordinateMap[coordinateString]) {
            coordinateMap[coordinateString]++;
        } else {
            coordinateMap[coordinateString] = 1;
        }
    });

    // Most frequent date considering only day, not time
    const mostFrequentDate = Object.keys(dateMap).reduce((a, b) => dateMap[a] > dateMap[b] ? a : b);

    // Most frequent coordinates
    const mostFrequentCoordinates = Object.keys(coordinateMap).reduce((a, b) => coordinateMap[a] > coordinateMap[b] ? a : b);

    // Number of unique dates
    const uniqueDatesCount = Object.keys(dateMap).length;

    // Number of unique coordinates
    const uniqueCoordinatesCount = Object.keys(coordinateMap).length;

    // Formatting output as structured JSON
    return {
        totalEntries,
        uniqueCoordinatesCount,
        uniqueDatesCount,
        mostFrequent: {
            date: mostFrequentDate,
            coordinates: mostFrequentCoordinates,
            dateOccurrences: dateMap[mostFrequentDate],
            coordinateOccurrences: coordinateMap[mostFrequentCoordinates]
        },
        dates: dateMap,
        coordinates: coordinateMap,
        avgTimePerLocation: calculateAverageTimePerLocation(locations)
    };
}

function calculateAverageTimePerLocation(locations) {
    const locationsByCoords = {};
    const timeSpent = {};

    locations.forEach((location, index) => {
        const coords = `${location.coordinates.lat}, ${location.coordinates.lng}`;
        const locationDate = new Date(location.date.$date);

        if (!locationsByCoords[coords]) {
            locationsByCoords[coords] = [];
        }
        locationsByCoords[coords].push(locationDate);
    });

    // Calculate total time spent at each coordinate
    Object.keys(locationsByCoords).forEach(coords => {
        const times = locationsByCoords[coords].sort((a, b) => a - b);
        let totalDuration = 0;
        let visitCount = 0;

        for (let i = 0; i < times.length; i++) {
            if (i + 1 < times.length) {
                // Calculate difference between consecutive timestamps
                const diff = (times[i + 1] - times[i]) / 1000; // difference in minutes
                console.log("time diff: ", diff)
                if (diff <= 15 * 60) {
                    totalDuration += diff;
                } else {
                    visitCount++;
                }
            } else {
                // Last timestamp, close out the last visit
                visitCount++;
            }
        }

        if (visitCount > 0) {
            timeSpent[coords] = totalDuration / visitCount;
        } else {
            timeSpent[coords] = 0; // handle cases where there is only one timestamp and no duration can be computed
        }
    });

    return timeSpent;
}


var statsTable = $('#avgTimeTable').DataTable({
    "columns": [
        { "data": "location" },
        { "data": "averageTime" }
    ],
    "order": [[1, "desc"]]
});;

let datesChart;
let locationChart;


function renderStats(stats) {
    document.getElementById("totalSightings").innerText = `Total Sightings: ${stats.totalEntries}` 
    document.getElementById("uniqueLocationsCount").innerText = `Unique Locations Count: ${stats.uniqueCoordinatesCount}`
    document.getElementById("uniqueDatesCount").innerText = `Unique Dates Count: ${stats.uniqueDatesCount}`
    
    
    document.getElementById("mf_date").innerText = `Date: ${stats.mostFrequent.date}`
    document.getElementById("mf_dateOcurrences").innerText = `Date Ocurrences Count: ${stats.mostFrequent.dateOccurrences}`
    
    document.getElementById("mf_location").innerText = `Location: ${stats.mostFrequent.coordinates}`
    document.getElementById("mf_locationOcurrences").innerText = `Location Ocurrences Count: ${stats.mostFrequent.coordinateOccurrences}`
    
    
    statsTable.clear()
    
    console.log("avg: ",stats.avgTimePerLocation)
    
    for (const loc_cords in stats.avgTimePerLocation) {
        statsTable.row.add({
            "location" : JSON.stringify(loc_cords),
            "averageTime": stats.avgTimePerLocation[loc_cords]
        }).draw(false);
    }
    
    const datesCtx = document.getElementById('datesGraph').getContext('2d');
    const locationsCtx = document.getElementById('locationsGraph').getContext('2d');


    if(datesChart) {
        datesChart.destroy()
    }

    datesChart = new Chart(datesCtx, {
        type: 'bar',
        data: {
            labels: Object.keys(stats.dates),
            datasets: [{
                label: 'Number of Sightings',
                data: Object.values(stats.dates),
                backgroundColor: 'rgba(54, 162, 235, 0.2)',
                borderColor: 'rgba(54, 162, 235, 1)',
                borderWidth: 1
            }]
        },
        options: {
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });

    if(locationChart) {
        locationChart.destroy()
    }

    locationChart = new Chart(locationsCtx, {
        type: 'bar',
        data: {
            labels: Object.keys(stats.coordinates),
            datasets: [{
                label: 'Number of Sightings',
                data: Object.values(stats.coordinates),
                backgroundColor: 'rgba(54, 162, 235, 0.2)',
                borderColor: 'rgba(54, 162, 235, 1)',
                borderWidth: 1
            }]
        },
        options: {
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });


}