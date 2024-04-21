$(document).ready(function() {
    var table = $('#cameraRadarTable').DataTable({
        "columns": [
            { "data": "ip" },
            { "data": "port" },
            { "data": "location" },
            { "data": "last_seen" }
        ],
        "order": [[3, "desc"]]
    });

    function fetchCameraRadarUpdates() {
        fetch('/get_updated_camera_radar')
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                updateTable(data);
            })
            .catch(error => {
                console.error('There has been a problem with your fetch operation:', error);
            });
    }

    function updateTable(data) {
        table.clear();  // Clear existing data in the table
        for (const ip in data) {
            if (data.hasOwnProperty(ip)) {
                const camera = data[ip];
                table.row.add({
                    "ip": ip,
                    "port": camera.port,
                    "location": camera.location || 'Unknown',
                    "last_seen": new Date(camera.last_seen * 1000).toLocaleString()
                }).draw(false);  // Add new row and redraw the table
            }
        }
    }

    setInterval(fetchCameraRadarUpdates, 5000);  // Fetch updates every 5 seconds
});
