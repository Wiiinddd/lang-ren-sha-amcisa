function getRoleCountElement(roleName) {
    return document.getElementById(roleName + "-count");
}


function getRoleValue(roleName) {
    return Number(getRoleCountElement(roleName).textContent);
}


function setRoleValue(roleName, value) {
    getRoleCountElement(roleName).textContent = value;
}


function changeRoleCount(roleName, change) {
    const currentValue = getRoleValue(roleName);
    const newValue = Math.max(currentValue + change, 0);

    setRoleValue(roleName, newValue);
    updateSelectedRoleCount();
}


function getAllRoleNames() {
    return Array.from(document.querySelectorAll(".role-row")).map(row => row.dataset.role);
}


function getRoleCounts() {
    const roleCounts = {};

    getAllRoleNames().forEach(roleName => {
        roleCounts[roleName] = getRoleValue(roleName);
    });

    return roleCounts;
}


function getTotalSelectedRoles() {
    return Object.values(getRoleCounts()).reduce((total, count) => total + count, 0);
}


function setMessage(text, color) {
    const message = document.getElementById("assign-message");

    if (message) {
        message.textContent = text;
        message.style.color = color;
    }
}


function updateSelectedRoleCount() {
    const playerCount = Number(document.getElementById("player-count").textContent);
    const selectedRoleCount = getTotalSelectedRoles();
    const display = document.getElementById("selected-role-count");

    if (display) {
        display.textContent = selectedRoleCount;
    }

    if (selectedRoleCount > playerCount) {
        setMessage("Too many roles selected", "#f87171");
    } else if (selectedRoleCount < playerCount) {
        setMessage("Too few roles selected", "#f87171");
    } else {
        setMessage("Role count matches player count", "#4ade80");
    }
}


function assignRoles() {
    const playerCount = Number(document.getElementById("player-count").textContent);
    const selectedRoleCount = getTotalSelectedRoles();

    if (selectedRoleCount > playerCount) {
        setMessage("Too many roles selected", "#f87171");
        return;
    }

    if (selectedRoleCount < playerCount) {
        setMessage("Too few roles selected", "#f87171");
        return;
    }

    fetch("/assign_roles", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(getRoleCounts())
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            setMessage(data.message, "#4ade80");

            setTimeout(() => {
                window.location.href = "/room";
            }, 800);
        } else {
            setMessage(data.message, "#f87171");
        }
    })
    .catch(error => {
        setMessage("Something went wrong.", "#f87171");
        console.error(error);
    });
}


document.addEventListener("DOMContentLoaded", function () {
    updateSelectedRoleCount();
});
