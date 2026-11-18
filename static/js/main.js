/**
 * CarePoint Hospital Management System - Frontend JavaScript
 * Handles navigation toggling, modal confirmations, dynamic dropdown cascading,
 * and client-side form validation.
 */

document.addEventListener("DOMContentLoaded", () => {
    // 1. Mobile Sidebar Toggle
    const menuToggle = document.getElementById("menuToggle");
    const sidebar = document.querySelector(".sidebar");

    if (menuToggle && sidebar) {
        menuToggle.addEventListener("click", () => {
            sidebar.classList.toggle("open");
        });

        // Close sidebar when clicking outside on mobile
        document.addEventListener("click", (e) => {
            if (window.innerWidth <= 992) {
                if (!sidebar.contains(e.target) && !menuToggle.contains(e.target) && sidebar.classList.contains("open")) {
                    sidebar.classList.remove("open");
                }
            }
        });
    }

    // 2. Alert Dismissal
    const alertCloses = document.querySelectorAll(".alert-close");
    alertCloses.forEach(btn => {
        btn.addEventListener("click", () => {
            const alert = btn.closest(".alert");
            if (alert) {
                alert.style.opacity = "0";
                setTimeout(() => alert.remove(), 200);
            }
        });
    });

    // 3. Delete Confirmation Modal
    const deleteModal = document.getElementById("deleteModal");
    const deleteForm = document.getElementById("deleteModalForm");
    const deleteMessage = document.getElementById("deleteModalMessage");
    const cancelDeleteBtn = document.getElementById("cancelDeleteBtn");

    window.openDeleteModal = function(actionUrl, recordType, recordName) {
        if (!deleteModal || !deleteForm) return;
        deleteForm.action = actionUrl;
        if (deleteMessage) {
            deleteMessage.textContent = `Are you sure you want to delete ${recordType} "${recordName}"? This action will check database referential integrity and cannot be undone.`;
        }
        deleteModal.classList.add("active");
    };

    if (cancelDeleteBtn && deleteModal) {
        cancelDeleteBtn.addEventListener("click", () => {
            deleteModal.classList.remove("active");
        });

        deleteModal.addEventListener("click", (e) => {
            if (e.target === deleteModal) {
                deleteModal.classList.remove("active");
            }
        });
    }

    // 4. Dynamic Appointment and Patient Filtering for Medical Records
    const medRecordPatient = document.getElementById("med_patient_id");
    const medRecordDoctor = document.getElementById("med_doctor_id");
    const medRecordAppointment = document.getElementById("med_appointment_id");

    if (medRecordPatient && medRecordAppointment) {
        medRecordPatient.addEventListener("change", () => {
            const selectedPatient = medRecordPatient.value;
            const options = medRecordAppointment.querySelectorAll("option");

            options.forEach(opt => {
                if (!opt.value) {
                    opt.style.display = ""; // Keep placeholder
                    return;
                }
                const optPatient = opt.getAttribute("data-patient");
                if (!selectedPatient || optPatient === selectedPatient) {
                    opt.style.display = "";
                } else {
                    opt.style.display = "none";
                    if (opt.selected) {
                        medRecordAppointment.value = "";
                    }
                }
            });
        });

        medRecordAppointment.addEventListener("change", () => {
            const selectedOpt = medRecordAppointment.options[medRecordAppointment.selectedIndex];
            if (selectedOpt && selectedOpt.value) {
                const optPatient = selectedOpt.getAttribute("data-patient");
                const optDoctor = selectedOpt.getAttribute("data-doctor");

                if (optPatient && medRecordPatient) {
                    medRecordPatient.value = optPatient;
                }
                if (optDoctor && medRecordDoctor) {
                    medRecordDoctor.value = optDoctor;
                }
            }
        });
    }

    // 5. Dynamic Appointment Filtering for Billing Form
    const billPatient = document.getElementById("bill_patient_id");
    const billAppointment = document.getElementById("bill_appointment_id");

    if (billPatient && billAppointment) {
        const filterBillingAppointments = () => {
            const selectedPatient = billPatient.value;
            const options = billAppointment.querySelectorAll("option");

            options.forEach(opt => {
                if (!opt.value) {
                    opt.style.display = "";
                    return;
                }
                const optPatient = opt.getAttribute("data-patient");
                if (!selectedPatient || optPatient === selectedPatient) {
                    opt.style.display = "";
                } else {
                    opt.style.display = "none";
                    if (opt.selected) {
                        billAppointment.value = "";
                    }
                }
            });
        };

        billPatient.addEventListener("change", filterBillingAppointments);
        // Initial run in case form loaded with pre-selected patient
        if (billPatient.value) {
            filterBillingAppointments();
        }

        billAppointment.addEventListener("change", () => {
            const selectedOpt = billAppointment.options[billAppointment.selectedIndex];
            if (selectedOpt && selectedOpt.value) {
                const optPatient = selectedOpt.getAttribute("data-patient");
                if (optPatient && billPatient && !billPatient.value) {
                    billPatient.value = optPatient;
                }
            }
        });
    }

    // 6. Client-side Form Validation Helpers
    const amountInputs = document.querySelectorAll('input[type="number"][name="amount"]');
    amountInputs.forEach(input => {
        input.addEventListener("input", () => {
            if (parseFloat(input.value) < 0) {
                input.setCustomValidity("Amount cannot be negative.");
            } else {
                input.setCustomValidity("");
            }
        });
    });
});

