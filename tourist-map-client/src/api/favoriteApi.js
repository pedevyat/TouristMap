// Функция для получения CSRF-токена из куки
export function getCookie(name) {
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
}

/**
 * Отправляет запрос на добавление/удаление места из избранного в Django
 * @param {Object} place - Объект места из Wikidata
 * @returns {Promise<Object>} - Результат ответа сервера ({ status: 'added'|'removed' })
 */
export async function sendToggleFavoriteRequest(place) {
  const cityName = place.cityLabel ? place.cityLabel.value : "Неизвестно";

  const response = await fetch('/api/toggle-favorite/', {
    method: 'POST',
    headers: { 
      'Content-Type': 'application/json', 
      'X-CSRFToken': getCookie('csrftoken') 
    },
    credentials: 'include',
    body: JSON.stringify({
      place_id: place.place.value,
      title: place.placeLabel.value,
      image_url: place.image ? place.image.value : null,
      coordinate: place.coord.value,
      city: cityName
    })
  });

  // Возвращаем объект с ответом и статусом, чтобы компонент обработал ошибки или редирект
  return {
    ok: response.ok,
    status: response.status,
    data: await response.json()
  };
}