/**
 * Speed Control Event Listeners Setup
 * Extracted from player.js for maintainability
 */

export function setupSpeedEventListeners(player) {
  console.log('Setting up speed event listeners:', {
    speedSlowBtn: !!player.speedSlowBtn,
    audioPlayer: !!player.audioPlayer,
    speed1xBtnId: `${player.containerId}-speed-1x`,
    speedSlowBtnId: `${player.containerId}-speed-slow`,
    actualSpeed1xBtn: document.getElementById(`${player.containerId}-speed-1x`),
    actualSpeedSlowBtn: document.getElementById(`${player.containerId}-speed-slow`),
  });

  const updateActive = (activeBtn, inactiveBtn) => {
    try {
      if (activeBtn) activeBtn.classList.add('active');
      if (inactiveBtn) inactiveBtn.classList.remove('active');
      console.log('Updated button states:', {
        activeBtn: activeBtn?.classList.contains('active'),
        inactiveBtn: inactiveBtn?.classList.contains('active'),
      });
    } catch (error) {
      console.error('Error updating button states:', error);
    }
  };

  // Re-query DOM elements if they weren't found during initialization
  if (!player.speed1xBtn) {
    player.speed1xBtn = document.getElementById(`${player.containerId}-speed-1x`);
  }
  if (!player.speedSlowBtn) {
    player.speedSlowBtn = document.getElementById(`${player.containerId}-speed-slow`);
  }

  console.log('After re-query attempt:', {
    speed1xBtn: !!player.speed1xBtn,
    speedSlowBtn: !!player.speedSlowBtn,
    audioPlayer: !!player.audioPlayer,
  });

  if (player.speed1xBtn && player.speedSlowBtn && player.audioPlayer) {
    console.log('Attaching speed button event listeners');

    // Normal speed
    player.speed1xBtn.addEventListener('click', () => {
      console.log('1x speed button clicked, setting playbackRate to 1.0');
      player.audioPlayer.playbackRate = 1.0;
      updateActive(player.speed1xBtn, player.speedSlowBtn);
    });

    // 1⁄8 speed
    player.speedSlowBtn.addEventListener('click', () => {
      console.log('1/8 speed button clicked, setting playbackRate to 0.125');
      player.audioPlayer.playbackRate = 0.125;
      updateActive(player.speedSlowBtn, player.speed1xBtn);
    });
  } else {
    console.log('Cannot set up speed buttons - missing elements:', {
      speed1xBtn: !!player.speed1xBtn,
      speedSlowBtn: !!player.speedSlowBtn,
      audioPlayer: !!player.audioPlayer,
    });
  }
}
