<template>
  <div id="map" class="w-100 h-100"></div>
</template>

<script setup>
import { onMounted, ref } from 'vue';

let myMap = null;
const isInitialized = ref(false);

let museumsData = [];
let parksData = [];
let embankmentsData = [];

async function loadPlacesFromWikidata(classQID) {
  let categoryFilter;
  
  if (classQID === 'Q11742') {
    categoryFilter = `
      VALUES ?type { wd:Q11742 wd:Q22698 wd:Q126877 wd:Q1496967 }
      ?place wdt:P31/wdt:P279* ?type.
    `;
  } else if (classQID === 'Q862454') {
    categoryFilter = `
      {
        VALUES ?type { wd:Q862454 wd:Q15631416 wd:Q3840711 }
        ?place wdt:P31/wdt:P279* ?type.
      }
    `;
  } else if (classQID === 'Q33506') {
    categoryFilter = `
      VALUES ?type { wd:Q33506 wd:Q205391 wd:Q54173 wd:Q833017 }
      ?place wdt:P31/wdt:P279* ?type.
    `;
  } else {
    categoryFilter = `?place wdt:P31/wdt:P279* wd:${classQID}.`;
  }

  const query = `
    SELECT DISTINCT ?place ?placeLabel ?coord ?image WHERE {
      ${categoryFilter}
      ?place wdt:P131* wd:Q159. 
      ?place wdt:P625 ?coord.
      OPTIONAL { ?place wdt:P18 ?image. }
      SERVICE wikibase:label { bd:serviceParam wikibase:language "ru,en". }
    }
  `;

  const url = "https://query.wikidata.org/sparql?format=json&query=" + encodeURIComponent(query);
  
  try {
    const response = await fetch(url);
    const data = await response.json();
    return data.results.bindings;
  } catch (e) {
    console.error("Ошибка Wikidata:", e);
    return [];
  }
}

onMounted(() => {
  if (isInitialized.value) return;

  ymaps.ready(async () => {
    myMap = new ymaps.Map("map", {
      center: [47.24, 39.71],
      zoom: 11,
      controls: ['zoomControl', 'typeSelector']
    });

    const museumGeoObjects = new ymaps.GeoObjectCollection();
    const parkGeoObjects = new ymaps.GeoObjectCollection();
    const embankmentGeoObjects = new ymaps.GeoObjectCollection();

    myMap.geoObjects.add(museumGeoObjects);
    myMap.geoObjects.add(parkGeoObjects);
    myMap.geoObjects.add(embankmentGeoObjects);

    // Кнопки фильтров
    const museumItem = new ymaps.control.ListBoxItem({ data: { content: 'Музеи' }, state: { selected: true }});
    const parkItem = new ymaps.control.ListBoxItem({ data: { content: 'Парки' }, state: { selected: true }});
    const embankmentItem = new ymaps.control.ListBoxItem({ data: { content: 'Набережные' }, state: { selected: true }});

    [[museumItem, museumGeoObjects], [parkItem, parkGeoObjects], [embankmentItem, embankmentGeoObjects]]
    .forEach(([item, collection]) => {
      item.events.add('click', () => {
        item.isSelected() ? myMap.geoObjects.remove(collection) : myMap.geoObjects.add(collection);
      });
    });

    myMap.controls.add(new ymaps.control.ListBox({
      data: { content: 'Категории' },
      items: [museumItem, parkItem, embankmentItem],
      options: { float: 'right', floatIndex: 10 }
    }));

    // Слушатель клика по звездам в балунах
    document.addEventListener('click', (e) => {
      if (e.target.classList.contains('favorite-star')) {
        const placeId = e.target.getAttribute('data-id');
        const allPlaces = [...museumsData, ...parksData, ...embankmentsData];
        const placeData = allPlaces.find(p => p.place.value === placeId);
        if (placeData) toggleFavorite(placeData, e.target);
      }
    });

    const renderPlaces = (data, collection, iconPreset) => {
      const favorites = JSON.parse(localStorage.getItem('favorites') || '[]');
      data.forEach(item => {
        const name = item.placeLabel.value;
        const placeId = item.place.value;
        const match = item.coord.value.match(/Point\(([-0-9.]+) ([-0-9.]+)\)/);
        if (!match) return;
        
        const isFav = favorites.some(fav => fav.id === placeId);
        const starColor = isFav ? '#ffc107' : '#ccc';
        
        const html = `
          <div style="max-width: 200px; position: relative;">
            <div style="display: flex; justify-content: space-between; align-items: flex-start;">
              <strong style="margin-right: 20px;">${name}</strong>
              <span class="favorite-star" data-id="${placeId}" style="cursor: pointer; font-size: 20px; color: ${starColor};">★</span>
            </div>
            ${item.image ? `<br><img src="${item.image.value}" class="balloon-img" style="width:100%;margin-top:8px;border-radius:4px;"/>` : ''}
          </div>`;
        
        collection.add(new ymaps.Placemark(
          [parseFloat(match[2]), parseFloat(match[1])], 
          { balloonContent: html }, 
          { preset: iconPreset }
        ));
      });
    };

    // Загрузка данных
    const [resM, resP, resE] = await Promise.all([
      loadPlacesFromWikidata('Q33506'), 
      loadPlacesFromWikidata('Q11742'),
      loadPlacesFromWikidata('Q862454')
    ]);

    // Сохраняем в переменные, которые видны везде в скрипте
    museumsData = resM;
    parksData = resP;
    embankmentsData = resE;

    // Отрисовка
    renderPlaces(museumsData, museumGeoObjects, 'islands#redLeisureIcon');
    renderPlaces(parksData, parkGeoObjects, 'islands#greenParkIcon');
    renderPlaces(embankmentsData, embankmentGeoObjects, 'islands#blueWaterParkIcon');

    isInitialized.value = true;
  });
});

function toggleFavorite(place, starElement) {
  let favorites = JSON.parse(localStorage.getItem('favorites') || '[]');
  const index = favorites.findIndex(fav => fav.id === place.place.value);

  if (index === -1) {
    favorites.push({
      id: place.place.value,
      name: place.placeLabel.value,
      image: place.image ? place.image.value : null,
      coord: place.coord.value
    });
    starElement.style.color = '#ffc107';
  } else {
    favorites.splice(index, 1);
    starElement.style.color = '#ccc';
  }
  localStorage.setItem('favorites', JSON.stringify(favorites));
}
</script>

<script>
export default {
  name: 'MapView'
}
</script>

<style scoped>
#map {
  background-color: #e5e3df;
}
:deep(.balloon-img) {
    background: url('https://i.gifer.com/ZKZg.gif') center center no-repeat;
    background-size: 30px;
    min-height: 100px;
    display: block;
}
</style>