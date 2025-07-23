document.addEventListener('DOMContentLoaded', function () {
  const editButtons = document.querySelectorAll('.edit-btn');
  const form = document.getElementById('editLotForm');

  editButtons.forEach(button => {
    button.addEventListener('click', () => {
      
      const imagePath = "/static/uploads/lot_" + button.dataset.lotid + ".png";
      document.getElementById('editSelectedImage').src = imagePath; 
      document.getElementById('editName').value = button.dataset.name;
      document.getElementById('editAddress').value = button.dataset.address;
      document.getElementById('editPincode').value = button.dataset.pincode;
      document.getElementById('editPrice').value = button.dataset.price;
      document.getElementById('editMaxSpots').value = button.dataset.maxspots;
      form.action = `/editparkinglot/${button.dataset.lotid}`;
    });
  });
});