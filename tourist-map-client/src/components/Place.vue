<template>
  <div class="container mt-5" v-if="place">
    <div class="row d-flex justify-content-between">
      <div class="col-md-6">
        <h1 class="fw-bold text-black">{{ place.label }}</h1>
        <p class="text-muted">{{ place.description }}</p>
        <li v-if="place.wikipedia">
            <a :href="place.wikipedia" target="_blank" rel="noopener noreferrer">
              <strong>Подробнее в Википедии</strong>
            </a>
        </li>
        <hr>
        <ul class="list-unstyled text-black">
          <li><strong>Город/регион:</strong> {{ place.city }}</li>
          <li><strong>Координаты:</strong> {{ place.coord }}</li>
          <li v-if="place.website">
            <strong>Сайт:</strong> <a :href="place.website" target="_blank">Перейти</a>
          </li>
        </ul>
      </div>
      <div class="col-md-6">
        <img :src="place.image" class="img-fluid rounded shadow" :alt="place.label">
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRoute } from 'vue-router';

const route = useRoute();
const place = ref(null);
const isLoading = ref(true);

const fetchWikipediaExtract = async (wikiUrl) => {
  try {
    const title = decodeURIComponent(wikiUrl.split('/wiki/').pop());
  
    // exintro=1 "только введение", explaintext=1 убирает HTML-теги
    const apiUrl = `https://ru.wikipedia.org/w/api.php?action=query&format=json&prop=extracts&exintro=1&explaintext=1&titles=${title}&origin=*`;
    
    const response = await fetch(apiUrl);
    if (!response.ok) return null;
    
    const data = await response.json();
    const pages = data.query.pages;
    const pageId = Object.keys(pages)[0];
    
    if (pageId === '-1') 
      return null; // Статья не найдена
    
    const fullExtract = pages[pageId].extract;
    const firstParagraph = fullExtract.split('\n')[0];
    return firstParagraph || null;
  } catch (error) {
    console.error("Не удалось загрузить текст из Википедии:", error);
    return null;
  }
};

const fetchFullInfo = async (qid) => {
  isLoading.value = true;
  const query = `
    SELECT ?label ?description ?image ?coord ?website ?cityLabel ?wikipedia WHERE {
      BIND(wd:${qid} AS ?item)
      ?item rdfs:label ?label.

      OPTIONAL {
        ?wikipedia schema:about ?item ;
                   schema:inLanguage "ru" ;
                   schema:isPartOf <https://ru.wikipedia.org/> .
      }
      
      OPTIONAL { ?item schema:description ?description. FILTER(LANG(?description) = "ru") }
      OPTIONAL { ?item wdt:P18 ?image. }
      OPTIONAL { ?item wdt:P625 ?coord. }
      OPTIONAL { ?item wdt:P856 ?website. }
      OPTIONAL { ?item wdt:P131 ?city. }
      
      FILTER(LANG(?label) = "ru")
      SERVICE wikibase:label { bd:serviceParam wikibase:language "ru,en". }
    } LIMIT 1`;

  const url = "https://query.wikidata.org/sparql";
  const params = new URLSearchParams({ query: query, format: 'json' });

  try {
    const response = await fetch(`${url}?${params}`);
    if (!response.ok) throw new Error("Ошибка при запросе к Wikidata");
    
    const data = await response.json();
    const results = data.results.bindings;

    if (results.length > 0) {
      const res = results[0];
      let finalDescription = res.description?.value || "";
      const wikiUrl = res.wikipedia?.value || null;
      if (wikiUrl) {
        const wikiExtract = await fetchWikipediaExtract(wikiUrl);
        if (wikiExtract) {
          finalDescription = wikiExtract;
        }
      }
      place.value = {
        label: res.label?.value || "Без названия",
        description: finalDescription || "Описание отсутствует",
        image: res.image?.value,
        coord: res.coord?.value || "Не указаны",
        city: res.cityLabel?.value || "Неизвестно",
        website: res.website?.value || null,
        wikipedia: res.wikipedia?.value || null
      };
    } else {
      console.error("Объект не найден в Wikidata");
    }
  } catch (error) {
    console.error("Ошибка загрузки полной информации об объекте:", error);
  } finally {
    isLoading.value = false;
  }
};

onMounted(() => {
  if (route.params.id) {
    fetchFullInfo(route.params.id);
  }
});
</script>

<style>

</style>