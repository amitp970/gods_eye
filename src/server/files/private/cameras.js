
$(document).ready(function () {
    var connectedCamerasTable = $('#connectedCamerasTable').DataTable({
        "columns": [
            { "data": "ip" },
            { "data": "port" },
            { "data": "location" },
            { "data": "disconnect", "orderable": false }
        ],
        "order": [[2, "desc"]],
        "columnDefs": [{
            "targets": 3,  // Index of the Disconnect column
            "data": "disconnect",
            "render": function (data, type, row, meta) {
                return '<button class="btn btn-primary disconnect-btn" data-host="' + data + '">Disconnect</button>';
            }
        }]
    });

    function fetchConnectedCamerasUpdates() {
        fetch('/get_connected_cameras')
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


    let liveVideosDiv = document.getElementById("liveVideos")

    function addLiveStreamDiv(id, ip, port, location) {
        // Create card container
        const card = document.createElement('div');
        card.className = 'card p-2 container col';
        card.id = `box-${id}`;  // Unique ID for each card

        // Create image container
        const img = document.createElement('img');
        img.id = `live-${id}`;
        img.className = 'row card videoImg m-3';
        card.appendChild(img);

        // Create button container
        const buttonContainer = document.createElement('div');
        buttonContainer.className = 'row m-3';

        // Create Start Video button
        const startBtn = document.createElement('button');
        startBtn.className = 'btn btn-primary startBtn col mx-1';
        startBtn.textContent = 'Start Video';
        startBtn.dataset.host = `${id}`;
        buttonContainer.appendChild(startBtn);

        // Create Stop Video button
        const stopBtn = document.createElement('button');
        stopBtn.className = 'btn btn-primary stopBtn col mx-1';
        stopBtn.textContent = 'Stop Video';
        stopBtn.dataset.host = `${id}`;
        buttonContainer.appendChild(stopBtn);

        // Append button container to card
        card.appendChild(buttonContainer);

        // Append the card to the liveVideos div
        document.getElementById('liveVideos').appendChild(card);
    }

    let connetedCamerasRecord = {};

    function updateTable(data) {
        connectedCamerasTable.clear();  // Clear existing data in the table

        for (const id in data) {
            if (data.hasOwnProperty(id)) {
                const camera = data[id];
                connectedCamerasTable.row.add({
                    "ip": camera.host,
                    "port": camera.port,
                    "location": JSON.stringify(camera.location) || 'Unknown',
                    "disconnect": id
                });

                if (!connetedCamerasRecord.hasOwnProperty(id)) {
                    connetedCamerasRecord[id] = data[id]
                    console.log("adding camera card")
                    addLiveStreamDiv(id, camera.host, camera.port, camera.location)
                }
            } 
        }

        connectedCamerasTable.draw();
    }

    // Event delegation to handle clicks on dynamically created buttons
    $('#connectedCamerasTable tbody').on('click', '.disconnect-btn', function () {
        let id = $(this).data('host');  // Get the IP address from the button's data attribute
        // Send a POST request to the server
        fetch('/disconnect_camera', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({'id' : id})
        })
            .then(response => response.json())
            .then(data => {
                console.log('Disconnection response:', data);
                if (data.success) {
                    let row = $(this).closest('tr');
                    connectedCamerasTable.row(row).remove().draw(false);

                    let videoBox = document.getElementById(`box-${id}`)
                    document.getElementById('liveVideos').removeChild(videoBox)
                }

            })
            .catch(error => {
                console.error('Error disconnecting camera:', error);
            });
    });


    // Attach the event handler to the parent element that exists on page load
    $('#liveVideos').on('click', '.startBtn', function () {
        // This function is called whenever a .startBtn within #liveVideos is clicked
        let id = $(this).data('host');  // Retrieve the host data attribute
        console.log('Starting video for', id);
        // Add your logic here to start the video stream

        fetch('/startLive', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({"id" : id})
        })
        .then(response => response.json())
        .then(data => {
            if(data.success) {
                let socket = io.connect(location.protocol + '//' + document.domain + ':' + '5000');
                socket.on(`live-${id}`, function(data) {
                    var img = document.getElementById(`live-${id}`);
                    img.src = 'data:image/jpeg;base64,' + data.frame;
                });
            }
        })
    });

    $('#liveVideos').on('click', '.stopBtn', function () {
        // This function is called whenever a .stopBtn within #liveVideos is clicked
        let id = $(this).data('host');  // Retrieve the host data attribute
        console.log('Stopping video for', id);
        // Add your logic here to stop the video stream

        fetch('/stopLive', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({"id" : id})
        })
    });


    fetchConnectedCamerasUpdates()

    setInterval(fetchConnectedCamerasUpdates, 5000);  // Fetch updates every 5 seconds
});
