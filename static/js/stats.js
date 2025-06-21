// Global variables for charts
let studentChart = null;
let dashboardData = null; // Initialize dashboard on page load
document.addEventListener("DOMContentLoaded", function () {
  loadDatasets();
  loadDashboardData();

  // Add event listener for dataset selection
  document
    .getElementById("dataset-select")
    .addEventListener("change", function () {
      loadDashboardData();
    });
}); // Load datasets for the selector
async function loadDatasets() {
  try {
    const response = await fetch("/api/datasets");
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const datasets = await response.json();

    const select = document.getElementById("dataset-select");
    select.innerHTML = '<option value="">All Datasets</option>';

    datasets.forEach((dataset) => {
      const option = document.createElement("option");
      option.value = dataset.id;
      option.textContent = `${dataset.hostel_name} (${dataset.total_recipients} recipients)`;
      select.appendChild(option);
    });
  } catch (error) {
    console.error("Error loading datasets:", error);
    const select = document.getElementById("dataset-select");
    select.innerHTML = '<option value="">Error loading datasets</option>';
  }
}

// Load dashboard data from backend
async function loadDashboardData() {
  try {
    const selectedDataset = document.getElementById("dataset-select").value;
    let url = "/api/dashboard-analytics";
    if (selectedDataset) {
      url += `?dataset_id=${selectedDataset}`;
    }

    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    dashboardData = await response.json();

    // Update all dashboard components
    updateStudentStatusChart();
    updateRoomOccupancyProgress();
    updateActivityLog();
    updateStatsPanel();
  } catch (error) {
    console.error("Error loading dashboard data:", error);
    showError("Failed to load dashboard data. Please try refreshing the page.");
  }
} // Create/Update Student Status Donut Chart
function updateStudentStatusChart() {
  const ctx = document.getElementById("studentStatusChart").getContext("2d");

  if (studentChart) {
    studentChart.destroy();
  }

  const data = dashboardData.student_status;
  const stats = dashboardData.statistics;

  // Calculate correct values for the chart
  const totalRegistered = stats.total_recipients; // All registered students
  const checkedIn = data.checked_in; // Students currently checked in
  const remaining = totalRegistered - checkedIn; // Students not yet checked in

  studentChart = new Chart(ctx, {
    type: "doughnut",
    data: {
      labels: ["Registered", "Checked In", "Remaining"],
      datasets: [
        {
          data: [totalRegistered, checkedIn, remaining],
          backgroundColor: [
            "#388bff", // Blue for total registered
            "#ffffff", // Green for checked in
            "#7A8492", // Orange for remaining (not checked in)
          ],
          borderWidth: 3,
          borderColor: "#2c333a",
          hoverBorderWidth: 3,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: "right",

          labels: {
            padding: 35,
            font: {
              size: 14,
              weight: "500",
            },
            boxWidth: 40,
            boxHeight: 20,
            color: "#ffffff",
          },
        },
        tooltip: {
          callbacks: {
            label: function (context) {
              const total = context.dataset.data.reduce((a, b) => a + b, 0);
              const percentage = ((context.parsed / total) * 100).toFixed(1);
              return (
                context.label + ": " + context.parsed + " (" + percentage + "%)"
              );
            },
          },
        },
      },
      cutout: "0%",
      layout: {
        padding: {
          right: 20,
          left: 10,
        },
      },
    },
  });
} // Update Room Occupancy Progress Bar (replacing Chart.js bar chart)
function updateRoomOccupancyProgress() {
  const data = dashboardData.room_occupancy;
  const occupied = data.occupied;
  const total = data.total;
  const remaining = data.remaining;

  // Calculate percentage
  const percentage = total > 0 ? Math.round((occupied / total) * 100) : 0;

  // Update progress bar
  const progressFill = document.getElementById("progress-fill");
  const progressText = document.getElementById("progress-text");
  const occupancyPercentage = document.getElementById("occupancy-percentage");
  const occupiedCount = document.getElementById("occupied-count");
  const remainingCount = document.getElementById("remaining-count");

  // Animate progress bar fill
  setTimeout(() => {
    progressFill.style.width = `${percentage}%`;
  }, 200);

  // Update text elements
  progressText.textContent = `${occupied} / ${total} Rooms`;
  occupancyPercentage.textContent = `${percentage}%`;
  occupiedCount.textContent = occupied;
  remainingCount.textContent = remaining;

  // Update progress bar color based on occupancy level
  if (percentage >= 90) {
    progressFill.style.background = "linear-gradient(90deg, #e74c3c, #c0392b)";
  } else if (percentage >= 70) {
    progressFill.style.background =
      "linear-gradient(90deg, #388bff,rgb(255, 175, 56))";
  } else {
    progressFill.style.background = "linear-gradient(90deg, #388bff, #388bff)";
  }
}

