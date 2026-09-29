/**
 * Social feed and trader profile API endpoints.
 */

import { ApiClient } from './apiClient.js';

export const SocialApi = {
    /**
     * Topluluk akışını getirir.
     */
    async getFeed(filter = 'latest', page = 1) {
        return ApiClient.get('/api/social/feed', { filter, page });
    },

    /**
     * Yeni analiz ve strateji paylaşımı oluşturur.
     */
    async createPost(data) {
        return ApiClient.post('/api/social/post', data);
    },

    /**
     * Gönderiyi beğenir.
     */
    async likePost(postId) {
        return ApiClient.post(`/api/social/post/${postId}/like`, {});
    },

    /**
     * Gönderiye yorum ekler.
     */
    async addComment(postId, author, text) {
        return ApiClient.post(`/api/social/post/${postId}/comment`, { author, text });
    },

    /**
     * Liderlik tablosunu çeker.
     */
    async getLeaderboard() {
        return ApiClient.get('/api/social/leaderboard');
    }
};
