// Initialize DataTable just once when the document is ready
$(document).ready(function () {

    // Listen for form submissions to update the DataTable
    document.getElementById('blacklistForm').addEventListener('submit', function (event) {
        event.preventDefault();
        // Your existing form submission handling logic here...
        const fullName = document.getElementById('fullName2').value;
        const fileInput = document.getElementById('suspectImages2');
        const files = fileInput.files;

        if (files.length > 0) {
            let imagesAsBase64 = [];
            let filesProcessed = 0;

            Array.from(files).forEach(file => {
                if (file.type.startsWith('image/')) {
                    const reader = new FileReader();
                    reader.onload = function (e) {
                        imagesAsBase64.push(e.target.result); // Add base64 encoding of the image to array
                        filesProcessed++;

                        // Check if all files have been processed
                        if (filesProcessed === files.length) {
                            const jsonData = {
                                fullName: fullName,
                                images: imagesAsBase64
                            };

                            // Send JSON data via fetch
                            fetch('/addSuspectToBlacklist', {
                                method: 'POST',
                                headers: {
                                    'Content-Type': 'application/json'
                                },
                                body: JSON.stringify(jsonData)
                            })
                                .then(response => response.json())
                                .then(data => {
                                    console.log('Success:', data);

                                    firstFile = files[0]

                                    // photo = firstFile ? URL.createObjectURL(firstFile) : null 

                                    // Update the blacklist table
                                    if (data.success) {
                                        // Assume data object contains necessary suspect details
                                        $('#blacklistTable').DataTable().row.add({
                                            "photo": data.profilePhotoUrl,
                                            "Name": fullName,
                                            "Embeddings Count": data.embeddingsCount,
                                            "remove": data.id
                                        }).draw(false);
                                    }
                                })
                                .catch(error => console.error('Error:', error));
                        }
                    };
                    reader.readAsDataURL(file); // Converts the image to base64
                } else {
                    console.error('All files must be JPEG images.');
                }
            });
        } else {
            console.error('Please upload at least one JPEG image.');
        }


    });
});


document.getElementById('searchSuspectForm').addEventListener('submit', function (event) {
    event.preventDefault();

    const fullName = document.getElementById('fullName1').value;
    const fileInput = document.getElementById('suspectImages1');
    const files = fileInput.files;

    if (files.length > 0) {
        let imagesAsBase64 = [];
        let filesProcessed = 0;

        Array.from(files).forEach(file => {
            if (file.type.startsWith('image/')) {
                const reader = new FileReader();
                reader.onload = function (e) {
                    imagesAsBase64.push(e.target.result); // Add base64 encoding of the image to array
                    filesProcessed++;

                    // Check if all files have been processed
                    if (filesProcessed === files.length) {
                        const jsonData = {
                            fullName: fullName,
                            images: imagesAsBase64
                        };

                        // Send JSON data via fetch
                        fetch('/searchSuspect', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify(jsonData)
                        })
                            .then(response => response.json())
                            .then(data => {
                                console.log('Success:', data);
                                // Assume data.locations is available and contains lat, lng
                                initMap(data.locations.map(location => ({
                                    coordinates: {
                                        'lat': parseFloat(location.coordinates.lat),
                                        'lng': parseFloat(location.coordinates.lng)
                                    },
                                    date: new Date(location.date.$date)
                                })));

                                analysisData = analyzeLocationData(data)

                                renderStats(analysisData)
                            })
                            .catch(error => {
                                console.error('Error:', error)
                                initMap()
                            });
                    }
                };
                reader.readAsDataURL(file); // Converts the image to base64
            } else {
                console.error('All files must be JPEG images.');
            }
        });
    } else {
        console.error('Please upload at least one JPEG image.');
    }
});
