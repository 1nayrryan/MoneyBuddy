document.addEventListener("DOMContentLoaded", () => {
	const promptEl = document.getElementById("prompt");
	const askBtn = document.getElementById("askBtn");
	const responseEl = document.getElementById("response");
	const statusEl = document.getElementById("status");

	askBtn.addEventListener("click", async () => {
		const prompt = promptEl.value.trim();
		responseEl.textContent = "";
		statusEl.textContent = "";

		if (!prompt) {
			statusEl.textContent = "Please enter a prompt.";
			return;
		}

		statusEl.textContent = "Thinking...";
		askBtn.disabled = true;

		try {
			const res = await fetch("/api/ask", {
				method: "POST",
				headers: { "Content-Type": "application/json" },
				body: JSON.stringify({ prompt }),
			});

			const data = await res.json();
			if (res.ok) {
				responseEl.textContent = data.response;
				statusEl.textContent = "";
			} else {
				responseEl.textContent = data.error || JSON.stringify(data);
				statusEl.textContent = "Error";
			}
		} catch (err) {
			responseEl.textContent = String(err);
			statusEl.textContent = "Network error";
		} finally {
			askBtn.disabled = false;
		}
	});
});
