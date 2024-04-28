// function postFormData(formId, serverEndpointURL) {
//     return function(event) {
//         event.preventDefault(); // Prevent the default form submission

//         const uploadForm = document.getElementById(formId);
//         const formData = new FormData(uploadForm); // Gather form data

//         fetch(serverEndpointURL, { // URL to server endpoint
//             method: 'POST',
//             body: formData
//         })
//         .then(response => response.json())
//         .then(data => {
//             console.log('Success:', data); // Handle success here
//         })
//         .catch((error) => {
//             console.error('Error:', error); // Handle errors here
//         });
//     };
//   }

// document.addEventListener("DOMContentLoaded", function() {
//     const formId = 'searchSuspectForm'; // Assuming 'uploadForm' is the ID of your form
//     const serverEndpointURL = '/searchSuspect'; // Replace with your actual endpoint

//     const formElement = document.getElementById(formId);
//     formElement.addEventListener('submit', postFormData(formId, serverEndpointURL));
// });

// document.addEventListener("DOMContentLoaded", function() {
//     const formId = 'blacklistForm'; // Assuming 'uploadForm' is the ID of your form
//     const serverEndpointURL = '/addSuspectToBlacklist'; // Replace with your actual endpoint

//     const formElement = document.getElementById(formId);
//     formElement.addEventListener('submit', postFormData(formId, serverEndpointURL));
// });



document.getElementById('searchSuspectForm').addEventListener('submit', function(event) {
    event.preventDefault();

    const fullName = document.getElementById('fullName1').value;
    const fileInput = document.getElementById('suspectImages1');
    const files = fileInput.files;

    if (files.length > 0) {
        let imagesAsBase64 = [];
        let filesProcessed = 0;

        Array.from(files).forEach(file => {
            if (file.type === "image/jpeg") {
                const reader = new FileReader();
                reader.onload = function(e) {
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





document.getElementById('blacklistForm').addEventListener('submit', function(event) {
    event.preventDefault();

    const fullName = document.getElementById('fullName2').value;
    const fileInput = document.getElementById('suspectImages2');
    const files = fileInput.files;

    if (files.length > 0) {
        let imagesAsBase64 = [];
        let filesProcessed = 0;

        Array.from(files).forEach(file => {
            if (file.type === "image/jpeg") {
                const reader = new FileReader();
                reader.onload = function(e) {
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
                        .then(data => console.log('Success:', data))
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

