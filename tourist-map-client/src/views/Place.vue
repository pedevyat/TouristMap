<template>
  <div class="scroll-container">
    <div class="container mt-5" v-if="place">
      <div class="row d-flex justify-content-between">
        <div class="col-md-6">
          <h1 class="fw-bold text-black d-flex align-items-center">
            {{ place.label }}
            <span class="favorite-star ms-3" 
                  @click="toggleFavorite"
                  :style="{ cursor: 'pointer', fontSize: '32px', color: isFavorite ? '#ffc107' : '#ccc' }"
                  title="Добавить в избранное">
              ★
            </span>
          </h1>
          <p class="text-muted">{{ place.description }}</p>
          <li v-if="place.wikipedia">
              <a :href="place.wikipedia" target="_blank" rel="noopener noreferrer">
                <strong>Подробнее в Википедии</strong>
              </a>
          </li>
          <div v-if="isAuthenticated" class="mt-3 mb-2 rating-interactive-block">
            <strong class="text-black me-2">Оцените место:</strong>
            <span v-for="star in 5" 
                  :key="star" 
                  @click="ratePlace(star)" 
                  style="cursor: pointer; font-size: 26px; transition: color 0.15s ease-in-out;"
                  :style="{ color: star <= userRating ? '#ffc107' : '#ccc' }"
                  :title="'Поставить ' + star + ' из 5'">
              ★
            </span>
          </div>
          <hr>
          <ul class="list-unstyled text-black">
            <li><strong>Город/регион:</strong> {{ place.city }}</li>
            <li><strong>Координаты:</strong> {{ place.coord }}</li>
            <li class="mt-1 mb-1">
              <strong>Рейтинг: </strong>  
              <span class="fw-bold"> {{ averageRating > 0 ? averageRating.toFixed(1) : '0.0' }}</span> 
              <span class="text-muted small"> ({{ reviewCount }})</span>
            </li>
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
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router'; 
import { sendToggleFavoriteRequest } from '@/api/favoriteApi.js'; 

const route = useRoute();
const router = useRouter(); 
const place = ref(null);
const isLoading = ref(true);
const isAuthenticated = ref(false);
const isFavorite = ref(false);
const averageRating = ref(0.0);
const reviewCount = ref(0);
const userRating = ref(0);

const getCookie = (name) => {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === (name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
};

// Загрузка статистики рейтинга из бэкенда
const fetchRatingData = async (qid) => {
  try {
    const response = await fetch(`http://127.0.0.1:8000/api/places/rating/?qid=${qid}`, {
      credentials: 'include'
    });
    if (response.ok) {
      const data = await response.json();
      averageRating.value = data.average_rating;
      reviewCount.value = data.review_count;
      userRating.value = data.user_rating; // Присвоит 0, если пользователь не оценивал
    }
  } catch (e) {
    console.error("Не удалось загрузить данные рейтинга:", e);
  }
};

// Отправка новой или измененной оценки
const ratePlace = async (value) => {
  const qid = route.params.id;
  try {
    const response = await fetch('http://127.0.0.1:8000/api/places/rating/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken')
      },
      credentials: 'include',
      body: JSON.stringify({
        qid: qid,
        value: value,
        name: place.value?.label || ''
      })
    });

    if (response.status === 401) {
      alert("Сессия истекла. Войдите в систему заново.");
      isAuthenticated.value = false;
      router.push({ name: 'login' });
      return;
    }

    if (response.ok) {
      const data = await response.json();
      averageRating.value = data.average_rating;
      reviewCount.value = data.review_count;
      userRating.value = data.user_rating;
    }
  } catch (e) {
    console.error("Ошибка при отправке оценки:", e);
    alert("Не удалось сохранить оценку. Проверьте подключение к серверу.");
  }
};

// Проверка авторизации и наличия текущего объекта в избранном
const checkAuthAndFavoriteStatus = async (qid) => {
  try {
    const response = await fetch('http://127.0.0.1:8000/api/favorites/', {
      credentials: 'include'
    });
    
    if (response.ok) {
      const data = await response.json();
      isAuthenticated.value = true;
      
      // бэкенд хранит полный URI Wikidata
      const fullUri = `http://www.wikidata.org/entity/${qid}`;
      isFavorite.value = data.some(item => item.id === fullUri || item.id === qid);
    } else if (response.status === 401 || response.status === 403) {
      isAuthenticated.value = false;
      isFavorite.value = false;
    }
  } catch (e) {
    console.error("Не удалось проверить статус избранного:", e);
  }
};

// Функция переключения избранного
const toggleFavorite = async () => {
  if (!isAuthenticated.value) {
    alert("Для добавления в избранное, войдите в свой аккаунт или зарегистрируйтесь");
    router.push({ name: 'login' });
    return;
  }

  const qid = route.params.id;
  const apiPlaceParam = {
    place: { value: `http://www.wikidata.org/entity/${qid}` },
    placeLabel: { value: place.value.label },
    image: place.value.image ? { value: place.value.image } : null,
    coord: { value: place.value.coord },
    cityLabel: { value: place.value.city }
  };

  try {
    const result = await sendToggleFavoriteRequest(apiPlaceParam);

    if (result.status === 401) {
      isAuthenticated.value = false;
      isFavorite.value = false;
      alert("Сессия истекла. Пожалуйста, войдите снова");
      router.push({ name: 'login' });
      return;
    }

    if (result.ok) {
      if (result.data.status === 'added') {
        isFavorite.value = true;
      } else if (result.data.status === 'removed') {
        isFavorite.value = false;
      }
    }
  } catch (e) {
    console.error("Ошибка при изменении статуса избранного:", e);
    alert("Не удалось сохранить в избранное. Проверьте соединение с сервером");
  }
};

const fetchWikipediaExtract = async (wikiUrl) => {
  try {
    const title = decodeURIComponent(wikiUrl.split('/wiki/').pop());
    const apiUrl = `https://ru.wikipedia.org/w/api.php?action=query&format=json&prop=extracts&exintro=1&explaintext=1&titles=${title}&origin=*`;
    
    const response = await fetch(apiUrl);
    if (!response.ok) return null;
    
    const data = await response.json();
    const pages = data.query.pages;
    const pageId = Object.keys(pages)[0];
    
    if (pageId === '-1') return null;
    
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

      let formattedCoord = "";
      const rawCoord = res.coord?.value; 
      if (rawCoord) {
        const match = rawCoord.match(/Point\(([^)]+)\)/);
        if (match) {
          formattedCoord = match[1].trim().replace(/\s+/, ', ');
        } else {
          formattedCoord = rawCoord;
        }
      }

      place.value = {
        label: res.label?.value,
        description: finalDescription || "Описание отсутствует",
        image: res.image?.value,
        coord: formattedCoord,
        city: res.cityLabel?.value,
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
  const qid = route.params.id;
  if (qid) {
    fetchFullInfo(qid);
    checkAuthAndFavoriteStatus(qid); // Параллельно запрашиваем статус избранного
    fetchRatingData(qid); // загружаем данные рейтинга
  }
});
</script>

<style scoped>
.scroll-container {
  max-height: 100vh;
  overflow-y: auto;     
  overflow-x: hidden;   
}

.rating-interactive-block span:hover {
  transform: scale(1.15);
}
</style>