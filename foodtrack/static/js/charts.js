document.addEventListener("DOMContentLoaded", function () {
  const ctx = document.getElementById("spendingChart");

  if (ctx && typeof Chart !== "undefined") {
    new Chart(ctx, {
      type: "line",
      data: {
        labels: labels,
        datasets: [
          {
            label: "Daily Spend (Ksh)",
            data: values,
            borderColor: "#0d6efd",
            backgroundColor: "rgba(13, 110, 253, 0.15)",
            borderWidth: 3,
            tension: 0.4,
            fill: true,
            pointRadius: 5,
            pointBackgroundColor: "#0d6efd",
          },
        ],
      },
      options: {
        plugins: {
          legend: { position: "top" },
          title: { display: false },
        },
        scales: {
          y: {
            beginAtZero: true,
            grid: { color: "rgba(0,0,0,0.05)" },
            ticks: { color: "#333" },
          },
          x: {
            ticks: { color: "#555" },
          },
        },
      },
    });
  }
});

// toggle password visibility
document.addEventListener("DOMContentLoaded", () => {
  const toggleIcons = document.querySelectorAll(".toggle-password");
  toggleIcons.forEach((icon) => {
    icon.addEventListener("click", () => {
      const input = icon.previousElementSibling;
      if (input.type === "password") {
        input.type = "text";
        icon.classList.remove("bi-eye-fill");
        icon.classList.add("bi-eye-slash-fill");
      } else {
        input.type = "password";
        icon.classList.remove("bi-eye-slash-fill");
        icon.classList.add("bi-eye-fill");
      }
    });
  });
});
