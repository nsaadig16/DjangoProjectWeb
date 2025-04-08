/* jshint esversion: 6 */
(function () {
  "use strict";

  const cartas = [
     {
    nombre: "Gimeno",
    imagen: "https://inkscape.app/wp-content/uploads/imagen-vectorial.webp",
    texto: "Devuelve tus cartas de cuarto curso a primer curso.",
    poder: "3/5",
    coste: 4,
    tipo: "Human"
  },
  {
    nombre: "Torres",
    imagen: "img/torres.jpg",
    texto: "Te obliga a reescribir tu TFG cada semana.",
    poder: "4/4",
    coste: 5,
    tipo: "Beast"
  },
  {
    nombre: "Martínez",
    imagen: "img/martinez.jpg",
    texto: "Cuando entra al campo, todos los estudiantes se duermen.",
    poder: "2/3",
    coste: 3,
    tipo: "Human"
  },
  {
    nombre: "Bestia del Lab",
    imagen: "img/bestia.jpg",
    texto: "Una criatura legendaria con hambre de proyectos.",
    poder: "6/6",
    coste: 6,
    tipo: "Beast"
  }
  ];

  const contenedor = document.getElementById('cardContainer');
  const searchInput = document.getElementById('search');
  const typeFilter = document.getElementById('typeFilter');

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

  renderCartas();
})();
