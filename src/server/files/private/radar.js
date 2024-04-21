$(document).ready(function() {
    var table = $('#cameraRadarTable').DataTable({
        "columns": [
            { "data": "ip" },
            { "data": "port" },
            { "data": "location" },
            { "data": "last_seen" },
            { "data": "connect", "orderable": false }
        ],
        "order": [[3, "desc"]],
        "columnDefs": [{
            "targets": 4,  // Index of the Connect column
            "data": "connect",
            "render": function(data, type, row, meta) {
                return '<button class="btn btn-primary connect-btn" data-ip="' + row.ip + '">Connect</button>';
            }
        }]
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
                    "last_seen": new Date(camera.last_seen * 1000).toLocaleString(),
                    "connect": null                    
                }).draw(false);  // Add new row and redraw the table
            }
        }
    }

    // Event delegation to handle clicks on dynamically created buttons
    $('#cameraRadarTable tbody').on('click', '.connect-btn', function() {
        var ip = $(this).data('ip');  // Get the IP address from the button's data attribute
        console.log("Connecting to IP:", ip);
        // Send a POST request to the server
        fetch('/connect_camera', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({'IP': ip})
        })
        .then(response => response.json())
        .then(data => {
            console.log('Connection response:', data);
            alert('Connection attempted to IP: ' + ip);
        })
        .catch(error => {
            console.error('Error connecting to camera:', error);
        });
    });

    setInterval(fetchCameraRadarUpdates, 5000);  // Fetch updates every 5 seconds
});
