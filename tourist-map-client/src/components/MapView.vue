<template>
  <div id="map" class="w-100 h-100"></div>
</template>

<script setup>
import { onMounted } from 'vue';

async function loadMuseumsFromWikidata() {
  const query = `
    SELECT ?museum ?museumLabel ?coord ?image WHERE {
      ?museum wdt:P31/wdt:P279* wd:Q33506.
      ?museum wdt:P17 wd:Q159.
      ?museum wdt:P625 ?coord.
      OPTIONAL { ?museum wdt:P18 ?image. }
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

    // --- ДОБАВЛЕНИЕ ПЕРЕКЛЮЧАТЕЛЯ КАТЕГОРИЙ ---
    const categoryListBox = new ymaps.control.ListBox({
      data: {
        content: 'Категории',
        image: ''
      },
      items: [
        new ymaps.control.ListBoxItem({data: {content: 'Музеи'}, state: {selected: true}}),
        new ymaps.control.ListBoxItem({data: {content: 'Парки'}, state: {selected: false}}),
      ],
      options: {
        // Позиционируем справа, чтобы было рядом со слоями
        float: 'right',
        // Отступ, чтобы не сливалось со слоями
        floatIndex: 10
      }
    });

    myMap.controls.add(categoryListBox);
    // ------------------------------------------

    const museums = await loadMuseumsFromWikidata();

    museums.forEach(item => {
      const name = item.museumLabel.value;
      const coordStr = item.coord.value;
      const imageUrl = item.image ? item.image.value : null;

      const match = coordStr.match(/Point\(([-0-9.]+) ([-0-9.]+)\)/);
      if (!match) return;

      const lon = parseFloat(match[1]);
      const lat = parseFloat(match[2]);

      let balloonHTML = `<div style="max-width: 200px;"><strong>${name}</strong>`;
      if (imageUrl) {
          balloonHTML += `<br><img src="${imageUrl}" class="balloon-img" style="width: 100%; height: auto; margin-top: 8px; border-radius: 4px;"/>`;
      }
      balloonHTML += `</div>`;

      const placemark = new ymaps.Placemark(
        [lat, lon],
        { balloonContent: balloonHTML },
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
:deep(.balloon-img) {
    background: url('https://i.gifer.com/ZKZg.gif') center center no-repeat;
    background-size: 30px;
    min-height: 100px;
    display: block;
}
</style>