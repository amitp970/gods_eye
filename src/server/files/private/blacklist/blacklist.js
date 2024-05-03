$(document).ready(function() {
    let blacklistTable = $('#blacklistTable').DataTable({
        "columns": [
            {"data": "photo", "render": function(data) { return '<img src="' + data + '" style="width:50px; height:50px; border-radius:50%;"/>'; }},
            {"data": "Name"},
            {"data": "Embeddings Count"},
            {"data": "remove", "orderable": false, "render": function(data, type, row, meta) {
                return '<button class="btn btn-primary remove-btn" data-suspectid="' + data + '">Remove</button>';
            }}
        ],
        "order": [[1, "desc"]]
    });

    function fetchBlacklist() {
        fetch('/getBlacklist')
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
        blacklistTable.clear();
        for (const suspectNum in data) {
            suspect = data[suspectNum]

            console.log(suspect)
            blacklistTable.row.add({
                "photo": suspect.profilePhotoUrl,
                "Name": suspect.fullName,
                "Embeddings Count": suspect.embeddingsCount,
                "remove": suspect.suspectId                    
            })
        }
        blacklistTable.draw();
        
    }

    fetchBlacklist();


    $('#blacklistTable tbody').on('click', '.remove-btn', function() {
        var suspectId = $(this).data('suspectid');

        console.log("Suspectid: ", suspectId)

        fetch('/removeBlacklistSuspect', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({"id" : suspectId})
        })
        .then(response => response.json())
        .then(data => {
            console.log('Suspect Removal response: ', data)

            if (data.success) {
                let row = $(this).closest('tr'); // Find the row element
                blacklistTable.row(row).remove().draw(); // Remove the row from the DataTable and redraw
            }
        })
        .catch(error => {
            console.log('Error removing suspect: ', error)
        });

    });





});