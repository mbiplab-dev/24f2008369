document.addEventListener('DOMContentLoaded', function () {
  const editButtons = document.querySelectorAll('.delete-spot-btn');
  const form = document.getElementById('deleteSpotForm');
  const commonClasses = ['show-spot-details','btn', 'mx-2'];
  editButtons.forEach(button => {
  button.addEventListener('click', () => {
    const spotStatusParent = document.getElementById('spotStatusParent');
    spotStatusParent.className = commonClasses.join(' ');
    document.getElementById('spot-id').innerText = button.dataset.spotid;
    document.getElementById('spot-status').innerText = button.dataset.status;
    spotStatusParent.dataset.showspotid=button.dataset.spotid;
    if (button.dataset.status === "A") {
    spotStatusParent.classList.add("btn-primary", "disabled");
    } else {
    spotStatusParent.classList.add("btn-danger");
    }
      
    form.action = `/deletespot/${button.dataset.spotid}`;
    });
  });
});