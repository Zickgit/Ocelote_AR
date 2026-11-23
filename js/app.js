// Ocelote UNACH · AR
// Controla animaciones, audio y estado de la experiencia de realidad aumentada.

const mv = document.getElementById('ocelote');
const voz = document.getElementById('voz');
const controls = document.getElementById('controls');
const btnSound = document.getElementById('btn-sound');
const hint = document.getElementById('hint');
const desktopNote = document.getElementById('desktop-note');
const progress = mv.querySelector('.progress');
const progressFill = mv.querySelector('.progress-fill');

// Animaciones que se reproducen una vez y luego regresan a "Idle".
const ONE_SHOT = new Set(['Saludo', 'Celebrar', 'Hablar']);
// Animación que va acompañada del audio de voz.
const TALK = 'Hablar';
// Archivo de audio de la voz (si no existe, la animación se reproduce sin sonido).
const AUDIO_SRC = 'audio/ocelote.mp3';
// Modelos para AR Quick Look (iOS): secuencia en bucle y versión que habla (con audio integrado).
const IOS_LOOP = 'models/ocelote.usdz';
const IOS_TALK = 'models/ocelote-habla.usdz';

let current = 'Idle';
let hasAudio = false;

async function exists(url) {
  try {
    const r = await fetch(url, { method: 'HEAD', cache: 'no-store' });
    return r.ok;
  } catch {
    return false;
  }
}

async function setupAudio() {
  if (await exists(AUDIO_SRC)) {
    voz.src = AUDIO_SRC;
    hasAudio = true;
  }
  btnSound.hidden = !hasAudio;
}

function stopVoice() {
  if (!voz.paused) voz.pause();
  voz.currentTime = 0;
}

function markActive(name) {
  controls.querySelectorAll('button[data-anim]').forEach((b) => {
    b.classList.toggle('active', b.dataset.anim === name);
  });
}

function playAnim(name) {
  if (!mv.availableAnimations.includes(name)) return;
  current = name;
  mv.animationName = name;
  mv.play({ repetitions: ONE_SHOT.has(name) ? 1 : Infinity });
  mv.currentTime = 0;
  markActive(name);

  if (name === TALK && hasAudio) {
    voz.currentTime = 0;
    voz.play().catch(() => { /* el navegador bloqueó el audio: la animación sigue */ });
  } else {
    stopVoice();
  }
}

// Mantiene la boca sincronizada con el audio mientras habla.
function syncLoop() {
  if (current === TALK && hasAudio && !voz.paused) {
    const drift = Math.abs(mv.currentTime - voz.currentTime);
    if (drift > 0.12) mv.currentTime = voz.currentTime;
  }
  requestAnimationFrame(syncLoop);
}

// --- Eventos -------------------------------------------------------------

controls.addEventListener('click', (e) => {
  const btn = e.target.closest('button[data-anim]');
  if (!btn) return;
  playAnim(btn.dataset.anim);
  // iPhone / iPad: Quick Look no muestra botones, así que elegimos qué versión abrir.
  // Tras tocar "Hablar", el AR abre la versión que habla con su voz; si no, la secuencia en bucle.
  mv.setAttribute('ios-src', btn.dataset.anim === TALK ? IOS_TALK : IOS_LOOP);
});

// Al entrar a AR paramos la voz de la página (en iOS, Quick Look trae su propio audio).
document.getElementById('ar-button').addEventListener('click', () => {
  if (current === TALK) playAnim('Idle');
});

btnSound.addEventListener('click', () => {
  voz.muted = !voz.muted;
  btnSound.textContent = voz.muted ? '🔇' : '🔊';
  btnSound.setAttribute('aria-pressed', String(!voz.muted));
});

mv.addEventListener('finished', () => {
  if (ONE_SHOT.has(current)) playAnim('Idle');
});

voz.addEventListener('ended', () => {
  if (current === TALK) playAnim('Idle');
});

mv.addEventListener('progress', (e) => {
  const p = e.detail.totalProgress;
  progressFill.style.width = `${Math.round(p * 100)}%`;
  progress.classList.toggle('hide', p >= 1);
});

mv.addEventListener('load', () => {
  playAnim('Saludo');
  if (!mv.canActivateAR) {
    const isTouch = matchMedia('(pointer: coarse)').matches;
    if (isTouch) {
      hint.textContent = 'Tu navegador no admite realidad aumentada; puedes girar el modelo con el dedo.';
    } else {
      hint.textContent = 'Arrastra para girar el modelo. Para verlo en AR, ábrelo desde tu celular.';
      desktopNote.hidden = false;
    }
  }
});

mv.addEventListener('ar-status', (e) => {
  const status = e.detail.status;
  if (status === 'session-started') {
    hint.hidden = true;
    playAnim('Saludo');
  } else if (status === 'not-presenting') {
    hint.hidden = false;
  } else if (status === 'failed') {
    hint.hidden = false;
    hint.textContent = 'No se pudo iniciar la cámara. Revisa los permisos e inténtalo de nuevo.';
  }
});

// Al salir de la pestaña (p. ej. al abrir Scene Viewer / Quick Look) pausamos la voz.
document.addEventListener('visibilitychange', () => {
  if (document.hidden && current === TALK) playAnim('Idle');
});

setupAudio();
syncLoop();
