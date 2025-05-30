document.addEventListener('DOMContentLoaded', function() {
    let isAuthenticated = false;
    let metricsInterval;

    const authOverlay = document.getElementById('authOverlay');
    const mainContent = document.getElementById('mainContent');
    const loginForm = document.getElementById('loginForm');
    const loginButton = document.getElementById('loginButton');

    const tabSelector = document.querySelector('.tab-selector');
    const tabs = document.querySelectorAll('.tab');
    const tabContents = document.querySelectorAll('.tab-content');
    const pageTitle = document.getElementById('pageTitle');
    const filesTab = document.getElementById('filesTab');

    let currentPath = ''; // Variable to store the current path

    function checkAuthentication() {
        const token = localStorage.getItem('authToken');
        if (token) {
            isAuthenticated = true;
            authOverlay.style.display = 'none';
            mainContent.style.display = 'block';
            startMetricsUpdates();
            showTab('performance');
        } else {
            isAuthenticated = false;
            authOverlay.style.display = 'block';
            mainContent.style.display = 'none';
            stopMetricsUpdates();
        }
    }

    function startMetricsUpdates() {
        if (!metricsInterval) {
            updateMetrics();
            metricsInterval = setInterval(updateMetrics, 1000);
        }
    }

    function stopMetricsUpdates() {
        if (metricsInterval) {
            clearInterval(metricsInterval);
            metricsInterval = null;
        }
    }

    function login() {
        const username = document.getElementById('loginUsername').value;
        const password = document.getElementById('loginPassword').value;

        fetch('/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: `username=${username}&password=${password}`,
        })
        .then(response => {
            if (response.ok) {
                return response.json();
            } else {
                throw new Error('Login failed');
            }
        })
        .then(data => {
            if (data.success) {
                localStorage.setItem('authToken', 'fakeToken');
                isAuthenticated = true;
                checkAuthentication();
            } else {
                alert(data.message || 'Login failed');
            }
        })
        .catch(error => {
            console.error('Error during login:', error);
            alert('Login failed. Please check your credentials.');
        });
    }

    function logout() {
    fetch('/logout')
        .then(response => {
            if (response.status === 302) {
                // Redirect successful, clear localStorage
                localStorage.removeItem('authToken');
                isAuthenticated = false;
                checkAuthentication(); // Update UI
            } else {
                console.error("Logout failed:", response.status);
                alert('Logout failed.');
            }
        })
        .catch(error => {
            console.error("Error during logout:", error);
            alert('Logout failed.');
        });
    }

   function updateMetrics() {
        if (!isAuthenticated) {
            console.log("Not authenticated, skipping metrics update.");
            return; // Don't fetch metrics if not authenticated
        }

        fetch('/api/metrics')
            .then(response => {
                if (response.status === 302) {
                    console.log("Received 302, stopping metrics updates.");
                    stopMetricsUpdates(); // Stop updates on redirect (logout)
                    return; // Stop processing the response
                }
                return response.json();
            })
            .then(data => {
                if (data && data.error) {
                    document.getElementById('error').innerText = "Error: " + data.error;
                    document.getElementById('error').style.display = 'block';
                } else if (data) { // Check if data is not null before updating
                    document.getElementById('error').style.display = 'none';

                    document.getElementById('cpu_usage').innerText = data.cpu_usage;
                    updateProgressBar('cpu', data.cpu_usage);

                    document.getElementById('memory_usage').innerText = data.memory_usage;
                    updateProgressBar('memory', data.memory_usage);

                    document.getElementById('disk_usage').innerText = data.disk_usage;
                    updateProgressBar('disk', data.disk_usage);

                    document.getElementById('uptime').innerText = data.uptime;
                    document.getElementById('disk_read_speed').innerText = data.disk_read_speed;
                }
            })
            .catch(error => {
                console.error("Error fetching metrics:", error);
                document.getElementById('error').innerText = "Error fetching data.";
                document.getElementById('error').style.display = 'block';
            });
    }

    function updateProgressBar(metric, value) {
        const progressBar = document.getElementById(`${metric}_progress`);
        progressBar.style.width = `${value}%`;

        let color = '#50fa7b';
        if (value > 90) {
            color = '#ff5555';
        } else if (value > 70) {
            color = '#f1fa8c';
        }
        progressBar.style.backgroundColor = color;
    }

    function showTab(tabId) {
        // Deactivate all tabs and tab contents
        tabs.forEach(tab => tab.classList.remove('active'));
        tabContents.forEach(content => content.classList.remove('active'));

        // Activate the selected tab and content
        const selectedTab = document.querySelector(`.tab[data-tab="${tabId}"]`);
        const selectedContent = document.getElementById(`${tabId}Tab`);

        if (selectedTab && selectedContent) {
            selectedTab.classList.add('active');
            selectedContent.classList.add('active');

            if (tabId === 'files') {
                loadFiles(); // Load files from the root directory by default
            }
        }

        // Update page title
        if (tabId === 'performance') {
            pageTitle.innerText = 'Server Monitoring';
        } else if (tabId === 'files') {
            pageTitle.innerText = 'File Overview';
        }
    }

    function loadFiles(path = '') {
        currentPath = path; // Update the current path
        fetch(`/files?path=${path}`)
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    filesTab.innerHTML = `<p class="error">Error: ${data.error}</p>`;
                } else {
                    let fileListHTML = '<ul>';
                    data.files.forEach(item => {
                        if (item.type === 'directory') {
                            fileListHTML += `<li class="directory" data-name="${item.name}">
                                               <i class="fas fa-folder"></i> ${item.name}
                                             </li>`;
                        } else if (item.type === 'file') {
                            fileListHTML += `<li class="file" data-name="${item.name}">
                                               <i class="fas fa-file"></i> ${item.name}
                                             </li>`;
                        }
                    });
                    fileListHTML += '</ul>';

                    // Back button
                    if (path !== '') {
                        fileListHTML = `<button id="backButton"><i class="fas fa-arrow-left"></i> Back</button>` + fileListHTML;
                    }

                    filesTab.innerHTML = fileListHTML;

                    // Event listeners for directory clicks
                    document.querySelectorAll('.directory').forEach(dir => {
                        dir.addEventListener('click', function() {
                            const dirName = this.dataset.name;
                            const newPath = path ? `${path}/${dirName}` : dirName;
                            loadFiles(newPath);
                        });
                    });

                    // Event listeners for file clicks
                    document.querySelectorAll('.file').forEach(file => {
                        file.addEventListener('click', function() {
                            const fileName = this.dataset.name;
                            installFile(fileName);
                        });
                    });

                    // Event listener for back button
                    if (path !== '') {
                        document.getElementById('backButton').addEventListener('click', function() {
                            const pathParts = path.split('/');
                            pathParts.pop();
                            const newPath = pathParts.join('/');
                            loadFiles(newPath);
                        });
                    }
                }
            })
            .catch(error => {
                console.error("Error loading files:", error);
                filesTab.innerHTML = '<p class="error">Error loading files.</p>';
            });
    }

   function installFile(filename) {
    const downloadURL = `/install?filename=${filename}&path=${currentPath}`;
    window.location.href = downloadURL;
}
    
/* Logout Event*/
window.addEventListener('beforeunload', function(event) {
    if (isAuthenticated) {
        localStorage.removeItem('authToken');
        // Prevent the browser from caching the page state
        navigator.sendBeacon('/logout', '');//This is to avoid sending the /logout request, because the redirect page can cancel the request
    }
});

    // Event Listeners
    loginButton.addEventListener('click', login);

    tabSelector.addEventListener('click', function(event) {
        if (event.target.classList.contains('tab')) {
            showTab(event.target.dataset.tab);
        }
    });

    checkAuthentication();
});