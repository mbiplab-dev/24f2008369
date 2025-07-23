document.addEventListener('DOMContentLoaded', function () {
  const editButtons = document.querySelectorAll('.delete-spot-btn');
    const form = document.getElementById('deleteSpotForm');
    
  editButtons.forEach(button => {
    button.addEventListener('click', () => {
      document.getElementById('spot-id').innerText = button.dataset.spotid;
      document.getElementById('spot-status').innerText = button.dataset.status;
      document.getElementById('spotStatusParent').dataset.showspotid=button.dataset.spotid;
      if (button.dataset.status === "A"){
        document.getElementById('spotStatusParent').classList.add("btn-primary");
        document.getElementById('spotStatusParent').classList.add("disabled");
      }
      else{
        document.getElementById('spotStatusParent').classList.add("btn-outline-danger");
        
      }
      
      form.action = `/deletespot/${button.dataset.spotid}`;
    });
  });
});