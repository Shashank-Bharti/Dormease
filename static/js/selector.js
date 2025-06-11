  const dashboard = document.querySelector(".dashboard");
  const verify = document.querySelector(".verify");
  const recipient = document.querySelector(".recipient");
  const datasets = document.querySelector(".datasets");
  const issues = document.querySelector(".issues");
  
  // Get the current page path
  const currentPath = window.location.pathname;
  
  // Set active class based on current path
  if (currentPath.includes('dashboard')) {
    dashboard.style.backgroundColor = "#454F59";
    
  } else if (currentPath.includes('verification')) {
    verify.style.backgroundColor = "#454F59";
    
  } else if (currentPath.includes('recipient')) {
    recipient.style.backgroundColor = "#454F59";
    
  } else if (currentPath.includes('datasets')) {
    datasets.style.backgroundColor = "#454F59";
    
  } else if (currentPath.includes('issues')) {
    issues.style.backgroundColor = "#454F59";
   
  }
  
  // Add click event listeners for click
  dashboard.addEventListener("click", () => {
    window.location.href = "/dashboard";
  });

  verify.addEventListener("click", () => {
    window.location.href = "/verification";
  });

  recipient.addEventListener("click", () => {
    window.location.href = "/recipients";
  });

  datasets.addEventListener("click", () => {
    window.location.href = "/datasets";
  });

  issues.addEventListener("click", () => {
    window.location.href = "/pages/issues.html";
  });