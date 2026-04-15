<template>
  <div id="map" class="w-100 h-100"></div>
</template>

<script setup>
import { onMounted } from 'vue';

onMounted(() => {
  ymaps.ready(() => {
    const myMap = new ymaps.Map("map", {
      center: [55.76, 37.64], // Москва
      zoom: 10,
      controls: ['zoomControl', 'typeSelector', 'fullscreenControl']
    });
    
    // TODO
    // Сюда потом добавим загрузку меток из Django API
  });
});
</script>

<style scoped>
#map {
  background-color: #e5e3df; /* Цвет фона пока карта грузится */
}
</style>