<template>
  <div id="map" class="w-100 h-100"></div>
</template>

<script setup>
import { onMounted } from 'vue';

async function loadMuseumsFromWikidata() {
  const query = `
    SELECT ?museum ?museumLabel ?coord WHERE {
      ?museum wdt:P31/wdt:P279* wd:Q33506.
      ?museum wdt:P17 wd:Q159.
      ?museum wdt:P625 ?coord.
      SERVICE wikibase:label { bd:serviceParam wikibase:language "ru,en". }
    }
  `;

  const url = "https://query.wikidata.org/sparql?format=json&query=" + encodeURIComponent(query);

  const response = await fetch(url, {
    headers: { "Accept": "application/sparql-results+json" }
  });

  const data = await response.json();
  return data.results.bindings;
}

onMounted(() => {
  ymaps.ready(async () => {
    const myMap = new ymaps.Map("map", {
      center: [55.76, 37.64],
      zoom: 4,
      controls: ['zoomControl', 'typeSelector']
    });

    const museums = await loadMuseumsFromWikidata();

    museums.forEach(item => {
      const name = item.museumLabel.value;
      const coordStr = item.coord.value; // "Point(30.3125 59.9398)"

      // Парсим координаты
      const match = coordStr.match(/Point\(([-0-9.]+) ([-0-9.]+)\)/);
      if (!match) return;

      const lon = parseFloat(match[1]);
      const lat = parseFloat(match[2]);

      const placemark = new ymaps.Placemark(
        [lat, lon],
        { balloonContent: `<strong>${name}</strong>` },
        { preset: 'islands#blueMuseumIcon' }
      );

      myMap.geoObjects.add(placemark);
    });
  });
});
</script>

<style scoped>
#map {
  background-color: #e5e3df;
}
</style>
