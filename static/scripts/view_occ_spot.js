document.addEventListener('DOMContentLoaded', function () {
    const showButtons = document.querySelectorAll('.show-spot-details');

    showButtons.forEach(button => {
      button.addEventListener('click', async () => {
        const spotId = button.getAttribute('data-showspotid');
        if (!spotId) {
          alert("No spot ID found on button.");
          return;
        }

        try {
          const response = await fetch(`/api/spot-details/${spotId}`);
          const data = await response.json();

          if (data.error) {
            alert("Spot not found!");
            return;
          }
          document.getElementById("showSpotId").textContent = data.spot_id ?? "-";
          document.getElementById("showUserId").textContent = data.user_id ?? "Not booked";
          document.getElementById("showVehicleNo").textContent = data.vehicle_no ?? "-";
          document.getElementById("showParkingTime").textContent = data.parking_time ?? "-";
          document.getElementById("showParkingCost").textContent = data.estimated_cost ?? "0";
          document.getElementById("showLotId").textContent = data.lot_id ?? "-";
          document.getElementById("showLotName").textContent = data.lot_name ?? "-";
          document.getElementById("showLotAddress").textContent = data.lot_address ?? "-";

          const modal = new bootstrap.Modal(document.getElementById('spotDetailsModal'));
          modal.show();
        } catch (err) {
          
        }
      });
    });
  });
