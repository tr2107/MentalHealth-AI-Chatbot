(function () {
  "use strict";

  const chatWindow = document.getElementById("chat-window");
  const chatForm = document.getElementById("chat-form");
  const chatInput = document.getElementById("chat-input");
  const typingIndicator = document.getElementById("typing-indicator");
  const clearBtn = document.getElementById("clear-btn");
  const quickButtons = document.querySelectorAll(".quick-btn");

  const breathingBtn = document.getElementById("breathing-btn");
  const breathingModal = document.getElementById("breathing-modal");
  const breathingClose = document.getElementById("breathing-close");
  const breathingCircle = document.getElementById("breathing-circle");
  const breathingPhaseLabel = document.getElementById("breathing-phase-label");
  const breathingInstructions = document.getElementById("breathing-instructions");
  const breathingStart = document.getElementById("breathing-start");
  const breathingStop = document.getElementById("breathing-stop");

  let isSending = false;

  /* ---------------- welcome message ---------------- */
  function renderWelcome() {
    chatWindow.innerHTML = "";
    const card = document.createElement("div");
    card.className = "welcome-card";
    card.innerHTML = `
      <h2>Hi, I'm MindCare AI 👋</h2>
      <p>I'm here to listen and help you talk through what's on your mind.</p>
      <p>You can talk to me about:</p>
      <ul>
        <li>Stress</li>
        <li>Exam or work pressure</li>
        <li>Overthinking</li>
        <li>Feeling overwhelmed</li>
        <li>Everyday worries</li>
        <li>General emotional wellbeing</li>
      </ul>
      <p>Your conversation is not permanently stored by this application.</p>
      <div class="disclaimer">MindCare AI provides general emotional support and is not a replacement for professional mental-health care.</div>
    `;
    chatWindow.appendChild(card);
  }

  /* ---------------- message rendering ---------------- */
  function appendMessage(role, text, opts) {
    opts = opts || {};
    const row = document.createElement("div");
    row.className = "msg-row " + (role === "user" ? "user" : "ai");

    const avatar = document.createElement("div");
    avatar.className = "avatar";
    avatar.textContent = role === "user" ? "🧑" : "🌿";

    const bubble = document.createElement("div");
    bubble.className = "bubble" + (opts.crisis ? " crisis" : "");
    bubble.textContent = text;

    if (opts.buttons && opts.buttons.length) {
      const btnWrap = document.createElement("div");
      btnWrap.className = "crisis-buttons";
      opts.buttons.forEach((b) => {
        const el = document.createElement(b.action.startsWith("tel:") ? "a" : "button");
        el.className = "crisis-btn" + (b.action === "trusted_contact" ? " secondary" : "");
        el.textContent = b.label;
        if (b.action.startsWith("tel:")) {
          el.href = b.action;
        } else if (b.action === "trusted_contact") {
          el.type = "button";
          el.addEventListener("click", () => {
            appendMessage(
              "ai",
              "If there's someone you trust — a friend, family member, roommate, or mentor — this could be a good moment to call or message them and let them know you don't want to be alone right now."
            );
          });
        }
        btnWrap.appendChild(el);
      });
      bubble.appendChild(document.createElement("br"));
      bubble.appendChild(btnWrap);
    }

    row.appendChild(avatar);
    row.appendChild(bubble);
    chatWindow.appendChild(row);
    scrollToBottom();
  }

  function scrollToBottom() {
    chatWindow.scrollTop = chatWindow.scrollHeight;
  }

  function setTyping(visible) {
    typingIndicator.classList.toggle("hidden", !visible);
    if (visible) scrollToBottom();
  }

  /* ---------------- sending messages ---------------- */
  async function sendMessage(text) {
    const trimmed = (text || "").trim();
    if (!trimmed || isSending) return;

    isSending = true;
    appendMessage("user", trimmed);
    chatInput.value = "";
    setTyping(true);

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: trimmed }),
      });

      const data = await res.json();
      setTyping(false);

      if (!res.ok) {
        appendMessage("ai", data.error || "Something went wrong. Please try again.");
        return;
      }

      const isCrisisLike = ["crisis", "danger_yes"].includes(data.type);
      appendMessage("ai", data.text, {
        crisis: isCrisisLike,
        buttons: data.buttons || null,
      });
    } catch (err) {
      setTyping(false);
      appendMessage(
        "ai",
        "I'm having trouble connecting right now. Please check your connection and try again. If you're in crisis, please contact Tele-MANAS at 14416 or emergency services at 112."
      );
    } finally {
      isSending = false;
      chatInput.focus();
    }
  }

  chatForm.addEventListener("submit", (e) => {
    e.preventDefault();
    sendMessage(chatInput.value);
  });

  quickButtons.forEach((btn) => {
    btn.addEventListener("click", () => sendMessage(btn.dataset.message));
  });

  /* ---------------- clear chat ---------------- */
  clearBtn.addEventListener("click", async () => {
    try {
      await fetch("/api/clear", { method: "POST" });
    } catch (err) {
      // Even if the network call fails, still reset the visible chat locally.
    }
    renderWelcome();
    chatInput.value = "";
    chatInput.focus();
  });

  /* ---------------- breathing exercise ---------------- */
  const BREATH_ROUNDS = 3;
  const PHASES = [
    { label: "Breathe in…", cls: "inhale", duration: 4000 },
    { label: "Hold…", cls: "hold", duration: 3000 },
    { label: "Breathe out…", cls: "exhale", duration: 6000 },
  ];
  let breathingTimer = null;
  let breathingActive = false;

  function openBreathingModal() {
    breathingModal.classList.remove("hidden");
    resetBreathingUI();
  }
  function closeBreathingModal() {
    breathingModal.classList.add("hidden");
    stopBreathing();
  }
  function resetBreathingUI() {
    breathingCircle.className = "breathing-circle";
    breathingPhaseLabel.textContent = "Ready?";
    breathingInstructions.textContent = "Press start whenever you're ready. We'll do a few gentle rounds together.";
    breathingStart.classList.remove("hidden");
    breathingStop.classList.add("hidden");
  }

  function runBreathingCycle(round, phaseIndex) {
    if (!breathingActive) return;
    if (round > BREATH_ROUNDS) {
      breathingPhaseLabel.textContent = "Well done";
      breathingInstructions.textContent = "Nice work. You can close this whenever you're ready, or run through it again.";
      breathingCircle.className = "breathing-circle";
      breathingStart.classList.remove("hidden");
      breathingStop.classList.add("hidden");
      breathingActive = false;
      return;
    }

    const phase = PHASES[phaseIndex];
    breathingCircle.className = "breathing-circle " + phase.cls;
    breathingPhaseLabel.textContent = phase.label;
    breathingInstructions.textContent = `Round ${round} of ${BREATH_ROUNDS}`;

    breathingTimer = setTimeout(() => {
      const nextPhaseIndex = (phaseIndex + 1) % PHASES.length;
      const nextRound = nextPhaseIndex === 0 ? round + 1 : round;
      runBreathingCycle(nextRound, nextPhaseIndex);
    }, phase.duration);
  }

  function startBreathing() {
    breathingActive = true;
    breathingStart.classList.add("hidden");
    breathingStop.classList.remove("hidden");
    runBreathingCycle(1, 0);
  }

  function stopBreathing() {
    breathingActive = false;
    if (breathingTimer) clearTimeout(breathingTimer);
    resetBreathingUI();
  }

  breathingBtn.addEventListener("click", openBreathingModal);
  breathingClose.addEventListener("click", closeBreathingModal);
  breathingStart.addEventListener("click", startBreathing);
  breathingStop.addEventListener("click", stopBreathing);
  breathingModal.addEventListener("click", (e) => {
    if (e.target === breathingModal) closeBreathingModal();
  });

  /* ---------------- init ---------------- */
  renderWelcome();
  chatInput.focus();
})();
