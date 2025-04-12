(function () {
  "use strict";

  const contenedor = document.getElementById('cardContainer');
  const searchInput = document.getElementById('search');
  const typeFilter = document.getElementById('typeFilter');
  let cartas = [];

  function crearCarta(carta) {
    const scene = document.createElement('div');
    scene.className = 'scene';

    const card = document.createElement('div');
    card.className = 'card';

    card.innerHTML = `
      <div class="card-face card-front">
        <div class="mana-cost">${carta.coste}</div>
        <div class="card-header">${carta.nombre}</div>
        <img class="card-image" src="${carta.imagen}" alt="Imagen de carta">
        <div class="card-type">Legendary Creature – ${carta.tipo}</div>
        <div class="card-text">${carta.texto}</div>
        <div class="card-power">${carta.poder}</div>
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

  function renderCartas() {
    contenedor.innerHTML = '';
    const texto = searchInput.value.toLowerCase();
    const tipo = typeFilter.value;

    const filtradas = cartas.filter(carta =>
      carta.nombre.toLowerCase().includes(texto) &&
      (tipo === '' || carta.tipo === tipo)
    );

    filtradas.forEach(carta => {
      contenedor.appendChild(crearCarta(carta));
    });
  }

  searchInput.addEventListener('input', renderCartas);
  typeFilter.addEventListener('change', renderCartas);

  fetch('/api/cartas/')
    .then(response => response.json())
    .then(data => {
      cartas = data;
      renderCartas();
    })
    .catch(error => console.error('Error cargando cartas:', error));
})();
