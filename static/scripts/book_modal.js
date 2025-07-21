document.addEventListener('DOMContentLoaded', function () {
  const bookButtons = document.querySelectorAll('.book-now-btn');
  const lot_id_input = document.getElementById('lot_id_input');

  bookButtons.forEach(button => {
    button.addEventListener('click', () => {
      const lotId = button.getAttribute('data-lot-id');
      lot_id_input.value = lotId;
    });
  });
});
