document.addEventListener('DOMContentLoaded', function () {
  const editButtons = document.querySelectorAll('.delete-spot-btn');
    const form = document.getElementById('deleteSpotForm');
    
  editButtons.forEach(button => {
    button.addEventListener('click', () => {
        console.log(button.dataset.spotid)
      document.getElementById('spot-id').innerText = button.dataset.spotid;
      document.getElementById('spot-status').innerText = button.dataset.status;
      form.action = `/deletespot/${button.dataset.spotid}`;
    });
  });
});