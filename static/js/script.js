// تصفية الجداول
document.addEventListener("DOMContentLoaded", function () {
  // تصفية جدول الموظفين
  const departmentFilter = document.getElementById("departmentFilter");
  const statusFilter = document.getElementById("statusFilter");
  const searchInput = document.getElementById("searchInput");
  const tableRows = document.querySelectorAll(".data-table tbody tr");

  // في static/js/script.js - تأكد من أن الفلترة تستخدم القيم الصحيحة
  function filterTable() {
    const departmentValue = departmentFilter.value;
    const statusValue = statusFilter.value;
    const searchValue = searchInput.value.toLowerCase();

    tableRows.forEach((row) => {
      const department = row.getAttribute("data-department");
      const status = row.getAttribute("data-status");
      const rowText = row.textContent.toLowerCase();

      const departmentMatch =
        !departmentValue || department === departmentValue;
      const statusMatch = !statusValue || status === statusValue;
      const searchMatch = !searchValue || rowText.includes(searchValue);

      if (departmentMatch && statusMatch && searchMatch) {
        row.style.display = "";
      } else {
        row.style.display = "none";
      }
    });
  }
  if (departmentFilter)
    departmentFilter.addEventListener("change", filterTable);
  if (statusFilter) statusFilter.addEventListener("change", filterTable);
  if (searchInput) searchInput.addEventListener("input", filterTable);

  // المخططات البيانية
  if (document.getElementById("departmentChart")) {
    renderCharts();
  }
});

// عرض المخططات البيانية
function renderCharts() {
  // مخطط توزيع الأقسام
  const departmentCtx = document
    .getElementById("departmentChart")
    .getContext("2d");
  const departmentChart = new Chart(departmentCtx, {
    type: "doughnut",
    data: {
      labels: ["تكنولوجيا المعلومات", "المبيعات", "المالية", "الموارد البشرية"],
      datasets: [
        {
          data: [12, 8, 6, 4],
          backgroundColor: ["#3498db", "#e74c3c", "#2ecc71", "#f39c12"],
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: "bottom",
          rtl: true,
        },
      },
    },
  });

  // مخطط توزيع الرواتب
  const salaryCtx = document.getElementById("salaryChart").getContext("2d");
  const salaryChart = new Chart(salaryCtx, {
    type: "bar",
    data: {
      labels: ["أقل من 10,000", "بين 10,000 و 20,000", "أكثر من 20,000"],
      datasets: [
        {
          label: "عدد الموظفين",
          data: [8, 15, 7],
          backgroundColor: "#3498db",
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: {
          beginAtZero: true,
        },
      },
    },
  });
}

// التحقق من صحة النماذج
function validateEmployeeForm() {
  const form = document.querySelector(".employee-form");
  const requiredFields = form.querySelectorAll("[required]");
  let isValid = true;

  requiredFields.forEach((field) => {
    if (!field.value.trim()) {
      field.style.borderColor = "#e74c3c";
      isValid = false;
    } else {
      field.style.borderColor = "#bdc3c7";
    }
  });

  if (!isValid) {
    alert("يرجى ملء جميع الحقول الإلزامية");
  }

  return isValid;
}

// إدارة التنبيهات
function showAlert(message, type = "success") {
  const alertDiv = document.createElement("div");
  alertDiv.className = `alert alert-${type}`;
  alertDiv.textContent = message;

  const container = document.querySelector(".container");
  container.insertBefore(alertDiv, container.firstChild);

  setTimeout(() => {
    alertDiv.remove();
  }, 5000);
}

// البحث المتقدم
function advancedSearch() {
  // يمكن إضافة وظائف بحث متقدم هنا
  console.log("الباحث المتقدم قيد التطوير...");
}
