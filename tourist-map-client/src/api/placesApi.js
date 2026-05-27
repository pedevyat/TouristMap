const BASE_URL = 'http://127.0.0.1:8000/api';

/**
 * Универсальный обработчик ответа от сервера
 */
async function handleResponse(response) {
  if (response.status === 429) {
    console.warn("Превышен лимит запросов к серверу (Rate Limit).");
    return [];
  }
  
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.error || `Ошибка сервера: ${response.status}`);
  }
  
  return await response.json();
}

export const placesApi = {
  /**
   * Получить достопримечательности по QID категории (для MapView)
   * @param {string} classQID - Идентификатор категории в Wikidata (напр. Q11742)
   * @returns {Promise<Array>} Список объектов
   */
  async getByCategory(classQID) {
    try {
      const response = await fetch(`${BASE_URL}/wikidata-places/?classQID=${classQID}`, {
        method: 'GET',
        credentials: 'include' // Если в будущем понадобится проверять сессию или подмешивать статус избранного прямо на сервере
      });
      return await handleResponse(response);
    } catch (error) {
      console.error(`Ошибка при получении категории ${classQID}:`, error);
      return []; // Возвращаем пустой массив, чтобы фронтенд не падал
    }
  },

  /**
   * Поиск мест по текстовому запросу (город или конкретное название объекта для SelectionView)
   * @param {string} queryText - Название города или объекта (напр. "Щепкинский лес")
   * @returns {Promise<Array>} Список найденных объектов
   */
  async searchPlaces(queryText) {
    if (!queryText.trim()) return [];
    
    try {
      const params = new URLSearchParams({ query: queryText.trim() });
      const response = await fetch(`${BASE_URL}/places/?${params}`, {
        method: 'GET',
        credentials: 'include'
      });
      return await handleResponse(response);
    } catch (error) {
      console.error(`Ошибка при поиске объектов по запросу "${queryText}":`, error);
      return [];
    }
  }
};