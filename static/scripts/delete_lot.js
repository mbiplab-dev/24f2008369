document.addEventListener('DOMContentLoaded', function () {
  const editButtons = document.querySelectorAll('.delete-btn');
    const form = document.getElementById('deleteLotForm');
  editButtons.forEach(button => {
    button.addEventListener('click', () => {
      document.getElementById('deleteName').value = button.dataset.name;
      document.getElementById('deleteAddress').value = button.dataset.address;
      form.action = `/deleteparkinglot/${button.dataset.lotid}`;
    });
  });
});