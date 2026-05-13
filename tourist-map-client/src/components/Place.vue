<template>
  <div class="container mt-5" v-if="place">
    <nav aria-label="breadcrumb">
      <ol class="breadcrumb">
        <li class="breadcrumb-item active">{{ place.label }}</li>
      </ol>
    </nav>

    <div class="row">
      <div class="col-md-6">
        <img :src="place.image" class="img-fluid rounded shadow" :alt="place.label">
      </div>
      <div class="col-md-6">
        <h1 class="fw-bold">{{ place.label }}</h1>
        <p class="text-muted">{{ place.description }}</p>
        <hr>
        <ul class="list-unstyled">
          <li><strong>Регион:</strong> {{ place.region }}</li>
          <li><strong>Координаты:</strong> {{ place.coord }}</li>
          <li v-if="place.website">
            <strong>Сайт:</strong> <a :href="place.website" target="_blank">Перейти</a>
          </li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script setup>
    import { ref, onMounted } from 'vue';
    import { useRoute } from 'vue-router';

    const route = useRoute();
    const place = ref(null);

    const fetchFullInfo = async (qid) => {
    const query = `
        SELECT ?label ?description ?image ?coord ?website WHERE {
        BIND(wd:${qid} AS ?item)
        ?item rdfs:label ?label.
        OPTIONAL { ?item schema:description ?description. }
        OPTIONAL { ?item wdt:P18 ?image. }
        OPTIONAL { ?item wdt:P625 ?coord. }
        OPTIONAL { ?item wdt:P856 ?website. }
        FILTER(LANG(?label) = "ru")
        FILTER(LANG(?description) = "ru")
        } LIMIT 1`;
    };

    onMounted(() => {
        fetchFullInfo(route.params.id);
    });
</script>