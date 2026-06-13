document.addEventListener("DOMContentLoaded", () => {
  const activitiesList = document.getElementById("activities-list");
  const activitySelect = document.getElementById("activity");
  const signupForm = document.getElementById("signup-form");
  const messageDiv = document.getElementById("message");

  // Function to fetch activities from API
  async function fetchActivities() {
    try {
      const response = await fetch("/activities");
      const activities = await response.json();

      // Clear loading message and reset select options
      activitiesList.innerHTML = "";
      activitySelect.innerHTML = '<option value="">-- Select an activity --</option>';

      // Populate activities list
      Object.entries(activities).forEach(([name, details]) => {
        const activityCard = document.createElement("div");
        activityCard.className = "activity-card";

        const spotsLeft = details.max_participants - details.participants.length;

        const title = document.createElement('h4');
        title.textContent = name;

        const desc = document.createElement('p');
        desc.textContent = details.description;

        const scheduleP = document.createElement('p');
        scheduleP.innerHTML = `<strong>Schedule:</strong> ${details.schedule}`;

        const availP = document.createElement('p');
        availP.innerHTML = `<strong>Availability:</strong> ${spotsLeft} spots left`;

        // Participants block
        const participantsDiv = document.createElement('div');
        participantsDiv.className = 'participants';
        const participantsTitle = document.createElement('strong');
        participantsTitle.textContent = 'Participants';
        participantsDiv.appendChild(participantsTitle);

        const ul = document.createElement('ul');
        ul.className = 'participants-list';

        if (details.participants && details.participants.length) {
          details.participants.forEach(p => {
            const li = document.createElement('li');
            const span = document.createElement('span');
            span.textContent = p;
            const btn = document.createElement('button');
            btn.className = 'delete-participant';
            btn.title = 'Remove participant';
            btn.dataset.activity = name;
            btn.dataset.email = p;
            btn.textContent = '✖';
            li.appendChild(span);
            li.appendChild(btn);
            ul.appendChild(li);
          });
        } else {
          const li = document.createElement('li');
          li.className = 'no-participants';
          li.textContent = 'No participants yet';
          ul.appendChild(li);
        }

        participantsDiv.appendChild(ul);

        activityCard.appendChild(title);
        activityCard.appendChild(desc);
        activityCard.appendChild(scheduleP);
        activityCard.appendChild(availP);
        activityCard.appendChild(participantsDiv);

        activitiesList.appendChild(activityCard);

        // Add option to select dropdown
        const option = document.createElement("option");
        option.value = name;
        option.textContent = name;
        activitySelect.appendChild(option);
      });
    } catch (error) {
      activitiesList.innerHTML = "<p>Failed to load activities. Please try again later.</p>";
      console.error("Error fetching activities:", error);
    }
  }

  // Handle form submission
  signupForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const email = document.getElementById("email").value;
    const activity = document.getElementById("activity").value;

    try {
      const response = await fetch(
        `/activities/${encodeURIComponent(activity)}/signup?email=${encodeURIComponent(email)}`,
        {
          method: "POST",
        }
      );

      const result = await response.json();

      if (response.ok) {
        messageDiv.textContent = result.message;
        messageDiv.className = "success";
        // Refresh activities so UI shows the new participant immediately
        await fetchActivities();
        signupForm.reset();
      } else {
        messageDiv.textContent = result.detail || "An error occurred";
        messageDiv.className = "error";
      }

      messageDiv.classList.remove("hidden");

      // Hide message after 5 seconds
      setTimeout(() => {
        messageDiv.classList.add("hidden");
      }, 5000);
    } catch (error) {
      messageDiv.textContent = "Failed to sign up. Please try again.";
      messageDiv.className = "error";
      messageDiv.classList.remove("hidden");
      console.error("Error signing up:", error);
    }
  });

    // Delegate delete clicks for participant removal
    activitiesList.addEventListener('click', async (e) => {
      if (!e.target.classList.contains('delete-participant')) return;
      const activity = e.target.dataset.activity;
      const email = e.target.dataset.email;
      if (!confirm(`Remove ${email} from ${activity}?`)) return;
      try {
        const response = await fetch(`/activities/${encodeURIComponent(activity)}/participants?email=${encodeURIComponent(email)}`, { method: 'DELETE' });
        const result = await response.json();
        if (response.ok) {
          await fetchActivities();
          messageDiv.textContent = result.message;
          messageDiv.className = 'success';
        } else {
          messageDiv.textContent = result.detail || 'Failed to remove participant';
          messageDiv.className = 'error';
        }
      } catch (err) {
        messageDiv.textContent = 'Failed to remove participant';
        messageDiv.className = 'error';
        console.error('Error removing participant:', err);
      }
      messageDiv.classList.remove('hidden');
      setTimeout(() => messageDiv.classList.add('hidden'), 4000);
    });

    // Initialize app
    fetchActivities();
});
