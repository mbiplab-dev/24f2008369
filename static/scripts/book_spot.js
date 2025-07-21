document.addEventListener("DOMContentLoaded", function () {
  const bookModal = document.getElementById("BookParking");

  if (!bookModal) return;

  bookModal.addEventListener("show.bs.modal", async function (event) {
    
    const button = event.relatedTarget;
    const lotId = button.getAttribute("data-lot-id");

    const lotInput = document.getElementById("lot_id");
    const spotInput = document.getElementById("spot_id");
    
    if (lotInput) lotInput.value = lotId;
    const imagePath = "/static/uploads/lot_" + lotId + ".png";
    document.getElementById('viewLotImage').src = imagePath; 
    try {
      const response = await fetch(`/api/first_free_spot/${lotId}`);
      const data = await response.json();

      if (data.spot_id) {
        if (spotInput) spotInput.value = data.spot_id;

          const container = document.getElementById('spotGrid');
          container.innerHTML = '';

          data.spots.forEach(spot => {
            const div = document.createElement('div');
            div.classList.add('spot');
            div.classList.add('d-flex');
            div.classList.add('flex-column');

            if (spot[0] === data.spot_id) {
              div.classList.add('allot');
            } else if (spot[1] === '0') {
              div.classList.add('occupied');
            } else if (spot[1] === 'A') {
              div.classList.add('available');
            }
            const h1 =document.createElement("h5")
            div.textContent = `Spot`;
            h1.textContent=`#${spot[0]}`;
            div.appendChild(h1);
            container.appendChild(div);
        });
      } else {
        alert("No available spots in this lot.");
        const modalInstance = bootstrap.Modal.getInstance(bookModal);
        if (modalInstance) modalInstance.hide();
      }
    } catch (error) {
      console.error("Error fetching spot:", error);
      alert("An error occurred while fetching spot info.");
    }
  });
});
