/**
 * Base HTTP API client with JSON parsing and error handling.
 */

export class ApiClient {
    /**
     * Generic GET isteği gönderir.
     * @param {string} endpoint - API url rotası
     * @param {object} params - Query parametreleri
     */
    static async get(endpoint, params = {}) {
        const url = new URL(endpoint, window.location.origin);
        Object.keys(params).forEach(key => url.searchParams.append(key, params[key]));

        try {
            const response = await fetch(url.toString(), {
                method: 'GET',
                headers: { 'Accept': 'application/json' }
            });
            return await this._handleResponse(response);
        } catch (error) {
            console.error(`API GET Hatası [${endpoint}]:`, error);
            throw error;
        }
    }

    /**
     * Generic POST isteği gönderir.
     * @param {string} endpoint - API url rotası
     * @param {object} data - JSON gövdesi
     */
    static async post(endpoint, data = {}) {
        try {
            const response = await fetch(endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                body: JSON.stringify(data)
            });
            return await this._handleResponse(response);
        } catch (error) {
            console.error(`API POST Hatası [${endpoint}]:`, error);
            throw error;
        }
    }

    /**
     * Generic DELETE isteği gönderir.
     * @param {string} endpoint - API url rotası
     */
    static async delete(endpoint) {
        try {
            const response = await fetch(endpoint, {
                method: 'DELETE',
                headers: {
                    'Accept': 'application/json'
                }
            });
            return await this._handleResponse(response);
        } catch (error) {
            console.error(`API DELETE Hatası [${endpoint}]:`, error);
            throw error;
        }
    }

    /**
     * Sunucu yanıtını inceler ve uygun JSON veya hata nesnesi fırlatır.
     * @private
     */
    static async _handleResponse(response) {
        const data = await response.json();
        if (!response.ok) {
            const errorMsg = data.message || `HTTP ${response.status} Hatası`;
            throw new Error(errorMsg);
        }
        return data;
    }
}
