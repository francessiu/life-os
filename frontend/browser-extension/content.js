// content.js

// 1. Create the Butler Element
const butlerDiv = document.createElement('div');
butlerDiv.id = 'lifeos-butler-overlay';
butlerDiv.innerHTML = `
  <div class="butler-character">🤖</div>
  <div class="butler-bubble" style="display:none">Focus!</div>
`;
document.body.appendChild(butlerDiv);

// 2. Listen for updates from Background Script
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.type === "UPDATE_BUTLER") {
    updateButlerEmotion(request.emotion);
  }
});

function updateButlerEmotion(emotion) {
  const char = butlerDiv.querySelector('.butler-character');
  if (emotion === 'happy') char.innerText = '😺';
  if (emotion === 'worried') char.innerText = '🙀';
  if (emotion === 'panicked') char.innerText = '😿';
}

// 3. Drag Logic (Simple implementation)
let isDragging = false;
butlerDiv.addEventListener('mousedown', () => isDragging = true);
window.addEventListener('mouseup', () => isDragging = false);
window.addEventListener('mousemove', (e) => {
  if (isDragging) {
    butlerDiv.style.top = e.clientY + 'px';
    butlerDiv.style.left = e.clientX + 'px';
  }
});