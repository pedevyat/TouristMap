<template>
  <div id="map" class="w-100 h-100"></div>
</template>

<script setup>
import { onMounted, ref } from 'vue';

let myMap = null;
const isInitialized = ref(false);
const dbFavoritesIds = ref(new Set());

let museumsData = [];
let parksData = [];
let embankmentsData = [];

// --- ЛОГИКА API ---

// Загрузка избранного из Django
const fetchDbFavorites = async () => {
  try {
    const response = await fetch('http://127.0.0.1:8000/api/favorites/');
    if (response.ok) {
      const data = await response.json();
      dbFavoritesIds.value = new Set(data.map(item => item.id));
    }
  } catch (e) {
    console.error("Не удалось подгрузить избранное для карты:", e);
  }
};

// Загрузка данных из Wikidata
async function loadPlacesFromWikidata(classQID) {
  let categoryFilter;
  if (classQID === 'Q11742') {
    categoryFilter = `VALUES ?type { wd:Q11742 wd:Q22698 wd:Q126877 wd:Q1496967 } ?place wdt:P31 ?type.`;
  } else if (classQID === 'Q862454') {
    categoryFilter = `VALUES ?type { wd:Q862454 wd:Q15631416 wd:Q3840711 } ?place wdt:P31 ?type.`;
  } else if (classQID === 'Q33506') {
    categoryFilter = `VALUES ?type { wd:Q33506 wd:Q205391 wd:Q54173 wd:Q833017 } ?place wdt:P31 ?type.`;
  } else {
    categoryFilter = `?place wdt:P31 wd:${classQID}.`;
  }

  const query = `
    SELECT DISTINCT ?place ?placeLabel ?coord ?image WHERE {
      SERVICE wikibase:around { 
          ?place wdt:P625 ?coord . 
          bd:serviceParam wikibase:center "Point(39.71 47.24)"^^geo:wktLiteral .
          bd:serviceParam wikibase:radius "30" . 
      }
      ${categoryFilter}
      OPTIONAL { ?place wdt:P18 ?image. }
      SERVICE wikibase:label { bd:serviceParam wikibase:language "ru,en". }
    }
  `;

  const url = "https://query.wikidata.org/sparql";
  const params = new URLSearchParams({ query: query, format: 'json' });
  
  try {
    const response = await fetch(`${url}?${params}`);
    if (response.status === 429) return [];
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
    const data = await response.json();
    return data.results.bindings;
  } catch (e) {
    console.error("Ошибка Wikidata:", e);
    return [];
  }
}

// Переключение избранного (POST на бэкенд)
async function toggleFavorite(place, starElement) {
  try {
    const response = await fetch('http://127.0.0.1:8000/api/favorites/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        place_id: place.place.value,
        title: place.placeLabel.value,
        image_url: place.image ? place.image.value : null,
        coordinate: place.coord.value,
        city: "Ростов-на-Дону"
      })
    });

    const result = await response.json();
    if (response.ok) {
      if (result.status === 'added') {
        starElement.style.color = '#ffc107';
        dbFavoritesIds.value.add(place.place.value);
      } else if (result.status === 'removed') {
        starElement.style.color = '#ccc';
        dbFavoritesIds.value.delete(place.place.value);
      }
    }
  } catch (e) {
    console.error("Сетевая ошибка при добавлении в избранное:", e);
    alert("Не удалось сохранить в избранное. Проверьте соединение с сервером.");
  }
}

// --- КАРТА ---

onMounted(() => {
  if (isInitialized.value) return;

  ymaps.ready(async () => {
    // Сначала загружаем ID избранных мест, чтобы знать, как красить звезды
    await fetchDbFavorites();

    myMap = new ymaps.Map("map", {
      center: [47.24, 39.71],
      zoom: 11,
      controls: ['zoomControl', 'typeSelector']
    });

    // Коллекции для фильтрации
    const collections = {
      museums: new ymaps.GeoObjectCollection(null, { preset: 'islands#redLeisureIcon' }),
      parks: new ymaps.GeoObjectCollection(null, { preset: 'islands#greenParkIcon' }),
      embankments: new ymaps.GeoObjectCollection(null, { preset: 'islands#blueWaterParkIcon' })
    };

    Object.values(collections).forEach(col => myMap.geoObjects.add(col));

    // Функция отрисовки
    const renderPlaces = (data, collection) => {
      data.forEach(item => {
        const placeId = item.place.value;
        const match = item.coord.value.match(/Point\(([-0-9.]+) ([-0-9.]+)\)/);
        if (!match) return;

        const isFav = dbFavoritesIds.value.has(placeId);
        const starColor = isFav ? '#ffc107' : '#ccc';

        const html = `
          <div style="max-width: 200px; font-family: sans-serif;">
            <div style="display: flex; justify-content: space-between;">
              <strong style="font-size: 14px;">${item.placeLabel.value}</strong>
              <span class="favorite-star" data-id="${placeId}" 
                    style="cursor: pointer; font-size: 20px; color: ${starColor};">★</span>
            </div>
            ${item.image ? `<img src="${item.image.value}" style="width:100%; margin-top:8px; border-radius:4px;"/>` : ''}
          </div>`;

        const placemark = new ymaps.Placemark(
          [parseFloat(match[2]), parseFloat(match[1])],
          { balloonContent: html }
        );
        collection.add(placemark);
      });
    };

    // Настройка фильтров (ListBox)
    const createMenuItem = (label, collection) => {
      const item = new ymaps.control.ListBoxItem({ data: { content: label }, state: { selected: true }});
      item.events.add('click', () => {
        item.isSelected() ? myMap.geoObjects.remove(collection) : myMap.geoObjects.add(collection);
      });
      return item;
    };

    const listBox = new ymaps.control.ListBox({
      data: { content: 'Категории' },
      items: [
        createMenuItem('Музеи', collections.museums),
        createMenuItem('Парки', collections.parks),
        createMenuItem('Набережные', collections.embankments)
      ],
      options: { float: 'right' }
    });
    myMap.controls.add(listBox);

    // Обработка клика по звезде (Делегирование)
    document.addEventListener('click', async (e) => {
      const starBtn = e.target.closest('.favorite-star');
      if (starBtn) {
        e.stopPropagation();
        const placeId = starBtn.getAttribute('data-id');
        const allData = [...museumsData, ...parksData, ...embankmentsData];
        const place = allData.find(p => p.place.value === placeId);
        if (place) await toggleFavorite(place, starBtn);
      }
    });

    // Загрузка данных
    const sleep = (ms) => new Promise(res => setTimeout(res, ms));
    
    try {
      museumsData = await loadPlacesFromWikidata('Q33506');
      renderPlaces(museumsData, collections.museums);
      await sleep(600); 

      parksData = await loadPlacesFromWikidata('Q11742');
      renderPlaces(parksData, collections.parks);
      await sleep(600);

      embankmentsData = await loadPlacesFromWikidata('Q862454');
      renderPlaces(embankmentsData, collections.embankments);

      isInitialized.value = true;
    } catch (err) {
      console.error("Ошибка данных:", err);
    }
  });
});
</script>