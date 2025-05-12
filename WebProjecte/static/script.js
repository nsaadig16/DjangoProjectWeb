/* jshint esversion: 6, browser: true */
function crearCarta(carta) {
  const scene = document.createElement('div');
  scene.className = 'scene';

  const card = document.createElement('div');
  card.className = 'card';

  card.innerHTML = `
    <div class="card-face card-front">
      <img class="card-image" src="${carta.imagen}" alt="Card image">
    </div>
    <div class="card-face card-back">
      <h2>EcoEdición Legendaria</h2>
      <p>Forjada en los hornos de la informática, con alma de patata y corazón de compilador.</p>
    </div>
  `;

  scene.appendChild(card);

  scene.addEventListener('click', () => {
    card.classList.toggle('is-flipped');
  });

  return scene;
}
