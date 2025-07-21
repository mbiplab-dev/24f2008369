function calculateTotalCost(parkingTime, releaseTime, pricePerHour) {
    const parseDateTime = (str) => new Date(str);

    const start = parseDateTime(parkingTime);
    const end = parseDateTime(releaseTime);

    const diffMs = end - start; // milliseconds
    const diffMinutes = diffMs / (1000 * 60); // convert to minutes
    const diffHours = diffMinutes / 60;

    const totalCost = diffHours * pricePerHour;
    return totalCost.toFixed(2); // round to 2 decimals
}

function getCurrentFormattedTime() {
    const now = new Date();

    const pad = (n) => n.toString().padStart(2, '0');

    const year = now.getFullYear();
    const month = pad(now.getMonth() + 1); // Months are zero-based
    const day = pad(now.getDate());

    const hours = pad(now.getHours());
    const minutes = pad(now.getMinutes());
    const seconds = pad(now.getSeconds());

    return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`;
}

document.addEventListener('DOMContentLoaded', function () {
  const editButtons = document.querySelectorAll('.release-btn');
  const form = document.getElementById('releaseForm');

  editButtons.forEach(button => {
    button.addEventListener('click', () => {
      document.getElementById('releaseCost').value = calculateTotalCost(button.dataset.parkingtime,getCurrentFormattedTime(),button.dataset.price);
      document.getElementById('releaseNowTime').value = getCurrentFormattedTime();
      document.getElementById('releaseSpotId').value = button.dataset.spotid;
      document.getElementById('releaseVehicleNo').value = button.dataset.vehicleno;
      document.getElementById('releaseParkingTime').value = button.dataset.parkingtime;
      form.action = `/releaseparking/${button.dataset.bookingid}`;    
    });
  });
});