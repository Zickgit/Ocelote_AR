// Ocelote UNACH · AR
// Un solo botón "Promocionar": reproduce la animación del modelo junto con su voz.

const mv = document.getElementById('ocelote');
const voz = document.getElementById('voz');
const controls = document.getElementById('controls');
const btnPromo = document.getElementById('btn-promo');
const hint = document.getElementById('hint');
const desktopNote = document.getElementById('desktop-note');
const progress = mv.querySelector('.progress');
const progressFill = mv.querySelector('.progress-fill');

// Voz del Ocelote (45 s); la animación del modelo dura lo mismo y está sincronizada con ella.
const AUDIO_SRC = 'audio/ocelote.mp3';

let playing = false;
let pendingPlay = false; // se tocó "Promocionar" mientras el modelo cargaba
let hasAudio = true;

function setupAudio() {
  voz.src = AUDIO_SRC;
  voz.addEventListener('error', () => {
    hasAudio = false;
    btnPromo.classList.remove('cargando');
  });
  // iOS no descarga audio hasta que hay un toque: lo pedimos con el primer toque en la página.
  document.addEventListener('pointerdown', () => {
    if (hasAudio && voz.readyState === 0) voz.load();
  }, { once: true, capture: true });
}

// Deja al Ocelote quieto en el primer cuadro de su animación.
function rest() {
  playing = false;
  btnPromo.classList.remove('active', 'cargando');
  if (!voz.paused) voz.pause();
  voz.currentTime = 0;
  if (mv.loaded) {
    mv.pause();
    mv.currentTime = 0;
  }
}

function promote() {
  if (!mv.loaded) {
    pendingPlay = true;
    btnPromo.classList.add('active');
    return;
  }
  playing = true;
  btnPromo.classList.add('active');
  mv.play({ repetitions: 1 });
  mv.currentTime = 0;
  if (hasAudio) {
    voz.currentTime = 0;
    btnPromo.classList.add('cargando');
    voz.play().catch(() => btnPromo.classList.remove('cargando'));
  }
}

// Mantiene boca y gestos sincronizados con la voz.
function syncLoop() {
  if (playing && hasAudio && !voz.paused) {
    const drift = Math.abs(mv.currentTime - voz.currentTime);
    if (drift > 0.12) mv.currentTime = voz.currentTime;
  }
  requestAnimationFrame(syncLoop);
}

// --- Eventos -------------------------------------------------------------

btnPromo.addEventListener('click', promote);

voz.addEventListener('playing', () => btnPromo.classList.remove('cargando'));
voz.addEventListener('ended', () => { if (playing) rest(); });
mv.addEventListener('finished', () => {
  // Sin audio, la animación marca el final; con audio esperamos a que termine la voz.
  if (playing && (!hasAudio || voz.paused)) rest();
});

mv.addEventListener('progress', (e) => {
  const p = e.detail.totalProgress;
  progressFill.style.width = `${Math.round(p * 100)}%`;
  progress.classList.toggle('hide', p >= 1);
});

mv.addEventListener('load', () => {
  controls.classList.remove('loading');
  mv.animationName = mv.availableAnimations[0];
  if (pendingPlay) {
    pendingPlay = false;
    promote();
  } else {
    // Activa la animación y, tras un par de cuadros, la congela en su primer cuadro
    // (si se pausa de inmediato se vería la pose base con los brazos abiertos).
    mv.play({ repetitions: 1 });
    requestAnimationFrame(() => requestAnimationFrame(() => { if (!playing) rest(); }));
  }
  if (!mv.canActivateAR) {
    const isTouch = matchMedia('(pointer: coarse)').matches;
    if (isTouch) {
      hint.textContent = 'Tu navegador no admite realidad aumentada; toca Promocionar para verlo aquí.';
    } else {
      hint.textContent = 'Toca Promocionar. Para verlo en realidad aumentada, ábrelo desde tu celular.';
      desktopNote.hidden = false;
    }
  }
});

// Al entrar a AR paramos la voz de la página (en iPhone, el USDZ trae su propia voz).
document.getElementById('ar-button').addEventListener('click', () => {
  if (playing) rest();
});

mv.addEventListener('ar-status', (e) => {
  const status = e.detail.status;
  if (status === 'session-started') {
    // Android (WebXR): igual que en iPhone, al aparecer en tu espacio empieza a promocionar.
    hint.hidden = true;
    promote();
  } else if (status === 'not-presenting') {
    hint.hidden = false;
    rest();
  } else if (status === 'failed') {
    hint.hidden = false;
    hint.textContent = 'No se pudo iniciar la cámara. Revisa los permisos e inténtalo de nuevo.';
  }
});

// Al salir de la pestaña (p. ej. al abrir Scene Viewer / Quick Look) detenemos todo.
document.addEventListener('visibilitychange', () => {
  if (document.hidden && playing) rest();
});

setupAudio();
syncLoop();
