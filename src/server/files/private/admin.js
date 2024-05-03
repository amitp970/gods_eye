$(document).ready(function () {
    let usersTable = $('#usersTable').DataTable({
        "columns": [
            { 'data': 'username' },
            { 'data': 'role' },
            { 'data': 'remove', 'render': function (data) { return '<button class="btn btn-primary removeUser-btn" data-username=' + data + '>remove</button>' } }
        ],
        "order": [[1, "asc"]],
    });


    function fetchUsers() {
        fetch('/getUsers')
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json()
            })
            .then(data => {
                updateTable(data)
            })
            .catch(error => {
                console.error('There has been a problem with your fetch operation:', error);
            })
    }

    function updateTable(data) {
        usersTable.clear();

        data.forEach(element => {
            let username = element[0]
            let role = element[1]

            usersTable.row.add({
                'username': username,
                'role': role,
                'remove': username
            }).draw(false);
        });
    }


    fetchUsers()

    $('#usersTable tbody').on('click', '.removeUser-btn', function () {
        let username = $(this).data('username');

        fetch('/removeUser', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ 'username': username })
        })
            .then(response => response.json())
            .then(data => {
                console.log('Removal Response:', data);

                if (data.success) {
                    let row = $(this).closest('tr');
                    usersTable.row(row).remove().draw(false);
                }
            })
            .catch(error => {
                console.error('Error Removing User:', error);
            });
    });


    document.getElementById('addUserForm').addEventListener('submit', function (event) {
        event.preventDefault();

        const username = document.getElementById('newUsername').value
        const password = document.getElementById('newPassword').value

        if (username && password) {
            fetch('/addUser', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ username: username, password: password })
            })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        usersTable.row.add({
                            'username': username,
                            'role': 1,
                            'remove': username
                        }).draw(false);
                        this.reset()
                    }
                })
                .catch(error => {
                    console.error('Error:', error)
                });
        }
    })


});