// Update Activity Log
function updateActivityLog() {
  const container = document.getElementById("activity-container");
  const activities = dashboardData.recent_activities;

  if (!activities || activities.length === 0) {
    container.innerHTML = '<div class="no-data">No recent activity found</div>';
    return;
  }

  let tableHTML = `
                <table class="activity-table">
                    <thead>
                        <tr>
                            <th>Name</th>
                            <th>Room</th>
                            <th>Action</th>
                            <th>Timestamp</th>
                        </tr>
                    </thead>
                    <tbody>
            `;
  activities.forEach((activity) => {
    const statusClass =
      activity.action === "Checked In"
        ? "status-checked-in"
        : "status-checked-out";

    // Format timestamp for better display
    let displayTime = activity.timestamp;
    if (displayTime !== "Unknown" && displayTime !== "Recent") {
      try {
        const date = new Date(activity.timestamp);
        displayTime = date.toLocaleString("en-US", {
          month: "short",
          day: "numeric",
          hour: "2-digit",
          minute: "2-digit",
          hour12: true,
        });
      } catch (e) {
        displayTime = activity.timestamp; // fallback to original if parsing fails
      }
    }

    tableHTML += `
                    <tr>
                        <td>${activity.name}</td>
                        <td>${activity.room_no}</td>
                        <td><span class="status-badge ${statusClass}">${activity.action}</span></td>
                        <td class="timestamp">${displayTime}</td>
                    </tr>
                `;
  });

  tableHTML += "</tbody></table>";
  container.innerHTML = tableHTML;
}

// Update Stats Panel
function updateStatsPanel() {
  const container = document.getElementById("stats-container");
  const stats = dashboardData.statistics;

  container.innerHTML = `
                <div class="stat-item">
                    <span class="stat-label">Hostel Name </span>
                    <span class="stat-value  style="color: #388bff;" hostel-name">${
                      stats.hostel_name || "Multiple Hostels"
                    }</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">Total Recipients </span>
                    <span class="stat-value">${stats.total_recipients}</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">Checked In </span>
                    <span class="stat-value" style="color: #2ecc71;">${
                      stats.checked_in
                    }</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">Checked Out </span>
                    <span class="stat-value" style="color: #e74c3c;">${
                      stats.checked_out
                    }</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">Total Rooms </span>
                    <span class="stat-value">${stats.total_rooms}</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">Occupied Rooms </span>
                    <span class="stat-value" style="color: #3498db;">${
                      stats.occupied_rooms
                    }</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">Occupancy Rate </span>
                    <span class="stat-value" style="color: #ffffff;">${
                      stats.occupancy_rate
                    }%</span>
                </div>
            `;
} // Refresh dashboard data
function refreshDashboard() {
  // Show loading state
  document.getElementById("activity-container").innerHTML =
    '<div class="loading">Refreshing activity data...</div>';
  document.getElementById("stats-container").innerHTML =
    '<div class="loading">Refreshing statistics...</div>';

  // Reset progress bar
  document.getElementById("progress-fill").style.width = "0%";
  document.getElementById("progress-text").textContent = "Loading...";

  // Reload data with current dataset selection
  loadDashboardData();
}

// Show error message
function showError(message) {
  const errorHTML = `<div style="color: #e74c3c; text-align: center; padding: 20px;">${message}</div>`;
  document.getElementById("activity-container").innerHTML = errorHTML;
  document.getElementById("stats-container").innerHTML = errorHTML;
}
